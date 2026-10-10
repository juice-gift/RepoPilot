import os
import subprocess
import sys
from pathlib import Path

import pytest

from repopilot.intelligence.analysis import AnalysisError, analyze_source


def test_python_definitions_ranges_parents_and_occurrences() -> None:
    source = "from .service import run as go\nLIMIT = 3\nclass App:\n    async def handle(self, token):\n        return go(token)\ndef outer():\n    def inner():\n        return LIMIT\n    return inner()\n"
    result = analyze_source(source, "python")
    assert [
        (s.qualified_name, s.kind, s.start_line, s.end_line) for s in result.symbols
    ] == [
        ("LIMIT", "variable", 2, 2),
        ("App", "class", 3, 5),
        ("App.handle", "method", 4, 5),
        ("outer", "function", 6, 9),
        ("outer.inner", "function", 7, 8),
    ]
    assert result.symbols[2].parent == 1
    assert result.imports[0].module == "service"
    assert result.imports[0].level == 1
    assert result.imports[0].alias == "go"
    assert ("go", 5) in [(r.name, r.line) for r in result.references]
    assert result == analyze_source(source, "python")


@pytest.mark.parametrize("language", ["javascript", "jsx", "typescript", "tsx"])
def test_js_family_function_class_arrow_and_static_import(language: str) -> None:
    source = "import { run as go } from './service';\nexport const handle = (token) => go(token);\nexport class App { method() { return handle('x'); } }\n"
    result = analyze_source(source, language)
    assert [(s.qualified_name, s.kind) for s in result.symbols] == [
        ("handle", "function"),
        ("App", "class"),
        ("App.method", "method"),
    ]
    assert result.symbols[2].parent == 1
    assert result.symbols[0].exported is True
    assert result.imports[0].name == "run"
    assert result.imports[0].alias == "go"
    assert ("go", 2) in [(r.name, r.line) for r in result.references]
    assert result == analyze_source(source, language)


def test_typescript_named_types_and_jsx_component() -> None:
    result = analyze_source(
        "export interface User { name: string; }\nexport type Alias = User;\nexport enum State { Ready, Done }\nexport const View = () => <User />;\n",
        "tsx",
    )
    assert [s.kind for s in result.symbols] == [
        "interface",
        "type_alias",
        "enum",
        "function",
    ]
    assert sum(r.name == "User" for r in result.references) == 2


@pytest.mark.parametrize(
    "language, source",
    [
        ("python", "def broken(:\n"),
        ("typescript", "export function broken( {"),
        ("javascript", "const a = ;"),
    ],
)
def test_syntax_failures_are_explicit(language: str, source: str) -> None:
    with pytest.raises(AnalysisError):
        analyze_source(source, language)


def test_markdown_has_no_structural_index() -> None:
    assert analyze_source("# hello", "markdown").symbols == []


def test_real_react_tsx_does_not_crash_native_parser() -> None:
    # 0.26.0 crashed the Windows process while traversing this actual TSX file.
    # A subprocess makes native failure reviewable instead of killing pytest.
    api_root = Path(__file__).resolve().parents[1]
    script = "from pathlib import Path; from repopilot.intelligence.analysis import analyze_source; a = analyze_source(Path('../web/src/App.tsx').read_text(encoding='utf-8'), 'tsx'); assert any(s.name == 'App' for s in a.symbols)"
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=api_root,
        env=dict(os.environ, PYTHONPATH=str(api_root / "src")),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "language, source",
    [
        ("python", 'label = "中文"; service.run()'),
        ("typescript", 'const label = "中文"; service.run();'),
    ],
)
def test_reference_locations_use_one_based_utf8_byte_columns(
    language: str, source: str
) -> None:
    result = analyze_source(source, language)
    reference = next(ref for ref in result.references if ref.name == "run")
    assert reference.line == 1
    assert reference.column == len(source[: source.index("run")].encode("utf-8")) + 1
