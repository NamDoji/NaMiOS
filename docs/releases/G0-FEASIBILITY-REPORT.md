# Báo cáo khả thi — Gate G0 (NaMiOS)

> Theo mẫu `docs/spec-package/qa/MAU_BAO_CAO.md`. Tiếng Việt, trung thực tuyệt đối.
> Phân loại nhận định: **FACT** (có bằng chứng/nguồn), **DESIGN** (quyết định dự án), **TARGET** (chỉ tiêu cần đo), **UNKNOWN** (chưa có bằng chứng).

**Mốc:** Cổng G0 (khả thi) — đánh giá sau khi lõi M1 + đường phân tích .NET + CLI thật đã có bằng chứng.
**Ngày:** 02/11/2026, múi giờ Asia/Ho_Chi_Minh.
**Source commit:** HEAD `df783f5` (baseline M1 437-green). **Lưu ý trung thực:** toàn bộ phần việc G0 mô tả dưới đây (wiring CLI thật, `namios_dotnet`, bộ test tích hợp + adversarial) hiện nằm trong **working tree CHƯA commit** (3 file modified: `pyproject.toml`, `src/namios_cli/deps.py`, `src/namios_cli/main.py`; 7 mục untracked: `src/namios_dotnet/`, `fixtures/dotnet/`, `tests/integration/`, `tests/unit/dotnet/`, `tests/qa/G0-NET/`, `tests/qa/G0-CLI/`, `qa/evidence-index/G0-{NET,CLI}/`). Cần commit để cố định bằng chứng.
**Người thực hiện:** đội M1 (các WP wiring + .NET + QA tester).
**Người kiểm tra:** QA kỹ thuật nội bộ (tester CLI + tester adversarial .NET). **CHƯA có QA độc lập ký nghiệm thu ứng dụng** — pha này chưa chạy ứng dụng thương mại nào.

---

## 1. Kết luận gate G0

**G0 ĐẠT PHẦN LÕI PHẦN MỀM + ĐƯỜNG PHÂN TÍCH .NET; BLOCKED PHẦN "WINE FIXTURE HOẠT ĐỘNG". KHÔNG tuyên bố G0 pass toàn phần.**

Đặc tả §18.4 định nghĩa G0 gồm bốn điều kiện: (a) **một Wine fixture hoạt động**; (b) **đường phân tích .NET đúng**; (c) **report pass/fail/blocked/untested cho từng app mục tiêu**; (d) **quyết định go/no-go/phạm vi hẹp**.

| Điều kiện G0 (§18.4) | Trạng thái | Bằng chứng / lý do |
| --- | --- | --- |
| (a) Một Wine fixture **chạy thật** | **BLOCKED** | Host hiện tại Debian 12 trong container, `/dev/kvm` ABSENT, không có `wine`/`winetricks`/`qemu`/`live-build` (FACT, `_m0_inventory_raw.md`). Không thể thực thi bất kỳ binary Windows nào ở đây. Đây là **gate M2 có chủ đích**, không phải lỗi. |
| (b) Đường phân tích .NET **đúng** | **ĐẠT (có bằng chứng)** | `namios_dotnet` — parser PE/CLR tĩnh thuần Python, không thực thi input; 45 unit test + 36 test adversarial PASS. |
| (c) Report pass/fail/blocked/untested từng app | **ĐẠT (dạng khung + đúng sự thật)** | Bảng app-mode-version mục 3: mọi app = `untested`/`blocked`, `vendor_support=unknown` — phản ánh ĐÚNG việc chưa có evidence chạy. |
| (d) Quyết định go/no-go/phạm vi | **ĐẠT** | Khuyến nghị **GO có điều kiện, chia pha** — mục 5. |

**Diễn giải:** Phần "khả thi về mặt phần mềm/kiến trúc" (lõi, CLI, phân tích .NET tĩnh, khung báo cáo, quyết định) đã có bằng chứng thật. Phần "khả thi chạy ứng dụng Windows thật qua Wine" **chưa chứng minh được tại host này** và phải chờ build host hợp lệ. Vì điều kiện (a) chưa đạt, **G0 KHÔNG được coi là pass toàn phần**; đây là "G0 đạt phần lõi + .NET-analysis, BLOCKED Wine-fixture".

---

## 2. Những gì đã CHỨNG MINH (số test thật)

Tất cả số dưới đây đo bằng lệnh chuẩn trong `CLAUDE.md`, chạy từ repo root `code_projects/namios` với `PYTHONPATH=src`. **Full suite: 562 passed, 1 skipped, 1 xfailed, 0 failed** (xfailed = defect CLI đã xác nhận mục 6; baseline trước G0 là 437 pass — phần tăng là test tích hợp/.NET/adversarial mới).

| Hạng mục đã chứng minh | Phạm vi | Test PASS | Phân loại |
| --- | --- | --- | --- |
| Lõi 10 module + core (M1) | `namios_core`, `namios_manifest`, `namios_catalog`, `namios_evidence`, `namios_planner`, `namios_recipe`, `namios_security`, `namios_doctor`, `namios_helper`, `namios_txstate`, `namios_cli` | thuộc 562 (baseline 437 GREEN) | FACT |
| CLI thật end-to-end (wiring) | `default_dependencies()` nối implementation THẬT (ManifestValidatorImpl / InMemoryCatalogStore / EvidenceValidatorImpl / DefaultInstallPlanner+RecipeEngineImpl); console-script `namios` | `tests/integration` = **13 passed** | FACT |
| .NET static analyzer (NET-001/002) | `namios_dotnet` — parser PE/COFF/CLR thuần, sidecar runtimeconfig/deps.json, suggested_mode, disclaimer tiếng Việt | `tests/unit/dotnet` = **45 passed** | FACT |
| Adversarial .NET (tester độc lập) | 8 mũi tấn công: e_lfanew biên, header cụt, count bịa, magic lạ, file 0 byte, file 256MiB/64MiB (đo thời gian <5s), fuzz 180 mẫu, chống thực thi (monkeypatch os.system/subprocess) | `tests/qa/G0-NET` = **36 passed, 0 defect** | FACT |
| QA CLI integration (tester độc lập) | doctor/catalog validate/evidence validate/app inspect/plan-install; bất biến "1 dòng JSON", exit 0–9, không lộ secret/path, chặn injection (url-script, template `{{ secrets }}`) | `tests/qa/G0-CLI` = **31 passed + 1 xfailed** (defect) | FACT |

**Lệnh thật đã verify (console-script):** `namios doctor --json` → đúng 1 dòng JSON envelope, `has_kvm=false` khớp FACT môi trường, exit 0. Tương tự `namios catalog validate`, `namios app inspect`, `namios app plan-install` đều ra 1 dòng JSON, status=ok, exit 0, dùng implementation thật (không fake). Manifest injection (recipe chứa khóa `shell`) bị chặn ở `ManifestValidatorImpl.load()`, CLI trả `E_INPUT_SCHEMA`/exit 2, không crash, không lộ payload.

**Chưa chứng minh (không được suy diễn thành đạt):** không có một dòng evidence CHẠY ứng dụng Windows/Wine nào; `app install` thật luôn BLOCKED ở M1 theo thiết kế; phân tích .NET là **gợi ý tĩnh**, KHÔNG phải chứng nhận chạy được (disclaimer bắt buộc đã nhúng trong kết quả).

---

## 3. Bảng app-mode-version (tất cả UNTESTED / BLOCKED — đúng sự thật)

> Không app thương mại nào có evidence chạy. `.NET analyzer` chỉ cho **suggested_mode** (gợi ý tĩnh), không phải kết quả chạy.

| App và build | Mode | Tác vụ bắt buộc | Kết quả | Giới hạn | Vendor support |
| --- | --- | --- | --- | --- | --- |
| Microsoft Word (build chưa chốt) | wine | chưa chốt (APP-OFF-003) | `untested` / blocked | Thiếu Wine + bộ cài hợp lệ + Windows tham chiếu | `unknown` |
| Microsoft Excel (build chưa chốt) | wine | chưa chốt (APP-OFF-004) | `untested` / blocked | VBA/add-in/Power Query là nhóm chứng nhận riêng | `unknown` |
| Microsoft Office — web | web | chưa chốt | `untested` | Hồ sơ khác; cần tài khoản + Internet; không gộp desktop | `unknown` |
| Zalo PC (build chưa chốt) | wine | chưa chốt (APP-ZAL-002/003) | `untested` / blocked | Call/video là nhóm riêng; tách khỏi web | `unknown` |
| Zalo Web | web | chưa chốt | `untested` | Cần Internet; không suy đầy đủ chức năng PC | `unknown` |
| MISA SME (build chưa chốt) | wine | MISA-01..06 | `untested` / blocked | SQL Server tách Windows; DB + ký số chưa kiểm | `unknown` |
| MISA AMIS Kế toán | web | chưa chốt (APP-MIS-006) | `untested` | Hồ sơ web riêng; ký số cần công cụ cục bộ | `unknown` |
| MISA KYSO / USB token | remote/wine | chưa chốt (APP-MIS-007) | `untested` / blocked | Token/middleware riêng theo hãng/model | `unknown` |
| App .NET (console/ASP.NET Core/WinForms/WPF/Framework) | tùy phân loại | NET-01..04 | `untested` (chỉ có **gợi ý tĩnh**) | `namios_dotnet` gợi ý mode: desktop (WinForms/WPF) → WINE kể cả net8.0; .NET Core hiện đại không desktop → NATIVE; native/mixed → WINE; thiếu bằng chứng → `None` (không đoán). **Gợi ý ≠ chạy được.** | `unknown` |

---

## 4. BLOCKED + điều kiện mở khóa

| ID | Mức | Phần bị chặn | Điều kiện mở khóa |
| --- | --- | --- | --- |
| BLK-G0-WINE | P0 | Wine fixture chạy thật (điều kiện (a) của G0) — thiếu `wine`/`winetricks` + `/dev/kvm` tại host | **Build host Linux amd64 có nested-virt** (`vmx`/`svm` + `/dev/kvm`) + Wine pin + fixture Win32 tự viết vô hại |
| BLK-M2 | P0 | Toàn bộ M2 (Wine/.NET runner thật, prefix isolation, sandbox proof, transaction recovery) | Như trên + runner detection/pin |
| BLK-M3 | P0 | M3 ISO/boot | Build host có `live-build`/`debootstrap`/`xorriso`/`qemu` + nested-virt để QEMU boot/install |
| BLK-M4 | P0 | M4 app thương mại + pilot | **Bộ cài Office/Zalo/MISA có quyền dùng hợp lệ** (chủ dự án cấp) + **5+ cấu hình phần cứng pilot** + USB token/middleware hợp lệ + **người kế toán QA** làm UAT nghiệp vụ |
| OWN-LEGAL | P1 | Pháp nhân phát hành, tra cứu trademark/domain "NaMiOS", contributor agreement | Chủ dự án + luật sư cung cấp |

**Phần cứng/token/credentials:** cần máy pilot thật (model/CPU/RAM/GPU/Wi-Fi/printer/token), bộ cài có license, tài khoản dịch vụ — ghi `blocked_external_dependency`, KHÔNG giả lập để báo đạt.

---

## 5. Quyết định tiếp tục (go/no-go/phạm vi hẹp)

**KHUYẾN NGHỊ: GO CÓ ĐIỀU KIỆN, CHIA PHA.**

- **GO** với phần đã chứng minh khả thi: lõi phần mềm M1 + CLI thật + đường phân tích .NET tĩnh là nền vững, 562 test xanh, không fake. Phần này tiếp tục làm chặt được ngay tại host hiện tại.
- **Điều kiện bắt buộc trước M2+:** phải có **build host Linux nested-virt + Wine + live-build + bộ cài hợp lệ** mới mở khóa điều kiện (a) của G0 và toàn bộ M2/M3/M4. Trước khi có hạ tầng đó, mọi tuyên bố "app chạy được" là vô căn cứ.
- **Phạm vi hẹp (cảnh báo WIN-008):** KHÔNG hứa "100% phần mềm Windows chạy nguyên vẹn". App có driver nhân Windows, chống gian lận, ký số phần cứng, tích hợp nội bộ nằm ngoài khả năng bảo đảm bằng lập trình. Kết quả khảo sát 100 app nhiều khả năng dẫn tới **danh mục app/thiết bị chứng nhận hẹp** hoặc **đường VM/remote có license** (phải công bố rõ phụ thuộc + chi phí; không quảng bá nhánh này là "không cần giấy phép Windows"). Nếu chủ dự án đồng thời đòi "không mua Windows" + "mọi Office/MISA desktop chạy nguyên vẹn" + "không đổi quy trình" → đây là giả thuyết phải kiểm chứng, **no-go hoặc phạm vi hẹp là đầu ra hợp lệ** (§21).
- **Không đạt được coi là alpha/stable:** G0 mới chỉ là cổng khả thi phần lõi; G1–G3 vẫn PENDING.

---

## 6. Vấn đề còn lại / defect

| ID | Mức | Mô tả | Trạng thái |
| --- | --- | --- | --- |
| G0-CLI-DEFECT-01 | medium | `_NonExitingArgumentParser` (`src/namios_cli/parser.py`): `-h`/`--help` ghi text help của argparse thẳng ra `sys.stdout` thật, bỏ qua stream `stdout=` inject vào `main()`. Lệnh `namios <cmd> --json -h` in 5 dòng help + 1 dòng JSON → vi phạm CLI-001 "stdout với --json luôn đúng 1 dòng JSON". | **CONFIRMED**, chưa fix (tester báo, không tự sửa); giữ bằng test `xfail(strict=True)` để fail to nếu ai sửa. |

Ngoài defect trên: không phát hiện defect thật ở `namios_dotnet` sau 36 test adversarial. Lưu ý thiết kế cần người tích hợp biết: AnyCPU là heuristic (không phải field PE); `unknown_dependencies` whitelist hẹp có chủ đích; `suggested_mode=None` khi thiếu bằng chứng là lựa chọn "không đoán", không phải bug.

---

## 7. Quyết định gate

- **Product owner:** chưa ký (anh Đỗ Chí Cường).
- **QA:** QA kỹ thuật nội bộ đã verify lõi/CLI/.NET; **QA độc lập ký nghiệm thu ứng dụng = chưa có** (chưa chạy app nào).
- **Gate G0:** **ĐẠT PHẦN LÕI + .NET-ANALYSIS; BLOCKED Wine-fixture (cần build host).** Không pass toàn phần. G1–G3 PENDING.
- **Bước tiếp theo:** (1) commit phần việc G0 đang untracked để cố định bằng chứng; (2) vá/ghi nhận G0-CLI-DEFECT-01; (3) chuẩn bị build host Linux nested-virt + Wine + live-build + bộ cài hợp lệ để mở khóa M2/M3/M4; (4) chốt phạm vi công bố theo WIN-008 trước khi đầu tư rộng.
