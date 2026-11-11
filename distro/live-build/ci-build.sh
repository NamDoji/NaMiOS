#!/bin/sh
# NaMiOS — ci-build.sh: build ISO bang live-build, chay BEN TRONG container
# debian:trixie --privileged tren runner (GitHub Actions). Day la build host
# Linux amd64 THAT (BUILD-001) — khong phai gia lap. Khong curl|bash, khong
# eval; tham so qua bien moi truong; moi lenh goi truc tiep.
set -eu

export NAMIOS_LB_DISTRIBUTION="${NAMIOS_LB_DISTRIBUTION:-trixie}"
export DEBIAN_FRONTEND=noninteractive

echo "=== apt update + cai live-build ==="
apt-get update
apt-get install -y --no-install-recommends live-build ca-certificates apt-utils xz-utils

# Pre-validate: bo (comment) goi KHONG co trong trixie + GHI LAI (trung thuc,
# khong im lang) de mot ten goi sai khong giet ca build ~40 phut. Phan bi bo
# se hien trong build.log de nguoi review biet va bo sung/sua sau.
# NaMiOS — mo contrib + non-free + non-free-firmware tren HOST container TRUOC
# khi pre-validate, de pham vi apt-cache show KHOP voi --archive-areas
# (auto/config) dung trong lb build. Thieu buoc nay: goi firmware-*/contrib/
# non-free (vi du libfdk-aac2t64 — xem auto/config va
# config/package-lists/0720-connectivity.list.chroot) bi DROP oan vi host
# container chi co main. (09/11: them "non-free" — truoc day chi co
# "main contrib non-free-firmware", thieu khu vuc "non-free" thuan.)
echo "=== Mo contrib + non-free + non-free-firmware tren HOST (khop --archive-areas) ==="
printf 'deb http://deb.debian.org/debian %s main contrib non-free non-free-firmware\n' "$NAMIOS_LB_DISTRIBUTION" > /etc/apt/sources.list.d/namios-prevalidate.list
apt-get update

echo "=== Pre-validate package-lists voi apt trixie (drop goi thieu, co log) ==="
# C5 (docs/release/RELEASE-READINESS-2026.11.md): vong lap duoi day tung AM
# THAM drop bat ky goi nao khong co trong trixie va VAN build xanh - mot ten
# goi go sai/doi ten o trixie se bien mat khoi anh ma khong ai biet. Ghi lai
# MOI goi bi drop vao DROPPED_LOG (ten goi::file nguon) de sau vong lap doi
# chieu voi allowlist MUST-HAVE ben duoi.
DROPPED_LOG="$(mktemp)"
trap 'rm -f "$DROPPED_LOG"' EXIT

for f in config/package-lists/*.list.chroot; do
    [ -f "$f" ] || continue
    tmp="${f}.filtered"
    : > "$tmp"
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            ''|\#*) printf '%s\n' "$line" >> "$tmp"; continue ;;
        esac
        if apt-cache show "$line" >/dev/null 2>&1; then
            printf '%s\n' "$line" >> "$tmp"
        else
            printf '# DROPPED-NOT-IN-TRIXIE: %s\n' "$line" >> "$tmp"
            echo "DROPPED (khong co trong trixie): $line  [tu $f]"
            printf '%s::%s\n' "$line" "$f" >> "$DROPPED_LOG"
        fi
    done < "$f"
    mv "$tmp" "$f"
done

echo "=== Kiem tra allowlist MUST-HAVE (C5: khong duoc im lang bo goi cot loi) ==="
# Danh sach toi thieu goi "song con" cua anh NaMiOS: desktop KDE, dang nhap
# do hoa, quan ly file, trinh cai dat, terminal, mang/am thanh/man hinh qua
# applet Plasma, trinh duyet, in an, mang day/khong day. Neu bat ky goi nao
# trong danh sach nay bi DROP o buoc tren (doi ten/thieu trong snapshot
# trixie) thi build PHAI DUNG LAI thay vi "CI xanh" voi anh thieu chuc nang.
# Danh sach "optional" (khong trong allowlist nay) van duoc phep drop im lang
# nhu truoc (hanh vi cu giu nguyen).
NAMIOS_MUST_HAVE_PACKAGES="task-kde-desktop sddm kwin-x11 dolphin calamares konsole plasma-nm plasma-pa kscreen plasma-systemmonitor firefox-esr cups print-manager network-manager"

MISSING_MUST_HAVE=""
for pkg in $NAMIOS_MUST_HAVE_PACKAGES; do
    if grep -q "^${pkg}::" "$DROPPED_LOG" 2>/dev/null; then
        MISSING_MUST_HAVE="${MISSING_MUST_HAVE} ${pkg}"
    fi
done

if [ -n "$MISSING_MUST_HAVE" ]; then
    echo "LOI NGHIEM TRONG (C5): cac goi MUST-HAVE sau bi DROP khoi anh (khong tim thay trong snapshot trixie hien tai):" >&2
    for pkg in $MISSING_MUST_HAVE; do
        grep "^${pkg}::" "$DROPPED_LOG" | sed 's/::/  <- tu /' >&2
    done
    echo "Day la goi COT LOI (desktop KDE/SDDM/quan ly file/trinh cai dat/terminal/trinh duyet/in an/mang) - KHONG the ship anh ISO thieu chung ma khong ai biet. Kiem tra ten goi dung voi apt-cache trong trixie that (co the da doi ten) roi sua package-lists tuong ung. DUNG BUILD." >&2
    exit 1
fi
echo "Allowlist MUST-HAVE: tat ca goi cot loi deu co mat (khong bi drop)."

# BUILD-002: dong dau build-metadata THAT vao /etc/namios-release truoc khi lb
# build (chay tren host CO git). Tranh ship "TBD" len ISO. Khong bia: neu khong
# co git/commit -> ghi "unknown" chu khong doan. (build-manifest.yaml van la
# TEMPLATE trong git; ban day du ghi canh ISO o buoc artifact.)
echo "=== dong dau build-metadata (namios-release) ==="
NAMIOS_RELEASE_FILE="config/includes.chroot/etc/namios-release"
BUILD_DATE_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
if [ -n "${GITHUB_SHA:-}" ]; then
  SRC_COMMIT="$GITHUB_SHA"
else
  SRC_COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
fi
if [ -f "$NAMIOS_RELEASE_FILE" ]; then
  sed -i "s|^NAMIOS_BUILD_DATE_UTC=.*|NAMIOS_BUILD_DATE_UTC=\"$BUILD_DATE_UTC\"|" "$NAMIOS_RELEASE_FILE"
  sed -i "s|^NAMIOS_SOURCE_COMMIT=.*|NAMIOS_SOURCE_COMMIT=\"$SRC_COMMIT\"|" "$NAMIOS_RELEASE_FILE"
  echo "Da dong dau: build_date=$BUILD_DATE_UTC commit=$SRC_COMMIT"
else
  echo "CANH BAO: khong thay $NAMIOS_RELEASE_FILE de dong dau build-metadata." >&2
fi

echo "=== lb config ==="
./auto/config

echo "=== lb build (debootstrap + chroot + squashfs + xorriso) ==="
lb build

echo "=== ket qua ISO ==="
ls -lh ./*.iso 2>/dev/null || { echo "KHONG co ISO — xem log tren"; exit 1; }
