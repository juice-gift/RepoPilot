import ast

from repopilot.intelligence.analysis import (
    Analysis,
    AnalysisError,
    Binding,
    Import,
    Reference,
    Symbol,
)


def analyze_python(content: str) -> Analysis:
    try:
        root = ast.parse(content)
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise AnalysisError(f"Python syntax analysis failed: {exc}") from exc
    analyzer = _PythonAnalyzer()
    analyzer.visit(root)
    return analyzer.result


class _PythonAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.result = Analysis("python")
        self.scope = 0
        self.parent: int | None = None
        self.class_scopes: set[int] = set()
        self.conditional = 0

    def _symbol(self, node: ast.AST, name: str, kind: str) -> int:
        parent = self.parent
        qualified = (
            f"{self.result.symbols[parent].qualified_name}.{name}"
            if parent is not None
            else name
        )
        index = len(self.result.symbols)
        self.result.symbols.append(
            Symbol(
                name,
                qualified,
                kind,
                parent,
                self.scope,
                node.lineno,
                node.end_lineno or node.lineno,
            )
        )
        self.result.bind(
            self.scope,
            name,
            Binding(
                "unknown" if self.conditional else "symbol",
                None if self.conditional else index,
            ),
        )
        return index

    def _definition(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    ) -> None:
        is_class = isinstance(node, ast.ClassDef)
        kind = (
            "class"
            if is_class
            else ("method" if self.scope in self.class_scopes else "function")
        )
        index = self._symbol(node, node.name, kind)
        for decorator in node.decorator_list:
            self.visit(decorator)
        if is_class:
            for base in node.bases:
                self.visit(base)
            for keyword in node.keywords:
                self.visit(keyword.value)
        else:
            for default in [*node.args.defaults, *node.args.kw_defaults]:
                if default is not None:
                    self.visit(default)
            if node.returns:
                self.visit(node.returns)
        old_scope, old_parent, old_conditional = (
            self.scope,
            self.parent,
            self.conditional,
        )
        lexical_parent = old_scope
        if not is_class and old_scope in self.class_scopes:
            lexical_parent = self.result.scopes[old_scope].parent
        self.scope = self.result.new_scope(lexical_parent)
        self.parent = index
        self.conditional = 0
        if is_class:
            self.class_scopes.add(self.scope)
        else:
            args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
            args += [arg for arg in (node.args.vararg, node.args.kwarg) if arg]
            for arg in args:
                self.result.bind(self.scope, arg.arg, Binding("unknown"))
        for statement in node.body:
            self.visit(statement)
        self.scope, self.parent, self.conditional = (
            old_scope,
            old_parent,
            old_conditional,
        )

    visit_FunctionDef = _definition
    visit_AsyncFunctionDef = _definition
    visit_ClassDef = _definition

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.result.references.append(
                Reference(
                    node.id,
                    self.scope,
                    node.lineno,
                    node.col_offset + 1,
                )
            )
        elif isinstance(node.ctx, (ast.Store, ast.Del)):
            self.result.bind(self.scope, node.id, Binding("unknown"))

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.ctx, ast.Load):
            qualifier = (
                node.value.id if isinstance(node.value, ast.Name) else "<dynamic>"
            )
            self.result.references.append(
                Reference(
                    node.attr,
                    self.scope,
                    node.lineno,
                    node.col_offset + 1,
                    qualifier,
                )
            )
        self.visit(node.value)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        for target in node.targets:
            if self.scope == 0 and isinstance(target, ast.Name):
                self._symbol(node, target.id, "variable")
            else:
                self.visit(target)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.visit(node.annotation)
        if node.value:
            self.visit(node.value)
        if self.scope == 0 and isinstance(node.target, ast.Name):
            self._symbol(node, node.target.id, "variable")
        else:
            self.visit(node.target)

    def visit_Import(self, node: ast.Import) -> None:
        for item in node.names:
            name = item.asname or item.name.split(".")[0]
            index = len(self.result.imports)
            self.result.imports.append(
                Import(
                    item.name,
                    None,
                    name,
                    self.scope,
                    node.lineno,
                    node.col_offset + 1,
                    namespace=bool(item.asname or "." not in item.name),
                )
            )
            self.result.bind(self.scope, name, Binding("import", index))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for item in node.names:
            name = item.asname or item.name
            index = len(self.result.imports)
            self.result.imports.append(
                Import(
                    node.module or "",
                    item.name,
                    name,
                    self.scope,
                    node.lineno,
                    node.col_offset + 1,
                    node.level,
                )
            )
            self.result.bind(self.scope, name, Binding("import", index))
            if item.name == "*":
                # A wildcard may overwrite any module/global binding.
                self.result.bind(self.scope, "*", Binding("unknown"))

    def visit_Global(self, node: ast.Global) -> None:
        # Writes through global/nonlocal declarations need runtime reasoning.
        for name in node.names:
            self.result.bind(self.scope, name, Binding("unknown"))
            self.result.bind(0, name, Binding("unknown"))

    visit_Nonlocal = visit_Global

    def visit_Lambda(self, node: ast.Lambda) -> None:
        old_scope = self.scope
        self.scope = self.result.new_scope(old_scope)
        args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        args += [arg for arg in (node.args.vararg, node.args.kwarg) if arg]
        for arg in args:
            self.result.bind(self.scope, arg.arg, Binding("unknown"))
        self.visit(node.body)
        self.scope = old_scope

    def _comprehension(self, node: ast.AST) -> None:
        old_scope = self.scope
        self.scope = self.result.new_scope(old_scope)
        self.generic_visit(node)
        self.scope = old_scope

    visit_ListComp = _comprehension
    visit_SetComp = _comprehension
    visit_DictComp = _comprehension
    visit_GeneratorExp = _comprehension

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self.result.bind(self.scope, node.name, Binding("unknown"))
        self.generic_visit(node)

    def _conditional(self, node: ast.AST) -> None:
        self.conditional += 1
        self.generic_visit(node)
        self.conditional -= 1

    visit_If = _conditional
    visit_Try = _conditional
    visit_TryStar = _conditional
    visit_For = _conditional
    visit_AsyncFor = _conditional
    visit_While = _conditional
    visit_Match = _conditional
