"""M1 owns cluster configuration and each edge's local runtime settings."""

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel


class NodeAddresses(BaseModel):
    """The addresses other edges use to reach a node."""

    http_url: str
    raft_address: str


class ClusterConfig(BaseModel):
    """Shape of infra/cluster.example.json and the local VM configuration."""

    nodes: dict[str, NodeAddresses]
    origin_base_url: str


@dataclass(frozen=True)
class EdgeConfig:
    """Settings selected for one edge process."""

    node_id: str
    cluster: ClusterConfig
    http_bind_host: str
    http_bind_port: int
    cache_dir: Path
    raft_dir: Path
    log_dir: Path


def load_config() -> EdgeConfig:
    """Read cluster settings and select the local node using NODE_ID."""
    # Load the JSON path, bind settings, and node-local paths. Validate that
    # edge-a, edge-b, and edge-c are configured before starting services.
    raise NotImplementedError
