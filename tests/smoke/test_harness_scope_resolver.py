from scripts.harness_scope_resolver import required_scope_for_files, resolve_scope


def test_scope_resolver_docs_only():
    required, reasons = required_scope_for_files(
        ["docs/ux.md", "docs/harness/TASK_PACKS/README.md"]
    )
    assert required == "docs"
    assert reasons == ["solo paths documentales"]


def test_scope_resolver_valoracion_paths_upgrade_docs():
    decision = resolve_scope(
        "docs",
        ["templates/valoracion_testigos.html"],
    )
    assert decision.required_scope == "valoracion"
    assert decision.effective_scope == "valoracion"
    assert decision.unsafe_override is False


def test_scope_resolver_critical_paths_force_full():
    decision = resolve_scope(
        "valoracion",
        ["app/database.py"],
    )
    assert decision.required_scope == "full"
    assert decision.effective_scope == "full"


def test_scope_resolver_static_requires_app():
    decision = resolve_scope(
        "docs",
        ["static/mobile.css"],
    )
    assert decision.required_scope == "app"
    assert decision.effective_scope == "app"


def test_scope_resolver_allows_explicit_unsafe_override():
    decision = resolve_scope(
        "docs",
        ["app/database.py"],
        allow_unsafe_scope=True,
    )
    assert decision.required_scope == "full"
    assert decision.effective_scope == "docs"
    assert decision.unsafe_override is True
