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
echo "=== Pre-validate package-lists voi apt trixie (drop goi thieu, co log) ==="
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
        fi
    done < "$f"
    mv "$tmp" "$f"
done

echo "=== lb config ==="
./auto/config

echo "=== lb build (debootstrap + chroot + squashfs + xorriso) ==="
lb build

echo "=== ket qua ISO ==="
ls -lh ./*.iso 2>/dev/null || { echo "KHONG co ISO — xem log tren"; exit 1; }
