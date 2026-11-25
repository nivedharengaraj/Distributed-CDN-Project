# Scope 1 implementation agreements

The prototype uses one FastAPI edge application on three university VMs. Each edge has its own filesystem cache and a locally applied PySyncObj/Raft catalog replica. Raft orders catalog metadata updates. Edges retrieve image bytes from their own cache, the other two edges, or the origin. The initial deployment puts the origin and Nginx on VM 1, subject to the VM checks below.

## Shared image and publication models

`ImageRecord` in `edge/models.py` is shared by the catalog, cache, and API. `PublishRequest` has the same fields plus the required, nullable `expected_version` field.

| Field | Contract |
| --- | --- |
| `id` | Stable image identifier used in public URLs |
| `title` | Display title |
| `version` | Positive integer identifying the image version |
| `content_type` | MIME type of the image bytes |
| `size_bytes` | Exact byte length |
| `sha256` | SHA-256 digest of the exact bytes, as a hexadecimal string |
| `origin_key` | Relative path to the immutable object under the origin's `objects/` directory |

To create an image, send `version=1` and `expected_version=null`. To replace an image, send its current version as `expected_version` and the next integer as `version`. The catalog checks the expectation when applying the replicated operation, after Raft has ordered it. If two replacement requests both expect version 1, at most one succeeds. Each successful application increments the catalog-wide `revision` once. A rejected operation leaves the revision unchanged. The revision tracks successful catalog changes across all images and is distinct from an individual image version or the Raft log index.

The publisher stages the complete object at the origin and ensures it is readable before it submits metadata to the leader's HTTP endpoint. The origin key includes both the proposed version and the digest, for example `forest/v2-<sha256>.jpg`. Two competing publishers can stage different bytes for version 2 without overwriting each other's object. The public URL stays `/media/forest/v2`, and the applied metadata selects the winning origin object.

### Example publication

An illustrative request to replace version 1 of `forest` uses the following shape. In a real request, the publisher computes the size and digest from the staged bytes.

```json
{
  "id": "forest",
  "title": "Forest",
  "version": 2,
  "expected_version": 1,
  "content_type": "image/jpeg",
  "size_bytes": 245000,
  "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "origin_key": "forest/v2-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef.jpg"
}
```

A successful response confirms application and includes the resulting revision.

```json
{"id": "forest", "version": 2, "revision": 3}
```

## Python component contracts

| Owner | Interface | Contract |
| --- | --- | --- |
| M3 · Catalog | `get_snapshot()` | Returns the locally applied revision and current image records together, so a gallery response describes one catalog state. |
| M3 · Catalog | `get_for_requested_version(image_id, version)` | Returns the record only if the requested version is current on this replica. |
| M3 · Catalog | `publish(record, expected_version)` | Reports applied success with the new revision, version conflict, temporary unavailability, or an unknown outcome. |
| M2 · Cache | `resolve(record)` | Resolves bytes from the local cache, then each peer's cache, then origin. Verifies received bytes against the record's length and SHA-256 before storing or serving them. Reports `local`, `peer`, or `origin` for a successful result. |
| M2 · Cache | `get_local_only(image_id, version)` | Returns a previously verified local copy for that exact version or a miss. Makes zero outbound requests. |
| M4 · API | Route handlers | Translate component results into HTTP responses. The public media handler looks up metadata for the exact requested version before resolving bytes. |

M2 can develop against example `ImageRecord` instances. M4 can use fake catalog and cache implementations to wire the routes. M3 will choose the PySyncObj callback integration after the feasibility test.

## HTTP contract

| Route | Response and behavior |
| --- | --- |
| `GET /` | Returns the gallery page. |
| `GET /api/gallery` | Returns `node_id`, `revision`, and `images` from the locally applied catalog. Each image has `id`, `title`, `version`, and `url`. |
| `GET /media/{id}/v{version}` | Returns the exact bytes with `Content-Type`, `X-Node-ID`, and `X-Cache-Source`. Returns `404` when the requested version is absent from the local catalog and `503` when the catalog knows the version but no source can supply valid bytes. |
| `GET /internal/media/{id}/v{version}` | Returns the exact local cached bytes or `404`. |
| `GET /internal/status` | Returns `node_id`, `ready`, and `revision` for peer checks. |
| `GET /admin/status` | Returns `node_id`, `revision`, and Raft role, plus the leader's node ID when known. The publisher uses this information to select the leader's HTTP endpoint. |
| `POST /admin/publish` | Returns `200` with `id`, `version`, and `revision` after confirmed application, `409` for a version conflict, and `422` for malformed input. Returns `503` with a machine-readable code for temporary unavailability or an unknown outcome. |

Use `publication_unavailable` when the edge knows it could not submit the request, for example when there is no known leader before submission. Use `publication_outcome_unknown` when the edge cannot confirm the outcome, for example after a timeout while awaiting application. The publisher checks the catalog before retrying. A lagging replica that has yet to show the change cannot establish that the operation failed.

### Example gallery response

```json
{
  "node_id": "edge-a",
  "revision": 3,
  "images": [
    {"id": "forest", "title": "Forest", "version": 2, "url": "/media/forest/v2"}
  ]
}
```

### Visibility across edges

The gallery reads the serving edge's local replica, so a publication can become visible on different edges at different times. A browser can get a gallery listing version 2 from Edge A and then receive a `404` for `/media/forest/v2` from Edge B while B is catching up. B never substitutes version 1. Once an edge applies version 2, the public URL for version 1 may also return `404`, even if its immutable bytes remain cached. During the demo, check that all three edges report the new revision before showing the updated gallery.

## Cluster configuration and VM checks

The cluster configuration has three entries named `edge-a`, `edge-b`, and `edge-c`. Each entry supplies a peer-reachable HTTP URL and a separate Raft address. The config also supplies the origin base URL, and `NODE_ID` selects the local entry. Each VM runs one edge worker and one Raft participant, with its own runtime directories. Nginx forwards browser requests for the page, gallery API, and public media. Peers call internal routes directly, and the publisher calls the selected leader directly.

[`infra/cluster.example.json`](../infra/cluster.example.json) shows the schema with example IP addresses. Use `infra/cluster.local.json` for deployment addresses. `origin_base_url` points to the origin HTTP root, and clients append `/objects/` and the record's `origin_key` to build the object URL.

The development baseline is Python 3.10. VM 1 reports Python 3.10.12. Record the versions on VMs 2 and 3 during setup and verify the pins in `requirements.txt` in a virtual environment on each VM.

The proposed ports are `8000` for edge HTTP, `4321` for Raft, `9000` for the origin, and `8080` for Nginx. M1 verifies the VM tools and permitted listening ports, then checks direct TCP reachability from each VM to both peers. M3 verifies the selected Python and PySyncObj combination and demonstrates one metadata operation applying on all three VMs. The VM 1 origin and Nginx are supporting processes, and the browser reaches Nginx through an SSH tunnel.
