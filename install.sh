#!/usr/bin/env sh
set -eu

repo_url="https://raw.githubusercontent.com/mmigdol/node-engine-guard/main/src/node_engine_guard"
target_dir="${HOME}/.local/lib/node-engine-guard"
bin_dir="${HOME}/.local/bin"

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
echo "For Codex hook setup, run:"
echo "  ${bin_dir}/node-engine-guard --print-codex-install"
