#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "usage: publish_release_asset_v1.sh <tag> <package> <receipt>" >&2
  exit 2
fi

TAG="$1"
PACKAGE="$2"
RECEIPT="$3"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY required}"
: "${GH_TOKEN:?GH_TOKEN required}"

for f in "$PACKAGE" "$RECEIPT"; do
  test -f "$f"
done

PKG_SHA="$(sha256sum "$PACKAGE" | awk '{print $1}')"
PKG_SIZE="$(stat -c %s "$PACKAGE")"
REC_SHA="$(sha256sum "$RECEIPT" | awk '{print $1}')"

if ! gh release view "$TAG" --repo "$GITHUB_REPOSITORY" >/dev/null 2>&1; then
  gh release create "$TAG"     --repo "$GITHUB_REPOSITORY"     --target "$GITHUB_SHA"     --title "Coreum V0.8 replay data $TAG"     --notes "Frozen V0.8 replay transport/checkpoint storage. Source/science unchanged."
fi

gh release upload "$TAG" "$PACKAGE" "$RECEIPT" --repo "$GITHUB_REPOSITORY" --clobber

RELEASE_JSON="$(gh api "repos/$GITHUB_REPOSITORY/releases/tags/$TAG")"
export RELEASE_JSON PACKAGE_NAME="$(basename "$PACKAGE")" RECEIPT_NAME="$(basename "$RECEIPT")" PKG_SHA PKG_SIZE REC_SHA
python3 - <<'PY'
import json, os, sys
j=json.loads(os.environ["RELEASE_JSON"])
assets={a["name"]:a for a in j.get("assets",[])}
pkg_name=os.environ["PACKAGE_NAME"]
rec_name=os.environ["RECEIPT_NAME"]
for name in (pkg_name,rec_name):
    if name not in assets:
        raise SystemExit(f"asset missing after upload: {name}")
pkg=assets[pkg_name]
rec=assets[rec_name]
want_pkg="sha256:"+os.environ["PKG_SHA"]
want_rec="sha256:"+os.environ["REC_SHA"]
if int(pkg["size"]) != int(os.environ["PKG_SIZE"]):
    raise SystemExit("uploaded package size mismatch")
if pkg.get("digest") != want_pkg:
    raise SystemExit(f"uploaded package digest mismatch got={pkg.get('digest')} want={want_pkg}")
if rec.get("digest") != want_rec:
    raise SystemExit(f"uploaded receipt digest mismatch got={rec.get('digest')} want={want_rec}")
print(json.dumps({
    "tag":j["tag_name"],
    "release_id":j["id"],
    "package":{
        "asset_id":pkg["id"],
        "name":pkg["name"],
        "size":pkg["size"],
        "digest":pkg["digest"],
        "state":pkg["state"],
    },
    "receipt":{
        "asset_id":rec["id"],
        "name":rec["name"],
        "size":rec["size"],
        "digest":rec["digest"],
        "state":rec["state"],
    },
    "remote_digest_verification_pass":True,
},indent=2,sort_keys=True))
PY
