"""M4 owns the FastAPI routes and wiring between the edge components."""

from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, status

from edge.models import (
    AdminStatusResponse,
    GalleryResponse,
    InternalStatusResponse,
    PublishRequest,
    PublishResponse,
)

app = FastAPI(title="Distributed CDN")
ImageVersion = Annotated[int, Path(gt=0)]

# Wire configuration, the catalog, and the cache into the app lifespan.


@app.get("/")
def gallery_page():
    """Return the gallery shell from frontend/index.html."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@app.get("/api/gallery", response_model=GalleryResponse)
def gallery():
    """Build a gallery response from one local catalog snapshot."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@app.get("/media/{id}/v{version}")
def media(id: str, version: ImageVersion):
    """Check the exact version against the catalog before resolving bytes."""
    # Map a catalog miss to 404 and exhausted cache sources to 503.
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@app.get("/internal/media/{id}/v{version}")
def peer_media(id: str, version: ImageVersion):
    """Serve a local cache entry directly or return a cache miss."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@app.get("/internal/status", response_model=InternalStatusResponse)
def peer_status():
    """Report local readiness and the applied catalog revision."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@app.get("/admin/status", response_model=AdminStatusResponse)
def admin_status():
    """Report the local Raft role and leader ID for publisher routing."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@app.post("/admin/publish", response_model=PublishResponse)
def publish(request: PublishRequest):
    """Submit a metadata change and confirm its applied result."""
    # Map conflicts and the two publication failure outcomes to the HTTP
    # statuses and error codes in docs/implementation.md.
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
