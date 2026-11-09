# NaMiOS — U14 (AI-0): Kiểm kê SmartAI Core thật trong repo

**Ngày:** 09/11/2026 · **Người lập:** đội phát triển (Claude Code) · **Mốc:** Phụ lục 14 §10 **AI-0** (Kiểm kê repo + ADR + event/error schema + danh mục typed tool + policy + mock 40 ca).
**Đối chiếu:** `docs/spec-package/NaMiOS_Phu_luc_14_SmartAI_Core_Nguoi_Viet.md` (§1–§10), `docs/spec-package/Phu_luc_04_SmartAI_Linh_hon_tuong_thich.md`, `docs/specs/SMARTAI-ORCHESTRATOR.md`, `docs/specs/EVENT-ERROR-CONTRACT.md`, `docs/specs/RELIABILITY-TESTS.md`, `docs/adr/ADR-0018-smartai-core.md`.

## 0. Tuyên bố trung thực (đọc trước)

> NaMiOS **đã có hai thân mã SmartAI RIÊNG BIỆT, CHƯA nối với nhau**, và **chưa có bằng chứng chạy trên máy/model/phần cứng thật nào**:
>
> 1. **Trợ lý desktop đang ship (bash)** — `namios-smartai` + `namios-smartai-policy.sh`: trợ lý **theo quy tắc** (rule-based) tiếng Việt, chẩn đoán **chỉ đọc** (uỷ `namios-chan-doan`), kế hoạch **≤3 bước**, cổng **xin phép** trước mọi thay đổi, **audit** đã che bí mật, **undo** (Timeshift), chạy **offline**. Đây là thứ **thật sự nằm trong ISO**. Nó phủ phần lớn **AI-1** và **một phần AI-2** ở mức **prototype**, nhưng **KHÔNG** có typed-tool broker, **KHÔNG** capability token, **KHÔNG** task ID, **KHÔNG** model router — nó dùng lệnh `argv` tĩnh + `pkexec`.
>
> 2. **Engine PL04 (Python) `src/namios_smartai/`** — khung **tất định, có kiểu** gần như đủ 6 lớp PL14 ở **mức hợp đồng dữ liệu**: Tool Broker fail-closed (`tools.py`), capability token + consent + 12 trạng thái task (`_types.py`), policy-as-code (`policy.py`), orchestrator cập-nhật-trạng-thái-từ-ToolResult (`orchestrator.py`), state machine (`state_machine.py`), intent seam (`intent.py`), idempotency/injection/redaction/observability/kill-switch/memory-scope. **NHƯNG** mọi executor là **MOCK** (không I/O hệ thống, không mạng thật), **KHÔNG nối** vào dịch vụ OS thật (NetworkManager/CUPS/BlueZ), **KHÔNG nối** vào trợ lý bash đang ship, và bộ tool mặc định hướng **app-compat** (`inspect_app`/`run_test`/`create_capsule`), **không phải** tool device-doctor (`printer.test_page`/`network.retry`/`bluetooth.set_output`) mà PL14 §3.1 nêu.
>
> **Hệ quả then chốt cho AI-0:** PL14 không phải "xây từ đầu", mà là **hợp nhất** hai thân mã này quanh một **hợp đồng typed-tool đã ký** (PL14 §3.1) + **Capability Registry** + **Context/Task Manager** có task ID chạy thật trên dịch vụ OS — phần CHƯA có.

**Quy tắc chấm trạng thái** (kế thừa Phụ lục 13 §5 / `docs/STATUS-U13-KIEM-KE.md`, dùng xuyên suốt U13/U15):

- `absent` — không có trong repo.
- `specified` — đã có yêu cầu/thiết kế/hợp đồng/mã trong repo, **chưa** có bằng chứng chạy trên máy thật.
- `partial` — có artifact + bằng chứng chạy **một phần** (ví dụ test mô phỏng xanh, hoặc mock engine có test đơn vị), **chưa** đủ cửa kiểm chứng PL14 §9.
- `completed` — **chỉ** khi chạy trên **máy/phần cứng/model thật** (pilot) qua đúng cửa kiểm chứng §9.

**Sự thật nền:** SmartAI hiện **chưa test trên máy thật, chưa nối model thật, chưa nối phần cứng thật**. Theo quy tắc trên, **không hạng mục SmartAI nào đạt `completed`.**

---

## 1. Hai thân mã SmartAI (bản đồ tệp — nguồn sự thật)

| Thân mã | Tệp | Vai trò thật | Trạng thái |
| --- | --- | --- | --- |
| **Trợ lý ship (bash)** | `distro/.../usr/local/bin/namios-smartai` | 10 playbook (mạng×3, in×3, IME×2, update, wine); menu kdialog/TTY; định tuyến câu tiếng Việt theo từ khoá; `--explain <mã>` | `specified` (review + smoke TTY; chưa máy thật/KDE) |
| | `distro/.../usr/local/bin/namios-smartai-policy.sh` | Lib chính sách: kế hoạch ≤3 bước + mức chắc chắn; `policy_classify`; AUDIT đã che + `correlation_id`; `catalog_lookup` đọc `error-catalog.json` | `specified` |
| | `distro/.../usr/local/bin/namios-chan-doan` | Chẩn đoán **chỉ đọc** (U13-08) — SmartAI uỷ, không tự chế lại | `partial` (8 mã có detector thật) |
| **Engine PL04 (Python)** | `src/namios_smartai/_types.py` | Hợp đồng dữ liệu: `Task`(task_id, 12 `TaskStatus`), `ToolSpec`/`ToolCall`/`ToolResult`, `CapabilityToken`, `ConsentRecord`, `PolicyRule`, `RiskTier` R0–R4, `MemoryScope`, `TraceEvent`, `KbEntry`/`Provenance`, `CompatibilityRecipe` | `specified` (mock, có test đơn vị) |
| | `src/namios_smartai/tools.py` | **Tool Broker** `ToolRegistry`: fail-closed (tool lạ / thiếu param / path-URL ngoài phạm vi / capability cho ghi). Executor **MOCK** | `specified` |
| | `src/namios_smartai/policy.py` | Policy-as-code `evaluate` (deny-priority; R4 cần xác nhận giao dịch) | `specified` |
| | `src/namios_smartai/orchestrator.py` | `run_plan`: policy gate → broker → cập nhật trạng thái **từ ToolResult** (không từ text AI); serialize/resume | `specified` |
| | `src/namios_smartai/state_machine.py` | Chuyển trạng thái hợp lệ; `COMPLETED` chỉ từ `VERIFYING` | `specified` |
| | `src/namios_smartai/intent.py` | `parse_intent` + `ModelProvider` Protocol (seam model); `FakeModelProvider` theo từ khoá | `specified` |
| | `src/namios_smartai/planner.py` | `build_task`: IntentResult → Task + PlanStep; `unknowns` còn → chỉ bước R0 | `specified` |
| | `route.py`, `idempotency.py`, `injection.py`, `redaction.py`, `observability.py`, `kill_switch.py`, `memory_scope.py`, `capsule.py`, `recipe.py`, `depgraph.py`, `inventory.py`, `triage.py`, `diagnose.py`, `repair.py`, `regression.py`, `promotion.py`, `vendorpack.py`, `knowledge_base.py`, `human_feedback.py`, `admin.py` | Các lớp cross-cutting + M1/M2/M3/M4 của PL04 (chẩn đoán, sửa có giới hạn, quản trị) | `specified` (mock) |
| **Hợp đồng + UI** | `docs/specs/EVENT-ERROR-CONTRACT.md` + `distro/.../usr/share/namios/error-catalog.json` | Phong bì sự kiện + catalog `NM-*` (phase, `safe_actions` có `kind`/`privileged`/`undo`/`playbook`) | `specified` |
| | `distro/.../usr/share/namios/qml/AIPlanCard.qml`, `ErrorCard.qml` | Thẻ KẾ HOẠCH ≤3 bước + thẻ lỗi (Qt/QML) | `specified` (`verified_on_host: NO`) |
| **Test** | `tools/reliability-tests/` | A4: 127 lượt kiểm (catalog schema 29 + sim net/print/bt 50 + bash policy 48) — **mô phỏng** | `partial` (xanh, mô phỏng) |
| | `tests/unit/smartai/` + `tests/security/smartai/` | 33 tệp test engine PL04 (đơn vị + đối kháng SAI-*) | `partial` (xanh, mock) |

**Bằng chứng tách rời (đã xác minh):**
`grep` trong trợ lý bash **không** tham chiếu `ToolRegistry`/`namios_smartai` (0 lần) → trợ lý ship **không** gọi engine Python. `grep` trong `src/namios_smartai/` **không** gọi `nmcli`/`bluetoothctl`/`os.system` (chỉ `tools.py` nhắc `subprocess` trong **docstring** để nói "KHÔNG dùng") → engine **không** chạm dịch vụ OS thật. Hai thân mã **độc lập hoàn toàn**.

---

## 2. Ánh xạ 6 lớp PL14 §3 → cái đang có

Mỗi lớp ghi: PL14 đòi gì · engine Python cho gì (mock) · trợ lý bash cho gì (thật, hẹp) · trạng thái tổng hợp.

| Lớp PL14 | Yêu cầu §3 | Engine PL04 (Python, mock) | Trợ lý ship (bash, thật) | Trạng thái |
| --- | --- | --- | --- | --- |
| **L1 — Giao diện + ngôn ngữ** | Thanh gọi nhanh `Super+Space`, ô hỏi ở Settings/Hub, trợ giúp trong lỗi, giọng nói tuỳ chọn, tác vụ có tên/tiến trình/Hủy/Tiếp-sau-reboot | — (engine không có UI) | Menu kdialog/TTY + plasmoid "Hỏi SmartAI"; định tuyến câu tiếng Việt; `--explain` bind nút ErrorCard; `AIPlanCard.qml`/`ErrorCard.qml` (QML, chưa dựng Qt) | **partial** — có panel + QML đặc tả; thiếu `Super+Space`, ô hỏi trong Settings/Hub, giọng nói, "Tiếp tục sau reboot" |
| **L2 — Context/Task Manager** | task ID, mục tiêu, bước, cửa sổ/tệp/thiết bị đã chọn, giới hạn thời gian, 7 trạng thái `proposed..verified/cancelled`; không quét toàn màn hình/clipboard/home | `Task`(task_id) + **12** `TaskStatus` + `state_machine` + serialize/resume (`task_to_dict`) — **mock, không bền hoá thật** | `correlation_id` mỗi phiên (nối chẩn đoán→hành động→kiểm) ghi vào audit; **không** có task ID/goal/bước bền | **partial** — mô hình trạng thái có (Python), nhưng chưa có Task Manager **chạy thật** có task ID + ngữ cảnh "đã chọn gì" |
| **L3 — Planner + Model Router** | quy tắc cho ca đơn giản; model local nhỏ; model remote chỉ khi bật + biết loại dữ liệu; router cân ngôn ngữ/nhạy cảm/trễ/CPU/RAM/pin/mạng/ngân sách/phiên bản | `planner.build_task` (quy tắc); `intent.ModelProvider` **seam** + `FakeModelProvider` (từ khoá); nhãn `đã xác nhận/khả năng/chưa rõ` qua `confidence`/`unknowns` | `backend_mode_line` chỉ **dò có/không** khoá LLM để đổi dòng chữ; luôn chạy playbook quy tắc; **không** route theo tài nguyên | **partial (planner) / absent (router)** — có planner quy tắc + seam model; **chưa có model router thật** (chưa chọn local/remote theo nhạy cảm/tài nguyên; `route.py` là compat-route-resolver, **không** phải model router) |
| **L4 — Policy/Tool Broker** | typed actions có schema, allow-list, precondition/postcondition, timeout, idempotency key, rate limit, cancel, owner, required consent, audit; broker độc lập model; không shell tự do; nội dung lấy về không tạo quyền | `ToolRegistry` fail-closed + `ToolSpec`(risk/scope/writes/rollback_class) + `CapabilityToken`(scope/hạn/một-lần/thu-hồi) + `policy.evaluate` + `idempotency` + `injection.guard_untrusted`. **Mock, bộ tool hướng app-compat** | `confirm_and_run`/`confirm_and_launch`: hiện kế hoạch + **argv tĩnh** + undo → xin đồng ý → chạy → KIỂM (read-only) → AUDIT; đặc quyền qua `pkexec` | **partial** — hai nửa của một broker: Python có **kiểu + fail-closed** (mock); bash có **cổng quyền + audit thật** (không kiểu). **Thiếu** hợp đồng §3.1 đầy đủ (preconditions/idempotency_key/expected_evidence/rollback/data_sent_to_model) + **catalog tool đã ký** + đối chiếu **trạng thái thật** |
| **L5 — Adapter dịch vụ** | NetworkManager/BlueZ/CUPS+scan/update/backup/App Center/portal/IME/Wine capsule/log đã che; mỗi adapter trả **lỗi cấu trúc**; API pin theo distro | `route.py` uỷ `namios_compat`; `capsule.py` (Wine capsule, mock); `redaction.py` (log đã che) | Gọi **thật** `nmcli`/`cups`/`fcitx5`/`winecfg`/`timeshift` qua argv tĩnh + `pkexec`; uỷ scan/BT sang `namios-ket-noi-thiet-bi` | **partial** — có lệnh thật nhưng **chưa** adapter trả lỗi cấu trúc (bash chỉ bắt rc + text); engine chưa nối adapter thật |
| **L6 — Outcome Validator + Knowledge/Audit** | validator nhận bằng chứng từ adapter; catalog app/version/workflow/test/date; audit ai/khi/quyền/tool/kết quả (đã che); recipe cộng đồng "chưa kiểm" tới khi lab duyệt | `knowledge_base`(Provenance/TestedLevel), `recipe`+`promotion`(RecipeState), `observability.Trace`, `regression` — mock | `VERIFY_CMD` (read-only) hiện **bằng chứng**, không tự tuyên bố "đã xong"; `smartai_audit` ghi dòng đã che + `correlation_id`; `catalog_lookup` | **partial** — audit + kiểm-bằng-chứng **thật** ở bash; validator/knowledge **có kiểu** ở Python (mock); chưa nối adapter thật để lấy bằng chứng |

**Tổng 6 lớp:** không lớp nào `absent` hoàn toàn, nhưng **không lớp nào `completed`**; điểm yếu tập trung ở **L3 model router** (gần `absent`) và ở việc **L4 chưa có hợp đồng §3.1 đầy đủ + catalog tool ký + nối trạng thái thật**, cộng **L2 chưa có Task Manager chạy thật**.

---

## 3. Ánh xạ mốc AI-0 … AI-4 → trạng thái

| Mốc | Bàn giao PL14 §10 | Đã có gì | Trạng thái |
| --- | --- | --- | --- |
| **AI-0** | Kiểm kê repo, ADR stack, event/error schema, danh mục typed tool + policy, **mock 40 ca** | Tài liệu này (kiểm kê) + `ADR-0018` + `EVENT-ERROR-CONTRACT.md`/`error-catalog.json` (event/error schema) + `SMARTAI-TOOL-BROKER.md`/`smartai-tools.schema.json` (hợp đồng typed-tool §3.1 + catalog allow-list) + `SMARTAI-40-CASES.md` (khung 40+20, subset có thật). Engine Python = policy/broker/registry có kiểu. | **partial → đang đóng bằng AI-0 này** (thiết kế/schema xong; chưa 40 ca viết đủ + chưa nối thật) |
| **AI-1** | Panel tiếng Việt + trợ giúp quy tắc cho mạng/in/Bluetooth; **mọi action read-only** | Trợ lý bash (10 playbook) + chẩn đoán chỉ đọc + QML; định tuyến tiếng Việt; **nhưng** nhiều action của bash là **state-change có cổng quyền**, không "mọi action read-only" | **partial** — gần đủ ở mức prototype; chưa chạy trên KDE/máy thật; Bluetooth uỷ `namios-ket-noi-thiet-bi` (chưa gắn mã phase thật) |
| **AI-2** | Planner, router local/remote tuỳ chọn, **broker, consent, audit, validator; 3 workflow máy thật** | Broker+consent+policy (Python mock) + cổng quyền+audit+kiểm-bằng-chứng (bash thật); planner quy tắc | **partial** — các mảnh có (hai nơi, mock/thật tách rời); **thiếu**: router thật, broker §3.1 nối trạng thái thật, **3 workflow trên máy thật** |
| **AI-3** | App Doctor + migration assessor, Wine capsule/VM lab, recipe review (3 app/version/workflow) | `capsule.py`/`recipe.py`/`promotion.py`/`diagnose.py`/`depgraph.py` + `docs/specs/WINE-CAPSULE.md` + `COMPAT-ROUTING.md`; App Doctor (`src/namios_doctor`) | **specified** — khung PL04 có; **chưa** recipe nào `pilot_verified` trên app/version thật |
| **AI-4** | Giọng nói tuỳ chọn, proactive có tắt, pilot giáo viên/văn phòng, dashboard chất lượng | — | **absent** |

---

## 4. Khoảng cách: hợp đồng typed-tool PL14 §3.1 **vs** `tools.py` hiện có

| Trường PL14 §3.1 đòi | `ToolSpec`/`ToolCall`/`CapabilityToken` cho sẵn | Khoảng trống phải xây |
| --- | --- | --- |
| `schema_version` | ✘ (không version hoá instance) | Thêm version cho mỗi tool-contract. |
| `tool` | ✔ `ToolCall.tool` + `ToolSpec.name` | — |
| `target` (id mờ) | ✔ `ToolCall.target` | Chuẩn hoá **id mờ** (opaque) do broker cấp, không để model tạo. |
| `task_id` | △ `Task.task_id` có ở engine nhưng **không** gắn vào `ToolCall` | Gắn `task_id` vào mọi lời gọi tool (truy vết). |
| `preconditions` (đối chiếu trạng thái thật) | ✘ `ToolSpec` chỉ có `required_params`/`scope`; **không** precondition đối chiếu trạng thái | Broker xác minh precondition với **trạng thái thật** (adapter), **model không tự tạo**. |
| `scope` | △ `filesystem_scope`/`network_scope`/`device_scope` (chuỗi thô) | Mở rộng scope ngữ nghĩa (vd `one_printer_one_page`). |
| `consent` (loại) | △ `ConsentRecord` tách; `ToolCall` **không** mang `consent` | Gắn hạng consent (`explicit_user_confirmation`/`transaction`) vào contract. |
| `timeout_seconds` | ✘ | Thêm timeout + cancel + rate-limit ở broker. |
| `idempotency_key` | △ có `idempotency.py` cho submission; **không** trong `ToolSpec` | Khoá idempotency cho **mọi** tool có side-effect. |
| `expected_evidence` | ✘ (bash có `VERIFY_CMD` rời) | Khai báo bằng chứng kỳ vọng để Outcome Validator kiểm. |
| `rollback` | △ `ToolSpec.rollback_class` (none/snapshot/reversible) | Nối rollback cụ thể (Timeshift/undo lệnh) + "không đảo ngược được → báo rõ". |
| `data_sent_to_model` | ✘ | Khai báo tường minh dữ liệu gửi model (minh bạch §1.1-6). |
| **Catalog tool đã ký** | ✘ `DEFAULT_TOOLS` là hằng số trong mã | **Capability Registry**: catalog tool do đội NaMiOS **ký**, broker đối chiếu; **model không nạp thêm tool**. |
| **Bộ tool device-doctor** | ✘ (`DEFAULT_TOOLS` hướng app-compat) | Thêm `printer.test_page`/`network.retry`/`bluetooth.set_output`... (xem `smartai-tools.schema.json`). |

---

## 5. Kết luận AI-0 + 3 khoảng trống lớn nhất cần đóng tiếp

1. **Dùng lại tối đa cái đã có, KHÔNG viết lại:** giữ **engine PL04** làm xương sống kiểu + fail-closed, giữ **trợ lý bash** làm lớp hành động thật + cổng quyền + audit + undo, giữ **catalog `NM-*`** làm nguồn cause_code/safe_actions. AI-0 chỉ **chốt hợp đồng** nối chúng lại (ADR-0018 + schema tool-broker), **chưa** hợp nhất mã.
2. **Trạng thái:** không tuyên bố "OS đã hỗ trợ"; mọi hạng mục ở `specified`/`partial` cho tới khi có bằng chứng **máy/model/HW thật** (AI-2 "3 workflow máy thật" + §9 cổng phát hành).

**Done / Partial / Absent cho AI-0…AI-4:**

- **AI-0 — gần xong (partial→đóng):** kiểm kê + ADR + event/error schema + hợp đồng typed-tool §3.1 + catalog allow-list + khung 40+20 **đã có trong AI-0 này**; còn thiếu: viết đủ 60 fixture + nối thật.
- **AI-1 — partial:** panel + 10 playbook quy tắc + chẩn đoán chỉ đọc có thật (bash), chưa máy thật/KDE; Bluetooth chưa gắn phase thật.
- **AI-2 — partial:** broker/consent/policy/audit/validator tồn tại **rải hai nơi** (Python mock + bash thật, chưa nối); **chưa** router thật, **chưa** 3 workflow máy thật.
- **AI-3 — specified:** khung App Doctor/capsule/recipe có (mock), chưa recipe `pilot_verified`.
- **AI-4 — absent.**

**Ba khoảng trống lớn nhất cần đóng kế tiếp (ưu tiên):**

1. **Hợp nhất Tool Broker + Capability Registry chạy thật (L4).** Mở rộng `ToolSpec`/`ToolCall` đủ 12 trường §3.1, thêm **catalog tool đã ký** (allow-list device-doctor), và cho **broker đối chiếu trạng thái thật** (NetworkManager/CUPS/BlueZ) thay vì mock — rồi cho **trợ lý bash gọi qua broker này** thay vì tự chạy `argv` rời. Đây là nút thắt để AI-2 thật.
2. **Context/Task Manager chạy thật + Model Router (L2+L3).** Bền hoá `Task`(task_id, 7+ trạng thái) có "ngữ cảnh đã chọn" + "Tiếp tục sau reboot"; xây **model router** chọn quy-tắc/local/remote theo **nhạy cảm dữ liệu + tài nguyên (CPU/RAM/pin/mạng) + tổ chức cho phép**, điều hiện **chưa tồn tại** (chỉ có seam `ModelProvider`).
3. **Bộ 40 ca chuẩn + 20 ca đối kháng với log giả đã che (L6/§9).** Gom các mảnh test đang rải (A4 reliability 127 lượt mô phỏng + 33 tệp test engine) thành **đúng** cấu trúc §9 (10 mạng/10 in-scan/6 BT-USB/6 tệp-Office-IME/4 Windows-.NET/4 update-backup + 20 đối kháng), **tách** kết quả mô phỏng/lab/máy thật — để có cổng phát hành đo được.
