"""M2 owns local storage, peer and origin lookups, and byte verification."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from edge.models import ImageRecord

CacheSource = Literal["local", "peer", "origin"]


@dataclass(frozen=True)
class ResolvedImage:
    """A verified local file and the source used to resolve the request."""

    path: Path
    source: CacheSource


class ImageCache:
    """Interface for public image resolution and cache-only peer requests."""

    def resolve(self, record: ImageRecord) -> ResolvedImage | None:
        """Try the local cache, each peer, and then the origin."""
        # Verify received bytes before storing them. Return a miss if all
        # sources fail to supply a valid copy.
        raise NotImplementedError

    def get_local_only(self, image_id: str, version: int) -> Path | None:
        """Return a verified local copy of this exact version or a miss."""
        # Peer requests make zero outbound calls.
        raise NotImplementedError
