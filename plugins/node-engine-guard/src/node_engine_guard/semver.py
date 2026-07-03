from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional, Tuple


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


ParsedVersion = Tuple[Optional[int], Optional[int], Optional[int]]


def parse_partial_version(value: str) -> ParsedVersion | None:
    match = re.search(r"v?(\d+)(?:\.(\d+|x|\*))?(?:\.(\d+|x|\*))?", value, re.I)
    if not match:
        return None

    parts: list[int | None] = []
    for part in match.groups():
        if part is None or part.lower() in {"x", "*"}:
            parts.append(None)
        else:
            parts.append(int(part))
    return parts[0], parts[1], parts[2]


def parse_version(value: str) -> Version | None:
    parsed = parse_partial_version(value)
    if parsed is None or any(part is None for part in parsed):
        return None
    major, minor, patch = parsed
    return Version(major, minor, patch)


def _fill(parsed: ParsedVersion) -> Version:
    return Version(*(part if part is not None else 0 for part in parsed))


def _wildcard_bounds(parsed: ParsedVersion) -> tuple[Version, Version]:
    lower = list(_fill(parsed).__dict__.values())
    wildcard_index = next(i for i, part in enumerate(parsed) if part is None)
    increment_index = max(0, wildcard_index - 1)
    upper = lower[:]
    upper[increment_index] += 1
    for index in range(increment_index + 1, 3):
        upper[index] = 0
    return Version(*lower), Version(*upper)


def satisfies_comparator(version: Version, comparator: str) -> bool:
    comparator = comparator.strip()
    if not comparator or comparator in {"*", "x", "X"}:
        return True

    match = re.match(r"^(>=|<=|>|<|=)?\s*v?(.+)$", comparator)
    if not match:
        return False

    op = match.group(1) or "="
    parsed = parse_partial_version(match.group(2).strip())
    if parsed is None:
        return False

    if op == "=" and any(part is None for part in parsed):
        lower, upper = _wildcard_bounds(parsed)
        return lower <= version < upper

    target = _fill(parsed)
    if op == "=":
        return version == target
    if op == ">=":
        return version >= target
    if op == "<=":
        return version <= target
    if op == ">":
        return version > target
    if op == "<":
        return version < target
    return False


def _expand_caret(token: str) -> list[str]:
    base = parse_version(token[1:])
    if base is None:
        return [token]
    if base.major > 0:
        upper = Version(base.major + 1, 0, 0)
    elif base.minor > 0:
        upper = Version(base.major, base.minor + 1, 0)
    else:
        upper = Version(base.major, base.minor, base.patch + 1)
    return [f">={base}", f"<{upper}"]


def _expand_tilde(token: str) -> list[str]:
    parsed = parse_partial_version(token[1:])
    if parsed is None:
        return [token]
    base = _fill(parsed)
    upper = Version(base.major, base.minor + 1, 0)
    return [f">={base}", f"<{upper}"]


def _comparators(raw_range: str) -> list[list[str]]:
    alternatives: list[list[str]] = []
    for alternative in [part.strip() for part in raw_range.split("||") if part.strip()]:
        hyphen = re.match(r"^(.+?)\s+-\s+(.+?)$", alternative)
        if hyphen:
            alternatives.append([f">={hyphen.group(1)}", f"<={hyphen.group(2)}"])
            continue

        comparators: list[str] = []
        for token in alternative.split():
            if token.startswith("^"):
                comparators.extend(_expand_caret(token))
            elif token.startswith("~"):
                comparators.extend(_expand_tilde(token))
            else:
                comparators.append(token)
        alternatives.append(comparators)
    return alternatives


def satisfies_range(version: Version, raw_range: str) -> bool:
    alternatives = _comparators(raw_range)
    if not alternatives:
        return True
    return any(
        all(satisfies_comparator(version, comparator) for comparator in comparators)
        for comparators in alternatives
    )
