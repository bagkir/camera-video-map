import uuid

from fastapi import APIRouter, Query

from src.api.v1.dependencies import AnalysisServiceDep, CameraServiceDep, CurrentUserDep
from src.api.v1.schemas.analysis import AnalysisListItem
from src.api.v1.schemas.camera import CameraListItem, GeoJSONFeatureCollection
from src.core.exceptions import NotFoundException
from src.data.models import AnalysisStatus, AnalysisType

router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.get("/geojson", response_model=GeoJSONFeatureCollection)
async def get_cameras_geojson(_: CurrentUserDep, camera_service: CameraServiceDep):
    return await camera_service.get_geojson()


@router.get("", response_model=list[CameraListItem])
async def list_cameras(
    _: CurrentUserDep,
    camera_service: CameraServiceDep,
    search: str | None = None,
    videos_from: int | None = Query(None, ge=0),
    videos_to: int | None = Query(None, ge=0),
    model: str | None = None,
    camera_type: str | None = None,
    camera_class: str | None = None,
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
):
    """Фильтруемый список для боковой панели (ТЗ 1.3.4), отдельно от карты."""
    rows = await camera_service.list_filtered(
        search=search,
        videos_from=videos_from,
        videos_to=videos_to,
        model=model,
        camera_type=camera_type,
        camera_class=camera_class,
        limit=limit,
        offset=offset,
    )
    return [
        CameraListItem(
            id=camera.id,
            camera_id=camera.camera_id,
            camera_name=camera.camera_name,
            camera_place=camera.camera_place,
            model=camera.model,
            camera_type=camera.camera_type,
            camera_class=camera.camera_class,
            video_count=video_count,
        )
        for camera, video_count in rows
    ]


@router.get("/{camera_id}", response_model=CameraListItem)
async def get_camera(
    _: CurrentUserDep,
    camera_id: uuid.UUID,
    camera_service: CameraServiceDep,
):
    row = await camera_service.get_by_id_with_count(camera_id)
    if row is None:
        raise NotFoundException("Camera", camera_id)
    camera, video_count = row
    return CameraListItem(
        id=camera.id,
        camera_id=camera.camera_id,
        camera_name=camera.camera_name,
        camera_place=camera.camera_place,
        model=camera.model,
        camera_type=camera.camera_type,
        camera_class=camera.camera_class,
        video_count=video_count,
    )


@router.get("/{camera_id}/analyses", response_model=list[AnalysisListItem])
async def list_camera_analyses(
    _: CurrentUserDep,
    camera_id: uuid.UUID,
    analysis_service: AnalysisServiceDep,
    analysis_type: AnalysisType | None = None,
    status: AnalysisStatus | None = None,
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
):
    analyses = await analysis_service.list_by_camera(
        camera_id=camera_id,
        analysis_type=analysis_type,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [
        AnalysisListItem(
            id=a.id,
            video_id=a.video_id,
            video_name=a.video.name,
            analysis_type=a.analysis_type,
            status=a.status,
            result=a.result,
            created_at=a.created_at,
            finished_at=a.finished_at,
        )
        for a in analyses
    ]
