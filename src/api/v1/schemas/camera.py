import uuid

from pydantic import BaseModel


class GeoJSONGeometry(BaseModel):
    type: str = "Point"
    coordinates: list[float]


class GeoJSONProperties(BaseModel):
    id: uuid.UUID
    camera_id: str
    camera_name: str
    has_video: bool


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    properties: GeoJSONProperties
    geometry: GeoJSONGeometry


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature]


class CameraListItem(BaseModel):
    id: uuid.UUID
    camera_id: str
    camera_name: str
    camera_place: str | None
    model: str | None
    camera_type: str | None
    camera_class: str | None
    video_count: int
