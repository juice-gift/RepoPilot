from repopilot.chunking.chunker import (
    MAX_CHUNK_CHARACTERS,
    MAX_CHUNK_LINES,
    chunk_source,
)


def test_python_chunking_preserves_functions_classes_and_methods() -> None:
    content = """import os

def top_level(value: int) -> int:
    return value + 1

class Greeter:
    prefix = "hello"

    def greet(self, name: str) -> str:
        return f"{self.prefix} {name}"

tail = True
"""

    chunks = chunk_source("service.py", "python", content)

    assert [(chunk.chunk_type, chunk.qualified_name) for chunk in chunks] == [
        ("module", None),
        ("function", "top_level"),
        ("class", "Greeter"),
        ("method", "Greeter.greet"),
        ("module", None),
    ]
    method = next(chunk for chunk in chunks if chunk.chunk_type == "method")
    assert method.parent_symbol == "Greeter"
    assert method.start_line == 9
    assert method.end_line == 10
    assert "File: service.py" in method.embedding_content
    assert "Symbol: Greeter.greet" in method.embedding_content
    assert method.raw_content != method.embedding_content


def test_invalid_python_falls_back_to_bounded_file_chunks() -> None:
    content = "def broken(:\n" + "x = 1\n" * (MAX_CHUNK_LINES + 1)

    chunks = chunk_source("broken.py", "python", content)

    assert len(chunks) == 2
    assert all(chunk.chunk_type == "file" for chunk in chunks)
    assert all(len(chunk.raw_content) <= MAX_CHUNK_CHARACTERS for chunk in chunks)
    assert chunks[0].end_line - chunks[0].start_line + 1 <= MAX_CHUNK_LINES


def test_javascript_chunking_ignores_braces_in_strings_and_comments() -> None:
    content = """import { helper } from "./helper";

export function format(value) {
  const text = "}";
  // } does not end the function
  return `{${value}}`;
}

export const render = (name) => {
  return <div>{name}</div>;
};
"""

    chunks = chunk_source("view.tsx", "tsx", content)

    functions = [chunk for chunk in chunks if chunk.chunk_type == "function"]
    assert [chunk.symbol_name for chunk in functions] == ["format", "render"]
    assert functions[0].start_line == 3
    assert functions[0].end_line == 7
    assert functions[1].start_line == 9
    assert functions[1].end_line == 11


def test_markdown_chunking_uses_headings_but_not_fenced_headings() -> None:
    content = """Preface

# Install
Run setup.

```md
# Not a section
```

## Usage
Call the API.
"""

    chunks = chunk_source("README.md", "markdown", content)

    assert [(chunk.chunk_type, chunk.symbol_name) for chunk in chunks] == [
        ("document", None),
        ("section", "Install"),
        ("section", "Usage"),
    ]
    assert chunks[1].start_line == 3
    assert chunks[1].end_line == 9


def test_oversized_single_line_is_split_without_losing_line_metadata() -> None:
    content = "x" * (MAX_CHUNK_CHARACTERS + 10)

    chunks = chunk_source("large.js", "javascript", content)

    assert [len(chunk.raw_content) for chunk in chunks] == [MAX_CHUNK_CHARACTERS, 10]
    assert all((chunk.start_line, chunk.end_line) == (1, 1) for chunk in chunks)
