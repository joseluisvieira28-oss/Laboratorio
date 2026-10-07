#!/usr/bin/env bash
# Public secret-4 snapshot restore. Validators and full nodes.
#   curl -fsSL -H 'Cache-Control: no-cache' -o restore.sh "https://docs.scrt.network/restore.sh?t=$(date +%s)" && bash restore.sh
#
# Verifies the tarball, deletes ~/.secretd/data and .compute, installs the
# snapshot. Keeps config.toml, priv_validator_key.json, and .node/.
# Writes data/priv_validator_state.json at height 0.
# Refuses archive-00 and archive-01.

set -euo pipefail

BASE="${SNAPSHOT_BASE:-https://mainnet-secret-snapshot.secret3.dev}"
NODE_HOME="${NODE_HOME:-${HOME}/.secretd}"
DATA="${NODE_HOME}/data"
SERVICE="${SERVICE:-secret-node}"
WORKDIR="${TMPDIR:-/tmp}/secret-snapshot-restore"
UPGRADE_HEIGHT=27286266

die() { echo "FATAL: $*" >&2; exit 1; }
ok() { echo "OK  $*"; }

was_running=0
data_removed=0
run_root() {
  if [[ -n "${SUDO+x}" ]]; then
    if [[ -n "$SUDO" ]]; then "$SUDO" "$@"; else "$@"; fi
  elif [[ "$(id -u)" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}
restart_if_abandoned() {
  local rc=$?
  if (( rc != 0 && was_running == 1 && data_removed == 0 )); then
    run_root systemctl start "$SERVICE" || true
  fi
  exit "$rc"
}
trap restart_if_abandoned EXIT

host="$(hostname -s 2>/dev/null || hostname)"
case "$host" in
  archive-01|archive-00)
    die "refusing hostname ${host}; this pruned snapshot is not for an archive node"
    ;;
esac

command -v curl >/dev/null || die "curl missing"
command -v tar >/dev/null || die "tar missing"
command -v sha256sum >/dev/null || die "sha256sum missing"
command -v jq >/dev/null || die "jq missing"
command -v zstd >/dev/null || command -v pzstd >/dev/null || die "zstd missing"
command -v secretd >/dev/null || die "secretd missing"

ver_line="$(secretd version 2>/dev/null | awk 'NF {print; exit}')"
[[ "$ver_line" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+) ]] || die "cannot read secretd version (got: ${ver_line:-empty})"
if (( BASH_REMATCH[1] < 1 || (BASH_REMATCH[1] == 1 && BASH_REMATCH[2] < 27) || (BASH_REMATCH[1] == 1 && BASH_REMATCH[2] == 27 && BASH_REMATCH[3] < 2) )); then
  die "secretd ${ver_line} is older than 1.27.2. Nothing was changed."
fi

if [[ -s "${NODE_HOME}/.node/new_seed.json" ]]; then
  echo "registration seed ${NODE_HOME}/.node/new_seed.json"
elif [[ -s "${NODE_HOME}/.node/seed.json" ]]; then
  echo "registration seed ${NODE_HOME}/.node/seed.json"
else
  die "no ${NODE_HOME}/.node/new_seed.json (or seed.json). Register first (tx register auth). Nothing was changed."
fi

mkdir -p "$WORKDIR"
cd "$WORKDIR"

echo "Fetching ${BASE}/latest.json"
curl -fsSL "${BASE}/latest.json" -o latest.json
chain="$(jq -r '.chain_id // empty' latest.json)"
file="$(jq -r '.file // empty' latest.json)"
sha="$(jq -r '.sha256 // empty' latest.json)"
size="$(jq -r '.size_bytes // empty' latest.json)"
unpacked="$(jq -r '.unpacked_bytes // empty' latest.json)"
height="$(jq -r '.height // empty' latest.json)"

[[ "$chain" == "secret-4" ]] || die "unexpected chain_id ${chain:-empty}"
[[ "$file" =~ ^secret-4-[0-9]+-[0-9]{8}T[0-9]{6}Z\.tar\.zst$ ]] || die "latest.json file is not a snapshot name: ${file}"
[[ "$sha" =~ ^[0-9a-fA-F]{64}$ ]] || die "latest.json missing sha256"
[[ "$height" =~ ^[0-9]+$ && "$size" =~ ^[0-9]+$ && "$unpacked" =~ ^[0-9]+$ ]] || die "latest.json height or size is not an integer"
(( height > UPGRADE_HEIGHT )) || die "snapshot height ${height} is not above upgrade height ${UPGRADE_HEIGHT}. Nothing was changed."
echo "Snapshot height=${height} file=${file}"

local_status="$(curl -fsS --max-time 3 http://127.0.0.1:26657/status 2>/dev/null || true)"
if [[ -n "$local_status" ]]; then
  local_height="$(jq -r '.result.sync_info.latest_block_height // empty' <<<"$local_status")"
  if [[ "$local_height" =~ ^[0-9]+$ && "$local_height" -gt "$height" ]]; then
    die "this node is at ${local_height}, snapshot is ${height}. Do not restore this snapshot onto this enclave. Nothing was changed.

The blocks above the snapshot are still on disk. Put those blocks back.

This consensus key is already a live validator. Do not register a second seed to get past the snapshot."
  fi
fi

if [[ -z "$local_status" && ( -d "${DATA}/application.db" || -d "${DATA}/blockstore.db" ) ]]; then
  die "127.0.0.1:26657 did not answer and ${DATA} already has a blockstore. Start the node so the height can be compared. Nothing was changed."
fi

kb="$(df -P -k "$NODE_HOME" | awk 'NR==2 {print $4}')"
[[ "$kb" =~ ^[0-9]+$ ]] || die "cannot read free space for ${NODE_HOME}"
need=$((size + unpacked + unpacked / 10))
(( kb * 1024 > need )) || die "not enough free space on ${NODE_HOME}"

echo "Downloading ${BASE}/${file}"
curl -fL --retry 3 -C - -o "$file" "${BASE}/${file}"
got_sha="$(sha256sum "$file" | awk '{print $1}' | tr 'A-F' 'a-f')"
[[ "$got_sha" == "$(printf '%s' "$sha" | tr 'A-F' 'a-f')" ]] || die "sha256 mismatch for ${file}. Nothing was changed."

if command -v systemctl >/dev/null && systemctl cat "${SERVICE}.service" >/dev/null 2>&1; then
  unit_installed=1
  if systemctl is-active --quiet "$SERVICE"; then
    was_running=1
    run_root systemctl stop "$SERVICE" || die "systemctl stop ${SERVICE} failed. Nothing was changed."
    systemctl is-active --quiet "$SERVICE" && die "${SERVICE} is still active after stop. Nothing was changed."
  fi
else
  unit_installed=0
fi

stage="${NODE_HOME}/.snapshot-restore-new"
rm -rf "$stage"
mkdir -p "$stage"
set -o pipefail
if command -v pzstd >/dev/null; then
  pzstd -dc "$file" | tar -xf - -C "$stage"
else
  tar -I zstd -xf "$file" -C "$stage"
fi

[[ -d "${stage}/data/application.db" ]] || die "archive has no data/application.db. Nothing was changed."
got_chain="$(jq -r '.chain_id // empty' "${stage}/config/genesis.json")"
[[ "$got_chain" == "secret-4" ]] || die "archive genesis chain_id is ${got_chain:-missing}. Nothing was changed."

data_removed=1
rm -rf "$DATA" "${NODE_HOME}/.compute"
mv "${stage}/data" "$DATA"
if [[ -d "${stage}/.compute" ]]; then
  mv "${stage}/.compute" "${NODE_HOME}/.compute"
fi
mkdir -p "${NODE_HOME}/config"
[[ -f "${stage}/config/genesis.json" ]] && cp -a "${stage}/config/genesis.json" "${NODE_HOME}/config/genesis.json"
[[ -f "${stage}/config/addrbook.json" ]] && cp -a "${stage}/config/addrbook.json" "${NODE_HOME}/config/addrbook.json"
rm -rf "$stage"
printf '%s\n' '{"height":"0","round":0,"step":0}' > "${DATA}/priv_validator_state.json"

[[ -d "${DATA}/application.db" ]] || die "application.db missing after install"

if [[ "$unit_installed" -eq 0 ]]; then
  ok "restored height=${height} into ${NODE_HOME}"
  echo "secret-node.service is not installed. Start secretd yourself."
  exit 0
fi
run_root systemctl enable --now "$SERVICE"
ok "restored height=${height} into ${NODE_HOME}"
echo "Follow logs: journalctl -u ${SERVICE} -f"
