import pytest

from repopilot.intelligence.analysis import analyze_source
from repopilot.intelligence.resolution import resolve_structure


def resolve(files: dict[str, tuple[str, str]]):
    analyses = {
        path: analyze_source(source, language)
        for path, (language, source) in files.items()
    }
    imports, references = resolve_structure(analyses)
    return analyses, imports, references


def test_python_lexical_imported_and_duplicate_resolution() -> None:
    analyses, imports, refs = resolve(
        {
            "pkg/__init__.py": ("python", ""),
            "pkg/service.py": ("python", "def run():\n    return 1\n"),
            "pkg/app.py": (
                "python",
                "from .service import run as go\nimport pkg.service as svc\ndef local():\n    return go() + svc.run()\ndef duplicate():\n    pass\ndef duplicate():\n    pass\nlocal()\nduplicate()\nmissing()\n",
            ),
        }
    )
    assert all(
        item.status == "resolved" and item.target == "pkg/service.py"
        for item in imports.values()
    )
    results = [
        (ref.name, refs[("pkg/app.py", i)])
        for i, ref in enumerate(analyses["pkg/app.py"].references)
    ]
    assert next(r for n, r in results if n == "go").target == ("pkg/service.py", 0)
    assert next(r for n, r in results if n == "run").target == ("pkg/service.py", 0)
    assert next(r for n, r in results if n == "local").status == "resolved"
    assert next(r for n, r in results if n == "duplicate").status == "ambiguous"
    assert next(r for n, r in results if n == "missing").status == "unresolved"


@pytest.mark.parametrize(
    "source",
    [
        "def run():\n    pass\ndef f(run):\n    return run()\n",
        "def run():\n    pass\ndef f():\n    run = other\n    return run()\n",
        "def run():\n    pass\ndef f():\n    return [run() for run in values]\n",
        "class C:\n    def run(self):\n        return run()\n",
        "def run():\n    pass\nfrom other import *\nrun()\n",
        "def run():\n    pass\ndef f():\n    match value:\n        case run:\n            run()\n",
        "def run():\n    pass\ndef f():\n    global run\n    return run()\n",
    ],
)
def test_python_shadowing_never_resolves_outer_name(source: str) -> None:
    analyses, _, refs = resolve({"app.py": ("python", source)})
    calls = [
        refs[("app.py", i)]
        for i, ref in enumerate(analyses["app.py"].references)
        if ref.name == "run"
    ]
    assert calls and all(r.status == "unresolved" and r.target is None for r in calls)


def test_js_exports_namespace_and_relative_import_ambiguity() -> None:
    analyses, _, refs = resolve(
        {
            "service.ts": (
                "typescript",
                "export function run() {}\nfunction hidden() {}\nexport default function main() {}\n",
            ),
            "app.ts": (
                "typescript",
                "import entry, { run as go, hidden } from './service';\nimport * as svc from './service';\ngo(); svc.run(); entry(); hidden();\n",
            ),
        }
    )
    calls = {
        ref.name: refs[("app.ts", i)]
        for i, ref in enumerate(analyses["app.ts"].references)
    }
    assert calls["go"].target == ("service.ts", 0)
    assert calls["run"].target == ("service.ts", 0)
    assert calls["entry"].target == ("service.ts", 2)
    assert calls["hidden"].status == "unresolved"
    analyses["service.js"] = analyze_source("export function run() {}", "javascript")
    from repopilot.intelligence.resolution import resolve_import

    assert (
        resolve_import("app.ts", analyses["app.ts"].imports[0], analyses).status
        == "ambiguous"
    )


@pytest.mark.parametrize(
    "source",
    [
        "function run() {} function f(run) { return run(); }",
        "function run() {} function f() { const run = other; return run(); }",
        "class C { run() { return run(); } }",
        "function run() {} function f() { if (true) { var run = other; } return run(); }",
        "function run() {} run = other; run();",
    ],
)
def test_js_shadowing_and_members_are_conservative(source: str) -> None:
    analyses, _, refs = resolve({"app.js": ("javascript", source)})
    calls = [
        refs[("app.js", i)]
        for i, ref in enumerate(analyses["app.js"].references)
        if ref.name == "run"
    ]
    assert calls and all(r.status == "unresolved" and r.target is None for r in calls)


def test_duplicate_source_roots_and_missing_local_modules() -> None:
    _, imports, _ = resolve(
        {
            "one/pkg/__init__.py": ("python", ""),
            "two/pkg/__init__.py": ("python", ""),
            "one/pkg/a.py": ("python", "def run(): pass"),
            "two/pkg/a.py": ("python", "def run(): pass"),
            "app.py": ("python", "from pkg.a import run\nfrom .missing import fail\n"),
        }
    )
    assert imports[("app.py", 0)].status == "ambiguous"
    assert imports[("app.py", 1)].status == "unresolved"


def test_relative_python_submodule_import_and_lexical_nested_function() -> None:
    analyses, imports, refs = resolve(
        {
            "pkg/__init__.py": ("python", ""),
            "pkg/service.py": ("python", "def run(): return 1"),
            "pkg/app.py": (
                "python",
                "from . import service\ndef outer():\n    def inner(): return 1\n    return inner()\nservice.run()\n",
            ),
        }
    )
    assert imports[("pkg/app.py", 0)].target == "pkg/service.py"
    by_name = {
        item.name: refs[("pkg/app.py", i)]
        for i, item in enumerate(analyses["pkg/app.py"].references)
    }
    assert by_name["inner"].target == ("pkg/app.py", 1)
    assert by_name["run"].target == ("pkg/service.py", 0)


def test_ts_generic_parameter_does_not_resolve_to_module_type() -> None:
    analyses, _, refs = resolve(
        {
            "a.ts": (
                "typescript",
                "export type T = string;\nfunction f<T>() { let value: T; return value; }\n",
            )
        }
    )
    assert all(
        refs[("a.ts", i)].status == "unresolved"
        for i, item in enumerate(analyses["a.ts"].references)
        if item.name == "T"
    )


def test_imported_js_duplicate_export_does_not_choose_exported_candidate() -> None:
    _, _, refs = resolve(
        {
            "service.js": ("javascript", "export function run() {}\nfunction run() {}"),
            "app.js": ("javascript", "import { run } from './service'; run();"),
        }
    )
    assert refs[("app.js", 0)].status == "ambiguous"
    assert refs[("app.js", 0)].target is None
