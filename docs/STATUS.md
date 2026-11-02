# Báo cáo trạng thái — NaMiOS

**Thương hiệu:** NaMiOS (thống nhất mọi nơi — OWN-001). **Nhà sáng lập/chủ dự án:** Đỗ Chí Cường + Đỗ Bảo Nam. NaMiOS KHÔNG sở hữu Debian/Linux/KDE/Wine — chỉ phần tự viết (§26, ADR 0009).
**Mốc hiện tại:** M1 (Hạt nhân phần mềm riêng) — lõi 10 module + CLI thật + .NET static analyzer đã GREEN; cổng G0 đạt phần lõi + .NET-analysis, BLOCKED phần Wine-fixture. M0 + đặc tả SUPERSET §26–§30 (delta vòng 2) đã hoàn tất.
**Ngày:** 02/11/2026, múi giờ Asia/Ho_Chi_Minh.
**Source commit:** xác định tại thời điểm commit (chưa chốt — tài liệu này được tạo trong pha M0).
**Người thực hiện:** đội BA/kỹ thuật M0.
**Người kiểm tra:** chưa có QA ký độc lập (pha M0 chưa yêu cầu nghiệm thu ứng dụng).

> Tài liệu này theo mẫu `docs/spec-package/qa/MAU_BAO_CAO.md`. Phân loại nhận định: FACT (có nguồn), DESIGN (quyết định dự án), TARGET (chỉ tiêu cần đo), UNKNOWN (chưa có bằng chứng).

---

## Kết luận

**Trạng thái tổng thể: chỉ mới scaffolding thư mục + M0 tài liệu, CHƯA có hệ điều hành, ISO hay ứng dụng nào đạt.** Không được đồng nhất việc đã có cây thư mục/skeleton với việc đã hoàn thành phần mềm hay hệ điều hành.

- Cấu trúc repository (§19) đã được dựng khung: `src/`, `catalog/`, `contracts/`, `distro/`, `fixtures/`, `qa/`, `tests/`, `docs/` — đây là scaffolding, không phải chức năng chạy được.
- Hợp đồng dữ liệu (`contracts/app-manifest.schema.json`, `contracts/evidence-report.schema.json`) và hai mẫu (`sample-misa-sme-wine.json`, `sample-evidence-not-run.json`) đã có ở dạng JSON Schema khởi đầu. Đây **chưa** phải manifest có chữ ký production và **chưa** có semantic validator kiểm điều kiện an toàn (sẽ ở M1).
- Môi trường build hiện tại chỉ đủ cho **M0** (tài liệu) và **M1** (lõi Python thuần). **M2 (Wine/.NET), M3 (ISO/boot), M4 (app thương mại) đang BLOCKED** vì thiếu KVM/Wine/live-build/QEMU và bộ cài có quyền dùng.
- **Chưa có evidence run nào.** Mọi dòng trong `qa/test-matrix.csv` giữ `not_run`. Không ứng dụng thương mại nào được gán trạng thái đạt. Toàn bộ app ở trạng thái `untested`, `vendor_support = unknown`.
- Mọi con số hiệu năng/quy mô trong đặc tả là **TARGET**, không phải kết quả đo (xem PERF-001/002/003, HW-*, SEC-011). Thêm từ §26–§30: 100 app khảo sát, 20 model lab, 20 app pilot, 15 người usability, 30 ngày pilot, 90% tác vụ — tất cả là **TARGET/ngưỡng đề xuất**, chưa đo.
- **Delta vòng 2 (§26–§30):** thêm backlog **B038–B043** và test **OWN-01 / DEV-01..08 / UI-04..08 / WIN-01..03 / HWPLUS / MIG** — tất cả `not_started` / `not_run`. Thêm 4 ADR mới **0009–0012** (proposed). Không app/thiết bị nào được gán trạng thái đạt.

**Gate G0: ĐẠT PHẦN LÕI + .NET-ANALYSIS, BLOCKED Wine-fixture (cần build host) — KHÔNG pass toàn phần. G1–G3: PENDING.** Xem `docs/releases/G0-FEASIBILITY-REPORT.md`.

> **Cảnh báo chiến lược (WIN-008).** KHÔNG thể bảo đảm 100% phần mềm Windows hiện hành chạy nguyên vẹn trên nền Linux/Wine, đặc biệt app có **driver nhân Windows** [S17], chống gian lận, dịch vụ đặc biệt, kích hoạt hoặc tích hợp nội bộ. Đây là **ranh giới chiến lược**, KHÔNG phải mức "cố gắng lập trình" mà Claude Code có thể bảo đảm. Nếu mục tiêu kinh doanh đòi "mọi app Windows chạy kể cả kernel driver" → phải **đánh giá lại chiến lược nền tảng** trước khi đầu tư rộng. Kết quả khảo sát 100 app có thể dẫn tới **phạm vi thiết bị/app chứng nhận hẹp** hoặc **đường VM/remote có license** phía sau (báo rõ phụ thuộc + chi phí). Xem ADR 0012, assumptions A93.

---

## Môi trường (từ `docs/_m0_inventory_raw.md`, tra cứu 02/11/2026)

| Hạng mục | Giá trị thật | Phân loại |
| --- | --- | --- |
| Host OS | Debian GNU/Linux 12 (bookworm) — **không phải** Debian 13 mục tiêu | FACT |
| Kernel | 5.14.0 (host RHEL9), chạy trong container | FACT |
| Kiến trúc | x86_64 | FACT |
| CPU | AMD EPYC-Rome 4 nhân; **không** có cờ `vmx`/`svm` | FACT |
| RAM | 7.5 GiB (≈5.8 available) | FACT |
| Disk workspace | 169G, trống ~70G | FACT |
| Ảo hóa | `/dev/kvm` **ABSENT** → không chạy nested VM/KVM tại đây | FACT |
| Toolchain CÓ | git 2.39.5, python 3.11.2, pip 26.2.1, venv, node v24.16.0 | FACT |
| Toolchain THIẾU | qemu-system-x86_64, lb (live-build), debootstrap, mmdebstrap, xorriso, fakeroot, wine, winetricks, mkisofs | FACT |
| pytest | chưa cài; cài được qua pip trong venv | FACT |
| Mạng | egress tới github.com HTTP 200 (~0.1s) OK | FACT |
| Desktop session | không có (môi trường headless/container) | FACT |
| Package snapshot phát hành | chưa chốt (mục tiêu Debian 13 trixie, pin ở M3) | UNKNOWN |
| Wine/runtime/profile/app versions + hashes | chưa có (chưa cài, chưa thu thập) | UNKNOWN |

> Host hiện tại là **Debian 12 trong container không có ảo hóa**, khác với nền **mục tiêu Debian 13** của sản phẩm. Điều này đủ cho M0/M1 nhưng không đại diện cho máy người dùng cuối; mọi kết luận về boot/ISO/Wine phải thực hiện trên build host hợp lệ.

---

## Phạm vi đã làm (requirement IDs)

| Phần | Requirement IDs | Hiện trạng | Phân loại |
| --- | --- | --- | --- |
| Inventory môi trường M0 | REPO-001 | Đã có `_m0_inventory_raw.md` + bảng trên | FACT |
| Đặc tả chính (§1–§25) | toàn bộ | Đã có `docs/specs/DAC_TA_HE_DIEU_HANH.md` | FACT (tài liệu) |
| ADR nền tảng (8 ADR) | — | Chuyển thành `docs/adr/0001..0008`, trạng thái `proposed` | DESIGN |
| ADR delta §26–§30 (4 ADR mới) | OWN/DEV/UI/WIN/MIG | Đã thêm `docs/adr/0009..0012` (ownership-brand, thiết bị-driver, giao diện quen thuộc, chuyển đổi-pilot), trạng thái `proposed` | DESIGN |
| Threat model sơ bộ | B004, SEC-001, SEC-003 | Đã có `docs/threat-model.md` | DESIGN |
| Bảng giả định FACT/DESIGN/TARGET/UNKNOWN | §2, §5, §24 | Đã có `docs/assumptions.md` | hỗn hợp |
| Hợp đồng manifest/evidence | §11, COMP-004 | Schema khởi đầu đã có; **semantic validator CHƯA viết** | DESIGN + UNKNOWN |
| Backlog + test matrix | REPO-001 | Đã có trong `spec-package/`; mọi dòng `not_started`/`not_run` | FACT |
| Lõi Python M1 (validator, doctor, state store, catalog, redaction, evidence model) | B005–B009 | **ĐÃ VIẾT + GREEN** — 10 module + core, CLI thật end-to-end (console-script `namios`), full suite 562 pass/1 skip/1 xfail | FACT |
| .NET static analyzer (parser PE/CLR tĩnh, không thực thi input) | NET-001/002 | **ĐÃ VIẾT + GREEN** — `namios_dotnet`, 45 unit + 36 adversarial test PASS; chỉ cho **suggested_mode** (gợi ý tĩnh, không chứng nhận chạy) | FACT |
| Ownership/brand + khảo sát 100 app (khung) | B038 / OWN-001/002/003, WIN-001 | Khung About/license/tra-cứu + template khảo sát làm được M0; **dữ liệu thật + pháp nhân chờ chủ dự án** | DESIGN + UNKNOWN |
| Desktop quen thuộc + onboarding | B039 / UI-001..005 | Design tokens/mapping phím tắt dạng tài liệu làm được; shell/file-manager chạy thật **M3 BLOCKED** | DESIGN + UNKNOWN |
| Ma trận thiết bị theo model + lab 20 model | B040 / DEV-001/002/003/007, HWPLUS-001 | Schema device DB + validator làm được M1; in/scan/firmware thật **M4 BLOCKED** | DESIGN + UNKNOWN |
| USB token + thiết bị nghiệp vụ | B041 / DEV-004/005/006/008 | Ma trận token (khung) làm được; ký sandbox + thiết bị thật **M4 BLOCKED** | DESIGN + UNKNOWN |
| Workflow Windows tham chiếu | B042 / WIN-002/003/004/005 | Schema tác vụ/mode/`not_ready_for_migration` làm được M1; chạy workflow thật **M4 BLOCKED** | DESIGN + UNKNOWN |
| Thử nghiệm chuyển đổi 30 ngày + usability 15 người | B043 / UI-006/007, WIN-006/007, MIG-001 | Checklist/template làm được; pilot 30 ngày + 15 người thật **M4 BLOCKED** | TARGET + UNKNOWN |

Thay đổi so với đặc tả: không có mâu thuẫn. ADR 0001–0008 giữ nguyên nội dung từ `ADR_KHOI_DAU.md` (chỉ bổ sung bối cảnh môi trường + spike/điều kiện chấp nhận). Bổ sung SUPERSET §26–§30 được phản ánh qua assumptions mục 13–17 (A60–A95), ADR 0009–0012, và backlog/test mới liệt kê ở trên.

---

## Bảng gate phát hành (§18.4)

| Gate | Nội dung điều kiện (tóm tắt) | Trạng thái | Lý do |
| --- | --- | --- | --- |
| **G0** khả thi | 1 Wine fixture chạy thật; đường phân tích .NET đúng; report pass/fail/blocked/untested cho từng app mục tiêu; quyết định go/no-go/phạm vi hẹp | **ĐẠT PHẦN LÕI + .NET-ANALYSIS, BLOCKED Wine-fixture (cần build host)** | Điều kiện (b) đường phân tích .NET + (c) report + (d) quyết định go/no-go: ĐÃ CÓ bằng chứng (lõi M1 + CLI thật end-to-end + `namios_dotnet`). Điều kiện (a) Wine fixture chạy thật: **BLOCKED** — thiếu Wine/KVM tại host này. KHÔNG pass toàn phần. Chi tiết: `docs/releases/G0-FEASIBILITY-REPORT.md` |
| **G1** alpha kỹ thuật | ISO boot Live; cài/reboot trong VM; app-center + fixture chạy; journal phục hồi; không root Wine; negative tests schema/path/signature đạt | **PENDING** | Thiếu live-build/QEMU; lõi M1 chưa viết nên negative tests chưa chạy (B017–B022 `not_started`) |
| **G2** pilot nghiệp vụ | Build/mode chốt; 100% tác vụ bắt buộc nhóm pilot đạt; backup/restore; phần cứng; cập nhật; hỗ trợ có người chịu trách nhiệm | **PENDING** | Chưa có bộ cài Office/Zalo/MISA có quyền dùng; chưa có phần cứng pilot; chưa có QA ký (B023–B034 `not_started`) |
| **G3** phát hành công khai | Kiểm toán quyền phân phối; metadata/package ký production; công bố nguồn/nghĩa vụ giấy phép; support/EOL; ma trận công khai; quy trình tiếp nhận lỗi | **PENDING** | Chưa có key production, chưa có maintainer/EOL, chưa có G2 (B035–B036 `not_started`) |

---

## Lệnh và kết quả thực

| Run ID | Lệnh hoặc test | Exit code | Kết quả | Evidence |
| --- | --- | --- | --- | --- |
| M1-FULL | `PYTHONPATH=src pytest tests -q` (repo root) | 0 | **562 passed, 1 skipped, 1 xfailed, 0 failed** | suite xanh toàn repo |
| G0-NET | `pytest tests/unit/dotnet` | 0 | 45 passed (.NET static analyzer) | `src/namios_dotnet/` |
| G0-NET-ADV | `pytest tests/qa/G0-NET` | 0 | 36 passed, 0 defect (adversarial PE/CLR) | `qa/evidence-index/G0-NET/` |
| G0-WIRING | `pytest tests/integration` | 0 | 13 passed (CLI thật end-to-end) | console-script `namios` |
| G0-CLI | `pytest tests/qa/G0-CLI` | 0 | 31 passed + 1 xfailed (G0-CLI-DEFECT-01, CONFIRMED) | `qa/evidence-index/G0-CLI/meta.json` |

> **Lưu ý:** mọi run trên là test lõi/phân tích tĩnh/CLI thuần Python. **KHÔNG** có evidence CHẠY ứng dụng Windows/Wine. Phân tích .NET là gợi ý tĩnh, không chứng nhận chạy được. Phần việc G0 hiện trong working tree **CHƯA commit** (HEAD `df783f5`). Mock/unit test **không** dùng để chứng nhận binary Office/MISA chạy được. Thiếu bộ cài/môi trường/credentials → ghi `blocked_external_dependency` với đầu vào cần bổ sung, không đổi `skipped`/`blocked` thành `pass`.

---

## Tình trạng ứng dụng (tất cả UNTESTED)

| App và build | Mode | Tác vụ bắt buộc | Kết quả | Giới hạn | Vendor support |
| --- | --- | --- | --- | --- | --- |
| Microsoft Word — build chưa chốt | wine | chưa chốt (APP-OFF-003) | `untested` | Thiếu build + bộ cài hợp lệ; cần môi trường Windows tham chiếu | `unknown` |
| Microsoft Excel — build chưa chốt | wine | chưa chốt (APP-OFF-004) | `untested` | VBA/add-in/Power Query là nhóm chứng nhận riêng | `unknown` |
| Microsoft Office — bản web | web | chưa chốt | `untested` | Hồ sơ khác; cần tài khoản + Internet; không gộp với desktop | `unknown` |
| LibreOffice | native | chưa chốt | `untested` | Phần mềm thay thế, KHÔNG tính là Microsoft desktop đạt | n/a |
| Zalo PC | wine | chưa chốt (APP-ZAL-002/003) | `untested` | Tách khỏi web; call/video là nhóm riêng | `unknown` |
| Zalo Web | web | chưa chốt | `untested` | Cần Internet; không suy đầy đủ chức năng PC | `unknown` |
| MISA SME — build chưa chốt | wine | MISA-01..06 | `untested` | SQL Server tách Windows; DB + ký số chưa kiểm; không dùng dữ liệu kế toán thật | `unknown` |
| MISA AMIS Kế toán | web | chưa chốt (APP-MIS-006) | `untested` | Hồ sơ web riêng; ký số cần công cụ cục bộ | `unknown` |
| MISA KYSO / USB token | remote/wine | chưa chốt (APP-MIS-007) | `untested` | Nhánh token/middleware riêng theo hãng/model | `unknown` |
| Ứng dụng .NET (console/ASP.NET Core/WinForms/WPF/Framework) | tùy phân loại | NET-01..04 | `untested` | Cần phân loại framework/phụ thuộc trước khi chọn mode | `unknown` |

> Mẫu `contracts/sample-misa-sme-wine.json` minh họa trạng thái đúng: `status: untested`, `vendor_support: unknown`, `last_tested: null`, `evidence_id: null`, runner chưa pin → semantic validator (M1) phải **chặn cài**.

---

## Dữ liệu và phục hồi

- Bộ dữ liệu bắt buộc (§18.2: WORD 12, EXCEL 15, MISA doanh nghiệp giả, DOTNET mẫu tự viết, FILES cây Unicode): **chưa tạo**. Không dùng dữ liệu kế toán/tài liệu thật làm fixture public.
- Round-trip, backup/restore, DB restore: **chưa chạy** (phụ thuộc M2/M4).
- Dữ liệu không thể hoàn nguyên: không có (chưa thao tác lên dữ liệu thật nào).

---

## Vấn đề còn lại / rủi ro

| ID | Mức | Mô tả | Điều kiện đóng |
| --- | --- | --- | --- |
| BLK-M2 | P0 | M2 (Wine/.NET fixture) blocked — thiếu wine/winetricks tại host | Build host Linux amd64 có Wine pin + fixture tự viết |
| BLK-M3 | P0 | M3 (ISO/boot) blocked — thiếu live-build/debootstrap/xorriso/qemu + `/dev/kvm` | Build host có nested-virt + bộ công cụ live-build |
| BLK-M4 | P0 | M4 (app thương mại) blocked — thiếu bộ cài có quyền dùng + phần cứng pilot | Chủ dự án cấp bộ cài hợp lệ + 5 cấu hình phần cứng + người kế toán QA |
| GAP-M1 | ~~P0~~ ĐÓNG | Lõi M1 (semantic validator, doctor, state store, catalog, evidence, planner, CLI thật) + .NET analyzer đã viết, 562 test GREEN | ĐÃ ĐÓNG — B005–B009 + negative tests đạt; còn G0-CLI-DEFECT-01 (medium) chờ vá; work chưa commit (HEAD df783f5) |
| OWN-LEGAL | P1 | Pháp nhân phát hành, tra cứu trademark/domain "NaMiOS", contributor agreement chưa có | Chủ dự án + luật sư cung cấp; ghi trạng thái tra cứu (OWN-001/002, ADR 0009) |
| WIN-STRAT | P0 | Kỳ vọng "100% app Windows chạy" (WIN-008) không bảo đảm được bằng lập trình | Chủ dự án quyết go/no-go/phạm vi hẹp/đường VM-remote có license trước khi đầu tư rộng (ADR 0012) |
| BLK-DEV-LAB | P0 | Lab ≥20 model thiết bị (in/scan/token/kết nối) + token/middleware hợp lệ chưa có | Chủ dự án cấp lab + build host nested-virt (DEV-*, HWPLUS-*, ADR 0010) |
| BLK-UI-DESKTOP | P1 | Desktop/file-manager/onboarding chạy thật + usability 15 người chưa có | ISO/desktop thật (M3) + 15 người tình nguyện (UI-*, ADR 0011) |
| BLK-MIG-PILOT | P0 | Workflow trọn vẹn + pilot 30 ngày chưa chạy | Thiết bị đã chứng nhận + nhóm tình nguyện + bộ cài hợp lệ (WIN-*, MIG-001, ADR 0012) |

---

## Quyết định gate

- **Product owner:** chưa ký (TBD — anh Đỗ Chí Cường).
- **QA:** chưa ký (độc lập, bắt buộc trước mọi `task_verified`).
- **Gate hiện tại:** G0 **ĐẠT PHẦN LÕI + .NET-ANALYSIS, BLOCKED Wine-fixture**; G1–G3 **PENDING**.
- **Phạm vi được công bố:** chưa có.
- **Đầu vào cần bổ sung:** xem §22 đặc tả (edition/build Office; mô hình MISA + SQL; danh sách .NET; máy pilot; đội + nhóm người dùng đầu).
- **Bước tiếp theo:** (1) commit phần việc G0 đang untracked để cố định bằng chứng; (2) vá/ghi nhận G0-CLI-DEFECT-01; (3) chuẩn bị build host Linux nested-virt + Wine + live-build + bộ cài hợp lệ để mở khóa M2/M3/M4 (điều kiện (a) của G0); (4) chốt phạm vi công bố theo WIN-008 trước khi đầu tư rộng.
