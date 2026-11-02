#!/usr/bin/env bash
# boot-test-qemu.sh — boot-test mot ISO NaMiOS bang qemu-system-x86_64 +
# OVMF (UEFI), che do Live, KHONG GHI DIA (khong gan bat ky virtual hard
# disk nao - chi CD-ROM read-only). Lien quan INSTALL-001 ("Live mode thu
# khong ghi o trong") va INSTALL-002 (UEFI bat buoc tren danh sach phan
# cung pilot).
#
# verified_on_host: NO — script nay CHUA duoc chay thanh cong (container
# phat trien hien tai KHONG co qemu-system-x86_64 va KHONG co /dev/kvm —
# xem docs/_m0_inventory_raw.md). Da kiem cu phap bang `bash -n` + review
# logic, CHUA boot thuc mot ISO nao.
#
# AN TOAN (CLAUDE.md):
#   - KHONG curl|bash, KHONG eval, KHONG shell=True-style.
#   - Tham so (duong dan ISO, RAM, OVMF...) chi qua argv.
#   - KHONG gan virtual disk nao vao VM (chi -cdrom, read-only) => dung
#     voi "Live mode khong ghi o trong".
#   - OVMF_VARS can mot ban copy GHI DUOC rieng (yeu cau cua UEFI
#     firmware), nhung ban copy nay nam trong thu muc tam (mktemp -d) va
#     bi xoa khi script ket thuc (trap EXIT) — KHONG ghi vao anh ISO,
#     KHONG ghi vao dia cung thuc cua may build.
#   - Neu thieu qemu/kvm/ovmf => bao "BLOCKED" + thoat non-zero, KHONG tu
#     bao "da boot thanh cong".
#
# Cach dung:
#   scripts/boot-test-qemu.sh --iso PATH [--mode uefi|bios] [--memory 2048]
#       [--cpus 2] [--no-kvm] [--headless] [--timeout SECONDS]
#       [--ovmf-code PATH] [--ovmf-vars-template PATH] [-h|--help]
#
# Exit code:
#   0  = qemu khoi dong duoc va thoat binh thuong (tu nguoi dung tat VM,
#        hoac het --timeout o che do --headless). KHONG tu suy ra "cai
#        dat/boot Live thanh cong ve mat chuc nang" - do la ket luan cua
#        nguoi kiem thu xem man hinh/log, khong phai cua exit code nay.
#   1  = loi cau hinh/thieu file.
#   2  = loi tham so dau vao.
#   3  = BLOCKED — thieu qemu-system-x86_64, hoac thieu ca KVM va
#        khong co --no-kvm, hoac thieu firmware OVMF.
#   4  = qemu chay nhung tra ve loi (exit code != 0 tu qemu-system-x86_64).

set -euo pipefail

ISO_PATH=""
MODE="uefi"
MEMORY_MB="2048"
CPUS="2"
USE_KVM=1
HEADLESS=0
TIMEOUT_SECONDS=""
OVMF_CODE_OVERRIDE=""
OVMF_VARS_TEMPLATE_OVERRIDE=""

usage() {
  cat <<EOF
boot-test-qemu.sh — boot-test ISO NaMiOS bang QEMU + OVMF, Live, khong ghi dia

Dung:
  scripts/boot-test-qemu.sh --iso PATH [tuy chon]

Tuy chon:
  --iso PATH                   Duong dan file ISO can boot-test (bat buoc).
  --mode uefi|bios             Che do firmware (mac dinh: uefi — INSTALL-002
                               yeu cau UEFI bat buoc tren danh sach phan cung pilot;
                               bios chi la phuong an doi chieu, khong phai muc tieu chinh).
  --memory MB                  RAM cap cho VM, MB (mac dinh: 2048).
  --cpus N                     So vCPU (mac dinh: 2).
  --no-kvm                     Dung TCG (phan mem) thay KVM — CHAM, chi dung de
                               kiem tra cau truc boot khi khong co /dev/kvm; KHONG
                               dai dien cho hieu nang/trai nghiem phan cung thuc.
  --headless                   Khong mo cua so do hoa (-display none), dua console
                               qua serial stdio — dung cho kiem tra tu dong/CI.
  --timeout SECONDS            (chi voi --headless) Tu dong tat QEMU sau N giay.
                               Khong dat = cho den khi VM tu tat hoac nguoi dung Ctrl-C.
  --ovmf-code PATH              Duong dan OVMF_CODE*.fd neu khac vi tri mac dinh.
  --ovmf-vars-template PATH     Duong dan OVMF_VARS*.fd goc dung lam template
                               (mac dinh: tu do tim trong cac vi tri Debian thong thuong).
  -h, --help                    In huong dan nay.

Vi du:
  scripts/boot-test-qemu.sh --iso build/out/20260101T000000Z/namios.iso
  scripts/boot-test-qemu.sh --iso namios.iso --headless --timeout 120 --no-kvm
EOF
}

log() { printf '[boot-test] %s\n' "$*"; }
err() { printf '[boot-test] LOI: %s\n' "$*" >&2; }

while [ $# -gt 0 ]; do
  case "$1" in
    --iso)
      [ $# -ge 2 ] || { err "--iso can 1 gia tri PATH"; exit 2; }
      ISO_PATH="$2"; shift 2 ;;
    --mode)
      [ $# -ge 2 ] || { err "--mode can uefi hoac bios"; exit 2; }
      MODE="$2"; shift 2 ;;
    --memory)
      [ $# -ge 2 ] || { err "--memory can 1 gia tri so (MB)"; exit 2; }
      MEMORY_MB="$2"; shift 2 ;;
    --cpus)
      [ $# -ge 2 ] || { err "--cpus can 1 gia tri so"; exit 2; }
      CPUS="$2"; shift 2 ;;
    --no-kvm)
      USE_KVM=0; shift ;;
    --headless)
      HEADLESS=1; shift ;;
    --timeout)
      [ $# -ge 2 ] || { err "--timeout can 1 gia tri so giay"; exit 2; }
      TIMEOUT_SECONDS="$2"; shift 2 ;;
    --ovmf-code)
      [ $# -ge 2 ] || { err "--ovmf-code can 1 duong dan"; exit 2; }
      OVMF_CODE_OVERRIDE="$2"; shift 2 ;;
    --ovmf-vars-template)
      [ $# -ge 2 ] || { err "--ovmf-vars-template can 1 duong dan"; exit 2; }
      OVMF_VARS_TEMPLATE_OVERRIDE="$2"; shift 2 ;;
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

if [ -z "${ISO_PATH}" ]; then
  err "thieu --iso PATH"; usage >&2; exit 2
fi
if [ ! -f "${ISO_PATH}" ]; then
  err "khong tim thay file ISO: ${ISO_PATH}"; exit 1
fi
case "${MODE}" in
  uefi|bios) ;;
  *) err "--mode phai la 'uefi' hoac 'bios', nhan: ${MODE}"; exit 2 ;;
esac
case "${MEMORY_MB}" in ''|*[!0-9]*) err "--memory phai la so nguyen (MB)"; exit 2 ;; esac
case "${CPUS}" in ''|*[!0-9]*) err "--cpus phai la so nguyen"; exit 2 ;; esac
if [ -n "${TIMEOUT_SECONDS}" ]; then
  case "${TIMEOUT_SECONDS}" in ''|*[!0-9]*) err "--timeout phai la so nguyen (giay)"; exit 2 ;; esac
fi

ISO_PATH="$(cd -- "$(dirname -- "${ISO_PATH}")" >/dev/null 2>&1 && pwd -P)/$(basename -- "${ISO_PATH}")"
log "ISO: ${ISO_PATH}"

if [ -f "${ISO_PATH%.iso}.sha256" ] || [ -f "$(dirname -- "${ISO_PATH}")/SHA256SUMS" ]; then
  SUMS_FILE="$(dirname -- "${ISO_PATH}")/SHA256SUMS"
  if [ -f "${SUMS_FILE}" ]; then
    log "doi chieu checksum voi ${SUMS_FILE} (chi canh bao, khong fail cung neu khong khop ten file chinh xac)"
    ( cd -- "$(dirname -- "${ISO_PATH}")" && sha256sum --ignore-missing -c "$(basename -- "${SUMS_FILE}")" ) \
      || log "CANH BAO: sha256sum -c khong khop hoac khong tim thay dong tuong ung — kiem tra lai ISO truoc khi tin ket qua boot-test."
  fi
fi

# ---- 1) preflight cong cu ----------------------------------------------------
if ! command -v qemu-system-x86_64 >/dev/null 2>&1; then
  err "BLOCKED: khong tim thay 'qemu-system-x86_64'. Cai: sudo apt-get install -y qemu-system-x86 qemu-utils"
  exit 3
fi

KVM_ARGS=()
if [ "${USE_KVM}" -eq 1 ]; then
  if [ -e /dev/kvm ] && [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
    KVM_ARGS=(-enable-kvm -cpu host)
  else
    err "BLOCKED: /dev/kvm khong ton tai hoac khong co quyen doc/ghi. Dung --no-kvm de"
    err "  chay bang TCG (CHAM, chi kiem cau truc boot) neu ban CO Y THUC ro day KHONG"
    err "  phai boot-test tren dieu kien phan cung thuc (INSTALL-002)."
    exit 3
  fi
else
  log "CANH BAO: --no-kvm — dung TCG (phan mem), ket qua KHONG dai dien hieu nang/trai"
  log "  nghiem boot tren phan cung thuc. Chi dung de kiem cau truc UEFI/ISO."
  KVM_ARGS=(-cpu max)
fi

OVMF_CODE=""
OVMF_VARS_TEMPLATE=""
if [ "${MODE}" = "uefi" ]; then
  if [ -n "${OVMF_CODE_OVERRIDE}" ]; then
    OVMF_CODE="${OVMF_CODE_OVERRIDE}"
  else
    for p in /usr/share/OVMF/OVMF_CODE.fd /usr/share/OVMF/OVMF_CODE_4M.fd \
             /usr/share/OVMF/OVMF.fd /usr/share/ovmf/OVMF.fd /usr/share/qemu/OVMF.fd; do
      if [ -r "${p}" ]; then OVMF_CODE="${p}"; break; fi
    done
  fi
  if [ -z "${OVMF_CODE}" ] || [ ! -r "${OVMF_CODE}" ]; then
    err "BLOCKED: khong tim thay firmware OVMF_CODE (UEFI). Cai: sudo apt-get install -y ovmf"
    err "  hoac truyen --ovmf-code PATH neu ban da co file o vi tri khac."
    exit 3
  fi

  if [ -n "${OVMF_VARS_TEMPLATE_OVERRIDE}" ]; then
    OVMF_VARS_TEMPLATE="${OVMF_VARS_TEMPLATE_OVERRIDE}"
  else
    for p in /usr/share/OVMF/OVMF_VARS.fd /usr/share/OVMF/OVMF_VARS_4M.fd /usr/share/ovmf/OVMF_VARS.fd; do
      if [ -r "${p}" ]; then OVMF_VARS_TEMPLATE="${p}"; break; fi
    done
  fi
  if [ -z "${OVMF_VARS_TEMPLATE}" ] || [ ! -r "${OVMF_VARS_TEMPLATE}" ]; then
    err "BLOCKED: khong tim thay template OVMF_VARS (UEFI NVRAM). Cai: sudo apt-get install -y ovmf"
    err "  hoac truyen --ovmf-vars-template PATH."
    exit 3
  fi
  log "OVMF_CODE: ${OVMF_CODE}"
  log "OVMF_VARS template: ${OVMF_VARS_TEMPLATE}"
fi

# ---- 2) thu muc tam cho ban copy OVMF_VARS ghi duoc (khong ghi dia thuc) ---
TMP_DIR=""
cleanup() {
  if [ -n "${TMP_DIR}" ] && [ -d "${TMP_DIR}" ]; then
    rm -rf -- "${TMP_DIR}"
  fi
}
trap cleanup EXIT

QEMU_ARGS=()
if [ "${MODE}" = "uefi" ]; then
  TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/namios-boot-test.XXXXXX")"
  OVMF_VARS_RW="${TMP_DIR}/OVMF_VARS.fd"
  cp -- "${OVMF_VARS_TEMPLATE}" "${OVMF_VARS_RW}"
  QEMU_ARGS+=(
    -drive "if=pflash,format=raw,readonly=on,file=${OVMF_CODE}"
    -drive "if=pflash,format=raw,file=${OVMF_VARS_RW}"
  )
  log "ban copy OVMF_VARS ghi duoc nam trong ${OVMF_VARS_RW} (xoa khi script ket thuc, KHONG lam thay doi ISO/dia thuc)."
fi

# ---- 3) lap lenh qemu — CHI -cdrom (read-only), KHONG -hda/-drive dia cung --
QEMU_ARGS+=(
  -name "namios-boot-test"
  -machine "q35,accel=$([ "${USE_KVM}" -eq 1 ] && echo kvm || echo tcg)"
  "${KVM_ARGS[@]}"
  -m "${MEMORY_MB}"
  -smp "${CPUS}"
  -boot "d"
  -cdrom "${ISO_PATH}"
  -net "none"
  -rtc "base=utc"
)

if [ "${HEADLESS}" -eq 1 ]; then
  QEMU_ARGS+=(-display none -serial stdio -monitor none)
  log "che do headless: console qua serial stdio, khong mo man hinh do hoa."
else
  QEMU_ARGS+=(-vga std)
  log "che do co man hinh (mac dinh). Dong cua so VM hoac ACPI shutdown de ket thuc."
fi

log "lenh qemu: qemu-system-x86_64 ${QEMU_ARGS[*]}"
log "KHONG co virtual hard disk nao duoc gan (chi -cdrom read-only) => dung voi"
log "  yeu cau INSTALL-001 'Live mode thu khong ghi o trong'."

run_qemu() {
  qemu-system-x86_64 "${QEMU_ARGS[@]}"
}

set +e
if [ "${HEADLESS}" -eq 1 ] && [ -n "${TIMEOUT_SECONDS}" ]; then
  if command -v timeout >/dev/null 2>&1; then
    timeout "${TIMEOUT_SECONDS}s" qemu-system-x86_64 "${QEMU_ARGS[@]}"
    QEMU_RC=$?
    if [ "${QEMU_RC}" -eq 124 ]; then
      log "da het --timeout ${TIMEOUT_SECONDS}s, da tu tat QEMU (xem la 'ket thuc binh thuong theo thoi gian dat', khong phai loi)."
      QEMU_RC=0
    fi
  else
    err "khong co lenh 'timeout' tren host — chay khong gioi han thoi gian (bo qua --timeout)."
    run_qemu
    QEMU_RC=$?
  fi
else
  run_qemu
  QEMU_RC=$?
fi
set -e

if [ "${QEMU_RC}" -ne 0 ]; then
  err "qemu-system-x86_64 thoat voi ma loi ${QEMU_RC}."
  exit 4
fi

log "QEMU da thoat binh thuong (exit 0)."
log "NHAC LAI: exit code nay chi xac nhan qemu KHOI DONG va THOAT duoc — KET LUAN"
log "  'boot/cai dat Live thanh cong ve chuc nang' (INSTALL-001/002) PHAI do nguoi"
log "  kiem thu quan sat man hinh/console thuc va ghi vao test report, khong suy ra"
log "  tu rieng exit code nay."

exit 0
