import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "app.main",
        "app.database",
        "app.services.informe",
        "app.services.verifactu",
    ],
)
def test_critical_imports_use_isolated_environment(isolated_import, module_name):
    module = isolated_import(module_name)

    assert module is not None

