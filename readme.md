# Distributed CDN for an Image Gallery

A Distributed Systems course project that uses image delivery to demonstrate peer communication, shared state, and consensus. The Scope 1 prototype is designed to run the same FastAPI application on three edge nodes. Each edge holds a local image cache and a replica of the image catalog.

**Current status.** The repository contains the project scaffold, shared schemas, configuration templates, and a smoke test. The FastAPI routes are registered and their placeholder handlers return `501`. Cache retrieval, Raft replication, image publishing, and gallery rendering are planned implementation work.

## Architecture

- **Browser and proxy.** Nginx is the planned browser entry point. It distributes requests for the gallery page (`/`), catalog (`/api/gallery`), and versioned images (`/media/{id}/v{version}`) across the three edges.
- **Image delivery.** An edge looks for the exact requested version in its local cache, then checks the other two edges before falling back to the origin. Peer lookups are cache-only. Fetched bytes are checked against the catalog's size and SHA-256 digest before they are stored or served.
- **Catalog and publication.** PySyncObj/Raft orders metadata changes across the three edges. Image bytes stay at the origin and in edge caches. Publication stages the immutable object at the origin first, then submits its metadata to the Raft leader. A replacement must match the catalog's current version when applied. An applied change increments the catalog revision.

Each gallery response reflects the serving edge's locally applied catalog, so visibility is eventually consistent. For example, a browser can see version 2 in the gallery from Edge A and receive a temporary `404` for that exact version from Edge B while B catches up. Edge B never substitutes an older version.

## Local development

The scaffold targets **Python 3.10**. From the repository root, create a virtual environment, install the pinned dependencies, and run the test suite.

**Windows PowerShell**

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest
```

**Linux**

```bash
python3.10 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest
```

The smoke test imports the FastAPI app and checks that it registers the agreed routes.

## Repository guide

| Area | Files | Lead |
| --- | --- | --- |
| Configuration, origin, and startup | `edge/config.py`, `infra/`, `scripts/`, `origin/objects/` | M1 |
| Cache and image retrieval | `edge/cache.py`, `tests/test_cache.py` | M2 |
| Shared schemas and replicated catalog | `edge/models.py`, `edge/catalog.py`, `tests/test_catalog.py` | M3 |
| FastAPI routes, gallery, and integration | `edge/main.py`, `frontend/`, `tests/test_integration.py` | M4 |

The [implementation agreements](docs/implementation.md#shared-image-and-publication-models) describe the data models, component interfaces, and HTTP contract. The [Scope 1 scenarios](scope1_scenarios.md#6-minimal-acceptance-checklist) describe the intended demo, including catalog agreement, version updates, and local, peer, and origin retrieval. [Video support](scope2_video_extension%20%281%29.md) is an optional extension. The [large-scale architecture](scope3_global_architecture.md) is a design exercise.
