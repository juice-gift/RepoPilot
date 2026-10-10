"""Parser-independent extraction records. Scope/binding facts are transient."""

import re
from dataclasses import dataclass, field
from typing import Literal

INDEX_VERSION = "structural-v2"
ResolutionStatus = Literal["resolved", "unresolved", "ambiguous"]


class AnalysisError(ValueError):
    """A source file cannot safely produce structural facts."""


def normalize_name(name: str) -> str:
    return re.sub(r"[^\w]", "", name.casefold()).replace("_", "")


@dataclass(frozen=True)
class Symbol:
    name: str
    qualified_name: str
    kind: str
    parent: int | None
    scope: int
    start_line: int
    end_line: int
    exported: bool = False
    default_export: bool = False


@dataclass(frozen=True)
class Import:
    module: str
    name: str | None
    alias: str | None
    scope: int
    line: int
    column: int
    level: int = 0
    namespace: bool = False


@dataclass(frozen=True)
class Reference:
    name: str
    scope: int
    line: int
    column: int
    qualifier: str | None = None


@dataclass(frozen=True)
class Binding:
    kind: Literal["symbol", "import", "unknown"]
    index: int | None = None


@dataclass
class Scope:
    parent: int | None
    bindings: dict[str, list[Binding]] = field(default_factory=dict)


@dataclass
class Analysis:
    language: str
    symbols: list[Symbol] = field(default_factory=list)
    imports: list[Import] = field(default_factory=list)
    references: list[Reference] = field(default_factory=list)
    scopes: list[Scope] = field(default_factory=lambda: [Scope(None)])

    def bind(self, scope: int, name: str, binding: Binding) -> None:
        self.scopes[scope].bindings.setdefault(name, []).append(binding)

    def new_scope(self, parent: int | None) -> int:
        self.scopes.append(Scope(parent))
        return len(self.scopes) - 1


def analyze_source(content: str, language: str) -> Analysis:
    # Imports stay lazy so parser implementation types do not cross this boundary.
    if language == "python":
        from repopilot.intelligence.python_analysis import analyze_python

        return analyze_python(content)
    if language in {"javascript", "typescript", "jsx", "tsx"}:
        from repopilot.intelligence.javascript_analysis import analyze_javascript

        return analyze_javascript(content, language)
    return Analysis(language)
