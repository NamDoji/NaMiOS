# ADR 0021 — Hợp nhất hai thân mã SmartAI: một Tool Broker + adapter đọc THẬT (PL14 AI-2, M4 backbone)

- **Trạng thái:** proposed · **Mức thực thi:** `partial` — Tool Broker Python là nguồn sự thật DUY NHẤT; hợp đồng bash→Python + 4 adapter **đọc-trạng-thái thật** đã chạy end-to-end qua broker (policy + fail-closed + redaction + audit) trong **test/sim**; **chưa** máy/model/HW thật, **chưa** ký catalog production, Model Router **chưa** nối.
- **Ngày:** 10/11/2026
- **Năng lực:** Phụ lục 14 — **AI-2** ("hợp nhất hai thân mã mà không viết lại; nối adapter đọc precondition thật cho Broker"). Nối tiếp **AI-0** (ADR-0018 chốt hợp đồng).
- **Liên quan:** ADR 0018 (SmartAI Core — 6 lớp/6 hợp đồng, §D5 thứ tự hợp nhất), ADR 0014 (snapshot + rollback = **undo** của SmartAI), ADR 0017 (Update↔SmartAI chỉ-đọc), ADR 0010 (không tải driver lạ). Hợp đồng máy-đọc: `docs/specs/SMARTAI-TOOL-BROKER.md` + `distro/.../usr/share/namios/smartai-tools.schema.json`.

## Bối cảnh

ADR-0018 (AI-0) xác nhận **lỗ hổng #1**: NaMiOS có **hai thân mã SmartAI độc lập, chưa nối**:

1. **Trợ lý bash đang ship** — `distro/.../usr/local/bin/namios-smartai` + `namios-smartai-policy.sh`: có **kế hoạch ≤3 bước + mức chắc chắn**, **cổng xin phép** (`confirm_and_run`), **audit** đã che + `correlation_id`, **undo** (Timeshift), chạy OS thật qua `argv` tĩnh/`pkexec`. Nhưng **không** typed-tool/capability/schema/task-id.
2. **Engine PL04 Python** — `src/namios_smartai/`: Tool Broker fail-closed (`tools.py`), `CapabilityToken`/`ConsentRecord`/12 `TaskStatus` (`_types.py`), `policy.py` (deny-ưu-tiên), `orchestrator.py` (cập-nhật-trạng-thái-**từ-ToolResult**), `injection.py`/`redaction.py`/`observability.py`. Nhưng executor **MOCK**, **chưa nối** dịch vụ OS, **chưa nối** trợ lý bash.

AI-0 chỉ **chốt hợp đồng**; ADR này quyết **cách hợp nhất + bước nối thật đầu tiên** (M4 backbone) mà **không viết lại** (ADR-0018 §D5).

## Quyết định

### D1 — Tool Broker Python (`src/namios_smartai`) là NGUỒN SỰ THẬT DUY NHẤT; bash là front-end mỏng

Mọi quyết định **policy / capability / audit / redaction / injection** nằm ở engine Python. Trợ lý bash **thôi chạy `argv` rời**; nó phát **MỘT yêu cầu JSON** tới Broker qua một **CLI ổn định** (`src/namios_smartai/cli.py`) và nhận **MỘT phản hồi có cấu trúc**. Bash chỉ giữ ba việc nó làm tốt + đúng ranh giới an toàn (ADR-0018 D1): **hỏi mật khẩu qua `pkexec`**, **hiển thị tiếng Việt/kdialog**, **undo bằng Timeshift**.

**Hợp đồng CLI (ổn định — bash↔Python):**

```
request  = { "intent": str,          # câu tiếng Việt NGƯỜI DÙNG (nội dung KHÔNG tin cậy)
             "tool":   str,          # tên tool trong catalog đã ký
             "args":   { … },        # tham số (id mờ do Broker/OS cấp, không phải tên thật do model sinh)
             "consent": { … } | null } # bằng chứng consent/giao dịch (cho hành động ghi)

response = { "plan":    [ {step, risk, confidence}, … ≤3 ],   # kế hoạch hữu hình
             "result":  { status, message_vi, error_code, data },  # data ĐÃ che bí mật
             "audit_id": str,                                  # nối Trace/correlation-id
             "status":  "success" | "failed" | "blocked" | "partial" }
```

Lời gọi thực tế trợ lý bash dùng: `python3 -m namios_smartai.cli '<json>'` (hoặc pipe JSON qua stdin). CLI **luôn exit 0** (không làm sập phiên) và **không raise** cho lỗi nghiệp vụ — fail-closed = trả `blocked`/`failed`. (Khuyến nghị đóng gói: đăng ký `project.scripts` `namios-smartai-broker` để tránh cảnh báo runpy khi gọi `-m`.)

### D2 — Ánh xạ tính năng bash → engine Python (gấp vào policy.py / observability.py, KHÔNG nhân đôi logic)

| Tính năng bash (thật, đang ship) | Gấp vào engine Python | Giữ nguyên bất biến |
| --- | --- | --- |
| **Kế hoạch ≤3 bước** (`smartai_plan_add` chặn bước thứ 4) | `cli._build_plan()` trả plan `[:3]` + `confidence` mỗi bước | Kế hoạch hữu hình, cắt cứng 3 bước |
| **Mức chắc chắn** (cao/vừa/thấp) | trường `confidence` trong mỗi plan step | — |
| **Cổng xin phép cho thay đổi** (`confirm_and_run`) | `policy.evaluate` (R2+ cần consent + capability) + `cli.PRIVILEGED_TOOLS` → phản hồi **GATED** (chuẩn bị, KHÔNG tự chạy) | R2+ cần consent phủ phạm vi; R4 cần xác nhận **giao dịch** |
| **AUDIT đã che + correlation_id** | `observability.Trace` (ghi `TraceEvent`, `note` tự redact — SAI-034) + `audit_id` mỗi request | Trace KHÔNG chứa prompt/credential |
| **Che bí mật** (`smartai_redact`: secret/PII/MAC/IP) | `redaction.redact_bundle` + che MAC trong `adapters._redact_adapter_data`; `Trace.record` scrub `note` | Dữ liệu rời tiến trình phải sạch (SAI-024) |
| **Undo** (Timeshift, ADR-0014) | **Giữ ở bash** (việc hệ thống cần `pkexec`); engine chỉ mang `ToolSpec.rollback_class`/`Capsule` | SmartAI không tự `--restore`, không chọn điểm hộ |
| **Chống lệnh-từ-log/web** (`argv` tĩnh) | `injection.guard_untrusted(intent)` fail-closed TRƯỚC định tuyến (SAI-019) | Nội dung không tin cậy là DỮ LIỆU, không thành `ToolCall` |

**Thứ tự fail-closed của `cli.handle_request`:** `tool có?` → `quét injection trên intent` → `tool đặc quyền? → GATED` → `adapter read-only đăng ký? → chạy thật` → trả phản hồi. Mỗi bước hỏng trả `blocked`/`failed`, không bịa thành công, không bịa biên nhận.

### D3 — Nối THẬT: bốn adapter ĐỌC-TRẠNG-THÁI qua Broker (`src/namios_smartai/adapters.py`)

Bước M4 đầu tiên rời `specified` cho các tool CHỈ-ĐỌC (ADR-0018 bảng Lớp 5 "Adapter trả lỗi cấu trúc + đọc precondition"). Mỗi adapter chạy CLI OS **thật** qua `subprocess` **argv tĩnh** (không shell, không `eval`, không lệnh từ log/web), parse → dict, rồi đi **qua Broker**:

> `policy.evaluate` (SAI-039) → `ToolRegistry.invoke` fail-closed (SAI-015/040) → kiểm lệnh khả dụng → chạy đọc thật → PARSE → **REDACT** (SAI-024) → **Trace** (SAI-034).

| Adapter (tool) | Lệnh OS thật (argv tĩnh) | Bằng chứng | Risk |
| --- | --- | --- | --- |
| `network.diagnose` | `nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device` | `online`, `device_count` | R0 |
| `printer.status` | `lpstat -p -d` | `printer_count`, `default` | R0 |
| `radio.status` | `rfkill list` | `radio_count`, `any_blocked` | R0 |
| `bluetooth.status` | `bluetoothctl show` | `powered` (MAC bộ điều khiển **đã che**) | R0 |

**Tất cả READ-ONLY** (`ToolSpec.writes=False`, R0) ⇒ `policy.evaluate` cho chạy **KHÔNG cần consent/xác nhận** — đúng ranh giới "mặc định chỉ đọc". `run_adapter` còn có **read-only guard** (phòng thủ chiều sâu): adapter nào có spec `writes`/risk > R1 bị **BLOCKED** ngay (`E_SAI_TOOL_SCOPE`) — đường đọc **không bao giờ** chạy hành động ghi.

**`tool_unavailable` trung thực:** CLI vắng trên máy → `shutil.which` trả `None` → `ToolResult(FAILED, E_SAI_TOOL_UNAVAILABLE, data.tool_unavailable=True)`; **KHÔNG bịa dữ liệu**, **không** coi là policy-deny (đây là điều kiện môi trường, không phải vi phạm quyền). Mã lỗi mới `E_SAI_TOOL_UNAVAILABLE` thêm vào `_errors.py`.

**Adapter KHÔNG trộn vào `DEFAULT_TOOLS`** — nằm ở `ADAPTER_TOOLS`/`build_adapter_registry()` riêng, giữ bộ tool M0 + test SAI-015 nguyên vẹn.

### D4 — Thứ tự nối tiếp (giữ ADR-0018 §D5)

1. (**xong ở ADR này**) adapter đọc-trạng-thái read-only + CLI hợp đồng, chạy qua broker trong sim/test.
2. Trợ lý bash gọi **qua** `namios_smartai.cli` thay vì `argv` rời; giữ `pkexec`/AUDIT/undo cho hành động **ghi** (vẫn gated).
3. Mở rộng `ToolSpec`/`ToolCall` đủ 12 trường §3.1 (`task_id`, `preconditions`, `idempotency_key`, `expected_evidence`, `data_sent_to_model`) + đối chiếu `preconditions` với trạng thái thật (adapter) cho tool **ghi**.
4. Ký catalog production (SBOM + provenance) + Broker từ chối catalog không ký (fail-closed).

## Các phương án đã cân nhắc

- **(a) Broker Python là nguồn sự thật, bash thành front-end mỏng gọi qua CLI JSON — ĐƯỢC CHỌN.** Tái dùng tối đa (engine có-kiểu + bash `pkexec`/undo), nối từng tool, giữ mọi bất biến. Hại (honest): còn hai tiến trình cho tới khi bash chuyển hẳn sang gọi CLI (bước D4.2).
- **(b) Viết lại broker chạy thật thay bash.** Vứt bỏ lớp `pkexec`/audit/undo đã kiểm + rủi ro Python chạm root; mâu thuẫn "không viết lại". Bác.
- **(c) Bash tự lên typed broker.** Bash không hợp mang schema/capability/catalog-ký; dễ sai fail-closed. Bác.
- **(d) Adapter ghi-thẳng (bật radio/reset CUPS) ở đợt này.** Vi phạm "mặc định chỉ đọc" + cần cổng consent/pkexec chưa nối. Bác — chỉ làm read-only trước.

## Hệ quả

**Tích cực:** một nguồn sự thật (Broker Python) cho policy/capability/audit/redaction; hợp đồng bash→Python ổn định đã chạy end-to-end; 4 adapter đọc-trạng-thái **thật** (không mock) đi qua broker với redaction + Trace + `tool_unavailable` trung thực; bất biến "tắt AI máy vẫn boot/gõ/in/cập nhật" giữ nguyên (CLI thuần userspace).

**Tiêu cực / nợ phải trả (HONEST — không quảng cáo quá):**
1. **Adapter gọi CLI thật trên OS/pilot, nhưng chạy trong SIM ở đây.** Sandbox này **không** cài `nmcli`/`lpstat`/`rfkill`/`bluetoothctl` → mọi lần chạy thật suy biến `tool_unavailable`. Phần **parse + đường policy/redaction/fail-closed** được unit-test bằng **fixture đã bắt sẵn** (`fixtures/smartai/*.txt`); **không** có xác nhận trên trixie/máy thật.
2. **Model Router VẪN chưa nối LLM thật** — CLI nhận `tool` **tường minh**; chưa có router chọn quy-tắc/local/remote theo nhạy-cảm + CPU/RAM/pin/mạng. Thiết kế-only (ADR-0018 Lớp L3).
3. **Executor ĐẶC QUYỀN vẫn gated — KHÔNG tự chạy.** `apt install`, `firewall.set`, `quarantine.apply`, reset CUPS/Bluetooth, bật radio… ở `PRIVILEGED_TOOLS` → phản hồi **GATED** (cần consent + pkexec). Broker CLI **không** thực thi và **không** bịa side-effect/biên nhận (parity SAI-022 + guardrail bash #1/#3).
4. **Catalog chưa ký production** (khoá lab placeholder) — bước D4.4.
5. **Tích hợp OS đầy đủ + security review = PILOT (nhóm B).** Chỉ mở theo nhóm máy/app được chứng nhận; cổng chặn kế thừa ADR-0018 §9 (xoá/ghi trái quyền, khuyên tải driver lạ, "đã nộp/đã in" sai, leak token, AI treo desktop, không rollback được action đã hứa → **chặn phát hành**).

**Đã kiểm (sim):** `tests/unit/smartai/test_adapters.py` (parse 4 CLI + đường broker đầy đủ + `tool_unavailable` + guard read-only + fail-closed tool chưa đăng ký) và `tests/unit/smartai/test_cli.py` (hợp đồng bash→Python: read-only chạy thật, tool đặc quyền GATED, tool lạ chặn, injection ở `intent` fail-closed, `main()` parse JSON + exit 0) — **19/19 pass**; toàn bộ `tests/unit/smartai` + phần không-cần-binary của `tests/security/smartai` **xanh** (4 ca đỏ sẵn do thiếu console-script `namios` trong sandbox, không liên quan thay đổi này).

## Tham chiếu

ADR 0018 (§D5 thứ tự hợp nhất, 6 lớp/6 hợp đồng), ADR 0014 (undo/Timeshift), ADR 0017 (Update↔SmartAI); `docs/specs/SMARTAI-TOOL-BROKER.md` (12 trường §3.1 + 14 typed tool); `distro/.../usr/share/namios/smartai-tools.schema.json`; mã: `src/namios_smartai/adapters.py`, `src/namios_smartai/cli.py`, `src/namios_smartai/_errors.py` (`E_SAI_TOOL_UNAVAILABLE`), `fixtures/smartai/*.txt`. PL14 §3–§4, §7, §9–§11.
