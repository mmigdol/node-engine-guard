from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess

from .semver import Version, parse_version, satisfies_range


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    message: str
    package_json: Path | None = None
    engine: str | None = None
    node_path: str | None = None
    node_version: Version | None = None


def find_package_json(start: Path) -> Path | None:
    path = start.expanduser().resolve()
    if path.is_file():
        path = path.parent
    for candidate in [path, *path.parents]:
        package_json = candidate / "package.json"
        if package_json.is_file():
            return package_json
    return None


def read_node_engine(package_json: Path) -> str | None:
    try:
        data = json.loads(package_json.read_text())
    except Exception:
        return None
    engine = data.get("engines", {}).get("node")
    return engine.strip() if isinstance(engine, str) and engine.strip() else None


def resolve_node(timeout: float = 5.0) -> tuple[str | None, Version | None, str | None]:
    node_path = shutil.which("node")
    if node_path is None:
        return None, None, "node was not found on the non-interactive PATH"

    try:
        result = subprocess.run(
            [node_path, "-p", "process.version + '|' + process.execPath"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except Exception as error:
        return node_path, None, f"node at {node_path} could not run: {error}"

    version_text, _, exec_path = result.stdout.strip().partition("|")
    version = parse_version(version_text)
    if version is None:
        return node_path, None, f"node at {node_path} returned an unparsable version: {version_text}"
    return exec_path or node_path, version, None


def check_node_engine(cwd: Path) -> CheckResult:
    package_json = find_package_json(cwd)
    if package_json is None:
        return CheckResult(True, "No package.json found.")

    engine = read_node_engine(package_json)
    if engine is None:
        return CheckResult(True, f"No engines.node found in {package_json}.", package_json=package_json)

    node_path, node_version, error = resolve_node()
    if error:
        return CheckResult(
            False,
            f"`package.json` requires engines.node `{engine}`, but {error}.",
            package_json=package_json,
            engine=engine,
            node_path=node_path,
            node_version=node_version,
        )

    if node_version is None or not satisfies_range(node_version, engine):
        return CheckResult(
            False,
            (
                f"Non-interactive node does not satisfy engines.node. "
                f"Project: {package_json.parent}. Required: `{engine}`. "
                f"Resolved: `{node_path}` ({node_version})."
            ),
            package_json=package_json,
            engine=engine,
            node_path=node_path,
            node_version=node_version,
        )

    return CheckResult(
        True,
        f"Non-interactive node satisfies engines.node `{engine}`: {node_path} ({node_version}).",
        package_json=package_json,
        engine=engine,
        node_path=node_path,
        node_version=node_version,
    )
