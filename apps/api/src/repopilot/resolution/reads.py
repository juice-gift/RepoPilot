"""Current revision reads. V1/V2 indexed evidence stays explicitly baseline-only."""

from repopilot.agent.tools import (
    ListFilesArguments,
    ReadFileArguments,
    SearchCodeArguments,
)
from repopilot.resolution.workspace import Workspace, WorkspaceError


class WorkspaceReader:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def list_files(self, args: ListFilesArguments) -> dict[str, object]:
        paths = sorted(self.workspace.sources())
        return self._result(
            [{"path": path} for path in paths[args.offset : args.offset + args.limit]],
            omitted=max(0, len(paths) - args.offset - args.limit),
        )

    def read_file(self, args: ReadFileArguments) -> dict[str, object]:
        end = args.end_line or args.start_line + 99
        if end < args.start_line or end - args.start_line + 1 > 200:
            raise WorkspaceError("Read range must contain 1 to 200 lines")
        lines = self.workspace.read(args.path).splitlines()
        if args.start_line > len(lines):
            raise WorkspaceError("Read range starts outside the file")
        end = min(end, len(lines))
        content = "\n".join(lines[args.start_line - 1 : end])
        return self._result(
            [
                {
                    "path": args.path,
                    "start_line": args.start_line,
                    "end_line": end,
                    "content": content[:8000],
                    "truncated": len(content) > 8000,
                }
            ]
        )

    def search_code(self, args: SearchCodeArguments) -> dict[str, object]:
        sources = self.workspace.sources()
        if args.file_path is not None:
            sources = {args.file_path: self.workspace.read(args.file_path)}
        items: list[dict[str, object]] = []
        for path, content in sorted(sources.items()):
            for line, text in enumerate(content.splitlines(), 1):
                if args.query in text:
                    if len(items) == args.limit:
                        return self._result(items, omitted=1)
                    items.append(
                        {
                            "path": path,
                            "line": line,
                            "content": text[:1000],
                            "truncated": len(text) > 1000,
                        }
                    )
        return self._result(items)

    def _result(
        self, items: list[dict[str, object]], omitted: int = 0
    ) -> dict[str, object]:
        return {
            "basis": "current_workspace",
            "workspace_id": self.workspace.workspace_id,
            "revision": self.workspace.revision,
            "items": items,
            "omitted": omitted,
        }
