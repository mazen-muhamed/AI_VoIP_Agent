from uuid import UUID
from fastapi import APIRouter, Depends, Response, status
from app.core.exceptions import ForbiddenError
from app.modules.calls.dependencies import get_calls_service, verify_ingest_key
from app.modules.calls.schemas import CallEventCreate, CallEventResponse
from app.modules.calls.service import CallsService


router = APIRouter(prefix="/calls", tags=["Calls"])

@router.post("/events", response_model=CallEventResponse)
async def ingest_call_event(
    event: CallEventCreate,
    response: Response,
    allowed_tenant_id: UUID = Depends(verify_ingest_key),
    service: CallsService = Depends(get_calls_service),
) -> CallEventResponse:
    if event.tenant_id != allowed_tenant_id:
        raise ForbiddenError("Ingest key is not authorized for this tenant")

    call, created = await service.process_event(event, allowed_tenant_id=allowed_tenant_id,)

    response.status_code = (status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    return CallEventResponse(
        call_uuid=call.call_uuid,
        created=created,
    )