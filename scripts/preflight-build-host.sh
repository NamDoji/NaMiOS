#!/usr/bin/env bash
# preflight-build-host.sh — Kiem tra host hien tai co du dieu kien lam
# "NaMiOS build host" (dung de build ISO bang Debian live-build va chay
# QEMU boot-test) hay chua. Xem docs/runbooks/BUILD-HOST-SETUP.md.
#
# Pham vi lien quan: BUILD-001, BUILD-002, BUILD-003 (docs/specs/
# DAC_TA_HE_DIEU_HANH.md muc 14) + dieu kien phan cung/VM cho INSTALL-001,
# INSTALL-002 (boot test UEFI).
#
# verified_on_host: NO — script nay CHUA duoc chay tren mot build host
# Debian 13 trixie amd64 that co nested-virt. Ket qua "OK" tren container
# phat trien hien tai (Debian 12, khong /dev/kvm) la KHONG the xay ra cho
# cac muc bat buoc; do la ket qua DUNG, khong phai loi script.
#
# AN TOAN (bat buoc theo CLAUDE.md):
#   - Khong curl|bash, khong tai/thuc thi noi dung tu xa.
#   - Khong "eval", khong dung bien chua lenh de thuc thi gian tiep.
#   - Tat ca tham so dau vao di qua getopts/case tren argv, khong noi
#     chuoi vao lenh shell.
#   - Khong yeu cau chay bang root; script chi DOC thong tin he thong
#     (os-release, /proc, df, command -v). Khong ghi, khong cai dat,
#     khong goi wine/qemu/sudo.
#   - set -euo pipefail + kiem tra moi bien truoc khi dung.
#
# Cach dung:
#   scripts/preflight-build-host.sh [--json] [--build-dir PATH]
#       [--min-ram-gb N] [--min-disk-gb N] [--min-cores N] [-h|--help]
#
# Exit code:
#   0  = tat ca muc BAT BUOC deu OK (host san sang build/boot-test).
#   2  = loi tham so dau vao.
#   3  = thieu it nhat mot muc BAT BUOC (dependency/quyen/phan cung).
#      (so exit code nay chon de khop tinh than CLI-003 cua dac ta,
#       khong phai hop dong CLI `namios` chinh thuc.)

set -euo pipefail

SCRIPT_NAME="preflight-build-host.sh"
SCHEMA_VERSION="1.0"

BUILD_DIR="$PWD"
MIN_RAM_GB=16
MIN_DISK_GB=100
MIN_CORES=4
OUTPUT_JSON=0

usage() {
  cat <<EOF
$SCRIPT_NAME — kiem tra dieu kien build host cho NaMiOS (BUILD-001..003)

Dung:
  $SCRIPT_NAME [--json] [--build-dir PATH] [--min-ram-gb N] \\
      [--min-disk-gb N] [--min-cores N] [-h|--help]

Tuy chon:
  --json              In KET QUA duy nhat la 1 doi tuong JSON ra stdout
                       (khong tron log/text khac vao stdout khi dung co nay).
  --build-dir PATH     Thu muc du dinh build ISO, dung de kiem dung luong
                       trong con lai (mac dinh: thu muc hien tai, $PWD).
  --min-ram-gb N       Nguong RAM toi thieu, GB (mac dinh: 16).
  --min-disk-gb N      Nguong disk trong toi thieu, GB (mac dinh: 100).
  --min-cores N        Nguong so nhan CPU toi thieu, khuyen nghi (mac dinh: 4).
  -h, --help           In huong dan nay roi thoat (exit 0).

Vi du:
  $SCRIPT_NAME
  $SCRIPT_NAME --json --build-dir /srv/namios-build
EOF
}

# ---- parse argv (khong eval, khong shell=True, chi case/while tren "$@") ---
while [ $# -gt 0 ]; do
  case "$1" in
    --json)
      OUTPUT_JSON=1
      shift
      ;;
    --build-dir)
      if [ $# -lt 2 ]; then
        echo "Loi: --build-dir can 1 gia tri PATH" >&2
        exit 2
      fi
      BUILD_DIR="$2"
      shift 2
      ;;
    --min-ram-gb)
      if [ $# -lt 2 ]; then
        echo "Loi: --min-ram-gb can 1 gia tri so" >&2
        exit 2
      fi
      MIN_RAM_GB="$2"
      shift 2
      ;;
    --min-disk-gb)
      if [ $# -lt 2 ]; then
        echo "Loi: --min-disk-gb can 1 gia tri so" >&2
        exit 2
      fi
      MIN_DISK_GB="$2"
      shift 2
      ;;
    --min-cores)
      if [ $# -lt 2 ]; then
        echo "Loi: --min-cores can 1 gia tri so" >&2
        exit 2
      fi
      MIN_CORES="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "Loi: tham so khong ro: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      echo "Loi: tham so thua khong duoc ho tro: $1" >&2
      exit 2
      ;;
  esac
done

case "$MIN_RAM_GB" in ''|*[!0-9]*) echo "Loi: --min-ram-gb phai la so nguyen" >&2; exit 2 ;; esac
case "$MIN_DISK_GB" in ''|*[!0-9]*) echo "Loi: --min-disk-gb phai la so nguyen" >&2; exit 2 ;; esac
case "$MIN_CORES" in ''|*[!0-9]*) echo "Loi: --min-cores phai la so nguyen" >&2; exit 2 ;; esac

if [ ! -d "$BUILD_DIR" ]; then
  echo "Loi: --build-dir khong ton tai hoac khong phai thu muc: $BUILD_DIR" >&2
  exit 2
fi

# ---- ket qua: moi dong la 1 record, phan tach bang Unit Separator (0x1F) ---
# truong: id<US>label<US>required(true|false)<US>status(ok|missing|warn)<US>detail<US>remediation
US=$'\x1f'
RESULTS=()

add_result() {
  RESULTS+=("$1${US}$2${US}$3${US}$4${US}$5${US}$6")
}

json_escape() {
  # Escape toi thieu cho gia tri JSON string: backslash, dau nhay kep,
  # va cac ky tu dieu khien (newline/tab) co the lot vao tu /proc hoac df.
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\t'/\\t}"
  printf '%s' "$s"
}

bin_path() {
  # Khong eval, chi dung command -v tren ten binary co dinh.
  command -v "$1" 2>/dev/null || true
}

# ------------------------- 1. Thong tin co ban he dieu hanh -----------------
OS_ID=""
OS_VERSION_CODENAME=""
OS_VERSION_ID=""
if [ -r /etc/os-release ]; then
  # doc truc tiep bang grep/cut, khong source file ngoai (tranh thuc thi
  # noi dung khong kiem soat duoc trong /etc/os-release).
  OS_ID="$(grep -m1 '^ID=' /etc/os-release | cut -d= -f2- | tr -d '"' || true)"
  OS_VERSION_CODENAME="$(grep -m1 '^VERSION_CODENAME=' /etc/os-release | cut -d= -f2- | tr -d '"' || true)"
  OS_VERSION_ID="$(grep -m1 '^VERSION_ID=' /etc/os-release | cut -d= -f2- | tr -d '"' || true)"
fi

if [ "$OS_ID" = "debian" ] && { [ "$OS_VERSION_CODENAME" = "trixie" ] || [ "$OS_VERSION_ID" = "13" ]; }; then
  add_result "os_debian13" "He dieu hanh = Debian 13 trixie amd64" "true" "ok" \
    "ID=$OS_ID VERSION_CODENAME=$OS_VERSION_CODENAME VERSION_ID=$OS_VERSION_ID" \
    ""
else
  add_result "os_debian13" "He dieu hanh = Debian 13 trixie amd64" "true" "missing" \
    "Phat hien ID=${OS_ID:-?} VERSION_CODENAME=${OS_VERSION_CODENAME:-?} VERSION_ID=${OS_VERSION_ID:-?} (khong phai Debian 13 trixie)" \
    "Dung VM/host sach Debian 13 trixie amd64 (xem docs/adr/0002-nen-debian-13.md); khong build tren distro khac roi bao da build."
fi

ARCH="$(uname -m)"
if [ "$ARCH" = "x86_64" ]; then
  add_result "arch_amd64" "Kien truc CPU = x86_64 (amd64)" "true" "ok" "uname -m = $ARCH" ""
else
  add_result "arch_amd64" "Kien truc CPU = x86_64 (amd64)" "true" "missing" \
    "uname -m = $ARCH (can x86_64/amd64)" "Dung may/VM x86_64; NaMiOS v1 khong build ISO cho kien truc khac."
fi

# ------------------------- 2. CPU / RAM / disk -------------------------------
NPROC_VAL="$(nproc 2>/dev/null || echo 0)"
if [ "$NPROC_VAL" -ge "$MIN_CORES" ]; then
  add_result "cpu_cores" "So nhan CPU >= $MIN_CORES (khuyen nghi)" "false" "ok" "nproc = $NPROC_VAL" ""
else
  add_result "cpu_cores" "So nhan CPU >= $MIN_CORES (khuyen nghi)" "false" "warn" \
    "nproc = $NPROC_VAL (< $MIN_CORES)" "Tang vCPU cho VM build; build live-build + QEMU boot-test cham/kho chiu voi it nhan."
fi

VMX_SVM="no"
if [ -r /proc/cpuinfo ] && grep -Eq '(vmx|svm)' /proc/cpuinfo; then
  VMX_SVM="yes"
fi
if [ "$VMX_SVM" = "yes" ]; then
  add_result "cpu_virt_flag" "CPU co co ao hoa (vmx Intel VT-x hoac svm AMD-V)" "true" "ok" \
    "Tim thay vmx hoac svm trong /proc/cpuinfo" ""
else
  add_result "cpu_virt_flag" "CPU co co ao hoa (vmx Intel VT-x hoac svm AMD-V)" "true" "missing" \
    "Khong tim thay vmx/svm trong /proc/cpuinfo" \
    "Chon host/VM co lo nested virtualization (VT-x/AMD-V) duoc bat o hypervisor cap tren; QEMU --accel kvm can co flag nay."
fi

if [ -e /dev/kvm ]; then
  KVM_RW="no"
  if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
    KVM_RW="yes"
  fi
  if [ "$KVM_RW" = "yes" ]; then
    add_result "dev_kvm" "/dev/kvm ton tai va user hien tai doc/ghi duoc" "true" "ok" \
      "/dev/kvm co, quyen doc/ghi OK cho user $(id -un 2>/dev/null || echo '?')" ""
  else
    add_result "dev_kvm" "/dev/kvm ton tai va user hien tai doc/ghi duoc" "true" "missing" \
      "/dev/kvm ton tai nhung user hien tai khong co quyen doc/ghi" \
      "sudo usermod -aG kvm \"\$USER\" && newgrp kvm (dang xuat/dang nhap lai neu can)."
  fi
else
  add_result "dev_kvm" "/dev/kvm ton tai va user hien tai doc/ghi duoc" "true" "missing" \
    "/dev/kvm khong ton tai tren host nay" \
    "Dung host/VM co /dev/kvm (bat nested-virt o hypervisor cap tren, hoac chay tren bare-metal co VT-x/AMD-V)."
fi

RAM_TOTAL_KB="$(grep -m1 '^MemTotal:' /proc/meminfo 2>/dev/null | awk '{print $2}' || echo 0)"
RAM_TOTAL_GB=$(( RAM_TOTAL_KB / 1024 / 1024 ))
if [ "$RAM_TOTAL_GB" -ge "$MIN_RAM_GB" ]; then
  add_result "ram_total" "RAM tong >= ${MIN_RAM_GB}GB" "true" "ok" \
    "MemTotal ~ ${RAM_TOTAL_GB}GB (${RAM_TOTAL_KB}kB)" ""
else
  add_result "ram_total" "RAM tong >= ${MIN_RAM_GB}GB" "true" "missing" \
    "MemTotal ~ ${RAM_TOTAL_GB}GB (${RAM_TOTAL_KB}kB), can >= ${MIN_RAM_GB}GB" \
    "Cap VM/host co RAM >= ${MIN_RAM_GB}GB; live-build + squashfs + QEMU boot-test dung nhieu RAM/tmpfs."
fi

DISK_AVAIL_KB="$(df -Pk "$BUILD_DIR" 2>/dev/null | awk 'NR==2{print $4}' || echo 0)"
case "$DISK_AVAIL_KB" in ''|*[!0-9]*) DISK_AVAIL_KB=0 ;; esac
DISK_AVAIL_GB=$(( DISK_AVAIL_KB / 1024 / 1024 ))
if [ "$DISK_AVAIL_GB" -ge "$MIN_DISK_GB" ]; then
  add_result "disk_free" "Dung luong trong tai $BUILD_DIR >= ${MIN_DISK_GB}GB" "true" "ok" \
    "Con trong ~ ${DISK_AVAIL_GB}GB" ""
else
  add_result "disk_free" "Dung luong trong tai $BUILD_DIR >= ${MIN_DISK_GB}GB" "true" "missing" \
    "Con trong ~ ${DISK_AVAIL_GB}GB, can >= ${MIN_DISK_GB}GB tai $BUILD_DIR" \
    "Cap them disk hoac doi --build-dir sang volume co du cho (chroot + squashfs + ISO + cache apt co the toi vai chuc GB moi lan build)."
fi

# ------------------------- 3. Cong cu build ISO (BUILD-001) -----------------
LB_BIN="$(bin_path lb)"
if [ -n "$LB_BIN" ]; then
  add_result "tool_live_build" "live-build (lenh 'lb')" "true" "ok" "Tim thay: $LB_BIN" ""
else
  add_result "tool_live_build" "live-build (lenh 'lb')" "true" "missing" "Khong tim thay lenh 'lb'" \
    "sudo apt-get update && sudo apt-get install -y live-build"
fi

DEBOOTSTRAP_BIN="$(bin_path debootstrap)"
MMDEBSTRAP_BIN="$(bin_path mmdebstrap)"
if [ -n "$DEBOOTSTRAP_BIN" ] || [ -n "$MMDEBSTRAP_BIN" ]; then
  DETAIL="debootstrap=${DEBOOTSTRAP_BIN:-khong co}; mmdebstrap=${MMDEBSTRAP_BIN:-khong co}"
  add_result "tool_debootstrap" "debootstrap hoac mmdebstrap" "true" "ok" "$DETAIL" ""
else
  add_result "tool_debootstrap" "debootstrap hoac mmdebstrap" "true" "missing" \
    "Khong tim thay debootstrap hoac mmdebstrap" \
    "sudo apt-get install -y debootstrap   # hoac: sudo apt-get install -y mmdebstrap"
fi

XORRISO_BIN="$(bin_path xorriso)"
if [ -n "$XORRISO_BIN" ]; then
  add_result "tool_xorriso" "xorriso (dung tao ISO)" "true" "ok" "Tim thay: $XORRISO_BIN" ""
else
  add_result "tool_xorriso" "xorriso (dung tao ISO)" "true" "missing" "Khong tim thay lenh 'xorriso'" \
    "sudo apt-get install -y xorriso"
fi

MKSQUASHFS_BIN="$(bin_path mksquashfs)"
if [ -n "$MKSQUASHFS_BIN" ]; then
  add_result "tool_squashfs" "squashfs-tools (lenh 'mksquashfs')" "true" "ok" "Tim thay: $MKSQUASHFS_BIN" ""
else
  add_result "tool_squashfs" "squashfs-tools (lenh 'mksquashfs')" "true" "missing" \
    "Khong tim thay lenh 'mksquashfs'" "sudo apt-get install -y squashfs-tools"
fi

FAKEROOT_BIN="$(bin_path fakeroot)"
if [ -n "$FAKEROOT_BIN" ]; then
  add_result "tool_fakeroot" "fakeroot" "true" "ok" "Tim thay: $FAKEROOT_BIN" ""
else
  add_result "tool_fakeroot" "fakeroot" "true" "missing" "Khong tim thay lenh 'fakeroot'" \
    "sudo apt-get install -y fakeroot"
fi

# ------------------------- 4. QEMU + OVMF (boot-test, INSTALL-001/002) ------
QEMU_BIN="$(bin_path qemu-system-x86_64)"
if [ -n "$QEMU_BIN" ]; then
  add_result "tool_qemu" "qemu-system-x86_64 (boot-test ISO)" "true" "ok" "Tim thay: $QEMU_BIN" ""
else
  add_result "tool_qemu" "qemu-system-x86_64 (boot-test ISO)" "true" "missing" \
    "Khong tim thay lenh 'qemu-system-x86_64'" "sudo apt-get install -y qemu-system-x86 qemu-utils"
fi

OVMF_FOUND=""
for p in \
  /usr/share/OVMF/OVMF_CODE.fd \
  /usr/share/OVMF/OVMF_CODE_4M.fd \
  /usr/share/OVMF/OVMF.fd \
  /usr/share/ovmf/OVMF.fd \
  /usr/share/qemu/OVMF.fd
do
  if [ -r "$p" ]; then
    OVMF_FOUND="$p"
    break
  fi
done
if [ -n "$OVMF_FOUND" ]; then
  add_result "tool_ovmf" "Firmware OVMF (UEFI boot-test, INSTALL-002)" "true" "ok" "Tim thay: $OVMF_FOUND" ""
else
  add_result "tool_ovmf" "Firmware OVMF (UEFI boot-test, INSTALL-002)" "true" "missing" \
    "Khong tim thay file OVMF_CODE*.fd/OVMF.fd o cac duong dan thong thuong" \
    "sudo apt-get install -y ovmf"
fi

# ------------------------- 5. Wine toolchain (M2, nhac trong runbook) -------
WINE_BIN="$(bin_path wine)"
if [ -n "$WINE_BIN" ]; then
  add_result "tool_wine" "wine" "true" "ok" "Tim thay: $WINE_BIN" ""
else
  add_result "tool_wine" "wine" "true" "missing" "Khong tim thay lenh 'wine'" \
    "Xem docs/runbooks/BUILD-HOST-SETUP.md phan Wine (them i386 arch truoc khi cai)."
fi

WINETRICKS_BIN="$(bin_path winetricks)"
if [ -n "$WINETRICKS_BIN" ]; then
  add_result "tool_winetricks" "winetricks" "true" "ok" "Tim thay: $WINETRICKS_BIN" ""
else
  add_result "tool_winetricks" "winetricks" "true" "missing" "Khong tim thay lenh 'winetricks'" \
    "sudo apt-get install -y winetricks"
fi

# ------------------------- 6. Thong tin tham khao (khong bat buoc) ---------
RUN_AS_ROOT="no"
if [ "$(id -u)" = "0" ]; then
  RUN_AS_ROOT="yes"
fi
if [ "$RUN_AS_ROOT" = "yes" ]; then
  add_result "not_root" "Khong chay script nay bang root" "false" "warn" \
    "Dang chay bang UID 0. CLAUDE.md: khong chay wine bang root; script nay chi doc thong tin nhung khuyen nghi khong dung tai khoan root cho toan bo quy trinh build/wine." \
    "Chay bang user thuong co quyen sudo rieng cho tung buoc can dac quyen."
else
  add_result "not_root" "Khong chay script nay bang root" "false" "ok" "UID = $(id -u)" ""
fi

KERNEL_VER="$(uname -r)"
add_result "kernel_info" "Thong tin kernel (tham khao, khong cham/dat)" "false" "ok" "uname -r = $KERNEL_VER" ""

# ------------------------- Tong hop ------------------------------------------
TOTAL=0
OK=0
MISSING_REQ=0
WARN=0
for row in "${RESULTS[@]}"; do
  IFS="$US" read -r _id _label _req _status _detail _rem <<< "$row"
  TOTAL=$((TOTAL + 1))
  case "$_status" in
    ok) OK=$((OK + 1)) ;;
    warn) WARN=$((WARN + 1)) ;;
    missing)
      if [ "$_req" = "true" ]; then
        MISSING_REQ=$((MISSING_REQ + 1))
      fi
      ;;
  esac
done

if [ "$MISSING_REQ" -eq 0 ]; then
  OVERALL="ready"
else
  OVERALL="not_ready"
fi

GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
HOSTNAME_VAL="$(hostname 2>/dev/null || echo unknown)"

if [ "$OUTPUT_JSON" -eq 1 ]; then
  # Chi in JSON ra stdout, khong tron log/text khac (giu tinh than CLI-001).
  printf '{\n'
  printf '  "schema_version": "%s",\n' "$(json_escape "$SCHEMA_VERSION")"
  printf '  "operation_id": "preflight-build-host",\n'
  printf '  "generated_at": "%s",\n' "$(json_escape "$GENERATED_AT")"
  printf '  "host": {"hostname": "%s", "kernel": "%s", "arch": "%s"},\n' \
    "$(json_escape "$HOSTNAME_VAL")" "$(json_escape "$KERNEL_VER")" "$(json_escape "$ARCH")"
  printf '  "build_dir": "%s",\n' "$(json_escape "$BUILD_DIR")"
  printf '  "overall_status": "%s",\n' "$OVERALL"
  printf '  "summary": {"total": %d, "ok": %d, "warn": %d, "missing_required": %d},\n' \
    "$TOTAL" "$OK" "$WARN" "$MISSING_REQ"
  printf '  "checks": [\n'
  n=0
  total_rows=${#RESULTS[@]}
  for row in "${RESULTS[@]}"; do
    IFS="$US" read -r _id _label _req _status _detail _rem <<< "$row"
    n=$((n + 1))
    printf '    {"id": "%s", "label": "%s", "required": %s, "status": "%s", "detail": "%s", "remediation": "%s"}' \
      "$(json_escape "$_id")" "$(json_escape "$_label")" "$_req" "$(json_escape "$_status")" \
      "$(json_escape "$_detail")" "$(json_escape "$_rem")"
    if [ "$n" -lt "$total_rows" ]; then
      printf ',\n'
    else
      printf '\n'
    fi
  done
  printf '  ],\n'
  printf '  "warnings": [],\n'
  if [ "$OVERALL" = "ready" ]; then
    printf '  "error": null\n'
  else
    printf '  "error": "missing_required_dependency"\n'
  fi
  printf '}\n'
else
  echo "== NaMiOS preflight-build-host.sh =="
  echo "Host: $HOSTNAME_VAL | Kernel: $KERNEL_VER | Arch: $ARCH | Thoi diem: $GENERATED_AT"
  echo "Build dir kiem tra disk: $BUILD_DIR"
  echo ""
  printf '%-22s %-8s %-8s %s\n' "MUC" "BAT_BUOC" "TRANG_THAI" "CHI_TIET"
  printf '%-22s %-8s %-8s %s\n' "---" "---" "---" "---"
  for row in "${RESULTS[@]}"; do
    IFS="$US" read -r _id _label _req _status _detail _rem <<< "$row"
    STATUS_UP=$(printf '%s' "$_status" | tr '[:lower:]' '[:upper:]')
    printf '%-22s %-8s %-8s %s\n' "$_id" "$_req" "$STATUS_UP" "$_detail"
    if [ "$_status" = "missing" ] && [ -n "$_rem" ]; then
      printf '%-22s %-8s %-8s -> %s\n' "" "" "" "$_rem"
    fi
  done
  echo ""
  echo "Tong: $TOTAL muc | OK: $OK | WARN: $WARN | THIEU (bat buoc): $MISSING_REQ"
  echo "Trang thai tong: $OVERALL"
  if [ "$OVERALL" != "ready" ]; then
    echo "=> Host nay CHUA du dieu kien build/boot-test ISO NaMiOS. Xem"
    echo "   docs/runbooks/BUILD-HOST-SETUP.md de biet lenh cai dat cu the."
  fi
fi

if [ "$MISSING_REQ" -gt 0 ]; then
  exit 3
fi
exit 0
