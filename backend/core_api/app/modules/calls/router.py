from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.modules.auth.models import Tenant
from app.modules.calls.repository import CallsRepository
from app.modules.calls.schemas import CallEventCreate, CallResponse
from app.modules.calls.service import CallsService


router = APIRouter(prefix="/calls", tags=["Calls"])


# Create a call event and store it using the ingest API key
@router.post("/events", response_model=CallResponse, status_code=status.HTTP_200_OK,)
async def ingest_call_event(
    event: CallEventCreate,
    x_ingest_key: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    # Validate the internal ingestion key
    if x_ingest_key != settings.CALLS_INGEST_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ingest key",)

    # Verify that the tenant exists
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == event.tenant_id))
    tenant = tenant_result.scalar_one_or_none()

    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found",)

    repository = CallsRepository(db)
    service = CallsService(repository)

    try:
        # Process and upsert the call event
        call = await service.process_event(event)

        await db.commit()
        await db.refresh(call)

        return call

    except ValueError as exc:
        await db.rollback()

        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc),)

    except Exception:
        await db.rollback()
        raise