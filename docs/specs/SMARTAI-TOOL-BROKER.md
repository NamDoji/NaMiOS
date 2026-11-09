# SmartAI Tool Broker — hợp đồng công cụ có kiểu + ma trận quyền (PL14 §3.1/§4)

**Trạng thái:** `specified` — hợp đồng (schema) + catalog tool có thật trong repo
(`distro/.../usr/share/namios/smartai-tools.schema.json`); **CHƯA có Broker chạy
đối chiếu trạng thái thật**, **chưa ký production**, **chưa nối** trợ lý bash với
engine Python. Theo quy ước `docs/STATUS-U13-KIEM-KE.md`: không có artifact chạy
trên máy thật thì trạng thái vẫn là `specified`.
**Ngày:** 09/11/2026 · **Mốc:** Phụ lục 14 — **AI-0**.

**Nguồn yêu cầu:** `docs/spec-package/NaMiOS_Phu_luc_14_SmartAI_Core_Nguoi_Viet.md`
§3 (Lớp 4 Policy/Tool Broker), **§3.1 (hợp đồng công cụ mẫu)**, **§4 (mức tự chủ
L0–L4 + ma trận quyền)**, §7 (chống prompt injection, model supply chain).

**Tệp đi kèm (nguồn sự thật máy-đọc):**
- `distro/live-build/config/includes.chroot/usr/share/namios/smartai-tools.schema.json`
  — JSON Schema `tool_contract` (12 trường §3.1) + `tool_catalog` (14 typed tool
  đã ký — hiện khoá lab) + ví dụ `printer.test_page`.

**Quan hệ với mã đã có (xem `docs/spec-package/U14-INVENTORY.md`):**
- `src/namios_smartai/tools.py` (`ToolRegistry`/`ToolSpec`) — Broker **có kiểu +
  fail-closed** của engine PL04, executor **MOCK**, bộ tool hướng app-compat.
- `distro/.../usr/local/bin/namios-smartai-policy.sh` (`confirm_and_run`,
  `policy_classify`, AUDIT, `catalog_lookup`) — cổng **quyền + audit + undo
  THẬT** của trợ lý bash, nhưng **không** có kiểu/schema.
- `error-catalog.json` (`safe_actions.kind/privileged/undo/playbook`) — nguồn
  cause_code + hành động an toàn cho device-doctor.

> **Mục tiêu AI-0 của tài liệu này:** chốt **một** hợp đồng typed-tool làm điểm
> hợp nhất hai thân mã trên — **không** viết lại Broker ngay, mà định nghĩa
> contract để khi hợp nhất (AI-2) không lệch.

---

## 1. Bất biến Broker (PL14 §3 Lớp 4 + §3.1)

1. **Broker là CỔNG DUY NHẤT** giữa kế hoạch (lớp lập kế hoạch phát ra
   `tool_contract`) và hành động thật. Không có đường nào khác tới dịch vụ OS.
2. **Model KHÔNG tự tạo `target`/`preconditions`/`consent` rồi tự xác nhận**
   (§3.1). Broker:
   - cấp **id mờ** cho `target` (không nhận đường dẫn/tên thật do model sinh);
   - **đối chiếu `preconditions` với TRẠNG THÁI THẬT** qua adapter (NetworkManager/
     CUPS/BlueZ) — thiếu/không khớp → `BLOCKED`, **không** chạy;
   - lấy `consent` từ **người/đơn vị có quyền** qua UI, không từ text model.
3. **Catalog tool do đội NaMiOS KÝ.** Broker chỉ cho chạy tool có trong
   `tool_catalog` đã ký (fail-closed với tool lạ). **Model không nạp thêm tool,
   không tải binary/driver, không có shell tự do** (§3). Catalog không ký hợp lệ
   → Broker TỪ CHỐI toàn bộ (không "tạm tin").
4. **Đặc quyền luôn qua polkit/pkexec** — `privileged:true` ⇒ hệ thống hỏi mật
   khẩu; không có sudoers vòng. Model không tắt bảo mật/không đổi mật khẩu.
5. **Nội dung không tin cậy (log/web/tài liệu/tên Wi-Fi) KHÔNG tạo quyền mới**
   (§7). Đi qua `injection.guard_untrusted` (đã có ở engine); là **dữ liệu**,
   không phải chỉ thị.
6. **"Đã gửi lệnh" ≠ "đã xong".** Broker trả `ToolResult` + bằng chứng
   (`expected_evidence`); **Outcome Validator** mới kết luận, và lời xác nhận
   cuối (có bản giấy/đã ký/đã nộp) thuộc **người dùng** — không phải model.
7. **Idempotency + timeout + cancel + rate-limit** cho mọi tool có side-effect:
   trùng `idempotency_key` → trả kết quả cũ, **không** chạy lại (tránh in/nộp 2 lần).

---

## 2. Hợp đồng công cụ `tool_contract` (12 trường — PL14 §3.1)

Schema đầy đủ ở `smartai-tools.schema.json#/$defs/tool_contract`. Tóm tắt +
ai-điền-gì (quan trọng cho bất biến "model không tự duyệt"):

| Trường | Người/Thành phần điền | Ghi chú |
| --- | --- | --- |
| `schema_version` | hệ thống | `const 1`. |
| `tool` | lớp lập kế hoạch | PHẢI có trong catalog ký (fail-closed nếu lạ). |
| `target` | **Broker** (id mờ) | Model KHÔNG sinh đường dẫn/tên thật. |
| `task_id` | Context/Task Manager | Nối Task (truy vết, Tiếp-tục-sau-reboot). |
| `preconditions` | **Broker đối chiếu trạng thái thật** | Thiếu/không khớp → `BLOCKED`. |
| `scope` | catalog (hẹp nhất) | Broker từ chối vượt scope (vd `one_printer_one_page`). |
| `consent` | **người/đơn vị có quyền** | `none`/`explicit_user_confirmation`/`authority_approval`/`transaction`. |
| `timeout_seconds` | catalog/Broker | 1..1800; kèm cancel. |
| `idempotency_key` | Broker | Chống lặp side-effect. |
| `expected_evidence` | catalog | Outcome Validator kiểm; ≥1 phần tử. |
| `rollback` | catalog/Broker | Cụ thể hoặc nói rõ "không đảo ngược được". |
| `data_sent_to_model` | lớp lập kế hoạch (khai báo) | Minh bạch §1.1-6; mặc định rỗng = không gửi. |

**Thứ tự kiểm fail-closed của Broker** (mở rộng thứ tự đã có ở `tools.py::invoke`):
`tool ∈ catalog ký?` → `required_params đủ?` → `scope hợp lệ?` →
`preconditions khớp trạng thái thật?` → `idempotency chưa dùng?` →
`consent đúng hạng cho autonomy_level?` → (nếu `privileged`) `polkit cho phép?` →
chạy adapter → thu `expected_evidence` → Validator. **Mỗi bước hỏng trả
`ToolResult(BLOCKED/…)`, không `raise`, không bịa thành công.**

---

## 3. Allow-list typed tool (14 tool — `tool_catalog`)

Rút gọn từ `smartai-tools.schema.json#/tool_catalog`. Cột **Mức** = autonomy
L0–L4 (§4); **Playbook** = nối về mã bash thật; **Detector** = adapter đọc
trạng thái thật đã có (`có`) hay mới là hợp đồng (`specified`).

| Tool | Mức | Loại | Quyền | Playbook (bash) | Detector |
| --- | --- | --- | --- | --- | --- |
| `network.diagnose` | L1 | read-only | — | `menu_net`/`namios-chan-doan` | **có** (NM-NET-001/002) |
| `network.radio_on` | L2 | state-change | user | `playbook_net_down` | specified |
| `network.retry` | L2 | state-change | user | `playbook_net_noinet`/`_resume` | specified |
| `printer.test_page` | L2 | state-change | user | `menu_print` (lp) | specified |
| `printer.clear_queue` | L2 | state-change | user | `playbook_print_usb`/`_blank` (`cancel -a`) | specified |
| `printer.restart_service` | L3 | state-change | **pkexec** | `playbook_print_*` (`pkexec systemctl restart cups`) | specified |
| `printer.add_gui` | L1 | launch | user | `playbook_print_net` | specified |
| `scanner.list` | L1 | read-only | — | `delegate_ket_noi` (NM-PRN-005) | specified |
| `bluetooth.set_output` | L2 | state-change | user | `delegate_ket_noi` (NM-BT-003) | specified |
| `bluetooth.restart_service` | L3 | state-change | **pkexec** | `delegate_ket_noi` (NM-BT-004) | specified |
| `ime.restart` | L2 | state-change | user | `playbook_ime_*` (`fcitx5 -r -d`) | specified |
| `system.open_timeshift` | L3 | launch | **pkexec** | `playbook_update` | specified |
| `app.open_wine_config` | L1 | launch | user | `playbook_wine` | specified |
| `support.export_diagnostics` | L1 | launch | user | `namios-chan-doan` (xuất log che) | **có** |

Chỉ **2/14** có detector trạng-thái-thật (`network.diagnose`,
`support.export_diagnostics`); 12 tool còn lại **đã có lệnh thật trong bash**
nhưng **chưa** có adapter đọc precondition để Broker đối chiếu — đó là ranh giới
`specified`, không được quảng cáo quá.

---

## 4. Ma trận mức tự chủ L0–L4 (PL14 §4) + playbook nào ở mức nào

| Mức | Nghĩa | Quy tắc Broker | Tool/playbook hiện có |
| --- | --- | --- | --- |
| **L0 — giải thích** | Giải nghĩa lỗi, chỉ vị trí Settings | Chỉ nguồn/sự kiện có quyền; **không** gọi tool thay đổi | `namios-smartai --explain <mã>` (đọc catalog, định tuyến); banner/guardrail text |
| **L1 — đọc chẩn đoán** | Đọc Wi-Fi/queue/model, log đã che | Read-only trong phạm vi phiên; hiện "AI đang kiểm gì" | `network.diagnose`, `scanner.list`, `printer.add_gui`, `app.open_wine_config`, `support.export_diagnostics`; uỷ `namios-chan-doan` |
| **L2 — thao tác đảo ngược** | Thử lại mạng, chuyển output âm thanh, sửa queue | Snapshot/diff + xác nhận + giới hạn thử + kiểm + hoàn tác khi sai | `network.radio_on`, `network.retry`, `printer.test_page`, `printer.clear_queue`, `bluetooth.set_output`, `ime.restart` → tất cả qua `confirm_and_run` |
| **L3 — thay đổi đáng kể** | Cài gói, đổi driver/backend, cấu hình mạng, reset dịch vụ hệ thống | Người dùng/IT **duyệt hành động cụ thể**; nguồn gói xác thực; backup/đường quay lại | `printer.restart_service`, `bluetooth.restart_service`, `system.open_timeshift` (đều `pkexec`); undo = Timeshift |
| **L4 — giao dịch/khó đảo ngược** | Xoá dữ liệu, flash firmware, phân vùng, **ký/nộp thuế, thanh toán** | AI **chỉ chuẩn bị + hướng dẫn**; người có quyền xác nhận **giao dịch** trong UI chính thức + kiểm nội dung/người nhận | **KHÔNG có tool nào** trong catalog ở L4 (cố ý). Engine PL04 mô hình hoá R4 (`ConsentRecord.transaction_confirmed`, `idempotency`, `SubmissionStatus`) nhưng **M0 không thực thi** (SAI-022: không bịa biên nhận) |

**Quy tắc consent (§4):** không gộp nhiều quyền trong một câu mơ hồ ("cho SmartAI
toàn quyền"). Consent nêu **đối tượng + thao tác + phạm vi + hệ quả**; hết phiên/
hủy → thu hồi. Trẻ em/máy tổ chức/phòng máy dùng policy bảo thủ nhất
(`UnitPolicy` ở engine). Nút **"Tắt SmartAI"** tức thì, không gián đoạn dịch vụ
nền (bất biến "AI không là điểm lỗi đơn").

**Ánh xạ engine ⇄ catalog:** `RiskTier` R0/R1 ↔ L0/L1; R2 ↔ L2; R3 ↔ L3; R4 ↔
L4. Broker thật nên dùng **autonomy_level** của catalog làm cổng UI/consent và
**RiskTier** của engine làm cổng capability — hai nhãn phải nhất quán (test parity
ở `SMARTAI-40-CASES.md`).

---

## 5. Khoảng trống để lên `partial`/`completed` (trung thực)

1. **Broker đối chiếu trạng thái thật:** viết adapter đọc precondition
   (`printer_discovered`, `cups_active`, `bt_device_connected`…) từ CUPS/
   NetworkManager/BlueZ — hiện **chưa có** cho 12/14 tool.
2. **Mở rộng `ToolSpec`/`ToolCall`** (engine) đủ 12 trường §3.1 (`task_id`,
   `preconditions`, `timeout`, `idempotency_key`, `expected_evidence`,
   `data_sent_to_model`) + đổi `DEFAULT_TOOLS` sang bộ device-doctor này.
3. **Ký catalog thật** (SBOM + provenance, không production key ở alpha) + Broker
   từ chối catalog không ký (fail-closed) — hiện chữ ký là placeholder lab.
4. **Nối trợ lý bash gọi qua Broker** thay vì chạy `argv` rời; giữ `pkexec` cho
   `privileged`, giữ AUDIT + undo đã có.
5. **Test §9:** 40 ca chuẩn + 20 đối kháng (gồm ca "tool không có quyền", "giả
   trạng thái đã xong", "lặp vô hạn") — xem `docs/specs/SMARTAI-40-CASES.md`.

Chỉ khi (1)–(4) chạy trên **máy thật** + test §9 pass thì Broker mới rời
`specified`.
