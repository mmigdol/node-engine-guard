#!/usr/bin/env sh
set -eu

repo_url="https://raw.githubusercontent.com/mmigdol/node-engine-guard/main/plugins/node-engine-guard/src/node_engine_guard"
target_dir="${HOME}/.local/lib/node-engine-guard"
bin_dir="${HOME}/.local/bin"
install_codex_hook=0

usage() {
  cat <<'EOF'
Usage: install.sh [--codex-hook] [--help]

Options:
  --codex-hook  Install the CLI and add a Codex SessionStart hook when safe.
  --help        Show this help.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --codex-hook)
      install_codex_hook=1
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
  echo "Next: print the Codex hook block and add it to ~/.codex/config.toml:"
  echo "  ${bin_dir}/node-engine-guard --print-codex-install"
}

install_codex_hook() {
  codex_dir="${HOME}/.codex"
  codex_config="${codex_dir}/config.toml"
  hook_command="${bin_dir}/node-engine-guard --codex-hook"

  if [ -f "${codex_config}" ] && grep -Fq "${hook_command}" "${codex_config}"; then
    echo "Codex hook already installed in ${codex_config}"
    return 0
  fi

  if [ -f "${codex_config}" ] && grep -Eq '^[[:space:]]*\[hooks\][[:space:]]*$' "${codex_config}"; then
    echo "A [hooks] table already exists in ${codex_config}; not editing it automatically." >&2
    echo "Merge this hook manually:" >&2
    "${bin_dir}/node-engine-guard" --print-codex-install >&2
    return 1
  fi

  mkdir -p "${codex_dir}"
  if [ -f "${codex_config}" ]; then
    backup="${codex_config}.bak.$(date +%Y%m%d%H%M%S)"
    cp "${codex_config}" "${backup}"
    echo "Backed up ${codex_config} to ${backup}"
  fi

  cat >> "${codex_config}" <<EOF

# node-engine-guard Codex hook
[hooks]
SessionStart = [
  { matcher = "startup|resume|clear|compact", hooks = [
    { type = "command", command = "${hook_command}", timeout = 5 }
  ] }
]
EOF

  echo "Installed Codex hook in ${codex_config}"
  echo "Restart Codex. The TUI may ask you to review and trust the new hook."
}

if [ "${install_codex_hook}" -eq 1 ]; then
  install_codex_hook
else
  print_codex_next_step
fi
