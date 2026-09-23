#Pydantic schemas for authentication

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class TenantResponse(BaseModel):
    #Tenant in response

    id: UUID
    name: str
    contact_email: Optional[str] = None
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class TenantCreate(BaseModel):
    #Create tenant request

    name: str = Field(..., min_length=1, max_length=100)
    contact_email: Optional[EmailStr] = None


class TenantUpdate(BaseModel):
    #Update tenant Request

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    contact_email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

    ## -- Permissions -- ##

class PermissionResponse(BaseModel):
    #Permission in response

    id: UUID
    name: str
    resource: str
    action: str
    description: Optional[str] = None
    model_config = {"from_attributes": True}


    ## --- Role --- ##

class RoleResponse(BaseModel):
    #Role in response

    id: UUID
    name: str
    description: Optional[str] = None
    tenant_id: Optional[UUID] = None
    permissions: List[PermissionResponse] = []
    model_config = {"from_attributes": True}


    ## -- User -- ##

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: Optional[EmailStr] = None
    full_name: str
    tenant_id: Optional[UUID] = None
    is_active: bool
    is_superuser: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    roles: List[RoleResponse] = []
    model_config = {"from_attributes": True}


        ## --- Auth --- ##

class LoginRequest(BaseModel):
    #Login request payload

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    #Token pair response

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  


class RefreshRequest(BaseModel):
    #Refresh token request

    refresh_token: str


class LogoutRequest(BaseModel):
    #Logout request

    refresh_token: Optional[str] = None

    ## --- User management --- ##

class UserCreate(BaseModel):
    #Create user (for Adminsss)

    username: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=100)
    tenant_id: Optional[UUID] = None
    is_active: bool = True
    role_ids: List[UUID] = []


class UserUpdate(BaseModel):
    #Update user request

    username: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    tenant_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    role_ids: Optional[List[UUID]] = None


class PasswordChange(BaseModel):
    #Password change request

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)