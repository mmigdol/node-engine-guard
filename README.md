# node-engine-guard

Codex plugin and CLI for checking that the `node` available to non-interactive
tools satisfies the current project's `package.json#engines.node`.

This catches a common source of confusing failures: your interactive terminal
uses `nvm`, aliases, shell functions, or a login-shell setup, while hooks and
agent subprocesses resolve a different `node` from `PATH`.

As a Codex `SessionStart` hook, `node-engine-guard` warns the agent when the
project's declared Node engine does not match the Node binary Codex can actually
run. It exits successfully by default, so it adds context without blocking your
session.

## Features

- Codex plugin with a `SessionStart` hook
- CLI check for local debugging and CI
- Strict mode for failing CI when Node is wrong
- No Node dependency, so it can run before Node is trusted
- Supports common `engines.node` semver ranges

## Install the Codex Plugin

```sh
codex marketplace add mmigdol/node-engine-guard
```

Then open the Codex app plugin marketplace and install **Node Engine Guard** from
the `node-engine-guard` marketplace.

Restart Codex after enabling the plugin. The TUI may ask you to review and trust
the new hook the first time it sees it.

This is the recommended install path. It lets Codex manage the plugin and hook
instead of asking a shell script to edit `~/.codex/config.toml`.

## CLI Install

The CLI is optional. Install it if you want to run checks manually or in CI:

```sh
curl -fsSL https://raw.githubusercontent.com/mmigdol/node-engine-guard/main/install.sh | sh
```

The installer writes a dependency-free Python CLI to:

```text
~/.local/bin/node-engine-guard
```

## Legacy Manual Hook Install

Prefer the plugin install above. This path exists for environments where Codex
plugin marketplaces are unavailable.

Install the CLI and add the hook when it is safe to patch `~/.codex/config.toml`
automatically:

```sh
curl -fsSL https://raw.githubusercontent.com/mmigdol/node-engine-guard/main/install.sh | sh -s -- --codex-hook
```

Manual install:

1. Print the hook block with your local install path:

   ```sh
   ~/.local/bin/node-engine-guard --print-codex-install
   ```

2. Add the printed block to `~/.codex/config.toml`.

3. Restart Codex. The TUI may ask you to review and trust the new hook the first
   time it sees it.

The hook block looks like this:

```toml
[hooks]
SessionStart = [
  { matcher = "startup|resume|clear|compact", hooks = [
    { type = "command", command = "/Users/you/.local/bin/node-engine-guard --codex-hook", timeout = 5 }
  ] }
]
```

As a Codex `SessionStart` hook, the guard exits `0` and injects warning context
only when there is a mismatch. It also emits a user-visible hook message so the
TUI can show the mismatch instead of only passing it to the agent. It does not
block sessions by default.

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
PYTHONPATH=plugins/node-engine-guard/src /usr/bin/python3 -m unittest discover -s tests
PYTHONPATH=plugins/node-engine-guard/src /usr/bin/python3 -m node_engine_guard --json
```
