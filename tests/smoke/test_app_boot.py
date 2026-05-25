from fastapi import FastAPI


def test_fastapi_app_imports_without_server(isolated_import):
    main_module = isolated_import("app.main")

    assert hasattr(main_module, "app")
    assert isinstance(main_module.app, FastAPI)

