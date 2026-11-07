NaMiOS - Huong dan tai & ghep file ISO
=======================================

File ISO (~2.8GB) bi GitHub chia nho (moi file Release < 2GB) nen co dang:
  namios-alpha-YYYYMMDD-amd64.iso.00.part
  namios-alpha-YYYYMMDD-amd64.iso.01.part
  namios-alpha-YYYYMMDD-amd64.iso.sha256   (file de kiem tra toan ven)

Tai HET cac file .part + file .sha256 ve CUNG MOT THU MUC.

CACH 1 - Tu dong (khuyen dung, khong can go lenh):
  - Windows:     tai them "ghep-iso.bat", de chung thu muc voi cac file .part roi BAM DUP.
  - Linux/macOS: tai them "ghep-iso.sh", mo terminal tai thu muc do roi chay:  sh ghep-iso.sh

CACH 2 - Go lenh tay:
  - Windows (mo Command Prompt tai thu muc chua file):
      copy /b namios-alpha-YYYYMMDD-amd64.iso.*.part namios.iso
  - Linux/macOS:
      cat namios-alpha-YYYYMMDD-amd64.iso.*.part > namios-alpha-YYYYMMDD-amd64.iso
      sha256sum -c namios-alpha-YYYYMMDD-amd64.iso.sha256

Sau khi co file .iso hoan chinh:
  - Ghi ra USB bang Rufus (Windows) hoac balenaEtcher (moi he) roi boot de cai thu, HOAC
  - Nap thang vao may ao VirtualBox / VMware / QEMU.

Day la ban ALPHA de dung thu. Gop y / bao loi: mo Issue tai
  https://github.com/NamDoji/NaMiOS/issues
