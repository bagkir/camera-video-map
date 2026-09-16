import uuid

from fastapi import APIRouter

from src.api.v1.dependencies import AnalysisServiceDep, CurrentUserDep
from src.api.v1.schemas.analysis import AnalysisOut, AnalysisRunRequest

router = APIRouter(prefix="/videos/{video_id}/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisOut, status_code=201)
async def run_analysis(
    _: CurrentUserDep,
    video_id: uuid.UUID,
    data: AnalysisRunRequest,
    analysis_service: AnalysisServiceDep,
):
    return await analysis_service.run_mock_analysis(video_id, data.analysis_type)


@router.get("", response_model=list[AnalysisOut])
async def list_analyses(
    _: CurrentUserDep,
    video_id: uuid.UUID,
    analysis_service: AnalysisServiceDep,
):
    return await analysis_service.get_by_video(video_id)
