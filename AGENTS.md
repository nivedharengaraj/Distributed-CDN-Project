# Distributed CDN project instructions

## Scope and ownership

- Build the Scope 1 image-gallery prototype. Run the same FastAPI edge app on three nodes, with a local filesystem cache and one PySyncObj/Raft participant per node. Use the [implementation agreements](docs/implementation.md) for API, model, and component contracts.
- Keep changes focused on the requested component. If an interface needs to change, identify the affected members and update the agreed contract with the code.

| Lead | Responsibility | Main files |
| --- | --- | --- |
| M1 | Configuration, origin, startup, and Nginx | `edge/config.py`, `infra/`, `scripts/` |
| M2 | Image cache, peer and origin retrieval, and byte verification | `edge/cache.py`, `tests/test_cache.py` |
| M3 | Shared schemas, catalog, and Raft publication | `edge/models.py`, `edge/catalog.py`, `tests/test_catalog.py` |
| M4 | FastAPI routes, gallery UI, and integration | `edge/main.py`, `frontend/`, `tests/test_integration.py` |

## Invariants

- Replicate catalog metadata through Raft. Deliver image bytes through the cache and origin. Stage the complete immutable object before submitting its metadata. Check the expected version when the command is applied, and increment the revision only after a successful applied change.
- A gallery response reflects one local catalog snapshot. The public media route returns `404` if the requested version is absent from that edge's local catalog. For a known version, try the local cache, then each peer as needed, then the origin. Peer media requests are cache-only. Verify fetched bytes against the recorded size and SHA-256 before storing or serving them.
- Read node identity and endpoints from configuration. Use `infra/cluster.example.json` for examples and the ignored `infra/cluster.local.json` for deployment values. Keep credentials, machine-specific settings, logs, and runtime state out of Git.

## Development and verification

- Follow the [team setup guide](docs/team-setup-guide.md). Start feature work from current `main`, work on a feature branch, and share changes through a pull request. Keep code compatible with Python 3.10 and use the dependencies in `requirements.txt`. The VM baseline is Python 3.10.12.
- Run `python -m pytest -q` from the repository root using the project virtual environment. Use fixtures or fakes for unfinished components. Report which checks passed and which behavior still needs validation on the VMs.
- Coordinate shared VM runs with the team. Use one agreed commit across all three nodes and keep cache and Raft state separate per node. Use your own account and checkout for individual VM work.
- Record AI assistance for the course submission as required by the course.
