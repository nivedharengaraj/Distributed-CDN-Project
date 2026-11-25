"""M3 owns the replicated image catalog and publication results."""

from dataclasses import dataclass

from edge.models import ImageRecord, PublishResponse


@dataclass(frozen=True)
class CatalogSnapshot:
    """Current records and revision read together from one local replica."""

    revision: int
    images: tuple[ImageRecord, ...]


@dataclass(frozen=True)
class RaftStatus:
    """Local readiness and leader information exposed to route handlers."""

    ready: bool
    role: str | None
    leader_node_id: str | None


class VersionConflict(Exception):
    """The requested change conflicts with the version at application time."""


class PublicationUnavailable(Exception):
    """The edge could determine that it could not submit the publication."""


class PublicationOutcomeUnknown(Exception):
    """The edge could not confirm the outcome after attempting publication."""


class Catalog:
    """Interface for local reads and replicated metadata changes."""

    def get_snapshot(self) -> CatalogSnapshot:
        """Capture the current image records and revision in one read."""
        raise NotImplementedError

    def get_for_requested_version(
        self, image_id: str, version: int
    ) -> ImageRecord | None:
        """Return the record if the requested version is current locally."""
        raise NotImplementedError

    def publish(
        self, record: ImageRecord, expected_version: int | None
    ) -> PublishResponse:
        """Return applied success or raise the corresponding publication error."""
        # Check the expected version at application time and increment the
        # catalog revision only for successful changes.
        raise NotImplementedError

    def get_raft_status(self) -> RaftStatus:
        """Provide readiness and leader information from the Raft participant."""
        raise NotImplementedError
