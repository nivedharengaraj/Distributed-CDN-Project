"""Image metadata and the HTTP payloads shared by the edge components."""

from pydantic import BaseModel, Field


class ImageRecord(BaseModel):
    """Current metadata for one immutable image version."""

    # Validate safe IDs and relative object paths before using them on disk.
    id: str
    title: str
    version: int = Field(gt=0)
    content_type: str
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    origin_key: str


class PublishRequest(ImageRecord):
    """Proposed version and the version the publisher expects to replace."""

    # The field is required. Explicit null means this is a new image.
    expected_version: int | None = Field(gt=0)


class PublishResponse(BaseModel):
    """Result of a publication confirmed as applied by the catalog."""

    id: str
    version: int
    revision: int


class GalleryImage(BaseModel):
    """Current image entry and its exact-version URL."""

    id: str
    title: str
    version: int
    url: str


class GalleryResponse(BaseModel):
    """One edge's locally applied catalog snapshot for the browser."""

    node_id: str
    revision: int
    images: list[GalleryImage]


class InternalStatusResponse(BaseModel):
    """Identity, readiness, and catalog revision for peer checks."""

    node_id: str
    ready: bool
    revision: int


class AdminStatusResponse(BaseModel):
    """Catalog and Raft status used by the publisher to identify the leader."""

    node_id: str
    revision: int
    role: str | None
    leader_node_id: str | None = None
