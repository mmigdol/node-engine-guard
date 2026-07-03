# node-engine-guard

Codex plugin and CLI for checking that the `node` available to non-interactive
tools satisfies the current project's `package.json#engines.node`.

This catches a common source of confusing failures: your interactive terminal
uses `nvm`, aliases, shell functions, or a login-shell setup, while hooks and
agent subprocesses resolve a different `node` from `PATH`.

As a Codex `SessionStart` hook, `node-engine-guard` stops the session when the
project's declared Node engine does not match the Node binary Codex can actually
run. The hook uses Codex's blocking hook contract: it exits successfully and
emits `{"continue": false, ...}` on mismatch.

## Features

- Codex plugin with a blocking `SessionStart` hook
- CLI check for local debugging and CI
- Strict mode for failing CI when Node is wrong
- No Node dependency, so it can run before Node is trusted
- Supports common `engines.node` semver ranges

## Install the Codex Plugin

```sh
codex plugin marketplace add mmigdol/node-engine-guard
codex plugin add node-engine-guard@node-engine-guard
```

Restart Codex after enabling or upgrading the plugin. Existing Codex TUI windows
and app-server processes may have already loaded their hook registry. The TUI may
ask you to review and trust the new hook the first time it sees it.

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

## Verify Manually

To see the same check yourself in a project, run:

```sh
node-engine-guard --json
```

Do not install the Codex hook with `install.sh --codex-hook`. That legacy path
edits `~/.codex/config.toml` directly and is not the recommended hook mechanism
for current Codex builds.

If you intentionally want non-blocking hook behavior in a custom hook, add
`--soft` to the hook command. Soft mode exits `0`, emits `continue:true`, and
injects context for the agent.

## Why SessionStart, Not PreToolUse?

This guard checks a project-level invariant: "the non-interactive Node available
to Codex satisfies this project's `package.json#engines.node`." A `SessionStart`
hook catches that before work begins and applies even if the agent never calls
`bash`.

A `PreToolUse` hook is useful when the goal is specifically to block one tool
call, such as `bash`, with exit code `2`. It is not the best default here because
it fires later, repeats on every matching tool call, and can miss workflows that
do not invoke that tool.

## Use

```sh
node-engine-guard
node-engine-guard --cwd /path/to/project
node-engine-guard --strict
node-engine-guard --json
node-engine-guard --codex-hook --soft
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
