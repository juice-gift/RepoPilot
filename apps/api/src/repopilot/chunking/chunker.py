import ast
import re
from dataclasses import dataclass
from hashlib import sha256

CHUNKING_VERSION = "v1-semantic-1"
MAX_CHUNK_CHARACTERS = 4_000
MAX_CHUNK_LINES = 160


@dataclass(frozen=True)
class ChunkDraft:
    sequence: int
    language: str
    chunk_type: str
    symbol_name: str | None
    qualified_name: str | None
    parent_symbol: str | None
    start_line: int
    end_line: int
    raw_content: str
    embedding_content: str
    content_hash: str
    chunking_version: str = CHUNKING_VERSION


@dataclass(frozen=True)
class SemanticRange:
    start_line: int
    end_line: int
    chunk_type: str
    symbol_name: str | None = None
    qualified_name: str | None = None
    parent_symbol: str | None = None


def chunk_source(file_path: str, language: str, content: str) -> list[ChunkDraft]:
    lines = content.splitlines(keepends=True)
    if not lines:
        return []

    if language == "python":
        ranges = _python_ranges(content, len(lines))
    elif language in {"javascript", "jsx", "typescript", "tsx"}:
        ranges = _javascript_ranges(lines)
    elif language == "markdown":
        ranges = _markdown_ranges(lines)
    else:
        ranges = [SemanticRange(1, len(lines), "file")]

    drafts: list[ChunkDraft] = []
    for semantic_range in ranges:
        for start_line, end_line, raw_content in _split_bounded_range(
            lines, semantic_range.start_line, semantic_range.end_line
        ):
            if not raw_content.strip():
                continue
            embedding_content = _build_embedding_content(
                file_path=file_path,
                language=language,
                chunk_type=semantic_range.chunk_type,
                symbol_name=semantic_range.qualified_name or semantic_range.symbol_name,
                raw_content=raw_content,
            )
            drafts.append(
                ChunkDraft(
                    sequence=len(drafts),
                    language=language,
                    chunk_type=semantic_range.chunk_type,
                    symbol_name=semantic_range.symbol_name,
                    qualified_name=semantic_range.qualified_name,
                    parent_symbol=semantic_range.parent_symbol,
                    start_line=start_line,
                    end_line=end_line,
                    raw_content=raw_content,
                    embedding_content=embedding_content,
                    content_hash=sha256(raw_content.encode("utf-8")).hexdigest(),
                )
            )
    return drafts


def _python_ranges(content: str, line_count: int) -> list[SemanticRange]:
    try:
        module = ast.parse(content)
    except SyntaxError:
        return [SemanticRange(1, line_count, "file")]

    semantic: list[SemanticRange] = []
    for node in module.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            semantic.append(
                SemanticRange(
                    _decorated_start(node),
                    node.end_lineno or node.lineno,
                    "function",
                    node.name,
                    node.name,
                )
            )
        elif isinstance(node, ast.ClassDef):
            semantic.extend(_python_class_ranges(node))
    return _with_gap_ranges(semantic, 1, line_count, "module")


def _python_class_ranges(node: ast.ClassDef) -> list[SemanticRange]:
    class_start = _decorated_start(node)
    class_end = node.end_lineno or node.lineno
    methods = [
        item
        for item in node.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    method_ranges = [
        SemanticRange(
            _decorated_start(method),
            method.end_lineno or method.lineno,
            "method",
            method.name,
            f"{node.name}.{method.name}",
            node.name,
        )
        for method in methods
    ]
    class_ranges_with_methods = _with_gap_ranges(
        method_ranges,
        class_start,
        class_end,
        "class",
        symbol_name=node.name,
        qualified_name=node.name,
    )
    class_gaps = [
        item for item in class_ranges_with_methods if item.chunk_type == "class"
    ]
    return sorted(
        [*class_gaps, *method_ranges], key=lambda item: (item.start_line, item.end_line)
    )


def _decorated_start(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> int:
    if node.decorator_list:
        return min(decorator.lineno for decorator in node.decorator_list)
    return node.lineno


def _javascript_ranges(lines: list[str]) -> list[SemanticRange]:
    sanitized = _sanitize_javascript(lines)
    patterns = (
        (
            "function",
            re.compile(
                r"^\s*(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+"
                r"([A-Za-z_$][\w$]*)"
            ),
        ),
        (
            "class",
            re.compile(
                r"^\s*(?:export\s+(?:default\s+)?)?class\s+([A-Za-z_$][\w$]*)"
            ),
        ),
        (
            "function",
            re.compile(
                r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)"
                r"(?:\s*:\s*[^=]+)?\s*=\s*(?:async\s*)?(?:\([^)]*\)|[\w$]+)\s*=>"
            ),
        ),
    )
    ranges: list[SemanticRange] = []
    top_level_depth = 0
    line_index = 0
    while line_index < len(lines):
        clean_line = sanitized[line_index]
        match: re.Match[str] | None = None
        chunk_type = "file"
        if top_level_depth == 0:
            for candidate_type, pattern in patterns:
                match = pattern.match(clean_line)
                if match:
                    chunk_type = candidate_type
                    break
        if match:
            end_index = _javascript_block_end(sanitized, line_index)
            symbol = match.group(1)
            ranges.append(
                SemanticRange(
                    line_index + 1,
                    end_index + 1,
                    chunk_type,
                    symbol,
                    symbol,
                )
            )
            for consumed in sanitized[line_index : end_index + 1]:
                top_level_depth += consumed.count("{") - consumed.count("}")
            line_index = end_index + 1
            continue
        top_level_depth += clean_line.count("{") - clean_line.count("}")
        line_index += 1

    return _with_gap_ranges(ranges, 1, len(lines), "module")


def _sanitize_javascript(lines: list[str]) -> list[str]:
    sanitized: list[str] = []
    in_block_comment = False
    quote: str | None = None
    escaped = False

    for line in lines:
        output: list[str] = []
        index = 0
        while index < len(line):
            character = line[index]
            following = line[index + 1] if index + 1 < len(line) else ""
            if in_block_comment:
                if character == "*" and following == "/":
                    in_block_comment = False
                    output.extend("  ")
                    index += 2
                else:
                    output.append(" ")
                    index += 1
                continue
            if quote is not None:
                output.append(" ")
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote:
                    quote = None
                index += 1
                continue
            if character == "/" and following == "*":
                in_block_comment = True
                output.extend("  ")
                index += 2
            elif character == "/" and following == "/":
                output.extend(" " * (len(line) - index))
                break
            elif character in {"'", '"', "`"}:
                quote = character
                output.append(" ")
                index += 1
            else:
                output.append(character)
                index += 1
        sanitized.append("".join(output))
    return sanitized


def _javascript_block_end(sanitized: list[str], start_index: int) -> int:
    depth = 0
    found_opening = False
    for index in range(start_index, len(sanitized)):
        for character in sanitized[index]:
            if character == "{":
                depth += 1
                found_opening = True
            elif character == "}" and found_opening:
                depth -= 1
        if found_opening and depth <= 0:
            return index
        if not found_opening and ";" in sanitized[index]:
            return index
    return start_index


def _markdown_ranges(lines: list[str]) -> list[SemanticRange]:
    headings: list[tuple[int, str]] = []
    in_fence = False
    for index, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line.rstrip("\r\n"))
        if match:
            headings.append((index, match.group(1)))

    if not headings:
        return [SemanticRange(1, len(lines), "document")]

    ranges: list[SemanticRange] = []
    if headings[0][0] > 1:
        ranges.append(SemanticRange(1, headings[0][0] - 1, "document"))
    for heading_index, (start_line, heading) in enumerate(headings):
        end_line = (
            headings[heading_index + 1][0] - 1
            if heading_index + 1 < len(headings)
            else len(lines)
        )
        ranges.append(
            SemanticRange(start_line, end_line, "section", heading, heading)
        )
    return ranges


def _with_gap_ranges(
    ranges: list[SemanticRange],
    start_line: int,
    end_line: int,
    gap_type: str,
    *,
    symbol_name: str | None = None,
    qualified_name: str | None = None,
) -> list[SemanticRange]:
    ordered = sorted(ranges, key=lambda item: (item.start_line, item.end_line))
    output: list[SemanticRange] = []
    cursor = start_line
    for item in ordered:
        if item.start_line > cursor:
            output.append(
                SemanticRange(
                    cursor,
                    item.start_line - 1,
                    gap_type,
                    symbol_name,
                    qualified_name,
                )
            )
        output.append(item)
        cursor = max(cursor, item.end_line + 1)
    if cursor <= end_line:
        output.append(
            SemanticRange(
                cursor,
                end_line,
                gap_type,
                symbol_name,
                qualified_name,
            )
        )
    return output


def _split_bounded_range(
    lines: list[str], start_line: int, end_line: int
) -> list[tuple[int, int, str]]:
    chunks: list[tuple[int, int, str]] = []
    current_lines: list[str] = []
    current_start = start_line
    current_characters = 0

    def flush(current_end: int) -> None:
        nonlocal current_lines, current_characters, current_start
        if current_lines:
            chunks.append((current_start, current_end, "".join(current_lines)))
        current_lines = []
        current_characters = 0

    for line_number in range(start_line, end_line + 1):
        line = lines[line_number - 1]
        if len(line) > MAX_CHUNK_CHARACTERS:
            flush(line_number - 1)
            for offset in range(0, len(line), MAX_CHUNK_CHARACTERS):
                chunks.append(
                    (
                        line_number,
                        line_number,
                        line[offset : offset + MAX_CHUNK_CHARACTERS],
                    )
                )
            current_start = line_number + 1
            continue
        would_exceed = current_lines and (
            current_characters + len(line) > MAX_CHUNK_CHARACTERS
            or len(current_lines) >= MAX_CHUNK_LINES
        )
        if would_exceed:
            flush(line_number - 1)
            current_start = line_number
        if not current_lines:
            current_start = line_number
        current_lines.append(line)
        current_characters += len(line)
    flush(end_line)
    return chunks


def _build_embedding_content(
    *,
    file_path: str,
    language: str,
    chunk_type: str,
    symbol_name: str | None,
    raw_content: str,
) -> str:
    metadata = [
        f"File: {file_path}",
        f"Language: {language}",
        f"Chunk type: {chunk_type}",
    ]
    if symbol_name:
        metadata.append(f"Symbol: {symbol_name}")
    return "\n".join([*metadata, "Source:", raw_content])
