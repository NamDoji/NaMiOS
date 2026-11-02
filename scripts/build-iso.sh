#!/usr/bin/env bash
# build-iso.sh — build ISO NaMiOS bang Debian live-build tren build host
# THAT (BUILD-001, BUILD-002, BUILD-003). KHONG duoc chay thanh cong tren
# container phat trien hien tai (Debian 12, thieu live-build/debootstrap/
# xorriso) - do la hanh vi DUNG: script phai bao loi ro + thoat non-zero,
# KHONG duoc gia lap tao ra file .iso.
#
# verified_on_host: NO — script nay CHUA duoc chay thanh cong tren bat ky
# build host nao (chi viet + kiem tra cu phap `bash -n` + review logic).
#
# AN TOAN (CLAUDE.md, bat buoc):
#   - KHONG curl|bash, KHONG tai/thuc thi noi dung tu xa.
#   - KHONG "eval", KHONG shell=True-style; moi lenh con goi bang array
#     (danh sach doc lap), khong noi chuoi vao mot chuoi roi thuc thi.
#   - Tham so dau vao chi di qua argv (case/while tren "$@"), kiem tra
#     gia tri truoc khi dung.
#   - KHONG nhung secret/production signing key vao script hay repo; chi
#     ho tro ky bang dev key NGUOI DUNG DA TU CAU HINH SAN (truyen qua
#     --sign-key-id), script khong tu tao/luu key nao.
#   - KHONG tu "lb build" bang root toan trinh neu khong can thiet — script
#     chi dung sudo cho dung lenh `lb build`/`lb clean` (live-build yeu cau
#     quyen root de debootstrap/chroot, day la yeu cau binh thuong cua
#     live-build, KHAC voi quy tac "khong chay wine bang root" (quy tac do
#     ap dung cho runner Wine o M2/M4).
#
# Cach dung:
#   scripts/build-iso.sh [--live-build-dir PATH] [--output-dir PATH]
#       [--snapshot-url URL] [--clean] [--no-sudo] [--skip-preflight]
#       [--sign-key-id KEYID] [-h|--help]
#
# Exit code:
#   0  = build thanh cong, ISO + SHA256SUMS da sinh ra that.
#   1  = loi cau hinh/thieu cong cu co ban (truoc khi goi preflight).
#   2  = loi tham so dau vao.
#   3  = host khong du dieu kien (preflight-build-host.sh bao missing_required).
#   4  = `lb build` chay nhung that bai (loi THAT tu live-build, khong gia lap qua).
#
# Xem them: distro/live-build/README.md (runbook day du), docs/specs/
# DAC_TA_HE_DIEU_HANH.md muc 14 (BUILD-001..004).

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd -P)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." >/dev/null 2>&1 && pwd -P)"

LIVE_BUILD_DIR="${REPO_ROOT}/distro/live-build"
OUTPUT_DIR="${REPO_ROOT}/build/out"
SNAPSHOT_URL=""
DO_CLEAN=0
NO_SUDO=0
SKIP_PREFLIGHT=0
SIGN_KEY_ID=""

usage() {
  cat <<EOF
build-iso.sh — build ISO NaMiOS bang Debian live-build (BUILD-001..003)

Dung:
  scripts/build-iso.sh [tuy chon]

Tuy chon:
  --live-build-dir PATH   Thu muc cau hinh live-build (mac dinh: distro/live-build).
  --output-dir PATH       Thu muc dat ISO + log + checksum sau build (mac dinh: build/out).
  --snapshot-url URL      Pin apt snapshot (vd snapshot.debian.org/...); truyen vao
                          bien NAMIOS_APT_SNAPSHOT_URL cho auto/config (BUILD-002).
  --clean                 Chay 'auto/clean --purge' truoc khi build lai tu dau.
  --no-sudo                Khong tu dong them 'sudo' truoc 'lb build'/'lb clean'
                          (dung khi ban da chay script nay bang root san).
  --skip-preflight         Bo qua buoc goi scripts/preflight-build-host.sh (KHONG
                          khuyen nghi; chi dung khi ban da tu kiem tra host).
  --sign-key-id KEYID      Ky SHA256SUMS bang dev GPG key KEYID da co san trong
                          keyring cua ban (gpg --detach-sign --local-user KEYID).
                          Script KHONG tao/luu key nao; bo trong = khong ky.
  -h, --help               In huong dan nay.

Vi du:
  scripts/build-iso.sh
  scripts/build-iso.sh --clean --output-dir /srv/namios-build/out
EOF
}

log() { printf '[build-iso] %s\n' "$*"; }
err() { printf '[build-iso] LOI: %s\n' "$*" >&2; }

# ---- parse argv (khong eval) ------------------------------------------------
while [ $# -gt 0 ]; do
  case "$1" in
    --live-build-dir)
      [ $# -ge 2 ] || { err "--live-build-dir can 1 gia tri PATH"; exit 2; }
      LIVE_BUILD_DIR="$2"; shift 2 ;;
    --output-dir)
      [ $# -ge 2 ] || { err "--output-dir can 1 gia tri PATH"; exit 2; }
      OUTPUT_DIR="$2"; shift 2 ;;
    --snapshot-url)
      [ $# -ge 2 ] || { err "--snapshot-url can 1 gia tri URL"; exit 2; }
      SNAPSHOT_URL="$2"; shift 2 ;;
    --clean)
      DO_CLEAN=1; shift ;;
    --no-sudo)
      NO_SUDO=1; shift ;;
    --skip-preflight)
      SKIP_PREFLIGHT=1; shift ;;
    --sign-key-id)
      [ $# -ge 2 ] || { err "--sign-key-id can 1 gia tri KEYID"; exit 2; }
      SIGN_KEY_ID="$2"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    --)
      shift; break ;;
    -*)
      err "tham so khong ro: $1"; usage >&2; exit 2 ;;
    *)
      err "tham so thua khong duoc ho tro: $1"; exit 2 ;;
  esac
done

if [ ! -d "${LIVE_BUILD_DIR}" ]; then
  err "khong tim thay thu muc live-build-dir: ${LIVE_BUILD_DIR}"
  exit 1
fi
if [ ! -x "${LIVE_BUILD_DIR}/auto/config" ]; then
  err "khong tim thay ${LIVE_BUILD_DIR}/auto/config (co the quen chmod +x, hoac sai --live-build-dir)"
  exit 1
fi

mkdir -p "${OUTPUT_DIR}"

# ---- 1) preflight: goi scripts/preflight-build-host.sh neu co --------------
PREFLIGHT_SCRIPT="${SCRIPT_DIR}/preflight-build-host.sh"
if [ "${SKIP_PREFLIGHT}" -eq 1 ]; then
  log "da bo qua preflight theo --skip-preflight (KHONG khuyen nghi)."
elif [ -x "${PREFLIGHT_SCRIPT}" ]; then
  log "chay preflight: ${PREFLIGHT_SCRIPT} --build-dir ${LIVE_BUILD_DIR}"
  set +e
  "${PREFLIGHT_SCRIPT}" --build-dir "${LIVE_BUILD_DIR}"
  PREFLIGHT_RC=$?
  set -e
  if [ "${PREFLIGHT_RC}" -eq 3 ]; then
    err "preflight-build-host.sh bao host THIEU dieu kien bat buoc (exit 3)."
    err "KHONG build tiep tren host nay. Xem huong dan khac phuc o output tren."
    exit 3
  elif [ "${PREFLIGHT_RC}" -ne 0 ]; then
    err "preflight-build-host.sh thoat voi ma loi khong mong doi (${PREFLIGHT_RC})."
    exit "${PREFLIGHT_RC}"
  fi
  log "preflight OK."
else
  log "khong tim thay scripts/preflight-build-host.sh (ket qua thuc thi khac tuy host) - tu kiem tra toi gian thay the."
  MISSING=0
  for tool in lb xorriso fakeroot mksquashfs; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
      err "thieu cong cu bat buoc: ${tool}. Cai: sudo apt-get install -y live-build xorriso fakeroot squashfs-tools"
      MISSING=1
    fi
  done
  if ! command -v debootstrap >/dev/null 2>&1 && ! command -v mmdebstrap >/dev/null 2>&1; then
    err "thieu debootstrap hoac mmdebstrap. Cai: sudo apt-get install -y debootstrap"
    MISSING=1
  fi
  if [ "${MISSING}" -eq 1 ]; then
    err "host nay KHONG du cong cu de build ISO. KHONG gia lap - thoat."
    exit 1
  fi
  log "kiem tra toi gian OK (khuyen nghi dung scripts/preflight-build-host.sh day du hon)."
fi

# ---- 2) tuy chon: clean truoc khi build -------------------------------------
SUDO_PREFIX=()
if [ "$(id -u)" -ne 0 ] && [ "${NO_SUDO}" -eq 0 ]; then
  SUDO_PREFIX=(sudo)
fi

if [ "${DO_CLEAN}" -eq 1 ]; then
  log "chay auto/clean --purge trong ${LIVE_BUILD_DIR}"
  (cd "${LIVE_BUILD_DIR}" && "${SUDO_PREFIX[@]}" ./auto/clean --purge)
fi

# ---- 3) auto/config ---------------------------------------------------------
log "chay auto/config trong ${LIVE_BUILD_DIR}"
if [ -n "${SNAPSHOT_URL}" ]; then
  (cd "${LIVE_BUILD_DIR}" && NAMIOS_APT_SNAPSHOT_URL="${SNAPSHOT_URL}" ./auto/config)
else
  (cd "${LIVE_BUILD_DIR}" && ./auto/config)
fi

# ---- 4) lb build + log thật -------------------------------------------------
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_OUT_DIR="${OUTPUT_DIR}/${TIMESTAMP}"
mkdir -p "${RUN_OUT_DIR}"
BUILD_LOG="${RUN_OUT_DIR}/build.log"

log "bat dau lb build (co the ton nhieu phut/chuc phut lan dau) — log: ${BUILD_LOG}"
set +e
(cd "${LIVE_BUILD_DIR}" && "${SUDO_PREFIX[@]}" lb build) 2>&1 | tee "${BUILD_LOG}"
LB_BUILD_RC=${PIPESTATUS[0]}
set -e

if [ "${LB_BUILD_RC}" -ne 0 ]; then
  err "lb build THAT BAI (exit ${LB_BUILD_RC}). Xem ${BUILD_LOG}. KHONG tao ISO gia."
  exit 4
fi

# ---- 5) tim ISO vua sinh ra, copy + checksum --------------------------------
mapfile -t ISO_FILES < <(find "${LIVE_BUILD_DIR}" -maxdepth 1 -type f -name '*.iso' 2>/dev/null)
if [ "${#ISO_FILES[@]}" -eq 0 ]; then
  err "lb build bao thanh cong (exit 0) nhung KHONG tim thay file *.iso trong ${LIVE_BUILD_DIR}."
  err "Day la mau thuan can dieu tra thu cong — KHONG tu tao ISO gia de 'cho du'."
  exit 4
fi

for iso in "${ISO_FILES[@]}"; do
  base="$(basename "${iso}")"
  cp -- "${iso}" "${RUN_OUT_DIR}/${base}"
  log "da copy ${base} -> ${RUN_OUT_DIR}/${base}"
done

(cd "${RUN_OUT_DIR}" && sha256sum -- *.iso > SHA256SUMS)
log "da sinh SHA256SUMS tai ${RUN_OUT_DIR}/SHA256SUMS"

# ---- 6) SBOM best-effort (khong fail build chi vi thieu tool SBOM) ---------
SBOM_NOTE="khong sinh duoc"
if command -v syft >/dev/null 2>&1; then
  if syft "dir:${LIVE_BUILD_DIR}/chroot" -o spdx-json > "${RUN_OUT_DIR}/sbom.spdx.json" 2>"${RUN_OUT_DIR}/sbom.syft.stderr.log"; then
    SBOM_NOTE="sinh boi syft -> sbom.spdx.json"
  else
    SBOM_NOTE="syft co mat nhung chay loi, xem sbom.syft.stderr.log"
  fi
else
  log "CANH BAO: khong tim thay cong cu SBOM ('syft'). BUILD-003 yeu cau SBOM trong artifact phat hanh;"
  log "  khong tu che SBOM gia o day. Cai syft hoac cong cu SBOM tuong duong roi build lai truoc khi phat hanh."
fi

# ---- 7) ky dev key tuy chon (khong bao gio ky bang production key o day) --
SIGN_NOTE="khong ky (mac dinh)"
if [ -n "${SIGN_KEY_ID}" ]; then
  if command -v gpg >/dev/null 2>&1; then
    if (cd "${RUN_OUT_DIR}" && gpg --batch --yes --local-user "${SIGN_KEY_ID}" --detach-sign --armor SHA256SUMS); then
      SIGN_NOTE="da ky bang dev key ${SIGN_KEY_ID} -> SHA256SUMS.asc"
      log "da ky SHA256SUMS bang dev key ${SIGN_KEY_ID} (CHI dung trong lab; key production do maintainer giu rieng)."
    else
      SIGN_NOTE="yeu cau ky bang ${SIGN_KEY_ID} nhung gpg loi — kiem tra key co trong keyring khong"
      err "${SIGN_NOTE}"
    fi
  else
    SIGN_NOTE="yeu cau ky nhung khong co lenh 'gpg' tren host"
    err "${SIGN_NOTE}"
  fi
fi

# ---- 8) tong ket -------------------------------------------------------------
log "BUILD HOAN TAT (lb build exit 0, ISO + SHA256SUMS da sinh ra THAT)."
log "  output: ${RUN_OUT_DIR}"
log "  SBOM:   ${SBOM_NOTE}"
log "  ky:     ${SIGN_NOTE}"
log ""
log "BUOC CON THIEU truoc khi coi la artifact phat hanh (BUILD-003):"
log "  - Cap nhat distro/live-build/build-manifest.yaml bang gia tri THAT (snapshot/kernel/package/commit)."
log "  - Viet test report (xem scripts/boot-test-qemu.sh) + release notes."
log "  - Neu chua co SBOM/chu ky o tren, bo sung truoc khi phat hanh ra ngoai lab."

exit 0
