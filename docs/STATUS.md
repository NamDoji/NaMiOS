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

## M0 Gói 1 — Khung inventory + 3 workflow đo-được + fixture tự tạo

**Trạng thái: khung + fixture đã có và đã giám khảo độc lập; KHẢO SÁT THẬT + ĐO TRÊN WINDOWS-REFERENCE + TEST APP THƯƠNG MẠI vẫn BLOCKED (chờ chủ dự án cấp dữ liệu/máy). Mọi app giữ UNTESTED.**

Theo `docs/specs/GIAO-VIEC-M0-M2.md` (Gói 1, mục tiêu "Nắm rõ người dùng và ứng dụng quyết định thành bại").

| Phần | Hiện trạng | Phân loại |
| --- | --- | --- |
| `inventory/applications.csv` | 16 dòng placeholder (Word/Excel/Zalo PC+Web/MISA SME+AMIS/3 lớp .NET/HTKK/ký số/HĐĐT/bộ gõ/PDF/họp/LibreOffice); **16/16 `status=unknown`, `windows_reference=TBD`** | DESIGN + UNKNOWN |
| `inventory/devices.csv` | 5 dòng placeholder (máy in IPP/máy in cũ/scanner eSCL-SANE/USB token ký số/máy in HĐ POS); **5/5 `support_status=not_tested`** | DESIGN + UNKNOWN |
| `inventory/workflows.md` | 3 workflow A (DOCX) / B (XLSX) / C (MISA) có bước + bảng tiêu chí pass/fail cụ thể, expected trỏ fixture; mục "Windows reference" đánh dấu **BLOCKED** riêng cho cả 3 | DESIGN |
| Fixture `A_docx/` | `baocao-tieng-viet.docx` thật (python-docx) + `expected.md`; verify round-trip bằng python-docx (KHÔNG có Word/LibreOffice thật) | FACT (tool-level) |
| Fixture `B_xlsx/` | `bangtinh.xlsx` (SUM/AVERAGE/IF/VLOOKUP/XLOOKUP/ngày/ROUND) + `bangtinh-vi-VN.csv` (locale vi-VN) + `expected.json` tự tính bằng Decimal/datetime (KHÔNG từ cache Excel) | FACT (tool-level) |
| Fixture `C_misa/` | `danhmuc-taikhoan.csv` + `chungtu.csv` hạch toán kép tự soạn + `expected-report.md` (bất biến Tổng Nợ=Tổng Có=126.500.000 VNĐ) | FACT (tool-level) |
| `scripts/make_workflow_fixtures.py` | Sinh lại toàn bộ fixture, tự assert khi chạy, idempotent | FACT |
| Giám khảo độc lập | `qa/evidence-index/M0-GOI1/ketqua-giamkhao.md`: tự tính lại bằng Python độc lập cho A/B/C — **KHỚP 100%, 0 defect**; xác nhận inventory không dòng nào bị gán pass/surveyed sai | FACT |

**BLOCKED (chờ chủ dự án cấp dữ liệu/máy — không được tính là "đã khảo sát"/"pass"):**
- Khảo sát 100 app / chọn 20 app pilot THẬT — chưa có dữ liệu thật, chỉ khung + placeholder.
- Đo THẬT cả 3 workflow A/B/C trên **Windows reference** — không có máy Windows/Office/MISA/SQL Server/máy in/scanner/USB token thật.
- Test MISA SME thật — cần license đúng năm/build + SQL Server + máy Windows lab + kế toán QA.
- Bước "in" (A) và "in chứng từ" (C) — không có máy in/driver thật → giữ `unknown`, không gán pass.

**Đầu vào THẬT còn thiếu (một chỗ, gọn — cần chủ dự án/Nam cấp):** (1) edition/build Word+Excel có license; (2) năm/build MISA SME + phiên bản SQL Server; (3) 2–3 app .NET thật (console/WinForms/WPF); (4) model máy in/scanner/USB token thật; (5) 1 máy Windows-reference (lab hợp lệ) để đo; (6) xác nhận 3 workflow ưu tiên đúng A/B/C; (7) nhóm pilot cụ thể (phòng ban + người). Chi tiết ở `inventory/README.md`.

---

## ECO (Phụ lục 02 — Hệ sinh thái phần mềm thiết yếu VN)

**Trạng thái: đã xây lõi Python thuần `namios_eco` + danh bạ ngành có URL thật + CLI `namios service`; mọi test giao dịch/nộp/ký THẬT trên cổng nhà nước = BLOCKED (sandbox/không có quyền). KHÔNG app/dịch vụ nào đạt `workflow_verified`.** Nguồn: `docs/specs/PHU-LUC-02-HE-SINH-THAI-VN.md` (ECO-001..024), chi tiết per-item ở `docs/specs/ECO-BACKLOG.md`.

Đã xây (done-at-core, test xanh):
- **7 nấc workflow** `discover→acquire→install_or_open→authenticate→execute→submit_or_export→verify_result` là bất biến kết cấu (không thể xoá nấc dù `not_applicable`), kèm rule web-app-không-binary — `src/namios_eco/workflow.py`.
- **GATE trạng thái công bố (8 trạng thái)** — `downloadable_only`/`launches_only` TUYỆT ĐỐI không bao giờ `is_usable()=True`; `workflow_verified` chỉ khi `submit_or_export` **và** `verify_result` đều `pass` + có `evidence_ref` thật — `src/namios_eco/status.py`.
- **Tách 2 trường độc lập** `tested_by_namios` vs `officially_supported_by_vendor` (ECO-004), `ServiceEntry` chủ đích KHÔNG có trường thực thi/lệnh (ECO-006) — `src/namios_eco/models.py`, `contracts/service-catalog.schema.json`.
- **Validator 2 tầng** (cấu trúc `catalog_schema.py` + ngữ nghĩa `validator.py`: URL chính thức, GATE usable, GATE workflow_verified↔evidence, quét-khóa-thực-thi đệ quy, cấm nhãn "ứng dụng chính thức của NaMiOS"), **coverage** (ECO-022, tách web/wine/vm/remote + "listed != working"), **search** không dấu (ECO-007).
- **Danh bạ ngành thật** `catalog/services/*.json` — 12 entry (thuế HTKK/eTax Mobile/thuedientu, kế toán+HĐĐT MISA SME/AMIS/hoadondientu, BHXH cổng giao dịch/I-VAN TS24-eBH/công cụ ký số, DVC quốc gia, CSDL ngành MOET, VNACCS hải quan), mỗi entry có URL chính thức xác minh qua web-search + `source_check` ghi rõ **host build không mở được BẤT KỲ domain .gov.vn/vendor nào** (6 WebFetch 02/11 đều ECONNREFUSED/ECONNRESET). Vì KHÔNG tự mở được trang, **cả 12 entry giữ `not_inventoried`** (bảo thủ hơn cả `launches_only`), `tested_by_namios=officially_supported_by_vendor=false`. CLI `namios service list|search|inspect` tính `usable` qua `is_usable` (không bao giờ true cho NEVER_USABLE) + luôn in listed-vs-workflow_verified = **12 vs 0**.

| Mã | Trạng thái |
| --- | --- |
| ECO-001 7 nấc workflow | done-core |
| ECO-002 chứng nhận đúng phạm vi | done-core + data (số liệu theo cổng/tỉnh) |
| ECO-003 8 trạng thái + GATE usable | done-core |
| ECO-004 tách tested/vendor-support | done-core (hiển thị 2 trường = cli) |
| ECO-005 công thức ưu tiên chuyển đổi | data (chờ khảo sát thật) |
| ECO-006 danh bạ service-catalog | done-core + **data (12 entry URL thật)** |
| ECO-007 search không dấu + cấm nhãn | done-core |
| ECO-008 doctor tự kiểm môi trường | cli (`namios_doctor`, chưa code) |
| ECO-009 trung tâm ký số nhiều tầng | data (chờ vendor/token model thật) |
| ECO-010 bridge ký số Linux | BLOCKED-sandbox (chờ văn bản hợp tác/quyền) |
| ECO-011 ký từ xa kênh chính thức | data (chờ vendor + sandbox) |
| ECO-012 dependency graph desktop | data (ngoài phạm vi phiên, gần planner) |
| ECO-013 round-trip định dạng ngành | data (cần fixture ngành thật) |
| ECO-014 ưu tiên API chính thức | data/chính sách |
| ECO-015 WindowsMode + tỉ lệ không-phụ-thuộc-Windows | done-core |
| ECO-016 không giao dịch thật khi chưa phép/không sandbox | done-core (cơ chế `blocked_external_dependency`) + **BLOCKED-sandbox (thực thi thật)** |
| ECO-017 3 mức độc lập (kỹ thuật/dữ liệu/đầu-cuối) | done-core một phần (a); (b)(c) chờ QA/nghiệp vụ |
| ECO-018 thử lỗi có thực | BLOCKED-sandbox |
| ECO-019 danh sách vendor cần liên hệ | data |
| ECO-020 chứng cứ cung cấp vendor | data (chờ chủ dự án duyệt) |
| ECO-021 nhãn "Supported on NaMiOS" | data (chờ tiêu chí + quyền logo/tên) |
| ECO-022 dashboard coverage listed!=working | done-core (hàm tính) + cli (render) |
| ECO-023 quy tắc dừng rollout | data/quy trình (primitives REVOKED đã có) |
| ECO-024 bảng app/cổng đã kiểm theo ngày | cli (render chưa làm) |

**Giám khảo độc lập (tester ECO, `qa/evidence-index/ECO/`, 10 file test đối kháng, 98 test):** GATE "downloadable_only/launches_only không bao giờ usable" và "workflow_verified cần evidence" ĐƯỢC GIỮ (các test regression-guard pass, có cả test chứng minh gate không phải "luôn false"). Nhưng tìm được **2 nhóm defect THẬT (8 test FAIL, verified độc lập, CHƯA vá)**:
- **[CAO] ECO-016-QA-01** — `derive_published_status` (`src/namios_eco/status.py:154`): chuỗi kiểm `blocked_external_dependency` không gồm `discover`/`acquire`. Khi `discover`/`acquire` bị `BLOCKED` (ĐÚNG tình huống thật của cả 12 entry hiện tại: không kết nối được .gov.vn), kết quả suy ra SAI thành `partial_workflow` (`is_usable()=True`) kèm `reasons_vi` khẳng định sai rằng authenticate/execute đã chạy. Vi phạm tinh thần GATE ECO-003/ECO-016 — hiển thị "dùng được" cho workflow chưa `discover` xong. Chưa làm sai dữ liệu catalog hiện tại (catalog không lưu `steps`, các entry đã cứng `not_inventoried`), nhưng sẽ sai NGAY khi có người tạo `WorkflowResult` thật rồi gọi `derive_published_status`.
- **[TRUNG BÌNH] ECO-007-QA-01** — `validate_no_official_claim_text` (`validator.py:271-286`): chỉ `casefold()`, không chuẩn hoá Unicode → cụm cấm "ứng dụng chính thức của NaMiOS" lọt qua khi ở dạng NFD hoặc chèn zero-width-space (dù hiển thị giống hệt). Cùng package đã có `search.fold_vn` xử lý đúng NFD nhưng validator không tái dùng.

Chi tiết repro/expected/actual/khuyến nghị-fix: `qa/evidence-index/ECO/defects.md`. 2 defect thuộc dev `namios_eco` (chưa vá trong phiên này — tester chỉ kiểm & báo; sửa cần chủ dự án giao lại cho dev ECO-core).

**BLOCKED (không giả lập, không bịa biên nhận):** test ký/nộp hồ sơ THẬT lên cổng nhà nước (ECO-016/018), bridge ký số Linux thật (ECO-010), round-trip định dạng ngành thật (ECO-013) — tất cả cần sandbox/host có token/HSM/quyền tích hợp vendor + cổng thật; host Debian 12 hiện tại không có. `windows_mode` của HTKK/MISA SME/công cụ ký số/VNACCS gán `windows_vm` là PHÂN LOẠI theo `published_os` công khai, KHÔNG phải kết quả test Wine/VM thật (cần spike Wine ECO-012 trước khi đổi).

**Đầu vào THẬT còn thiếu (cần chủ dự án/Nam cấp):** (1) sandbox/host có kết nối tới cổng .gov.vn + tài khoản/token thật để nâng entry lên `launches_only`/`partial_workflow`/`workflow_verified`; (2) chọn nhà cung cấp I-VAN pilot thật (trong 14 nhà BHXH công nhận); (3) dữ liệu khảo sát thật để tính công thức ưu tiên ECO-005 + danh sách vendor ECO-019; (4) quyết go/no-go vá 2 defect trên trước khi bất kỳ luồng nào suy `published_status` từ `WorkflowResult` thật.

Phạm vi file (xác nhận `git status --porcelain` chỉ thấy mục mới, không phá file owner khác): `src/namios_eco/`, `src/namios_cli/service_catalog_loader.py` (+ bổ sung thuần-cộng-thêm vào `main.py`/`parser.py`), `catalog/services/`, `contracts/service-catalog.schema.json`, `docs/specs/ECO-BACKLOG.md`, `tests/unit/eco/`, `tests/integration/...service...`, `tests/qa/ECO/`, `qa/evidence-index/ECO/`. Test: 93 unit `namios_eco` + 18 integration service-catalog + 90/98 QA đối kháng pass (8 FAIL = 2 defect thật chưa vá); 563 test nền trước đó KHÔNG bị phá.

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

---

## M3-prep (đã soạn sẵn — chờ build host)

Theo BUILD-001 ("host không build được thì tạo hướng dẫn/cấu hình build"), đã soạn-trước (tất cả `verified_on_host: NO`, CHƯA chạy ở container hiện tại):
- `docs/runbooks/BUILD-HOST-SETUP.md` + `scripts/preflight-build-host.sh` — preflight ĐÃ chạy thật ở container này: `not_ready`, exit 3, 14/18 mục bắt buộc MISSING (đúng, khớp inventory M0).
- `distro/live-build/` — cấu hình live-build (Debian 13 + KDE + Fcitx5/bộ gõ Việt + font + LibreOffice + Firefox ESR + CUPS + Wine + list `namios-*` để `.disabled`), hook locale/timezone/IME, branding NaMiOS chỉ-text (không tài sản Microsoft, LIC-006 có ghi chú non-free-firmware), `build-manifest.yaml` pin = TBD-chốt-trên-host.
- `scripts/build-iso.sh` + `scripts/boot-test-qemu.sh` — argv-only, `set -euo pipefail`, không curl|bash/eval; thiếu toolchain → thoát non-zero, KHÔNG tạo ISO giả; boot-test chỉ `-cdrom` read-only (INSTALL-001).
- `packaging/debian/namios-base/` — skeleton metapackage (control/changelog/rules/copyright Apache-2.0).
- Giám khảo QA (`qa/evidence-index/M3-PREP/`): 0 defect; full suite 772 pass/1 skip giữ nguyên (chỉ thêm docs/config/script, không đụng `src/`).

Lần chạy `scripts/build-iso.sh` + `boot-test-qemu.sh` ĐẦU TIÊN trên build host thật = bước xác minh M3 thật sự (G1).
