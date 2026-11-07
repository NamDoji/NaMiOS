@echo off
rem NaMiOS - ghep cac phan ISO (.part) thanh 1 file + kiem tra toan ven.
rem Dat file nay CUNG THU MUC voi cac file *.iso.*.part roi BAM DUP.
setlocal
echo ================================================
echo   NaMiOS - Ghep file ISO + kiem tra toan ven
echo ================================================
echo.
echo [1/2] Dang ghep cac phan .part thanh namios.iso ...
copy /b "*.iso.*.part" "namios.iso" >nul
if errorlevel 1 (
  echo LOI: khong ghep duoc. Hay dam bao cac file .part nam CUNG THU MUC voi file .bat nay.
  pause
  exit /b 1
)
echo     Xong: namios.iso
echo.
echo [2/2] Ma bam SHA256 cua namios.iso:
certutil -hashfile "namios.iso" SHA256 | findstr /i /v "hash certutil"
echo.
echo Ma o tren PHAI trung voi so trong file *.iso.sha256 (mo bang Notepad de xem).
echo Neu trung = file chuan. Ghi namios.iso ra USB bang Rufus / balenaEtcher roi boot de cai thu.
echo.
pause
