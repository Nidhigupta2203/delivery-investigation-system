from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.recording import (
    RecordingDetailResponse,
    RecordingInvestigationUpdate,
    SensorTimeSeriesResponse,
)
from app.services.recording_service import (
    get_media_bytes,
    get_recording,
    get_sensor_timeseries,
    update_investigation,
)

router = APIRouter()

@router.get("/{recording_id}", response_model=RecordingDetailResponse, tags=["Recordings"])
def recording_detail(recording_id: str, db: Session = Depends(get_db)):
    # FastAPI will validate UUID format; we keep string for simplicity
    try:
        rec = get_recording(db, recording_id)
    except HTTPException as e:
        raise e
    return RecordingDetailResponse.from_orm(rec)

@router.get("/{recording_id}/media", tags=["Recordings"])
def recording_media(recording_id: str, db: Session = Depends(get_db)):
    content, mime = get_media_bytes(db, recording_id)
    return StreamingResponse(iter([content]), media_type=mime)

@router.get("/{recording_id}/sensor-data", response_model=SensorTimeSeriesResponse, tags=["Recordings"])
def recording_sensor_data(recording_id: str, db: Session = Depends(get_db)):
    return get_sensor_timeseries(db, recording_id)

@router.patch(
    "/{recording_id}/investigate",
    response_model=RecordingDetailResponse,
    status_code=status.HTTP_200_OK,
    tags=["Recordings"],
)
def recording_investigate(
    recording_id: str,
    payload: RecordingInvestigationUpdate,
    db: Session = Depends(get_db),
):
    rec = update_investigation(db, recording_id, payload)
    return RecordingDetailResponse.from_orm(rec)
