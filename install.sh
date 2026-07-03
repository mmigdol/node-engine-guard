#!/usr/bin/env sh
set -eu

repo_url="https://raw.githubusercontent.com/mmigdol/node-engine-guard/main/plugins/node-engine-guard/src/node_engine_guard"
target_dir="${HOME}/.local/lib/node-engine-guard"
bin_dir="${HOME}/.local/bin"
request_codex_hook=0

usage() {
  cat <<'EOF'
Usage: install.sh [--codex-hook] [--help]

Options:
  --codex-hook  Deprecated. Install the Codex plugin instead.
  --help        Show this help.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --codex-hook)
      request_codex_hook=1
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

mkdir -p "${target_dir}/node_engine_guard" "${bin_dir}"

curl -fsSL "${repo_url}/__init__.py" -o "${target_dir}/node_engine_guard/__init__.py"
curl -fsSL "${repo_url}/__main__.py" -o "${target_dir}/node_engine_guard/__main__.py"
curl -fsSL "${repo_url}/cli.py" -o "${target_dir}/node_engine_guard/cli.py"
curl -fsSL "${repo_url}/check.py" -o "${target_dir}/node_engine_guard/check.py"
curl -fsSL "${repo_url}/semver.py" -o "${target_dir}/node_engine_guard/semver.py"

cat > "${bin_dir}/node-engine-guard" <<EOF
#!/usr/bin/env sh
PYTHONPATH="${target_dir}" exec /usr/bin/python3 -m node_engine_guard "\$@"
EOF
chmod +x "${bin_dir}/node-engine-guard"

echo "Installed ${bin_dir}/node-engine-guard"
echo

print_codex_next_step() {
  echo "Next: install the Codex plugin to enable the SessionStart hook:"
  echo "  codex plugin marketplace add mmigdol/node-engine-guard"
  echo "  codex plugin add node-engine-guard@node-engine-guard"
}

if [ "${request_codex_hook}" -eq 1 ]; then
  echo "--codex-hook is deprecated for install.sh." >&2
  echo "The CLI was installed, but no Codex config was edited." >&2
  echo "Install the Codex plugin instead:" >&2
  echo "  codex plugin marketplace add mmigdol/node-engine-guard" >&2
  echo "  codex plugin add node-engine-guard@node-engine-guard" >&2
  exit 1
else
  print_codex_next_step
fi
