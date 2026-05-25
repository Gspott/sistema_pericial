from fastapi.testclient import TestClient


ALLOWED_BASIC_STATUSES = {200, 302, 303, 401, 403}


def test_basic_get_routes_do_not_error(isolated_import):
    main_module = isolated_import("app.main")
    client = TestClient(main_module.app)

    for path in ("/", "/login", "/ping"):
        response = client.get(path, follow_redirects=False)
        assert response.status_code in ALLOWED_BASIC_STATUSES

