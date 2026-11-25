"""M4 owns API wiring checks and the eventual three-edge integration tests."""

from edge.main import app


def test_scaffold_registers_cdn_routes():
    # Exercise the app import and verify that FastAPI registers the agreed API.
    assert set(app.openapi()["paths"]) == {
        "/",
        "/api/gallery",
        "/media/{id}/v{version}",
        "/internal/media/{id}/v{version}",
        "/internal/status",
        "/admin/status",
        "/admin/publish",
    }
