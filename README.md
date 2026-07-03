# node-engine-guard

Codex hook and CLI for checking that the `node` available to non-interactive
tools satisfies the current project's `package.json#engines.node`.

This catches a common source of confusing failures: your interactive terminal
uses `nvm`, aliases, shell functions, or a login-shell setup, while hooks and
agent subprocesses resolve a different `node` from `PATH`.

As a Codex `SessionStart` hook, `node-engine-guard` warns the agent when the
project's declared Node engine does not match the Node binary Codex can actually
run. It exits successfully by default, so it adds context without blocking your
session.

## Features

- Codex `SessionStart` hook mode with valid hook JSON output
- CLI check for local debugging and CI
- Strict mode for failing CI when Node is wrong
- No Node dependency, so it can run before Node is trusted
- Supports common `engines.node` semver ranges

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/mmigdol/node-engine-guard/main/install.sh | sh
```

The installer writes a dependency-free Python CLI to:

```text
~/.local/bin/node-engine-guard
```

## Use

```sh
node-engine-guard
node-engine-guard --cwd /path/to/project
node-engine-guard --strict
node-engine-guard --json
```

By default the command exits `0` and prints a warning or success message.
Use `--strict` in CI to fail when the resolved non-interactive Node does not
satisfy `engines.node`.

## Codex Hook

Print a Codex hook snippet:

```sh
node-engine-guard --print-codex-install
```

Manual example:

```toml
[hooks]
SessionStart = [
  { matcher = "startup|resume|clear|compact", hooks = [
    { type = "command", command = "/Users/you/.local/bin/node-engine-guard --codex-hook", timeout = 5 }
  ] }
]
```

As a Codex `SessionStart` hook, the guard exits `0` and injects warning context
only when there is a mismatch. It does not block sessions by default.

## Why not just rely on nvm?

`nvm` is usually loaded by interactive shell startup files. Non-interactive
subprocesses often do not source those files, so `node` may resolve to a stale
global install or may not exist at all. This tool checks what the subprocess
actually sees.

## Supported ranges

The built-in range checker supports common `engines.node` forms:

- exact versions like `22.22.2`
- major/minor shorthands like `22` or `22.22`
- comparators like `>=22 <23`
- caret and tilde ranges like `^22.0.0` and `~22.22.0`
- OR ranges like `^20.19.0 || >=22`

It is intentionally dependency-free so it can run before Node is trusted.

## Development

```sh
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s tests
PYTHONPATH=src /usr/bin/python3 -m node_engine_guard --json
```
