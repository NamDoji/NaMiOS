# NaMiOS — Kiểm kê độ phủ các Phụ lục (PHU-LUC-COVERAGE)

**Ngày:** 10/11/2026 · **Người lập:** đội phát triển (release auditor) · **Mục đích:** trả lời trung thực câu hỏi của chủ dự án — *"~18 phụ lục đã xử lý đầy đủ chưa?"*

## Quy tắc chấm (theo Phụ lục 13 §5)

> *"Nếu không có artifact chạy trên **máy thật** (pilot), trạng thái vẫn là `specified/partial`, **không** phải `completed`."* Dev/QEMU = **đã dựng (dev)**, không phải **hoàn tất**.

- ✅ **ĐÃ DỰNG (dev/QEMU, verified_on_host: NO)** — lõi honest-core/logic đã build đủ trong repo, có test ở mức dev.
- 🟡 **MỘT PHẦN** — mới xong một mốc/một tập con; còn khoảng trống nêu tên.
- ⛔ **CHƯA / KHÔNG TÌM THẤY** — không có doc phụ lục hoặc gần như không có hiện thực.
- 🔴 **CHẶN (group B)** — cửa nghiệm thu cần **máy thật / giấy phép / vendor / model / pilot**; không thể đóng ở mức dev.

**Sự thật nền:** NaMiOS **chưa chạy trên bất kỳ máy thật nào** (chưa có lab 5 máy pilot + 3 máy in theo M0). Mọi bằng chứng tới nay là **boot QEMU/TCG (không GPU)** + unit-test thư viện. Vì vậy **không năng lực nào đạt `completed`** — mỗi dòng ✅ bên dưới đều kèm một cửa 🔴 group-B chưa mở.

---

## Bảng độ phủ

| Phụ lục | Tên / Chủ đề | Trạng thái | Bằng chứng (file / commit) | Việc còn thiếu (🔴 = cần group B) |
| --- | --- | --- | --- | --- |
| **PL01** | *(không có doc "Phụ lục 01" riêng)* | ⛔ KHÔNG TÌM THẤY | Nền là **Đặc tả NaMiOS 1.1** `docs/specs/DAC_TA_HE_DIEU_HANH.md` + giao việc M0–M2 (`GIAO-VIEC-M0-M2.md`) | Không phải phụ lục đánh số; đã phủ qua M0/M1 (desktop Việt boot QEMU). 🔴 M0 khảo sát + M1 máy thật. |
| **PL02** | Hệ sinh thái phần mềm thiết yếu VN (ECO-001–024) | ✅ ĐÃ DỰNG (dev) | `src/namios_eco/` (9 file), `docs/specs/PHU-LUC-02-HE-SINH-THAI-VN.md`; honest-core chuỗi phụ thuộc + gate | Chạy chuỗi nghiệp vụ thật (ký/nộp/token). 🔴 vendor + máy thật. |
| **PL03** | Kiến trúc tương thích & nâng cấp (COMP-025–054) | 🟡 MỘT PHẦN | `src/namios_compat/` commit `bb40d8c` — **Giai đoạn A, 11/30 mã** (COMP-025/028/031/032/036/038/045/048/049/052/054) | 19/30 mã COMP còn lại (nghiệm thu .NET/Office/thiết bị). 🔴 app thật. |
| **PL04** | SmartAI — linh hồn tương thích (SAI-001–042) | ✅ ĐÃ DỰNG (dev) | `src/namios_smartai/` (30 file) commit `0f3220c` — tool broker fail-closed, capability token, 12 trạng thái task, policy-as-code, orchestrator; **executor = MOCK** | Executor là mock, **chưa nối dịch vụ OS thật**, chưa model thật. 🔴 model + máy thật. |
| **PL05** | Máy làm việc hằng ngày + SmartAI chủ động (SYS-001–042) | ✅ ĐÃ DỰNG (dev) | `src/namios_sys/` (11 file) commit `ec02be5` — data_authority + action broker + K3-logic chủ động | Nghiệm thu "máy làm việc chính" trên người dùng thật. 🔴 pilot. |
| **PL06** | Thiết bị đa năng/Office/.NET/UX SmartAI (PRA-001–044) | ✅ ĐÃ DỰNG (dev) | `src/namios_pra/` (10 file) commit `fdfc86e` — Doctor-taxonomy + device per-function + Office route/fidelity + design-system 5 màn | In/scan/Office/.NET **thật**. 🔴 thiết bị + Office round-trip. |
| **PL07** | Office tích hợp + chứng nhận thiết bị (ODC-001–048) | ✅ ĐÃ DỰNG (dev) | `src/namios_odc/` (9 file) commit `5c8fd7e` + `ADR-0013` — Document Broker + Route Matrix 6-mode + Device-cert state machine | Round-trip MS-Office thật, cert thiết bị thật. 🔴 thiết bị + Office. |
| **PL08** | Quản trị driver / .NET / SmartAI vận hành (E08-001–040) | ✅ ĐÃ DỰNG (dev) | `src/namios_e08/` (9 file) commit `d1167ca` — driver event-bus debounce + match-theo-hardware-ID + install-giao-dịch + depgraph + bounded-actuator | Nghiệm thu driver/thiết bị cắm-là-chạy. 🔴 máy + USB token thật. |
| **PL09** | — | ⛔ KHÔNG TÌM THẤY | `grep` toàn repo: **không có** "Phụ lục 09" | Không tìm thấy phụ lục 09 trong repo — không bịa độ phủ. |
| **PL10** | Chuyển đổi từ Windows (N10-001–060) | ✅ ĐÃ DỰNG (dev) | `src/namios_mig/` (10 file) commit `3474e1b` — Migration Assessor redact-secret + readiness + Compatibility Broker + PE an toàn + evidence | "Chuyển đổi" thật trên máy người dùng. 🔴 pilot máy thật. |
| **PL11** | Bộ ứng dụng thiết yếu + cập nhật thống nhất (APP11-001–036) | ✅ ĐÃ DỰNG (dev) | `src/namios_essentials/` (13 file) commit `3474e1b` (vá 9 lỗ honest-status fail-closed) + `docs/specs/essentials-manifest.json` | Shortcut Zalo/YouTube/Maps… trong ISO + phân loại native/web/Wine còn thiếu (U13-05 partial). 🔴 danh mục app+version từ chủ dự án. |
| **PL12** | Thiết kế giao diện / phím tắt / hình nền (UX12-001–048) | ✅ ĐÃ DỰNG (dev) | `src/namios_ux/` (8 file) commit `7f226d6` — registry phím tắt + dò xung đột; + vỏ desktop Plasma "Sen" chạy trong **QEMU** (wallpaper/icon/menu Meta) | Trải nghiệm trên màn hình/GPU thật, WCAG đo thật. 🔴 máy thật. |
| **PL13** | Ưu tiên nâng cấp + cổng phát hành | ✅ ĐÃ DỰNG (kiểm kê) | `docs/STATUS-U13-KIEM-KE.md` (14 năng lực) + `docs/ROADMAP.md` + commit `ad633a4` | Đây là phụ lục **phương pháp**: đã lập kiểm kê trung thực + lộ trình A/B/C. 🔴 chính các cửa B1–B5. |
| **PL14** | SmartAI Core người Việt (mốc AI-0) | 🟡 MỘT PHẦN | `docs/spec-package/U14-INVENTORY.md` + `ADR-0018` + `SMARTAI-ORCHESTRATOR.md`/`SMARTAI-TOOL-BROKER.md`/`SMARTAI-40-CASES.md` + engine `src/namios_smartai`, commit `ee19308` | Chỉ xong **AI-0** (kiểm kê/ADR/schema/40 ca mock). **2 thân mã SmartAI (bash ship + Python engine) CHƯA nối nhau**; chưa typed-tool broker chạy OS, chưa model router, chưa máy thật. 🔴 hợp nhất + model + HW. |
| **PL15** | Update Center + bảo mật chuỗi cập nhật (mốc U15-A) | 🟡 MỘT PHẦN | `docs/spec-package/U15-INVENTORY.md` + `ADR-0017` + `UPDATE-CENTER-UI.md` + `U15C-STAGED-ROLLBACK.md`; nguyên mẫu staged/rollback/fault-inject commit `2f4fda7`,`2b78bd6` | **Chưa** Update Service ký riêng, **chưa** UI 4-chế-độ, metadata kiểu TUF, **fwupd vắng mặt**. Test cắt-điện-giữa-update chỉ giả lập VM. 🔴 khóa ký thật + 5 máy pilot + firmware. |
| **PL16** | SmartAI kiểu osGPT, tác vụ toàn desktop (mốc OSG-M0) | 🟡 MỘT PHẦN | `docs/spec-package/U16-INVENTORY.md` + `ADR-0019` + `task-graph.schema.json` + `capability-registry.schema.json` (`distro/.../usr/share/namios/`) + `VN-OS-TASKS.md` khung | Chỉ có **schema/ADR/khung test**. Agent "dùng máy tính" **VẮNG MẶT**: không AT-SPI, không ScreenCast/RemoteDesktop, không task-graph engine, không Capability Registry service, không 2 chế độ guide/do-with-me, 100 ca VN-OS mới là TODO. 🔴 cả tầng agent. |
| **PL17** | — | ⛔ KHÔNG TÌM THẤY | `grep` toàn repo: **không có** "Phụ lục 17" | Không tìm thấy phụ lục 17 trong repo — không bịa độ phủ. |
| **PL18** | NaMiPDF cài sẵn (mốc M0) | 🟡 MỘT PHẦN | `docs/specs/namipdf-v18/` + `docs/pdf/` + `ADR-0001-namipdf-engine.md` + Thanh tra PDF + **13 fixtures**, commit `01c19ea` (nền Okular) | Mới M0 (baseline xem + inspector). **Chưa** redaction thật, **chưa** PAdES/ký số, **chưa** pipeline OCR, PDF/A·PDF/UA. 🔴 corpus thật + ký số. |
| **NaMiOffice v1/v2** | Bộ Office đầy đủ tương đương MS Office (mốc M0) | 🟡 MỘT PHẦN | `docs/specs/namioffice-v2/` (5 file) + `docs/office/COMPAT-MATRIX.md` + `feature-registry.json` (61KB) + Thanh tra tương thích C0–C3 + NaMiMail + fixtures, commit `5c96cc4`; rebrand + bộ kiểm 79 hàm commit `ec84e9b` | Mới M0 (nền LibreOffice rebrand + ma trận + inspector + lát cắt dọc). **Chưa** round-trip MS-Office thật, VBA/COM/VSTO, Power Query, đồng tác giả, Exchange/OneDrive. 🔴 corpus .docx/.xlsx/.pptx thật + pilot. |

---

## Tóm tắt trung thực (bottom line)

**Đếm trạng thái (18 phụ lục đánh số + bộ NaMiOffice):**

- ✅ **ĐÃ DỰNG (dev):** **10** — PL02, PL04, PL05, PL06, PL07, PL08, PL10, PL11, PL12, PL13.
- 🟡 **MỘT PHẦN:** **6** — PL03 (11/30 mã), PL14 (chỉ AI-0), PL15 (chỉ U15-A), PL16 (chỉ OSG-M0 schema), PL18 (chỉ M0), NaMiOffice v1/v2 (chỉ M0).
- ⛔ **KHÔNG TÌM THẤY:** **3** — PL01 (không có doc riêng; nền là đặc tả 1.1), **PL09**, **PL17**.
- 🔴 **CHẶN (group B):** **toàn bộ** — 0 phụ lục đạt `completed`; mọi dòng ✅/🟡 đều treo ở cửa máy-thật/giấy-phép/vendor/model/pilot.

**Nói thẳng:** phần lớn công việc đã **dựng ở mức dev/QEMU + honest-core có test**, nhưng **không phụ lục nào "hoàn tất"** theo đúng luật Phụ lục 13 vì **chưa có một lần chạy trên máy thật nào**. "Đã xử lý đầy đủ chưa?" → **Chưa.** Đã xử lý **ở mức đặc tả + dev** cho 16 phụ lục; còn 3 số hiệu (01/09/17) không có tài liệu trong repo.

**Khoảng trống xuyên suốt (top cross-cutting gaps):**

1. **SmartAI có 2 thân mã CHƯA nối** — trợ lý bash đang ship (rule-based, trong ISO) và engine Python PL04 (typed, mock, có test) chưa hợp nhất quanh một typed-tool broker chạy thật (PL14/PL16).
2. **Chưa có khóa ký thật** cho Update Service / PAdES — Update Center mới là cấu hình tĩnh + apt upstream; fwupd vắng mặt (PL15, PL18).
3. **Chưa có thiết bị thật** — in/scan/Bluetooth/Wi-Fi/USB-token/.NET chỉ `specified`; QEMU không có phần cứng (PL06, PL07, PL08, M1–M5 group B).
4. **MS-Office round-trip chưa đo** — NaMiOffice mới M0 rebrand + ma trận; chưa chứng minh C0 trên corpus thật; không VBA/COM/collab (NaMiOffice, PL07).
5. **PAdES / redaction / OCR chưa dựng** cho NaMiPDF — mới baseline xem (PL18).
6. **Agent computer-use vắng mặt** — không AT-SPI/portal/task-graph engine; osGPT mới là mục tiêu + schema (PL16).

**Cổng duy nhất mở được kế tiếp:** chủ dự án cấp **1 máy thật + 1 máy in** để khép vòng **M1** (cắm USB, làm 8 việc cơ bản) — biến "chạy trong máy ảo" thành bằng chứng máy thật đầu tiên. Đó là bước duy nhất chuyển bất kỳ ✅/🟡 nào sang `completed`.
