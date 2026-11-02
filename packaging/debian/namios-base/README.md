# `namios-base` — skeleton metapackage (M3-PREP)

**verified_on_host: NO.** Đây CHỈ là khung Debian packaging
(`debian/control`, `debian/changelog`, `debian/rules`, `debian/copyright`,
`debian/source/format`) cho metapackage `namios-base` (§5.2 module 1 của
`docs/specs/DAC_TA_HE_DIEU_HANH.md`: *"package metapackage, branding, mặc
định desktop, locale, font và nguồn cập nhật"*). **CHƯA có `.deb` nào
được build ở đây** — container phát triển hiện tại thiếu
`dpkg-dev`/`debhelper`/`lintian` thật (chưa xác minh lại trong lần soạn
tài liệu này; xem `docs/_m0_inventory_raw.md` cho danh sách công cụ build
ISO đã xác nhận thiếu — toolchain `dpkg-buildpackage` cần kiểm tra riêng
trên build host).

## Vì sao đặt trong `packaging/debian/namios-base/` (không phải thẳng
`packaging/debian/`)

`packaging/debian/` ở gốc đã có sẵn file của WP7 (`namios-system-helper`):
`org.namios.SystemHelper1.conf` (D-Bus policy) và
`org.namios.SystemHelper1.policy` (Polkit action) — xem
`docs/specs/M1-WORK-PACKAGES.md` dòng "Sở hữu: ... `packaging/debian/`
phần policy file + D-Bus/Polkit `.policy`/`.conf` mẫu (chỉ file của WP7)".
Để không đụng/đè file của module khác, skeleton `namios-base` được đặt
trong một thư mục con riêng theo đúng layout chuẩn của một source package
Debian (`<tên-nguồn>/debian/*`), sao cho sau này có thể build độc lập:

```sh
cd packaging/debian/namios-base
dpkg-buildpackage -us -uc -b   # build THẬT trên host có dpkg-dev/debhelper
```

## Nội dung hiện có (skeleton, chưa build)

- `debian/control` — khai báo package `namios-base`, `Architecture: all`,
  `Depends` liệt kê nhóm gói desktop/locale/IME/font cơ bản (tên gói cần
  xác nhận lại trên snapshot Debian 13 trixie thật, giống điều kiện ở
  `distro/live-build/config/package-lists/`). **Không** có dependency tới
  một "apt repo NaMiOS ký riêng" nào — hạ tầng đó (phần "nguồn cập nhật"
  trong mô tả §5.2) **chưa tồn tại**, nên không thể khai trong `Depends`
  mà không làm `apt`/`dpkg-buildpackage` fail thật khi kiểm tra phụ
  thuộc.
- `debian/changelog` — một entry `UNRELEASED`, version `0.0.0~dev0-1`
  (khớp `version = "0.0.0.dev0"` trong `pyproject.toml` ở gốc repo, đổi
  `.` thành `~` theo quy ước version Debian cho bản pre-release).
- `debian/rules` — dùng `dh $@` (debhelper sequencer) qua
  `debhelper-compat (= 13)` trong `Build-Depends` (không có file
  `debian/compat` riêng — đúng khuyến nghị hiện tại thay `compat` cũ).
  Vì đây là metapackage (không có mã nguồn/binary riêng để build), rule
  `override_dh_auto_build`/`override_dh_auto_test` được no-op có chủ ý.
- `debian/copyright` — định dạng machine-readable
  (`https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/`):
  phần mã/metadata packaging tự viết dùng Apache-2.0 (khớp
  `license = { text = "Apache-2.0" }` trong `pyproject.toml`); có ghi chú
  rõ `namios-base` **không đóng gói lại** mã nguồn Debian/KDE/Fcitx5/Wine
  — nó chỉ là metapackage kéo phụ thuộc, các thành phần đó giữ giấy phép
  gốc của chính chúng (không claim sở hữu — OWN-001).
- `debian/source/format` — `3.0 (native)` (NaMiOS tự viết toàn bộ phần
  packaging, không có tarball upstream riêng để quilt-patch).

## CHƯA có trong skeleton này (việc còn lại)

- Chưa build `.deb` thật, chưa chạy `lintian`, chưa cài thử (`dpkg -i`)
  trong môi trường cách ly.
- Chưa có asset branding nhị phân thật để đóng gói (xem
  `distro/live-build/config/includes.chroot/usr/share/namios-branding/README-PLACEHOLDER.md`)
  — vì vậy `namios-base` hiện tại là package **Depends-only** (không có
  `debian/namios-base.install` vì chưa có file nguồn thật nào để cài).
- Chưa có apt repo NaMiOS ký riêng để wiring "nguồn cập nhật" vào
  `Depends`/`sources.list.d`.
- Tên gói trong `Depends` chưa được xác nhận lại bằng `apt-cache show`
  trên Debian 13 trixie thật (đồng bộ với điều kiện spike ADR 0002).

## Liên quan requirement

`docs/specs/DAC_TA_HE_DIEU_HANH.md` §5.2 (module `namios-base`), §14
BUILD-001/002, OWN-001 (không claim sở hữu thành phần bên thứ ba), VN-001
(locale), VN-002 (IME), VN-005 (font).
