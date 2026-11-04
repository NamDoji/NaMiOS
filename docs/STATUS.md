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

## COMP (Phụ lục 03 — Trung tâm tương thích & nâng cấp) — Giai đoạn A

**Trạng thái: đã xây lõi Python thuần `namios_compat` (resolver + classifier + device registry + workflow pack + schema chống-metadata-giả + gate evidence) + CLI `namios compat` + 6 entry catalog ngành TRUNG THỰC (`not_inventoried`). Mọi chứng nhận THẬT (Wine chạy, thiết bị/token/máy in thật, ký số có vendor, DB MISA thật, pilot 3 nhóm) = BLOCKED Giai đoạn B/C/D (cần vendor + build host). KHÔNG workflow nào đạt `workflow_verified`.** Nguồn: `docs/spec-package/Phu_luc_03_Kien_truc_tuong_thich_va_nang_cap.md` (COMP-025..054).

Nối thẳng ECO-001..024 (KHÔNG dựng lại gate): tái dùng `namios_eco` (7 nấc `WorkflowStepName`, gate `derive_published_status`, `WindowsMode` 5 chế độ, chuẩn hoá NFKC, `validate_no_executable_keys`), `namios_dotnet` (classifier .NET/PE tĩnh), `namios_core` (envelope/exitcode/AppMode), lớp common song ngữ `namios_i18n` (toàn bộ chuỗi compat.* VN+EN qua `add_catalog`).

Đã xây (done-at-core, test xanh) — Giai đoạn A của §5 tài liệu:
- **COMP-025 Resolver** (`resolver.py`): chọn mode theo thứ tự điều tra `native_linux→web_linux→wine→remote_windows→windows_vm`, lọc feasibility (license/mạng/chính sách tổ chức), **trả `no_verified_route` khi không mode nào verified** (không đoán "chạy được"), và **làm MẤT HIỆU LỰC chứng nhận khi `app_version`/`token_model` đổi** so bản đã chứng nhận. **20 profile Gate A** phủ mọi nhánh + 2 bất biến nghiệm thu.
- **COMP-048 Schema** (`schema.py`): validator chống-metadata-giả — từ chối `technical_status=verified`/`end_to_end_status=pass` thiếu `tested_at`+`evidence_ids`, `vendor_support=supported` thiếu bằng chứng, `revoked=true` mà route còn usable, sai 7 nấc, sai schema_version/enum.
- **COMP-049 Evidence + GATE tổng hợp** (`evidence.py`): provenance đầy đủ (test_case_id/fixture_hash sha256/expected-actual/người-duyệt/môi trường sandbox|lab|production), `evaluate_route_status` = CHỒNG 3 tầng trung thực (thu hồi · nghiệp vụ chưa/không duyệt · quá hạn tái kiểm) lên gate kỹ thuật ECO-003 — chỉ HẠ, không NÂNG; metadata một mình KHÔNG tạo ra `workflow_verified`.
- **COMP-028 Runtime Classifier** (`classifier.py`): phân loại .NET hiện đại vs .NET Framework/WinForms/WPF vs native Win32 vs WebView2/SQLServer-client (nhãn phát hiện/suy đoán/chưa rõ, KHÔNG suy từ đuôi `.exe`); **driver nhân (PE subsystem=NATIVE) → KHÓA đường Wine**; dựa trên analyzer tĩnh `namios_dotnet` (không exec binary).
- **COMP-032 Device Registry** (`device_registry.py`): năng lực theo VID/PID/model/firmware/giao thức (IPP/CUPS, eSCL/SANE, PKCS#11…) + **chức năng test RIÊNG từng model**; thiết bị cùng hãng khác model KHÔNG tự được công nhận.
- **COMP-031 Workflow Pack** (`workflow_pack.py`): 6 pack ngành (thuế/kế toán/BHXH/giáo dục/hành chính công/ngành dọc) dữ liệu GIẢ, đủ 7 nấc, điểm-dừng-trước-giao-dịch-thật, cổng/nhà cung cấp `unresolved`/`unknown`; validator quét secret + khóa thực thi bị cấm.
- **COMP-050 CLI** `namios compat workflows|route|preflight|evidence|blocker` (song ngữ help; envelope JSON; `route` có `--app-version/--token-model/--license-ok/--offline/--allow-remote`). 6 catalog `catalog/compat/*.json` tất cả `not_inventoried` → `route` trả `no_verified_route=True` đúng sự thật.

| Mã | Trạng thái |
| --- | --- |
| COMP-025 Compatibility Resolver | done-core (20 profile Gate A) |
| COMP-026 App Capsule / COMP-027 Install Assistant | data/schema (chạy/rollback thật = Giai đoạn B, cần Wine host) |
| COMP-028 Runtime Classifier | done-core |
| COMP-029 Desktop Integration Bridge | BLOCKED-host (cần Wine + desktop thật) |
| COMP-030 Windows Workstation Fallback | data (cần quyền tổ chức + remote thật) |
| COMP-031 Workflow Pack 6 ngành | done-core (dữ liệu giả) |
| COMP-032 Device Capability Registry | done-core (registry + no-carryover) |
| COMP-033 Signing Broker | BLOCKED-vendor (cần API/SDK/PKCS#11 + sandbox) |
| COMP-034 Browser Environment Doctor | data (cần portal/middleware thật) |
| COMP-035/036 Print-Scan / thiết bị chuyên ngành | BLOCKED-host (cần thiết bị + pilot) |
| COMP-037 Document Fidelity Lab | data/schema (cần round-trip Office thật) |
| COMP-038 Database Compatibility Profile | data (cần DB/connector thật) |
| COMP-039 Data Migration Assistant | one-phần (nối `namios_welcome` DATA-002); audit đầy đủ cần máy Windows thật |
| COMP-040/041 Identity-Shares / Offline-Sync | data (cần domain/pilot) |
| COMP-042 Vietnamese UX Baseline | one-phần (locale/bộ gõ ở UX v1; đo 100 câu cần boot) |
| COMP-043 Accessibility & Familiar Desktop | one-phần (desktop skel ở UX v1; usability pilot BLOCKED) |
| COMP-044 Update Rings & Kill Switch | data/quy trình (primitives REVOKED/pin đã có) |
| COMP-045 Privacy-safe Diagnostics | done-core nền (redaction `namios_security` + nhãn evidence) |
| COMP-046 Helpdesk & Status | cli (một phần: blocker/route có chỉ dẫn) |
| COMP-047 Security Boundary | done-core nền (safe_path/safe_exec/no-RunCommand đã có từ M1) |
| COMP-048 Schema & Evidence | done-core |
| COMP-049 Provenance | done-core |
| COMP-050 Compatibility API/CLI | done-core |
| COMP-051 Phân khúc pilot | data (cần khảo sát người dùng thật) |
| COMP-052 Acceptance Matrix | done-core nền (3 cột kỹ thuật/nghiệp vụ/đầu-cuối tách ở `Certification`) |
| COMP-053 TCO & mức phụ thuộc Windows | data (cần số liệu vận hành) |
| COMP-054 Release Decision | done-core nền (gate + revoked/needs-retest; công bố cần chủ sở hữu test) |

**BLOCKED (không giả lập, đúng §6 tài liệu — cần chủ dự án/đơn vị pilot cấp):** (1) ≥30 app/cổng thật + 10 workflow bắt buộc/nhóm cho 3 chân dung pilot; (2) 2–3 máy in + 1 scanner + 1 token/ký-từ-xa thật + driver/middleware/CA; (3) tài khoản thử + sandbox được cổng cho phép; (4) phần mềm có license + bộ cài nhà phát hành + tài liệu API vendor; (5) máy Windows đối chứng + kế hoạch backup/rollback. Thiếu các thứ này chỉ thử tới bước TRƯỚC khi phát sinh hồ sơ/chữ ký/giao dịch thật.

**Tester đối kháng độc lập (COMP gate, `tests/security/compat/`, 102 case tấn công thẳng gate trung thực):** thử ép metadata giả → verified bằng mọi ngả (fake-verified, Unicode/enum/type-confusion, revoked-còn-usable, evidence-gap, business-bypass, never-usable-recommend, stale-cert, provenance). Bắt **5 lỗ hổng THẬT → em đã VÁ hết + khóa bằng test thường (regression guard)**: (1) COMPAT-ADV-002 [CAO] so hạn tái kiểm bằng so-chuỗi từ-điển → ngày không zero-pad `2026-2-1` làm cert quá-hạn-8-tháng vẫn verified → vá: `evidence._parse_iso` so NGÀY THẬT + schema `_is_iso_date` chặn định dạng sai khi nạp; (2) ADV-001 `evidence_ids=[""]` coi như có bằng chứng → `_has_real_evidence` đòi ID không rỗng; (3) ADV-003 `app_version=""` coi như khớp → bảo thủ: rỗng = chưa xác nhận = stale; (4) ADV-004 `token_model=None` ở workflow ký số bỏ qua kiểm → None = chưa xác nhận token = stale; (5) ADV-005 cert `verified` mà `app.version` chưa pin → miễn nhiễm drift vĩnh viễn → schema CẤM verified khi version chưa pin + resolver invalidate route verified/partial khi cert version chưa pin. Sau vá: 102/102 case pass.

Phạm vi file (chỉ thêm mới + bổ sung thuần-cộng vào CLI, không phá owner khác): `src/namios_compat/`, `src/namios_cli/compat_catalog_loader.py` (+ thêm block compat vào `main.py`/`parser.py`), `catalog/compat/`, `fixtures/compat/`, `docs/spec-package/Phu_luc_03_*`, `tests/unit/compat/`, `tests/security/compat/`. Gate: `ruff check src` + `black --check src` + `mypy src/namios_core` SẠCH; full suite **1206 pass / 1 skip / 0 fail** (compat 118 test unit + 102 case đối kháng).

---

## SAI (Phụ lục 04 — SmartAI) — M0 Khung an toàn + M1 Chẩn đoán + M2 Tự sửa (mô phỏng) + M3/M4 Quản trị-An toàn (buildable)

**Trạng thái: đã xây KHUNG AN TOÀN (M0) + CHẨN ĐOÁN (M1) + TỰ SỬA CÓ GIỚI HẠN (M2, sandbox mô phỏng) + LỚP QUẢN TRỊ & KIỂM SOÁT AN TOÀN (phần buildable của M3/M4) trong `namios_smartai` — build + test được ngay tại chỗ, fake provider + mock sandbox (determinism). KHÔNG model thật, KHÔNG root shell cho AI, KHÔNG thực thi giao dịch/cài-Wine thật.** Nguồn: `docs/spec-package/Phu_luc_04_SmartAI_Linh_hon_tuong_thich.md` (SAI-001..042).

Bất biến cốt lõi (SAI §1/§8): **LỜI AI ≠ SỰ THẬT** — trạng thái task chỉ cập nhật từ `ToolResult`; policy/consent/tool-contract là MÃ QUYẾT ĐỊNH ĐƯỢC (không phụ thuộc suy đoán model); AI chỉ phát action CÓ CẤU TRÚC. Nối COMP-025 (route), ECO/COMP (evidence/gate), `namios_i18n` (VN/EN), `namios_security` (an toàn).

Đã xây (done-at-core, test xanh — Giai đoạn M0 của §6):
- **SAI-003/038 State Machine** (`state_machine.py`): 12 trạng thái, `apply_tool_result` cập nhật TỪ kết quả tool — tool FAILED → `failed` dù AI nói "xong"; `completed` CHỈ từ `verifying`; terminal bất biến; durable serialize/resume.
- **SAI-039/017 Policy-as-Code** (`policy.py`): luật allow/deny tách khỏi prompt, **deny ưu tiên**; **R4 (ký/nộp/thanh toán) PHẢI xác nhận GIAO DỊCH cụ thể — "cứ làm đi" KHÔNG qua được**; R2+ cần consent+capability; **đổi mục tiêu → consent cũ vô hiệu**; consent/capability hết hạn/thu hồi/one-time đều chặn.
- **SAI-015/016/040 Tool Broker** (`tools.py`): 11 typed tool, KHÔNG shell/eval/subprocess; `invoke` fail-closed (tool lạ/sai schema/ngoài phạm vi path-url/thiếu capability đều BLOCKED); capability token scoped + revoke + one-time + hết hạn.
- **SAI-019 Prompt-Injection Defense** (`injection.py`): dữ liệu không tin cậy (log/web/file) là DỮ LIỆU, không thành lệnh; `scan_untrusted`/`guard_untrusted` fold VN, chặn "bỏ qua quy tắc/upload/send to http/sudo…".
- **SAI-001/002 Intent + Planner** (`intent.py`/`planner.py`): tiếng Việt (có/không dấu) → intent cấu trúc + mức chắc chắn + `unknowns`; **KHÔNG tự đoán người nộp/số tiền** (thiếu → hỏi lại, task `awaiting_input`); plan hữu hình, bước R2+ `consent_required`.
- **SAI-003/038/022 Orchestrator** (`orchestrator.py`): chạy plan tất định qua policy gate → tool broker → cập nhật trạng thái từ tool; **giao dịch thật R4 DỪNG TRUNG THỰC (blocked_external_dependency) — M0 không thực thi, không bịa biên nhận** (SAI-022); injection ở input → block.
- **SAI-050 CLI** `namios smartai plan "<tiếng Việt>"` (lập kế hoạch, chưa thực thi) · `namios smartai tools` (liệt kê tool + bậc rủi ro). Song ngữ help.

Đã xây thêm (M1 — Chẩn đoán, §6 "3 lỗi giả → kết luận đúng + không lộ secret"):
- **SAI-006 System Inventory** (`inventory.py`): CHỈ metadata (host OS/CPU/arch qua `platform`; app/thiết bị/token = khai báo) — KHÔNG đọc nội dung tài liệu/quét home; `read_fields` minh bạch (chỉ `host.*`/`declared.*`), `out_of_scope` liệt kê vùng cá nhân bị từ chối.
- **SAI-007 Dependency Graph** (`depgraph.py`): node installer→runtime→DB/service→thiết bị/token→portal với `observed|inferred|unknown`; **node bắt buộc chưa `observed` hoặc có blocker → CHẶN execute** (app mở được ≠ hoàn thành).
- **SAI-008 Route Selection** (`route.py`): tái dùng COMP-025 resolver; nhãn ".NET" KHÔNG tự thành `native_linux`; route Windows hiện rõ phụ thuộc + đổi app_version vô hiệu route.
- **SAI-009 Error Triage** (`triage.py`): **redact PII/secret TRƯỚC** (dùng `namios_security.redact_text`) rồi phân loại tất định 8 nhóm (missing_runtime/db_unreachable/device_missing/portal_plugin/license/unsupported_api/data_mismatch/unknown); thiếu-DLL ≠ license; không dấu hiệu → unknown.
- **`diagnose.py`**: gộp inventory + triage + depgraph + route → `Diagnosis` TRUNG THỰC (nêu blocker + đề xuất bước kế: vendor-report / route / gom-thêm-thông-tin); KHÔNG tự nhận "đã sửa"/"tương thích".
- **SAI-050 CLI** `namios smartai diagnose "<triệu chứng>"` (phân loại + redact + đề xuất, chưa sửa).

Đã xây thêm (M2 — Tự sửa có giới hạn, §6 "1 ca pass / 1 ca phải dừng; không sửa app gốc"; sandbox mô phỏng — Wine thật là M2-host):
- **SAI-018/020 Capsule + Supply-chain** (`capsule.py`): thử trên BẢN SAO frozen có snapshot — **bản gốc bất biến**, rollback hoàn nguyên, không mount home/DB/token thật; `check_supply_chain` chặn http/thiếu-hash/miền-không-chính-thức.
- **SAI-010 Bounded Repair** (`repair.py`): mỗi phép thử ĐÚNG 1 thay đổi + rollback; **giới hạn số phép thử/bước**, **dừng CỨNG** khi dữ-liệu-sai/thiếu-license/bảo-mật/cần-vendor, mọi ứng viên fail → dừng nêu lý do (KHÔNG retry vô hạn); executor TIÊM vào (mock M2 / Wine-sandbox sau). Recipe candidate CHỈ sinh từ phép thử SUCCESS thật.
- **SAI-011/041 Recipe** (`recipe.py`): schema đầy đủ; thiếu source/hash, hoặc đổi-hệ-thống mà thiếu rollback → **không publish được**; x86 KHÔNG tự áp x64; AI candidate mặc định `experimental`.
- **SAI-012/042 Promotion Gate** (`promotion.py`): draft/experimental→lab_passed→pilot_verified→published CHỈ qua `promote()` với tool-pass evidence + approver + reviewers + business_ok; **AI gán nhãn `state` KHÔNG nâng được** (`is_legitimately_published` tính lại); evidence quá hạn/nguồn giả → `needs_retest`; nguồn vendor/user chỉ tham khảo.
- **SAI-033 Regression** (`regression.py`): đổi bất kỳ thành phần khóa (Wine/model/app version/device…) → recipe/workflow `needs_retest` trước stable.
- **SAI-050 CLI** `namios smartai recipe-check <recipe.json>` (kiểm đủ điều kiện publish, không publish).

Đã xây thêm (M3/M4 — Quản trị & kiểm soát an toàn, phần buildable logic; pilot/vendor/model thật vẫn BLOCKED):
- **SAI-035 Kill Switch** (`kill_switch.py`): tắt ĐỘC LẬP model/tool/recipe/signing-adapter/auto-repair/release-ring (có wildcard tắt cả lớp); `guard()` để caller chặn an toàn; phát hiện sai dữ-liệu/chữ-ký → `block_release` tự chặn phát hành kế tiếp (thu hồi recipe pilot → tác vụ mới bị chặn).
- **SAI-037 Multiuser Administration** (`admin.py`): chính sách theo ĐƠN VỊ, phân quyền tất định — chỉ admin CÙNG đơn vị + có MEMBERSHIP mới sửa/duyệt R3-R4; **vai trò không = quyền** (phải trong `admin_users`); helpdesk chỉ đọc log khi cùng đơn vị + bật thu-log; **không admin một-cửa chéo đơn vị** (giáo viên không sửa được chính sách kế toán).
- **SAI-014 Vendor Pack** (`vendorpack.py`): dựng BẢN NHÁP báo cáo tái hiện — log REDACT (reuse `namios_security` + PII scrub) + quét secret còn sót → `contains_secrets`/`is_safe_to_share`; KHÔNG có hàm tự gửi/liên hệ; `collaboration` mặc định `desired`, không tự nâng `vendor_approved`.
- **SAI-022 Submission Idempotency** (`idempotency.py`): correlation ID; timeout/mơ hồ → `needs_lookup` (cần tra cứu), **`should_auto_resend` LUÔN False**; chỉ `confirmed` khi có biên nhận được kiểm.

Đã xây thêm (cross-cutting — an toàn dữ liệu / quan sát / cách ly, buildable logic):
- **SAI-024 Redaction Pipeline** (`redaction.py`): lớp lọc DÙNG CHUNG cho bundle chẩn đoán/telemetry — `redact_bundle` đệ quy che secret (reuse `namios_security`) + PII dãy số dài (CCCD/CMND/MST/tài khoản) + cookie/connection-string; `is_shareable` chỉ True khi không còn dấu hiệu secret sót; `scrub_all` scrub tối đa cho nơi phải sạch tuyệt đối; KHÔNG over-block hash hợp lệ.
- **SAI-034 Observability** (`observability.py`): `TraceEvent` chỉ gồm ID + nhãn + kết quả (plan/action/policy/tool/evidence/correlation) — `Trace.record` redact `note`, trace KHÔNG chứa credential; `classify_error_source` phân biệt rõ 5 nguồn lỗi model/policy/tool/vendor/portal; `reject_reasons` cho người dùng/admin xem lý do gate từ chối.
- **SAI-026 Memory Scope** (`memory_scope.py`): trí nhớ tách session/machine/org/public; **cách ly đa tenant** — get/list/export/delete non-public yêu cầu `requester == owner` (2 đơn vị KHÔNG đọc/xuất/xoá dữ liệu của nhau); public đọc tự do; tự-phục-vụ xem/xuất/xoá cấu hình của chính mình.

Đã xây thêm (batch cuối buildable — kiến thức có nguồn + phản hồi con người):
- **SAI-025 Knowledge Base có nguồn** (`knowledge_base.py`): tách 4 tầng provenance (chứng nhận NaMiOS / tài liệu chính thức / cộng đồng CHƯA kiểm / suy luận AI); `answer(app, version)` trả mức thử THẬT + provenance + ngày + độ tin + cờ cũ. **Chỉ chứng nhận NaMiOS nâng được `tested_level`**; không có chứng nhận cho ĐÚNG version → `UNTESTED` = "chưa kiểm" (KHÔNG suy từ version khác, KHÔNG để cộng đồng/AI nâng mức). Chứng nhận mới nhất thắng (FAILED mới đè VERIFIED cũ). `install_guidance_allowed` chỉ True khi có chứng nhận-chạy-được hoặc tài liệu chính thức — **không dùng lời đồn cộng đồng/AI để cài driver** (SAI-025). Nghiệm thu: "MISA chạy được không?" → đúng mức thử của version cụ thể hoặc "chưa kiểm".
- **SAI-029 Human Feedback** (`human_feedback.py`): người dùng đánh dấu "đã giải quyết/chưa giải quyết" + mô tả; IT và nghiệp vụ đánh giá RIÊNG (`verdicts_by_role` không gộp vai trò). **Phản hồi ≠ chứng nhận**: `would_promote_to_workflow_verified` và `can_certify_from_feedback` LUÔN False (dù nghìn lượt "đã giải quyết" từ mọi vai trò). Đầu ra DUY NHẤT có tác dụng = `suggested_test_cases` (UNRESOLVED→tái hiện, RESOLVED→hồi quy; UNCLEAR/không-mô-tả→bỏ qua). Nghiệm thu: một lượt "thành công" KHÔNG nâng `workflow_verified`.

| Nhóm | Trạng thái |
| --- | --- |
| SAI-001/002 Intent→Workflow + Task Plan | done-core |
| SAI-003 Honest status / SAI-038 Durable state | done-core |
| SAI-015/040 Typed Tools + Tool Contract | done-core |
| SAI-016 Capability Token / SAI-017 Risk Tiers | done-core |
| SAI-019 Prompt-Injection Defense | done-core |
| SAI-039 Policy-as-Code | done-core |
| SAI-022 External Submission + Idempotency | done-core (chặn trung thực + correlation-ID/needs_lookup/không auto-resend) |
| SAI-006 Inventory / SAI-007 Dependency Graph | done-core (M1) |
| SAI-008 Route Selection | done-core (M1, tái dùng COMP-025 resolver) |
| SAI-009 Error Triage (redact trước, 8 nhóm) | done-core (M1) |
| SAI-004/005 Giải thích VN / Accessibility | one-phần (chuỗi VN + CLI; a11y UI = sau) |
| SAI-010 Bounded Repair / SAI-011/041 Recipe / SAI-012 Promotion | done-core (M2, sandbox mô phỏng; Wine thật = M2-host) |
| SAI-018 Capsule+Rollback / SAI-020 Supply-chain / SAI-033 Regression / SAI-042 Trust | done-core (M2) |
| SAI-031 Compare Windows Baseline | data/comparator (ngưỡng nghiệp vụ); baseline Windows thật = M3 |
| SAI-014 Vendor Collaboration Pack | done-core (redact + no-secret gate + bản nháp, không auto-send) |
| SAI-013 Community learning | M4 (manifest ký/canary/thu hồi — cần hạ tầng phát hành) |
| SAI-021/030/031 Ký số/evidence/baseline thật | BLOCKED (vendor/thiết bị/Windows đối chứng) |
| SAI-024 Redaction Pipeline / SAI-023 Privacy | done-core (redact_bundle + is_shareable + scrub_all) |
| SAI-034 Observability | done-core (trace cấu trúc redact + phân loại 5 nguồn lỗi) |
| SAI-026 Memory Scope (cách ly tenant) | done-core |
| SAI-025 Knowledge Base provenance | done-core (4 tầng nguồn; chỉ cert NaMiOS nâng mức thử; "chưa kiểm" khi thiếu) |
| SAI-029 Human Feedback | done-core (phản hồi≠chứng nhận, LUÔN không nâng workflow_verified; chỉ gợi ý test case) |
| SAI-027/028 Model abstraction/budget | seam (ModelProvider Protocol + FakeModelProvider + RepairBudget); provider thật = sau |
| SAI-035 Kill Switch | done-core (tắt độc lập + wildcard + block-release) |
| SAI-037 Multiuser Administration | done-core (authz theo đơn vị; vai-trò≠quyền; không admin một-cửa) |
| SAI-036 Local operation | OS-level (desktop/app offline — thuộc distro/live-build) |

**BLOCKED (đúng §9 — cần đơn vị pilot/vendor):** M2-host = chạy Wine thật 2 app OSS (engine + recipe/promotion/regression đã xong trên sandbox mô phỏng; chỉ thiếu executor Wine thật — cùng interface `TrialExecutor`); M3/M4 = model AI thật + quyền đưa dữ liệu ra ngoài, app/version/license/Windows đối chứng, thiết bị/token/CA/portal sandbox, người duyệt nghiệp vụ R3/R4. M0/M1/M2-sim KHÔNG cần các thứ này (fake provider + mock tools/sandbox + fixture — đúng §9).

**QA độc lập — 16 test bắt buộc §7 (`tests/security/smartai/test_sai_acceptance.py`, T01–T16):** **12 pass THẬT + 4 skip TRUNG THỰC** (T05 sandbox-file=M2, T11 redaction=M1, T13 recipe-registry=M2, T16 offline-desktop=OS — mỗi skip VẪN assert primitive M0 trước khi skip, lỗi primitive sẽ FAIL chứ không ẩn). **KHÔNG lỗ hổng**: mọi bất biến an toàn M0 (T01/03/04/06/07/08/09/12/13/14) đứng vững — AI nói "xong" mà tool fail→`failed`; injection→0 lần gọi tool; R4 "cứ làm đi"→DENY; submit xác-nhận→BLOCKED không bịa biên nhận, chạy 2 lần không nhân đôi; đổi app_version→mất hiệu lực route (tái dùng COMP-025); durable round-trip + resume. QA nêu 1 edge (chạy lại task BLOCKED ra PARTIAL) → em siết: task terminal/blocked/awaiting-input = no-op.

**QA độc lập M1 (`tests/security/smartai/test_m1_adversarial.py`, 9 case):** đánh rò-secret qua `log_text` + `crash_signature` (password/token/Bearer/OTP/khối PEM), CCCD/đường home, bypass chặn-execute (quét mọi tổ hợp NodeStatus×blocker), diagnose-không-nhận-"đã sửa", never-crash (chuỗi rỗng/100k/unicode/bytes), inventory đúng phạm vi. **9/9 giữ vững, KHÔNG lỗ hổng.** QA nêu: redactor chung không che CCCD trần → em vá bằng lớp PII SmartAI (`triage._scrub_pii` che dãy ≥9 chữ số, không đụng exit code) + khóa bằng test.

**QA độc lập M2 (`tests/security/smartai/test_m2_adversarial.py`, SAI-032):** đánh ép-retry-vô-hạn/budget, đột-biến-bản-gốc, dừng-cứng, bịa-recipe, **fake promotion bằng nhãn `state`**, evidence quá-hạn/sai-định-dạng, supply-chain lookalike, arch cross-apply, regression. Bắt **1 lỗ hổng THẬT**: `evidence_expired` có `if not now: return False` → gọi `promote()` QUÊN truyền `now` thì evidence năm-2000 vẫn "còn hạn", có thể lên published (bất biến SAI-042 không tự-bảo-vệ). → Em vá **fail-closed**: có `valid_until` mà không biết `now` → coi QUÁ HẠN; khóa bằng test (22/22 pass sau vá).

**QA độc lập M3/M4 governance (`tests/security/smartai/test_m34_adversarial.py`, 15 case):** đánh bypass kill-switch (wildcard/name-trick casing-whitespace), **leo quyền chéo đơn vị** (giả admin đơn vị khác, vai-trò-không-membership), rò secret vendorpack (password/token/Bearer/PEM/CCCD + token lọt), ép auto-resend/confirm-không-biên-nhận. **15/15 giữ vững, KHÔNG lỗ hổng.** QA nêu regex quét-secret hẹp → em mở rộng high-confidence (gh-variant/AWS/Slack) + giữ không over-block hash hợp lệ.

**QA độc lập cross-cutting (`tests/security/smartai/test_crosscutting_adversarial.py`):** đánh rò bundle lồng nhau, rò trace-note, xuất/xoá chéo tenant + case/whitespace trick. **13 pass; bắt 2 lỗi phân-loại-nguồn-lỗi THẬT** (không rò secret — là sai nhãn): khớp chuỗi-con làm "b**risk**et"→POLICY, "horo**scope**"→TOOL. → Em vá bằng khớp RANH-GIỚI-TỪ (`\b`) + khóa test (giờ pass thật). Em cũng tự siết authz `export_tenant`/`delete_tenant` (thêm `requester==owner`) trước QA.

**QA độc lập KB + Feedback (`tests/security/smartai/test_kb_feedback_adversarial.py`, 36 case):** đánh bắc-cầu-version (near-miss `2024.0/2024.1/2024-sp1`, chữ số full-width), ép community/AI-tự-gắn-VERIFIED (kể cả 50+ bản ghi confidence 0.99) nâng mức, ép lật FAILED, bẫy stale (now rác/bằng-hạn/thiếu), và mọi khối lượng feedback (3000 lượt RESOLVED × 3 vai trò) ép `workflow_verified`/`can_certify`. **Feedback: 0 lỗ hổng** (hai gate chứng nhận là `return False` vô điều kiện). **KB: bắt 1 lỗ hổng THẬT (I5)** — `answer()` chọn chứng nhận "mới nhất" bằng SO-CHUỖI trên `as_of` → ngày không zero-pad `2026-9-1` > `2026-10-01` theo chuỗi (và ISO có offset múi giờ) khiến VERIFIED CŨ che FAILED MỚI + bật install (cùng lớp lỗi COMPAT-ADV-002). → Em vá: chọn mới-nhất theo NGÀY THẬT (`_parse_utc` + UTC-aware; ngày hỏng → coi cũ nhất, fail-closed), cùng mốc → ưu tiên mức BẢO THỦ hơn (FAILED đè VERIFIED); khóa bằng 2 test regression (giờ pass thật). Sau vá: 36/36 pass.

Phạm vi file (chỉ thêm mới + bổ sung thuần-cộng vào CLI): `src/namios_smartai/` (M0: state_machine/policy/tools/injection/intent/planner/orchestrator; M1: inventory/depgraph/triage/route/diagnose; M2: capsule/repair/recipe/promotion/regression; M3/M4-gov: kill_switch/admin/vendorpack/idempotency; cross-cutting: redaction/observability/memory_scope; batch cuối: knowledge_base/human_feedback), `src/namios_cli/` (block smartai + import i18n), `tests/unit/smartai/`, `tests/security/smartai/`, `docs/spec-package/Phu_luc_04_*`. Gate: `ruff check src` + `black --check src` + `mypy src/namios_core` SẠCH; full suite **1483 pass / 5 skip / 0 fail** (SmartAI M0+M1+M2+M3/M4-gov+cross-cutting+KB/feedback + acceptance T01-T16 + đối kháng M1 9 / M2 22 / M3-4 15 / cross-cutting 15 / KB-feedback 36).

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
