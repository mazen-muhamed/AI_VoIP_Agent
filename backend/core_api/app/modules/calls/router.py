from fastapi import APIRouter, Depends, Response, status
from app.modules.calls.dependencies import get_calls_service, verify_ingest_key
from app.modules.calls.schemas import CallEventCreate, CallEventResponse
from app.modules.calls.service import CallsService


router = APIRouter(prefix="/calls", tags=["Calls"])


@router.post("/events", response_model=CallEventResponse, dependencies=[Depends(verify_ingest_key)],)
async def ingest_call_event(event: CallEventCreate, response: Response, service: CallsService = Depends(get_calls_service),) -> CallEventResponse:
    call, created = await service.process_event(event)

    if created:
        response.status_code = status.HTTP_201_CREATED
    else:
        response.status_code = status.HTTP_200_OK

    return CallEventResponse(
        call_uuid=call.call_uuid,
        created=created,
    )