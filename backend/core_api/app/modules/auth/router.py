# API Endpoint, user login , logout , Get user by_id
# Rate Limiting per ip 
# Get Client IP get_client_ip

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.modules.auth.dependencies import (
    get_auth_service,
    get_current_active_user,
    require_superuser,
)
from app.modules.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])

def get_client_ip(request: Request) -> Optional[str]:
    # Check X-Forwared-For Only if trusted proxies configured
    if settings.TRUSTED_PROXY_CIDRS:
        forward = request.headers.get("X-Forwarded-For")
        
        if forward:
            # Take First IP (original Client)
            client_ip = forward.split(",")[0].strip()
            return client_ip
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

    # Fallback with no trusted proxy
    return request.client.host if request.client else None



@router.post('/login', response_model=TokenResponse, summary="User Login")
async def login(
    request: LoginRequest,
    req: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:

# Authenticate User & Return Access + Refresh token
# Rate limit : 5 trials per 5 mins per IP

    ip = get_client_ip(req)
    return await auth_service.login(request, ip=ip)


# Refresh Access Token. 'fromLogin' || previousRefresh
#Old Token Revoked, new issued. Reuse Detection
@router.post('/refresh', response_model=TokenResponse, summary="Refresh access token")
async def refresh(
    request: RefreshRequest,
    req: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:

    ip = get_client_ip(req)
    return await auth_service.refresh_tokens(request.refresh_token, ip=ip)


@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT, summary="User Logout")
async def logout(
    request: LogoutRequest,
    response: Response,
    req: Request,
    x_refresh_token: Optional[str] = Header(None, alias="X-Refresh-Token"),
    auth_service: AuthService = Depends(get_auth_service)
) -> None:

    refresh_token = request.refresh_token or x_refresh_token

    if not refresh_token:
        raise AuthenticationError("Refresh token required!")
    
    ip = get_client_ip(req)
    success = await auth_service.logout(refresh_token, ip=ip)
    if not success:
        raise AuthenticationError("Invalid refresh token")

@router.get('/me', response_model=UserResponse, summary="Get current user profile")
async def get_me(
    current_user: UserResponse = Depends(get_current_active_user),
) -> UserResponse:
    return current_user

# Admin only endpoints
@router.post('/users', response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create User(admin)")
async def create_user(
    request: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
    _: UserResponse = Depends(require_superuser),
) -> UserResponse:
    #Create a new user with roles (Superusers only)
    user = await auth_service.create_user(request)
    return UserResponse.model_validate(user)


@router.get('/users/{user_id}', response_model=UserResponse, summary="Get user by ID")
async def get_user(
    user_id: UUID,
    auth_service: AuthService = Depends(get_auth_service),
    _: UserResponse = Depends(require_superuser),
) -> UserResponse:
# Get user by id (Superusers only)

    user = await auth_service.get_user_profile(user_id)
    return UserResponse.model_validate(user)