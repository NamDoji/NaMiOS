# Cổng Dịch vụ Việt + Trung tâm Ký số (namios-dichvu)

- **Mốc:** scaffold đầu tiên, 11/11/2026 (VN-2 + VN-3,
  `docs/roadmap/NEW-FUNCTIONS-DIRECTION.md`).
- **verified_on_host: NO cho toàn bộ ứng dụng** (lớp giao diện PySide6 +
  hook cài đặt) — container phát triển hiện tại KHÔNG có PySide6/display,
  KHÔNG có `lb build` để dựng ảnh thật. **ĐÃ chạy thật** (không chỉ đọc lại)
  toàn bộ lớp lõi KHÔNG-GUI (`catalog.py`/`envcheck.py`) bằng Python 3.11
  thật trong sandbox này + `python3 -m py_compile` cho mọi file `.py` + kiểm
  `services_vn.json` parse đúng JSON — xem mục 6.

## 1. Đây là gì

Một launcher trung thực, một chỗ, dẫn người Việt (đặc biệt kế toán/hộ kinh
doanh) tới đúng cổng: **Thuế · Bảo hiểm xã hội · Dịch vụ công · Ngân hàng ·
Kế toán · Hoá đơn điện tử · Giáo dục · Ngành dọc · Ký số**. Mỗi dịch vụ hiển
thị: nhà cung cấp, mô tả, URL chính thức (nếu có), **nhãn trạng thái thực tế**
(`works-web`/`works-native`/`wine-candidate`/`blocked`), và — khi có — trạng
thái công bố 7 nấc (`published_status`, ECO-003) lấy trực tiếp từ
`catalog/services/*.json`.

**Trung tâm Ký số** là một mục riêng trong cùng app (category `kyso`), trình
bày đúng 3 tuyến theo thứ tự đáng tin nhất (theo
`docs/wine/KY-SO-PKCS11-RESEARCH.md`):

1. **Ký số từ xa** (VNPT SmartCA, Viettel MySign) — web, không cần Wine,
   **khuyến nghị thử trước**.
2. **Ký PDF bằng chứng thư mềm `.p12`** qua Okular/LibreOffice — tính năng
   NATIVE đã có sẵn trên Linux, không qua Wine, không qua web.
3. **USB token vật lý qua PKCS#11** — **BỊ CHẶN** với cả 3 hãng CA lớn
   (Viettel-CA/VNPT-CA/FPT-CA) theo khảo sát công khai 11/11/2026 (chưa có
   middleware Linux chính hãng công khai) — có nút **"Dò token USB (chỉ
   đọc)"** để người dùng tự kiểm máy mình (`pkcs11-tool --list-slots`,
   không PIN, không ghi/sửa gì).

Ứng dụng này **KHÔNG tự đăng nhập** vào bất kỳ cổng nào, **KHÔNG host lại**
bộ cài phần mềm nào, **KHÔNG thu PIN/mật khẩu/khoá** ký số nào — mọi nút
"Mở web"/"Mở app" chỉ gọi `xdg-open <url>`/mở ứng dụng có sẵn trên máy
(Okular/LibreOffice), mọi việc đăng nhập/ký thật xảy ra trong trang
web/app đó, ngoài phạm vi mã nguồn của app này.

## 2. File đã tạo (TOÀN BỘ mới, không sửa file có sẵn nào của app khác)

| File | Vai trò |
| --- | --- |
| `includes.chroot/opt/namios/namios_dichvu-src/__init__.py` | Gói Python — re-export + đăng ký i18n khi import |
| `includes.chroot/opt/namios/namios_dichvu-src/__main__.py` | Entry point `python3 -m namios_dichvu`; thiếu PySide6 → **quiet exit 0** |
| `includes.chroot/opt/namios/namios_dichvu-src/catalog.py` | Nạp + lọc `services_vn.json`; tìm không dấu (ECO-007); Python thuần, test không cần GUI |
| `includes.chroot/opt/namios/namios_dichvu-src/envcheck.py` | Tự kiểm môi trường read-only (ECO-008) + dò PKCS#11 (`pkcs11-tool --list-slots`, VN-3) |
| `includes.chroot/opt/namios/namios_dichvu-src/_i18n.py` | Catalog song ngữ VI/EN cho chrome giao diện (qua `namios_i18n`) |
| `includes.chroot/opt/namios/namios_dichvu-src/branding.py` | Đọc `brand.json` (fail-safe) + dựng QSS + bảng màu trạng thái |
| `includes.chroot/opt/namios/namios_dichvu-src/ui.py` | Cửa sổ PySide6: tìm kiếm + danh mục + thẻ dịch vụ + banner Ký số + dialog tự kiểm |
| `includes.chroot/opt/namios/namios_dichvu-src/services_vn.json` | Dữ liệu dịch vụ (16 mục) — xem mục 3 cho nguồn |
| `includes.chroot/opt/namios/namios_dichvu-src/py.typed` | Marker PEP 561 |
| `includes.chroot/usr/share/applications/namios-dichvu.desktop` | Launcher "Cổng Dịch vụ Việt" (menu Hệ thống/Tiện ích/Văn phòng/Tài chính) |
| `hooks/normal/0308-namios-dichvu.hook.chroot` | Hook cài vào `/opt/namios/namios_dichvu` + tạo wrapper `/usr/bin/namios-dichvu`; mirror cấu trúc `0305` nhưng wrapper **quiet exit 0** khi thiếu PySide6 (khớp quy ước mới hơn `0307-namios-lich`) |
| `includes.chroot/usr/share/namios/docs/CONG-DICH-VU.md` | Tài liệu này |

## 3. Nguồn dữ liệu `services_vn.json` — CATALOG thật, không bịa

- **12/16 mục** chuyển thể trực tiếp từ `catalog/services/*.json` đã có sẵn
  trong repo (khảo sát 02/11/2026): `thue.htkk`, `thue.thuedientu`,
  `thue.etax-mobile`, `bhxh.cong-giao-dich-dien-tu`, `bhxh.cong-cu-ky-so`,
  `bhxh.ivan-ts24-ebh`, `giaoduc.csdl-nganh-moet`, `hanhchinh.dvc-quocgia`,
  `ketoan.hoadondientu`, `ketoan.misa-amis`, `ketoan.misa-sme`,
  `nganhdoc.vnaccs-hai-quan`. Trường `official_url`/`windows_mode`/
  `published_status`/`tested_by_namios`/`officially_supported_by_vendor` giữ
  NGUYÊN giá trị gốc từ catalog — KHÔNG tự đổi.
- **4/16 mục còn lại** (`kyso.vnpt-smartca`, `kyso.viettel-mysign`,
  `kyso.p12-local-sign`, `kyso.usb-token-pkcs11`) là mục **mới**, tác giả dựa
  trên `docs/wine/KY-SO-PKCS11-RESEARCH.md` (khảo sát 11/11/2026) — URL
  dùng đúng domain đã được trích dẫn làm nguồn trong tài liệu đó
  (`smartca.vnpt.vn`, `viettelca.vn`), **KHÔNG đoán URL mới**.
- **`name_vi`/`name_en`** (tên hiển thị ngắn) do người viết module này tự
  đặt cho dễ đọc — đây là NHÃN HIỂN THỊ, không phải dữ liệu nghiệp vụ, không
  ảnh hưởng tới các trường sự thật (`official_url`/`published_status`/...).
- **Danh mục "Ngân hàng" (`nganhang`) để TRỐNG có chủ đích** — repo hiện
  KHÔNG có entry ngân hàng nào trong `catalog/services/`, và yêu cầu phạm vi
  của wave này là "chỉ dùng URL chính thức thật, không đoán" — thêm một URL
  ngân hàng cụ thể mà chưa khảo sát là bịa dữ liệu, bị cấm rõ. UI hiển thị
  một ghi chú trung thực ở danh mục này thay vì danh sách trống không giải
  thích gì.

### 3.1 Toàn bộ URL đã ship (16 mục, chính xác)

```
https://www.gdt.gov.vn/wps/portal/home/hotrokekhai      (thue.htkk)
https://thuedientu.gdt.gov.vn/                          (thue.thuedientu)
https://canhan.gdt.gov.vn                               (thue.etax-mobile)
https://dichvucong.baohiemxahoi.gov.vn/                 (bhxh.cong-giao-dich-dien-tu)
https://dichvucong.baohiemxahoi.gov.vn/#/tro-giup       (bhxh.cong-cu-ky-so)
https://ebh.vn/                                         (bhxh.ivan-ts24-ebh)
https://csdl.moet.gov.vn/Default.aspx                   (giaoduc.csdl-nganh-moet)
https://dichvucong.gov.vn/                               (hanhchinh.dvc-quocgia)
https://hoadondientu.gdt.gov.vn/                         (ketoan.hoadondientu)
https://amis.misa.vn/amis-ke-toan/                       (ketoan.misa-amis)
https://sme.misa.vn/                                     (ketoan.misa-sme)
https://www.customs.gov.vn/                              (nganhdoc.vnaccs-hai-quan)
https://smartca.vnpt.vn/                                 (kyso.vnpt-smartca)
https://viettelca.vn/chu-ky-so-tu-xa-mysign-viettel       (kyso.viettel-mysign)
(không có URL — action=open_app, mở Okular/LibreOffice có sẵn)  (kyso.p12-local-sign)
(không có URL — action=probe_pkcs11, dò bằng pkcs11-tool)        (kyso.usb-token-pkcs11)
```

## 4. Nhãn trạng thái — honest taxonomy, KHÔNG phải xác nhận của ai khác

`realistic_status` chỉ nhận 1 trong 4 giá trị (ép cứng trong `catalog.py`,
giá trị lạ → `blocked`, không đoán "tốt"):

| Giá trị | Ý nghĩa | Ví dụ trong `services_vn.json` |
| --- | --- | --- |
| `works-web` | Chạy qua trình duyệt, không cần Wine | `thue.thuedientu`, `ketoan.misa-amis`, `kyso.vnpt-smartca` |
| `works-native` | Chạy bằng tính năng có sẵn trên Linux (không Wine, không web) | `kyso.p12-local-sign` (Okular/LibreOffice) |
| `wine-candidate` | Chưa kiểm thật — có cơ hội qua lớp "Chạy phần mềm Windows" | `thue.htkk` (chỉ bước lập/xuất tờ khai) |
| `blocked` | Không chạy được ở thời điểm này | `ketoan.misa-sme` (cần SQL Server), `bhxh.cong-cu-ky-so` + `kyso.usb-token-pkcs11` (USB token) |

Đây là phân loại **riêng của NaMiOS**, viết thủ công dựa trên dữ liệu đã có
trong repo (`catalog/services/*.json` + `docs/wine/WINE-COMPAT-MATRIX.md` +
`docs/wine/KY-SO-PKCS11-RESEARCH.md`) — ghi rõ trong
`services_vn.json["disclaimer_vi"]` và hiển thị ở chân cửa sổ app. KHÔNG
đồng nghĩa `published_status` (ECO-003, 7 nấc) — hai trường hiển thị riêng,
không gộp. `downloadable_only`/`launches_only`/`not_inventoried` (các giá trị
`published_status` thật đang có trong catalog, toàn bộ 12 mục catalog hiện
đều là `not_inventoried`) KHÔNG BAO GIỜ hiển thị là "dùng được" ở đây.

## 5. Ký số — tóm tắt trung thực (nhắc lại KY-SO-PKCS11-RESEARCH.md)

- **KHÔNG claim** MISA SME/USB token/iTaxViewer chạy được qua Wine — tất cả
  xếp `blocked`/`wine-candidate` (chưa kiểm), KHÔNG `works`.
- **Tuyến khuyến nghị thật** cho kế toán Việt: **ký số từ xa** (VNPT
  SmartCA/Viettel MySign) — khóa bí mật không bao giờ chạm máy tính, chỉ cần
  trình duyệt + điện thoại. Cả cổng thuế điện tử lẫn BHXH đều xác nhận công
  khai hỗ trợ loại chữ ký số này song song USB Token.
- **Chứng thư mềm `.p12`** (nếu bạn có, khác USB token vật lý) ký được NGAY
  bằng Okular/LibreOffice có sẵn trên NaMiOS — không cần cài gì thêm.
- **MacSigner** (công cụ cộng đồng, có build Linux, nhắm riêng VNPT) được
  nhắc trong `KY-SO-PKCS11-RESEARCH.md` §3 nhưng **CHỦ Ý KHÔNG** đưa vào
  `services_vn.json`/UI của app này — chưa được CA nào xác nhận chính thức,
  NaMiOS chưa tự kiểm chứng/đọc mã nguồn, và không nên xuất hiện như một
  "dịch vụ có nút bấm" dễ gây hiểu lầm là được NaMiOS khuyến nghị. Người
  muốn tìm hiểu đọc `docs/wine/KY-SO-PKCS11-RESEARCH.md` §3 trực tiếp.

## 6. Đã tự kiểm gì trong sandbox này (KHÔNG phải trên máy NaMiOS thật)

- `python3 -m py_compile` sạch cho `__init__.py`/`__main__.py`/`_i18n.py`/
  `branding.py`/`catalog.py`/`envcheck.py`/`ui.py`.
- `services_vn.json` parse JSON hợp lệ; 16/16 mục có `realistic_status` hợp
  lệ (1 trong 4 giá trị cho phép); mọi `category` tham chiếu đúng một mục
  trong `categories`; 16 id duy nhất.
- Chạy THẬT (import + gọi hàm, không chỉ đọc mã) `catalog.load_catalog()` +
  `catalog.filter_services()` + `catalog.fold_vi()`: xác nhận tìm "khai thue"
  khớp "HTKK"/"Thuế điện tử" (có dấu trong dữ liệu), tìm "bao hiem" khớp 2
  mục BHXH, lọc danh mục `kyso` trả đúng 5 mục (4 mục tự thêm + 1 mục catalog
  gốc `bhxh.cong-cu-ky-so`) theo đúng thứ tự ưu tiên (`priority`/
  `recommended`).
- Chạy THẬT `envcheck.run_env_check()` + `envcheck.probe_pkcs11_slots()`
  trong sandbox (không có `xdg-open`/`pkcs11-tool` ở đây) — xác nhận cả hai
  trả kết luận trung thực "thiếu công cụ" (`unknown`), KHÔNG crash, KHÔNG
  giả vờ "works".
- `bash -n` cho `0308-namios-dichvu.hook.chroot` + script wrapper nhúng
  trong heredoc — cú pháp hợp lệ.
- **CHƯA kiểm** (cần build host/desktop thật, ngoài phạm vi sandbox này):
  `lb build` dựng ảnh thật, mở cửa sổ PySide6 thật, bấm nút "Mở web" thật
  bằng NaMiBrowser, cắm USB token thật để xem `pkcs11-tool --list-slots` trả
  gì trên phần cứng thật, test resize/splitter/scroll bằng mắt.

## 7. Liên quan

- `docs/roadmap/NEW-FUNCTIONS-DIRECTION.md` §VN-2/§VN-3 — acceptance criteria gốc.
- `docs/wine/KY-SO-PKCS11-RESEARCH.md` — nguồn chi tiết cho toàn bộ mục Ký số.
- `docs/wine/WINE-COMPAT-MATRIX.md` — nguồn cho các mục `wine-candidate`/`blocked` của Thuế/Kế toán/Hải quan.
- `includes.chroot/usr/share/namios/docs/KE-TOAN-TREN-NAMIOS.md` — bản tóm tắt dành cho người không rành kỹ thuật (kế toán); app này là bản THAO TÁC ĐƯỢC (bấm mở) của câu chuyện đó, không thay thế tài liệu đó.
- `catalog/services/*.json`, `catalog/compat/*.json` — nguồn dữ liệu gốc (ECO workflow 7 nấc).
