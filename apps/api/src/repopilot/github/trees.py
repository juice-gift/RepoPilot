"""Compute exact nested Git trees from immutable blob metadata, without execution."""

import hashlib
import re
from collections.abc import Mapping

from repopilot.github.client import GitHubMCPError


def object_hash(kind: str, raw: bytes) -> str:
    return hashlib.sha1(f"{kind} {len(raw)}\0".encode() + raw).hexdigest()


def nested_tree(entries: Mapping[str, Mapping[str, str]]) -> str:
    if len(entries) > 5000:
        raise GitHubMCPError("git_tree_limit")
    root: dict = {}
    for path, value in entries.items():
        if (
            not isinstance(path, str)
            or len(path) > 500
            or "\\" in path
            or any(part in {"", ".", ".."} or "\0" in part for part in path.split("/"))
            or value.get("mode") not in {"100644", "100755", "120000"}
            or not re.fullmatch(r"[a-f0-9]{40}", value.get("sha", ""))
        ):
            raise GitHubMCPError("git_tree_entry_invalid")
        node = root
        parts = path.split("/")
        for part in parts[:-1]:
            if part in node and not isinstance(node[part], dict):
                raise GitHubMCPError("git_tree_path_collision")
            node = node.setdefault(part, {})
        if parts[-1] in node:
            raise GitHubMCPError("git_tree_path_collision")
        node[parts[-1]] = (value["mode"], value["sha"])

    def encode(node: dict) -> str:
        data = []
        # Git compares directory names as if they end with '/', using UTF-8 bytes.
        for name, child in sorted(
            node.items(),
            key=lambda item: (
                item[0] + ("/" if isinstance(item[1], dict) else "")
            ).encode(),
        ):
            mode, sha = ("40000", encode(child)) if isinstance(child, dict) else child
            data.append(
                mode.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(sha)
            )
        return object_hash("tree", b"".join(data))

    return encode(root)


def replace_blobs(
    entries: Mapping[str, Mapping[str, str]], files: Mapping[str, str]
) -> dict[str, dict[str, str]]:
    result = {path: dict(value) for path, value in entries.items()}
    for path, content in files.items():
        if path not in result or result[path]["mode"] not in {"100644", "100755"}:
            raise GitHubMCPError("publication_edit_not_regular_file")
        result[path]["sha"] = object_hash("blob", content.encode())
    nested_tree(result)
    return result
