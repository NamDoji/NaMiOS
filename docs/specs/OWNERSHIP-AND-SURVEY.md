# OWNERSHIP-AND-SURVEY — Quyền sở hữu NaMiOS + Khung khảo sát 100 app + Checklist di chuyển

**Trạng thái:** DESIGN/TEMPLATE (02/11/2026). Hiện thực phần **M0 soạn được** của backlog **B038** (P0): template quyền sở hữu + khung khảo sát + checklist migration. **Phần dữ liệu thật BLOCKED** — chờ chủ dự án (Đỗ Chí Cường + Đỗ Bảo Nam) cấp nội dung.
**Nguồn:** đặc tả §26 (OWN-001/002/003), §29 (WIN-001..003), §30 (MIG-001); CLAUDE.md non-negotiables; `docs/assumptions.md` A52–A54.
**Truy vết test:** OWN-01 (gate G3, review), WIN-01 (gate G0, review). Cả hai giữ `not_run` cho tới khi có dữ liệu + người ký.

> Phân loại: **FACT** = dẫn đặc tả; **DESIGN** = đề xuất M0; **TARGET** = ngưỡng/chỉ tiêu cần đo, CHƯA đạt; **UNKNOWN** = chưa có bằng chứng.
>
> ⚠️ Toàn bộ file này là **KHUNG/BIỂU MẪU**. KHÔNG tuyên bố đã khảo sát, đã có app chạy được, đã đăng ký nhãn hiệu, hay đã xác lập pháp nhân. Mọi ô dữ liệu để **TRỐNG** cho chủ dự án / nhóm người dùng điền thực. Agent KHÔNG tự điền pháp nhân, không tự liên hệ vendor, không tự tra/đăng ký trademark-domain.

---

## PHẦN A — Ownership & Legal checklist (cần chủ dự án điền)

OWN-001/002/003 (FACT §26): NaMiOS chỉ sở hữu **phần tự viết**; KHÔNG sở hữu Debian/Linux/KDE/Wine/tài sản bên thứ ba. Mọi ô dưới chưa xác lập giữ **UNKNOWN**; ô đánh **[BLOCKED — chờ chủ dự án]** không được agent tự điền.

| # | Hạng mục | Yêu cầu (FACT §26) | Giá trị | Trạng thái |
| --- | --- | --- | --- | --- |
| A-01 | Pháp nhân phát hành | Tên chủ thể pháp lý sở hữu phần phát triển riêng + phát hành NaMiOS | _(trống)_ | **BLOCKED — chờ chủ dự án** (UNKNOWN) |
| A-02 | Nhà sáng lập/chủ dự án | Ghi đúng **Đỗ Chí Cường** + **Đỗ Bảo Nam** trong About/tài liệu/website | Đỗ Chí Cường; Đỗ Bảo Nam | FACT (đã chốt §26) |
| A-03 | Phân định IP phần tự viết | Hồ sơ tác giả + nguồn gốc cho mã/asset do dự án viết (để 2 founders quản trị dài hạn — OWN-003) | _(trống — cần log tác giả theo commit/asset)_ | **BLOCKED — chờ quy trình** (DESIGN: yêu cầu DCO/author trailer) |
| A-04 | Contributor License Agreement (CLA/DCO) | Thỏa thuận đóng góp + chuyển giao quyền với người đóng góp trước phát hành | _(trống)_ | **BLOCKED — chờ chủ dự án** (DESIGN: đề xuất DCO `Signed-off-by`) |
| A-05 | Giấy phép mã mới | Giấy phép cho phần tự viết | **Đề xuất Apache-2.0** (DESIGN — cần chủ dự án duyệt) | PENDING duyệt |
| A-06 | Giấy phép thành phần upstream | Liệt kê + tuân thủ nghĩa vụ GPL/LGPL/… của Debian/KDE/Wine/font; công bố nguồn (OWN-002) | _(trống — lập SBOM ở M3)_ | **BLOCKED — M3 SBOM** (FACT A44) |
| A-07 | Tra cứu nhãn hiệu "NaMiOS" | Kiểm trademark trước công bố rộng; GHI trạng thái tra cứu; đặt tên trong tài liệu ≠ đăng ký bảo hộ (OWN-002) | **CHƯA tra cứu** | **UNKNOWN** (agent KHÔNG tự tra/đăng ký) |
| A-08 | Tên miền NaMiOS | Kiểm tra + đăng ký domain trước công bố | **CHƯA kiểm tra** | **UNKNOWN** (agent KHÔNG tự đăng ký) |
| A-09 | Quyền dùng tên NaMiOS | Quy định ai được dùng tên NaMiOS (sản phẩm/dịch vụ/đại lý) trước phát hành | _(trống)_ | **BLOCKED — chờ chủ dự án** |
| A-10 | Điều kiện dịch vụ kèm theo | Kho app bên thứ ba / hỗ trợ / app thương mại (nếu có) công bố điều kiện riêng (OWN-003) | _(trống)_ | **BLOCKED — chờ mô hình kinh doanh** |
| A-11 | Không nhúng tài sản độc quyền | KHÔNG chép pixel/icon/âm thanh/font Microsoft; không nhúng key/secret/installer/DB thật (FACT CLAUDE.md, §28) | _(ràng buộc kỹ thuật — đã khóa)_ | FACT (enforce ở semantic validator + review) |

**Ánh xạ xuống M1 (FACT):** chỉ A-02 + A-05 + A-11 chạm lõi M1 — qua `AboutInfo` trong `namios_core` (M1-INTERFACES §1b): `founders` cố định 2 người, `legal_entity=None` cho tới khi A-01 xác lập, `licenses[]` khai Apache-2.0 (mã mới) + giấy phép upstream. Màn About hiển thị là M3.

---

## PHẦN B — Khung khảo sát 100 ứng dụng Windows (WIN-001)

FACT §29 WIN-001: danh mục **100 app** khảo sát từ **người dùng mục tiêu**, ghi phiên bản cụ thể + 10 tác vụ phổ biến; chọn **20 app ưu tiên** cho pilot. Đây là **TARGET của khảo sát** — **CHƯA khảo sát, CHƯA có app nào chạy được** (FACT STATUS: mọi app `untested`). Bảng dữ liệu để **TRỐNG** cho nhóm người dùng điền.

### B.1 — Biểu mẫu trường dữ liệu mỗi app (1 dòng/app, điền thực tế)

| Trường | Mô tả | Bắt buộc |
| --- | --- | --- |
| `app_name` | Tên ứng dụng | ✔ |
| `vendor` | Nhà cung cấp | ✔ |
| `version_build` | Phiên bản + build cụ thể (KHÔNG "latest") | ✔ (FACT WIN-001) |
| `architecture` | 32-bit / 64-bit | ✔ |
| `user_group` | Nhóm người dùng (văn phòng / giáo viên / kế toán / hộ KD) | ✔ |
| `frequency` | Tần suất dùng (hằng ngày / tuần / tháng / hiếm) | ✔ (yếu tố chọn 20) |
| `importance` | Mức quan trọng (bắt buộc-công việc / quan trọng / tiện ích) | ✔ (yếu tố chọn 20) |
| `top_10_tasks` | 10 tác vụ phổ biến nhất (text, mỗi tác vụ 1 dòng) | ✔ (FACT WIN-001) |
| `install_type` | Loại cài (MSI/EXE/Store/portable/web) | ✔ (WIN-002) |
| `runtime` | Runtime cần (vd .NET Framework 4.x / .NET 8 / VC++ / JRE) | ✔ |
| `com_activex` | Phụ thuộc COM/ActiveX (có/không + chi tiết) | ✔ |
| `service_driver` | Windows service / kernel driver `.sys` cần (có → `requires_windows_environment`) | ✔ (FACT §27/WIN-002) |
| `dotnet` | Loại .NET (Framework / modern / WinForms / WPF / ASP.NET Core) | ✔ |
| `token_sign` | Phụ thuộc USB token / smartcard / middleware ký số | ✔ (FACT §27 DEV-005) |
| `print_dep` | Phụ thuộc in (driver riêng / khổ / mã vạch-QR / chứng từ) | ✔ |
| `other_dep` | registry / ODBC-OLEDB / WebView / fonts / add-in / macro / liên ứng dụng | — |
| `license_mode` | Cách cấp phép + kích hoạt (cần bản dùng hợp pháp để test động) | ✔ |
| `migration_difficulty` | Độ khó di chuyển (dễ / trung bình / khó / chặn — có kernel driver) | ✔ (yếu tố chọn 20) |
| `candidate_mode` | Mode dự kiến: native / web / wine / vm / remote (`AppMode` §1b) | — |

> Lưu ý (FACT WIN-002): phân tích **động** chỉ trong máy ảo cô lập với bản dùng **hợp pháp** — là M2/M4 BLOCKED tại host này. Khảo sát (điền biểu mẫu) là M0 làm được; chạy/đo app là sau.

### B.2 — Bảng dữ liệu 100 app (ĐỂ TRỐNG — chủ dự án/nhóm người dùng điền)

| # | app_name | vendor | version_build | arch | user_group | frequency | importance | migration_difficulty | candidate_mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | _(trống)_ | | | | | | | | |
| … | _(tới 100 dòng)_ | | | | | | | | |

**Bắt buộc có trong nhóm khảo sát (FACT WIN-001):** Word, Excel, Zalo PC, MISA SME, và các lớp **.NET** phải nằm trong 100 app. (Edition/build cụ thể: UNKNOWN — chờ chủ dự án, xem assumptions A52–A54.)

### B.3 — Phương pháp chọn 20 app ưu tiên cho pilot (DESIGN)

Điểm ưu tiên đề xuất (TARGET — ngưỡng cần chủ dự án duyệt trước khi dùng):

```
priority_score = w_f·frequency + w_i·importance + w_d·migration_difficulty
```

- `frequency`, `importance`, `migration_difficulty` quy về thang 1–5 (difficulty: khó hơn = điểm CAO hơn vì rủi ro/giá trị di chuyển lớn, cần ưu tiên khảo sát sâu — KHÔNG đồng nghĩa ưu tiên "chạy được").
- Trọng số đề xuất `w_f=0.4, w_i=0.4, w_d=0.2` (DESIGN, cần duyệt).
- Chọn 20 app điểm cao nhất, NHƯNG **ghim cứng** Word/Excel/Zalo PC/MISA SME + ≥1 app .NET vào 20 bất kể điểm (FACT WIN-001).
- App có `service_driver = kernel driver` → gắn `requires_windows_environment`, KHÔNG hứa chạy Wine; cân nhắc đường VM/remote có giấy phép (FACT §29).

> ⚠️ CHỌN 20 ≠ cam kết 20 app chạy được. Đây là 20 app **ưu tiên khảo sát/pilot**. Trạng thái tương thích mỗi app vẫn `untested` cho tới khi có evidence theo tuple + QA ký (FACT §11.2, WP9 gate).

---

## PHẦN C — Migration checklist (MIG-001, rút gọn)

FACT §30 MIG-001: checklist **trước chuyển đổi**; thử trên máy phụ/Live mode trước; chỉ chuyển máy chính khi workflow được nghiệm thu + có bản sao dữ liệu phục hồi được. Mẫu dưới điền **mỗi người dùng/máy** sắp chuyển.

| # | Hạng mục | Nội dung cần ghi | Trạng thái |
| --- | --- | --- | --- |
| C-01 | Danh mục ứng dụng | App + version đang dùng trên máy này (từ Phần B) | ☐ |
| C-02 | Danh mục thiết bị | Máy in/scan/token/POS + model + firmware (từ device DB M4) | ☐ |
| C-03 | Phiên bản dữ liệu | Định dạng + phiên bản file dữ liệu (DOCX/XLSX/DB MISA…) + vị trí | ☐ |
| C-04 | Backup/restore | Cơ chế sao lưu + ĐÃ test khôi phục được (bắt buộc trước khi chuyển) | ☐ |
| C-05 | Tài khoản/giấy phép | Tài khoản + license từng app; cách kích hoạt lại hợp pháp | ☐ |
| C-06 | Người hỗ trợ | Người chịu trách nhiệm hỗ trợ trong+sau chuyển đổi | ☐ |
| C-07 | Kế hoạch quay về | Điều kiện + cách rollback về Windows nếu workflow fail | ☐ |
| C-08 | Thử trên máy phụ/Live | Đã chạy workflow trọn vẹn trên máy phụ/Live TRƯỚC khi đụng máy chính | ☐ |
| C-09 | Nghiệm thu workflow | Mọi bước bắt buộc của workflow đạt (nếu 1 bước chặn → `not_ready_for_migration`, FACT WIN-006) | ☐ |
| C-10 | Người ký chấp thuận | Chữ ký người dùng + người phụ trách trước khi chuyển máy chính | ☐ |

> Gate (FACT §30): KHÔNG chuyển máy chính khi còn ô C-04/C-08/C-09/C-10 chưa đạt. Checklist này là template; thực thi (lab thiết bị, pilot 30 ngày WIN-007) thuộc **M4 BLOCKED**.

---

## Trạng thái tổng kết (B038)

- **Soạn được tại M0 (DONE trong file này):** Phần A template + ánh xạ M1, Phần B biểu mẫu + phương pháp chọn 20, Phần C checklist.
- **BLOCKED chờ chủ dự án:** A-01/A-03/A-04/A-07/A-08/A-09/A-10 (ownership/legal/trademark), B.2 bảng 100 app thật (edition/build Office/MISA — UNKNOWN A52–A54), và toàn bộ chạy/đo app (M2/M4).
- **KHÔNG claim:** chưa khảo sát xong, chưa có app chạy được, chưa đăng ký nhãn hiệu/domain, chưa xác lập pháp nhân. OWN-01/WIN-01 giữ `not_run`.
