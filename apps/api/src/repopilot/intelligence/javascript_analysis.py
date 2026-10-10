"""JS family syntax extraction; Tree-sitter nodes never leave this module."""

import tree_sitter_javascript
import tree_sitter_typescript
from tree_sitter import Language, Node, Parser

from repopilot.intelligence.analysis import (
    Analysis,
    AnalysisError,
    Binding,
    Import,
    Reference,
    Symbol,
)


def analyze_javascript(content: str, language: str) -> Analysis:
    grammar = (
        tree_sitter_typescript.language_tsx()
        if language == "tsx"
        else tree_sitter_typescript.language_typescript()
        if language == "typescript"
        else tree_sitter_javascript.language()
    )
    root = Parser(Language(grammar)).parse(content.encode("utf-8")).root_node
    if root.has_error:
        raise AnalysisError(
            "JavaScript/TypeScript syntax tree contains errors or missing nodes"
        )
    analyzer = _JavaScriptAnalyzer(language)
    analyzer.visit(root)
    return analyzer.result


class _JavaScriptAnalyzer:
    def __init__(self, language: str) -> None:
        self.result = Analysis(language)
        self.scope = 0
        self.parent: int | None = None
        self.exported = False
        self.default_export = False

    @staticmethod
    def text(node: Node) -> str:
        return (node.text or b"").decode("utf-8")

    def symbol(self, node: Node, name: str, kind: str) -> int:
        index = len(self.result.symbols)
        qualified = (
            f"{self.result.symbols[self.parent].qualified_name}.{name}"
            if self.parent is not None
            else name
        )
        self.result.symbols.append(
            Symbol(
                name,
                qualified,
                kind,
                self.parent,
                self.scope,
                node.start_point.row + 1,
                node.end_point.row + 1,
                self.exported and self.scope == 0,
                self.default_export and self.scope == 0,
            )
        )
        self.result.bind(self.scope, name, Binding("symbol", index))
        return index

    def bind_pattern(self, node: Node | None) -> None:
        if node is None:
            return
        if node.type in {"identifier", "shorthand_property_identifier_pattern"}:
            self.result.bind(self.scope, self.text(node), Binding("unknown"))
        elif node.type in {"required_parameter", "optional_parameter", "pair_pattern"}:
            self.bind_pattern(
                node.child_by_field_name("pattern") or node.child_by_field_name("value")
            )
        elif node.type == "assignment_pattern":
            self.bind_pattern(node.child_by_field_name("left"))
            right = node.child_by_field_name("right")
            if right:
                self.visit(right)
        else:
            for child in node.named_children:
                if child.type not in {
                    "type_annotation",
                    "type_identifier",
                    "property_identifier",
                }:
                    self.bind_pattern(child)

    def function(self, node: Node, symbol_index: int | None = None) -> None:
        old_scope, old_parent = self.scope, self.parent
        self.scope = self.result.new_scope(old_scope)
        if symbol_index is not None:
            self.parent = symbol_index
        # A named function expression's name exists only inside the function.
        name = node.child_by_field_name("name")
        if name and node.type == "function_expression":
            self.result.bind(self.scope, self.text(name), Binding("unknown"))
        self.bind_pattern(
            node.child_by_field_name("parameters")
            or node.child_by_field_name("parameter")
        )
        body = node.child_by_field_name("body")
        if body:
            self.visit(body)
        self.scope, self.parent = old_scope, old_parent

    def visit(self, node: Node) -> None:
        kind = node.type
        if kind == "export_statement":
            old = self.exported, self.default_export
            self.exported = True
            self.default_export = any(
                child.type == "default" for child in node.children
            )
            declaration = node.child_by_field_name("declaration")
            if declaration:
                self.visit(declaration)
            # Re-exports and export lists remain unsupported (no invented export facts).
            self.exported, self.default_export = old
            return
        if kind == "import_statement":
            self.import_statement(node)
            return
        if kind in {
            "function_declaration",
            "generator_function_declaration",
            "method_definition",
        }:
            name = node.child_by_field_name("name")
            if name and name.type in {"identifier", "property_identifier"}:
                index = self.symbol(
                    node,
                    self.text(name),
                    "method" if kind == "method_definition" else "function",
                )
                self.function(node, index)
            else:
                self.function(node)
            return
        if kind in {"arrow_function", "function_expression", "generator_function"}:
            self.function(node)
            return
        if kind in {
            "class_declaration",
            "interface_declaration",
            "type_alias_declaration",
            "enum_declaration",
        }:
            name = node.child_by_field_name("name")
            if name:
                index = self.symbol(
                    node,
                    self.text(name),
                    {
                        "class_declaration": "class",
                        "interface_declaration": "interface",
                        "type_alias_declaration": "type_alias",
                        "enum_declaration": "enum",
                    }[kind],
                )
                old_parent = self.parent
                self.parent = index
                for child in node.named_children:
                    if child.id != name.id:
                        self.visit(child)
                self.parent = old_parent
            return
        if kind == "variable_declarator":
            name = node.child_by_field_name("name")
            value = node.child_by_field_name("value")
            if name and name.type == "identifier" and self.scope == 0:
                is_function = value is not None and value.type in {
                    "arrow_function",
                    "function_expression",
                    "generator_function",
                }
                index = self.symbol(
                    node, self.text(name), "function" if is_function else "variable"
                )
                if is_function:
                    self.function(value, index)
                elif value:
                    self.visit(value)
            else:
                self.bind_pattern(name)
                if value:
                    self.visit(value)
            return
        if kind in {
            "statement_block",
            "for_statement",
            "for_in_statement",
            "catch_clause",
        }:
            old_scope = self.scope
            self.scope = self.result.new_scope(old_scope)
            if kind == "catch_clause":
                self.bind_pattern(node.child_by_field_name("parameter"))
            for child in node.named_children:
                if kind != "catch_clause" or child != node.child_by_field_name(
                    "parameter"
                ):
                    self.visit(child)
            self.scope = old_scope
            return
        if kind in {
            "assignment_expression",
            "augmented_assignment_expression",
            "update_expression",
        }:
            left = node.child_by_field_name("left") or node.child_by_field_name(
                "argument"
            )
            self.bind_pattern(left)
            # Assignment may affect a var/global binding from any nested scope.
            if left and left.type == "identifier":
                name = self.text(left)
                scope = self.result.scopes[self.scope].parent
                while scope is not None:
                    self.result.bind(scope, name, Binding("unknown"))
                    scope = self.result.scopes[scope].parent
            right = node.child_by_field_name("right")
            if right:
                self.visit(right)
            return
        if kind == "member_expression":
            obj, prop = (
                node.child_by_field_name("object"),
                node.child_by_field_name("property"),
            )
            if prop:
                self.result.references.append(
                    Reference(
                        self.text(prop),
                        self.scope,
                        prop.start_point.row + 1,
                        prop.start_point.column + 1,
                        self.text(obj)
                        if obj and obj.type == "identifier"
                        else "<dynamic>",
                    )
                )
            if obj:
                self.visit(obj)
            return
        if kind in {"identifier", "type_identifier", "shorthand_property_identifier"}:
            self.result.references.append(
                Reference(
                    self.text(node),
                    self.scope,
                    node.start_point.row + 1,
                    node.start_point.column + 1,
                )
            )
            return
        if kind in {
            "jsx_opening_element",
            "jsx_self_closing_element",
            "jsx_closing_element",
        }:
            name = node.child_by_field_name("name")
            if name and self.text(name)[:1].isupper():
                self.visit(name)
            for child in node.named_children:
                if name is None or child.id != name.id:
                    self.visit(child)
            return
        if kind in {
            "property_identifier",
            "string",
            "comment",
            "jsx_text",
            "enum_body",
        }:
            return
        for child in node.named_children:
            self.visit(child)

    def import_statement(self, node: Node) -> None:
        source = node.child_by_field_name("source")
        if source is None:
            return
        module = self.text(source)[1:-1]
        clause = next(
            (child for child in node.named_children if child.type == "import_clause"),
            None,
        )
        occurrences: list[tuple[str | None, str | None, bool, Node]] = []
        if clause:
            for child in clause.named_children:
                if child.type == "identifier":
                    occurrences.append(("default", self.text(child), False, child))
                elif child.type == "namespace_import":
                    alias = next(
                        (
                            item
                            for item in child.named_children
                            if item.type == "identifier"
                        ),
                        None,
                    )
                    if alias:
                        occurrences.append((None, self.text(alias), True, alias))
                elif child.type == "named_imports":
                    for specifier in child.named_children:
                        name = specifier.child_by_field_name("name")
                        alias = specifier.child_by_field_name("alias") or name
                        if name and alias:
                            occurrences.append(
                                (self.text(name), self.text(alias), False, specifier)
                            )
        if not occurrences:
            occurrences.append((None, None, False, node))
        for name, alias, namespace, location in occurrences:
            index = len(self.result.imports)
            self.result.imports.append(
                Import(
                    module,
                    name,
                    alias,
                    self.scope,
                    location.start_point.row + 1,
                    location.start_point.column + 1,
                    namespace=namespace,
                )
            )
            if alias:
                self.result.bind(self.scope, alias, Binding("import", index))
