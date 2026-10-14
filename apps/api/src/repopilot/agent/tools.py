"""Allowlisted tools over persisted data; no filesystem or execution access."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from repopilot.agent.models import Evidence, Observation, ToolExecution
from repopilot.db.models import SnapshotFile
from repopilot.embeddings.providers import (
    EmbeddingConfigurationError,
    EmbeddingProvider,
)
from repopilot.intelligence import navigation
from repopilot.intelligence.service import SnapshotNotFoundError, require_snapshot
from repopilot.retrieval.retriever import (
    RetrievalSnapshotNotFoundError,
    RetrievalStrategy,
    SnapshotNotIndexedError,
    retrieve_evidence,
)


class ReadRangeError(ValueError):
    pass


def validate_path(value: str) -> str:
    # Snapshot paths are POSIX relative paths. Never normalize away traversal.
    if (
        not value
        or len(value) > 512
        or value.startswith("/")
        or "\\" in value
        or ":" in value
        or any(ord(char) < 32 for char in value)
        or any(part in ("", ".", "..") for part in value.split("/"))
    ):
        raise ValueError("Expected a relative snapshot file path")
    return value


def validate_single_line_query(value: str) -> str:
    if not value.strip() or "\n" in value or "\r" in value:
        raise ValueError("Expected a nonempty single-line literal query")
    return value


def validate_optional_path(value: str | None) -> str | None:
    return validate_path(value) if value is not None else None


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ListFilesArguments(Arguments):
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=100_000)


class ReadFileArguments(Arguments):
    path: str = Field(min_length=1, max_length=512)
    start_line: int = Field(default=1, ge=1, le=1_000_000)
    end_line: int | None = Field(default=None, ge=1, le=1_000_000)

    _path = field_validator("path")(validate_path)


class SearchCodeArguments(Arguments):
    query: str = Field(min_length=1, max_length=200)
    file_path: str | None = None
    limit: int = Field(default=10, ge=1, le=20)

    _query = field_validator("query")(validate_single_line_query)
    _path = field_validator("file_path")(validate_optional_path)


class SearchSymbolArguments(Arguments):
    query: str = Field(min_length=1, max_length=200)
    match: Literal["exact", "qualified", "normalized"] = "exact"
    file_path: str | None = None
    limit: int = Field(default=10, ge=1, le=20)

    _query = field_validator("query")(validate_single_line_query)
    _path = field_validator("file_path")(validate_optional_path)


class RetrieveContextArguments(Arguments):
    query: str = Field(min_length=1, max_length=2_000)
    top_k: int = Field(default=5, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Query must not be empty")
        return value.strip()


@dataclass(frozen=True)
class RunScope:
    repository_id: int
    snapshot_id: int


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    arguments: type[Arguments]
    handler: Callable[[Arguments], Observation]


def bound_observation(observation: Observation, limit: int) -> Observation:
    """Bound the entire serialized object, preserving valid JSON and metadata."""
    bounded = observation.model_copy(deep=True)
    while len(bounded.model_dump_json()) > limit and bounded.items:
        bounded.truncated = True
        item = bounded.items[-1]
        if item.content:
            content = item.content
            item.content = ""
            item.truncated = True
            if len(bounded.model_dump_json()) < limit:
                # Search actual JSON size: escaped quotes/backslashes must retain
                # a useful prefix rather than dropping the entire saved source.
                low, high = 0, len(content)
                while low < high:
                    middle = (low + high + 1) // 2
                    item.content = content[:middle]
                    if len(bounded.model_dump_json()) <= limit:
                        low = middle
                    else:
                        high = middle - 1
                item.content = content[:low]
                break
        bounded.items.pop()
        bounded.omitted_items += 1
    return bounded


class ToolRegistry:
    def __init__(
        self,
        session: Session,
        scope: RunScope,
        *,
        embedding_factory: Callable[[], EmbeddingProvider],
        retrieval_strategy: RetrievalStrategy = "hybrid",
        observation_limit: int = 12_000,
    ) -> None:
        if observation_limit < 1_000:
            raise ValueError("Observation limit must be at least 1000 characters")
        self.session = session
        self.scope = scope
        self.embedding_factory = embedding_factory
        self.retrieval_strategy = retrieval_strategy
        self.observation_limit = observation_limit
        self._tools = {
            tool.name: tool
            for tool in (
                Tool(
                    "list_files",
                    "List saved snapshot files, ordered by path. Paginate with offset.",
                    ListFilesArguments,
                    self._list_files,
                ),
                Tool(
                    "read_file",
                    "Read saved source, one-based inclusive lines, at most 200 lines. Default 100 lines. Output may truncate.",
                    ReadFileArguments,
                    self._read_file,
                ),
                Tool(
                    "search_code",
                    "Case-sensitive literal substring search in saved source; no regex. Returns line snippets in file/line order.",
                    SearchCodeArguments,
                    self._search_code,
                ),
                Tool(
                    "search_symbol",
                    "Search V2 indexed definitions by exact, qualified or normalized name. Returns metadata; use read_file for source. Index must already exist.",
                    SearchSymbolArguments,
                    self._search_symbol,
                ),
                Tool(
                    "retrieve_context",
                    "Retrieve ranked V1 source evidence. Requires existing matching embedding index. Does not generate an answer.",
                    RetrieveContextArguments,
                    self._retrieve_context,
                ),
            )
        }

    def definitions(self) -> list[dict[str, object]]:
        return [
            {
                "type": "function",
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.arguments.model_json_schema(),
            }
            for tool in self._tools.values()
        ]

    def execute(
        self, name: str, raw_arguments: str, *, evidence_prefix: str
    ) -> ToolExecution:
        tool = self._tools.get(name)
        if tool is None:
            return self._error("unknown_tool", "Tool is not in the read-only allowlist")
        if len(raw_arguments) > 4_000:
            return self._error(
                "invalid_arguments", "Tool arguments exceed the size limit"
            )
        try:
            args = tool.arguments.model_validate(json.loads(raw_arguments))
            if isinstance(args, ReadFileArguments):
                end = args.end_line or args.start_line + 99
                if end < args.start_line or end - args.start_line + 1 > 200:
                    raise ValueError("Read range must contain 1 to 200 lines")
        except (ValueError, TypeError, ValidationError, RecursionError):
            return self._error(
                "invalid_arguments", "Arguments do not match the tool schema or bounds"
            )
        validated = args.model_dump(mode="json")
        try:
            # Every call validates both IDs, even when its underlying query uses snapshot_id.
            require_snapshot(
                self.session, self.scope.repository_id, self.scope.snapshot_id
            )
            result = tool.handler(args)
        except (SnapshotNotFoundError, RetrievalSnapshotNotFoundError):
            return self._error(
                "snapshot_not_found", "Repository snapshot not found", validated
            )
        except navigation.ResourceNotFoundError:
            return self._error(
                "file_not_found", "Saved snapshot file not found", validated
            )
        except (navigation.IndexNotReadyError, SnapshotNotIndexedError):
            return self._error(
                "index_not_ready", "Required snapshot index is not ready", validated
            )
        except EmbeddingConfigurationError:
            return self._error(
                "provider_configuration",
                "Embedding provider is not configured",
                validated,
            )
        except ReadRangeError:
            return self._error(
                "invalid_range",
                "Requested line range is outside the saved file",
                validated,
            )
        except Exception:  # noqa: BLE001 - tool boundary returns safe failure, no raw exception
            # Roll back an aborted read transaction so the model can recover safely.
            self.session.rollback()
            return self._error("tool_failure", "Repository tool failed", validated)
        for index, item in enumerate(result.items, start=1):
            if item.start_line is not None:
                item.evidence_id = f"{evidence_prefix}_{index}"
        return ToolExecution(
            validated_arguments=validated,
            observation=bound_observation(result, self.observation_limit),
        )

    @staticmethod
    def _error(
        code: str, message: str, args: dict[str, object] | None = None
    ) -> ToolExecution:
        return ToolExecution(
            validated_arguments=args,
            observation=Observation(
                status="error", error_code=code, error_message=message
            ),
        )

    def _list_files(self, arguments: Arguments) -> Observation:
        args = ListFilesArguments.model_validate(arguments.model_dump())
        files = navigation.list_files(
            self.session,
            self.scope.repository_id,
            self.scope.snapshot_id,
            limit=args.limit + 1,
            offset=args.offset,
        )
        return Observation(
            items=[
                Evidence(file_path=f.path, language=f.language)
                for f in files[: args.limit]
            ],
            omitted_items=int(len(files) > args.limit),
        )

    def _read_file(self, arguments: Arguments) -> Observation:
        args = ReadFileArguments.model_validate(arguments.model_dump())
        file = self.session.scalar(
            select(SnapshotFile).where(
                SnapshotFile.snapshot_id == self.scope.snapshot_id,
                SnapshotFile.path == args.path,
            )
        )
        if file is None:
            raise navigation.ResourceNotFoundError("Snapshot file not found")
        lines = file.content.splitlines()
        if args.start_line > len(lines):
            raise ReadRangeError("Start outside file")
        end = min(args.end_line or args.start_line + 99, len(lines))
        return Observation(
            items=[
                Evidence(
                    file_path=file.path,
                    language=file.language,
                    start_line=args.start_line,
                    end_line=end,
                    content="\n".join(lines[args.start_line - 1 : end]),
                )
            ]
        )

    def _search_code(self, arguments: Arguments) -> Observation:
        args = SearchCodeArguments.model_validate(arguments.model_dump())
        statement = select(SnapshotFile).where(
            SnapshotFile.snapshot_id == self.scope.snapshot_id,
            SnapshotFile.content.contains(args.query, autoescape=True),
        )
        if args.file_path is not None:
            # An unknown filter is a failure, not a misleading successful empty search.
            file = self.session.scalar(
                select(SnapshotFile.id).where(
                    SnapshotFile.snapshot_id == self.scope.snapshot_id,
                    SnapshotFile.path == args.file_path,
                )
            )
            if file is None:
                raise navigation.ResourceNotFoundError("Snapshot file not found")
            statement = statement.where(SnapshotFile.path == args.file_path)
        items: list[Evidence] = []
        files = self.session.scalars(
            statement.order_by(SnapshotFile.path).execution_options(yield_per=50)
        )
        for file in files:
            for line_number, line in enumerate(file.content.splitlines(), start=1):
                if args.query in line:
                    if len(items) == args.limit:
                        return Observation(items=items, omitted_items=1)
                    items.append(
                        Evidence(
                            file_path=file.path,
                            language=file.language,
                            start_line=line_number,
                            end_line=line_number,
                            content=line,
                        )
                    )
        return Observation(items=items)

    def _search_symbol(self, arguments: Arguments) -> Observation:
        args = SearchSymbolArguments.model_validate(arguments.model_dump())
        symbols = navigation.search_symbols(
            self.session,
            self.scope.repository_id,
            self.scope.snapshot_id,
            query=args.query,
            match=args.match,
            file_path=args.file_path,
            limit=args.limit + 1,
        )
        return Observation(
            items=[
                Evidence(
                    file_path=s.file_path,
                    language=s.language,
                    symbol_name=s.name,
                    qualified_name=s.qualified_name,
                    symbol_id=s.id,
                    start_line=s.start_line,
                    end_line=s.end_line,
                )
                for s in symbols[: args.limit]
            ],
            omitted_items=int(len(symbols) > args.limit),
        )

    def _retrieve_context(self, arguments: Arguments) -> Observation:
        args = RetrieveContextArguments.model_validate(arguments.model_dump())
        result = retrieve_evidence(
            self.session,
            repository_id=self.scope.repository_id,
            snapshot_id=self.scope.snapshot_id,
            question=args.query,
            top_k=args.top_k,
            provider=self.embedding_factory(),
            strategy=self.retrieval_strategy,
        )
        return Observation(
            items=[
                Evidence(
                    file_path=e.file_path,
                    language=e.language,
                    symbol_name=e.symbol_name,
                    qualified_name=e.qualified_name,
                    start_line=e.start_line,
                    end_line=e.end_line,
                    content=e.content,
                    rank=e.rank,
                    score=e.score,
                    distance=e.distance,
                )
                for e in result.evidence
            ]
        )
