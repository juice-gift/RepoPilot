"""Conservative static binding and repository-local module resolution."""

import posixpath
from dataclasses import dataclass
from pathlib import PurePosixPath

from repopilot.intelligence.analysis import (
    Analysis,
    Binding,
    Import,
    Reference,
    ResolutionStatus,
)


@dataclass(frozen=True)
class ImportResolution:
    status: ResolutionStatus
    target: str | None
    reason: str


@dataclass(frozen=True)
class ReferenceResolution:
    status: ResolutionStatus
    target: tuple[str, int] | None
    reason: str


def resolve_import(
    path: str, item: Import, analyses: dict[str, Analysis]
) -> ImportResolution:
    files = set(analyses)
    language = analyses[path].language
    candidates: set[str] = set()
    if language == "python":
        module = item.module.replace(".", "/")
        if item.level:
            base = PurePosixPath(path).parent
            for _ in range(item.level - 1):
                if str(base) == ".":
                    return ImportResolution(
                        "unresolved", None, "relative import escapes snapshot"
                    )
                base = base.parent
            bases = [str(base)]
        else:
            # Infer only conventional source roots from persisted package markers.
            roots = {"."}
            roots.update(
                str(PurePosixPath(p).parent.parent)
                for p in files
                if p.endswith("/__init__.py")
            )
            bases = sorted(roots)
        for base in bases:
            stem = posixpath.normpath(posixpath.join(base, module))
            options = {f"{stem}.py", posixpath.join(stem, "__init__.py")}
            candidates.update(options & files)
        # `from . import module` can name a submodule rather than a definition.
        if (
            item.name
            and item.name != "*"
            and not any(
                item.name in analyses[candidate].scopes[0].bindings
                for candidate in candidates
            )
        ):
            submodules: set[str] = set()
            for base in bases:
                stem = posixpath.normpath(posixpath.join(base, module, item.name))
                submodules.update(
                    {f"{stem}.py", posixpath.join(stem, "__init__.py")} & files
                )
            if submodules:
                candidates = submodules
    else:
        if not item.module.startswith("."):
            return ImportResolution(
                "unresolved", None, "package/alias import outside baseline"
            )
        stem = posixpath.normpath(posixpath.join(posixpath.dirname(path), item.module))
        if stem.startswith("../") or stem == "..":
            return ImportResolution(
                "unresolved", None, "relative import escapes snapshot"
            )
        # Preserve explicit extensions. Runtime .js specifiers may select TS sources.
        if PurePosixPath(stem).suffix:
            candidates.update({stem} & files)
            if not candidates and stem.endswith(".js"):
                candidates.update({stem[:-3] + ".ts", stem[:-3] + ".tsx"} & files)
        else:
            candidates.update(
                {stem + suffix for suffix in (".js", ".jsx", ".ts", ".tsx")} & files
            )
            candidates.update(
                {
                    posixpath.join(stem, "index" + suffix)
                    for suffix in (".js", ".jsx", ".ts", ".tsx")
                }
                & files
            )
    if len(candidates) == 1:
        return ImportResolution(
            "resolved", next(iter(candidates)), "unique snapshot-local static module"
        )
    if candidates:
        return ImportResolution(
            "ambiguous", None, "multiple snapshot-local module candidates"
        )
    return ImportResolution("unresolved", None, "no snapshot-local static module")


def _lookup(analysis: Analysis, scope: int, name: str) -> list[Binding]:
    current: int | None = scope
    while current is not None:
        facts = analysis.scopes[current]
        if "*" in facts.bindings:
            return [Binding("unknown")]
        if name in facts.bindings:
            return facts.bindings[name]
        current = facts.parent
    return []


def _definition(
    path: str,
    name: str,
    analyses: dict[str, Analysis],
    *,
    exported: bool,
    default: bool = False,
) -> ReferenceResolution:
    analysis = analyses[path]
    if default:
        indexes = [
            i for i, symbol in enumerate(analysis.symbols) if symbol.default_export
        ]
        bindings = [Binding("symbol", i) for i in indexes]
        if any(
            binding.kind != "symbol"
            for i in indexes
            for binding in analysis.scopes[0].bindings.get(analysis.symbols[i].name, [])
        ):
            return ReferenceResolution(
                "unresolved", None, "default export binding is reassigned"
            )
    else:
        bindings = analysis.scopes[0].bindings.get(name, [])
    if "*" in analysis.scopes[0].bindings or any(b.kind != "symbol" for b in bindings):
        return ReferenceResolution(
            "unresolved", None, "target binding is unsupported or reassigned"
        )
    if len(bindings) > 1:
        return ReferenceResolution("ambiguous", None, "multiple imported definitions")
    candidates = [
        b.index
        for b in bindings
        if b.index is not None and (not exported or analysis.symbols[b.index].exported)
    ]
    if len(candidates) == 1:
        return ReferenceResolution(
            "resolved", (path, candidates[0]), "unique imported definition"
        )
    if len(candidates) > 1:
        return ReferenceResolution("ambiguous", None, "multiple imported definitions")
    return ReferenceResolution(
        "unresolved", None, "no supported exported/imported definition"
    )


def resolve_reference(
    path: str,
    item: Reference,
    analyses: dict[str, Analysis],
    imports: dict[tuple[str, int], ImportResolution],
) -> ReferenceResolution:
    analysis = analyses[path]
    binding_name = item.qualifier or item.name
    bindings = _lookup(analysis, item.scope, binding_name)
    if not bindings or any(b.kind == "unknown" for b in bindings):
        return ReferenceResolution(
            "unresolved", None, "missing, shadowed, dynamic or reassigned binding"
        )
    if len(bindings) != 1:
        return ReferenceResolution("ambiguous", None, "multiple lexical bindings")
    binding = bindings[0]
    if binding.index is None:
        return ReferenceResolution("unresolved", None, "binding has no definition")
    if binding.kind == "symbol":
        if item.qualifier:
            return ReferenceResolution(
                "unresolved",
                None,
                "member dispatch requires unsupported type/runtime evidence",
            )
        symbol = analysis.symbols[binding.index]
        if (
            analysis.language == "python"
            and symbol.scope == item.scope
            and item.line < symbol.start_line
        ):
            return ReferenceResolution(
                "unresolved", None, "Python use precedes definition in the same scope"
            )
        return ReferenceResolution(
            "resolved", (path, binding.index), "unique lexical definition"
        )
    imported = analysis.imports[binding.index]
    module = imports[(path, binding.index)]
    if module.status != "resolved" or module.target is None:
        return ReferenceResolution(module.status, None, module.reason)
    if item.qualifier:
        python_submodule = (
            analysis.language == "python"
            and imported.name is not None
            and (
                imported.name == PurePosixPath(module.target).stem
                or (
                    PurePosixPath(module.target).name == "__init__.py"
                    and imported.name == PurePosixPath(module.target).parent.name
                )
            )
        )
        if not imported.namespace and not python_submodule:
            return ReferenceResolution(
                "unresolved", None, "non-namespace member access"
            )
        name = item.name
    else:
        if imported.name is None or imported.name == "*":
            return ReferenceResolution(
                "unresolved", None, "module object is not a symbol definition"
            )
        name = imported.name
    return _definition(
        module.target,
        name,
        analyses,
        exported=analysis.language != "python",
        default=analysis.language != "python" and name == "default",
    )


def resolve_structure(
    analyses: dict[str, Analysis],
) -> tuple[
    dict[tuple[str, int], ImportResolution], dict[tuple[str, int], ReferenceResolution]
]:
    imports = {
        (path, i): resolve_import(path, item, analyses)
        for path, analysis in analyses.items()
        for i, item in enumerate(analysis.imports)
    }
    references = {
        (path, i): resolve_reference(path, item, analyses, imports)
        for path, analysis in analyses.items()
        for i, item in enumerate(analysis.references)
    }
    return imports, references
