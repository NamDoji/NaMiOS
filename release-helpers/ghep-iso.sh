#!/bin/sh
# NaMiOS - ghep cac phan ISO (.part) thanh 1 file + kiem tra sha256.
# Dat file nay cung thu muc voi cac file *.iso.*.part roi chay:  sh ghep-iso.sh
set -e

ISO="$(ls -- *.iso.*.part 2>/dev/null | head -n1 | sed 's/\.[0-9][0-9]*\.part$//')"
if [ -z "$ISO" ]; then
  echo "Khong tim thay file .part nao. Dat ghep-iso.sh cung thu muc voi cac file *.iso.*.part."
  exit 1
fi

echo "[1/2] Ghep cac phan -> $ISO ..."
cat -- "$ISO".*.part > "$ISO"
echo "    Xong: $ISO"

echo "[2/2] Kiem tra sha256 ..."
if [ -f "$ISO.sha256" ]; then
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum -c "$ISO.sha256"
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 -c "$ISO.sha256"
  else
    echo "Khong co sha256sum/shasum de kiem tra - bo qua."
  fi
else
  echo "Khong thay $ISO.sha256 - bo qua kiem tra."
fi

echo "Xong. Ghi $ISO ra USB (balenaEtcher) hoac nap vao may ao (VirtualBox/VMware/QEMU) de cai thu."
