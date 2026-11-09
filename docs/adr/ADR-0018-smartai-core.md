# ADR 0018 — SmartAI Core là lớp điều phối ở TẦNG NGƯỜI DÙNG (PL14 AI-0)

- **Trạng thái:** proposed · **Mức thực thi:** `specified` (có hai thân mã SmartAI + hợp đồng; **chưa** nối thật, **chưa** máy/model/HW thật)
- **Ngày:** 09/11/2026
- **Năng lực:** Phụ lục 14 — **AI-0** ("Kiểm kê repo, ADR stack, event/error schema, danh mục typed tools + policy, mock 40 ca"). Cửa kiểm chứng của chuỗi (AI-1→AI-4 + §9): *"chẩn đoán đúng bước lỗi ≥90%; 0 hành động trái quyền; 0 báo-hoàn-thành-sai cho ký/nộp/in/backup; AI tắt vẫn làm 8 việc thường ngày; không rollback được action đã hứa = chặn phát hành."*
- **Liên quan:** ADR 0001 (Linux + Wine), ADR 0005 (tách chế độ ứng dụng), ADR 0008 (chứng nhận theo tác vụ), ADR 0010 (driver — không tải driver lạ), ADR 0014 (snapshot + rollback + health — **undo của SmartAI dựa vào đây**), ADR 0016 (design system cho UI), ADR 0017 (Update Service ↔ SmartAI chỉ-đọc). Kiểm kê nền: `docs/spec-package/U14-INVENTORY.md`. Hợp đồng: `docs/specs/SMARTAI-TOOL-BROKER.md` + `smartai-tools.schema.json`, `docs/specs/EVENT-ERROR-CONTRACT.md`, `docs/specs/SMARTAI-40-CASES.md`.

## Bối cảnh

Kiểm kê AI-0 (`docs/spec-package/U14-INVENTORY.md`) xác nhận **sự thật nền**: NaMiOS đã có **hai thân mã SmartAI độc lập, chưa nối với nhau**, và **chưa chạy trên máy/model/phần cứng thật nào**.

- **Trợ lý desktop đang ship (bash)** — `namios-smartai` + `namios-smartai-policy.sh`: trợ lý **theo quy tắc** tiếng Việt, chẩn đoán **chỉ đọc** (uỷ `namios-chan-doan`), kế hoạch **≤3 bước** + mức chắc chắn, **cổng xin phép** trước mọi thay đổi (`confirm_and_run`), **audit** đã che + `correlation_id`, **undo** (Timeshift), chạy **offline**. Lệnh đều **argv tĩnh** + `pkexec` cho đặc quyền. Đây là thứ **thật nằm trong ISO** — phủ phần lớn **AI-1** + một phần **AI-2** ở mức prototype. **Không** có typed-tool broker/capability/task-id/model-router.
- **Engine PL04 (Python) `src/namios_smartai/`** — khung **tất định, có kiểu** gần đủ 6 lớp PL14 ở mức hợp đồng dữ liệu: Tool Broker fail-closed (`tools.py`), `CapabilityToken`/`ConsentRecord`/12 `TaskStatus` (`_types.py`), policy-as-code (`policy.py`), orchestrator cập-nhật-trạng-thái-**từ-ToolResult** (`orchestrator.py`), state machine, intent **seam** (`ModelProvider` + `FakeModelProvider`), idempotency/injection/redaction/observability/kill-switch/memory-scope + M1/M2/M3/M4 (chẩn đoán/sửa-có-giới-hạn/quản-trị). **NHƯNG** executor **MOCK** (không I/O/mạng thật), **chưa nối** dịch vụ OS thật, **chưa nối** trợ lý bash, bộ tool mặc định hướng **app-compat**.
- **Hợp đồng + UI**: `EVENT-ERROR-CONTRACT.md` + `error-catalog.json` (`NM-*` phase + `safe_actions`); `AIPlanCard.qml`/`ErrorCard.qml` (QML, `verified_on_host: NO`).

PL14 §1 ra **quyết định kiến trúc cốt lõi**: *"SmartAI là lớp điều phối ở tầng người dùng, không chạy trong Linux kernel và không giữ quyền root thường trực. OS vẫn khởi động, gõ tiếng Việt, mở tệp, dùng mạng, in, sao lưu, cập nhật khi AI tắt hoặc hỏng."* Và §11 lệnh trực tiếp: *"không cấp root shell cho model... typed tool, consent theo action, audit/undo và test prompt injection."* ADR này phải chốt: **(1)** ranh giới tầng (user-space, no kernel, no persistent root), **(2)** 6 hợp đồng không-được-vi-phạm, **(3)** 6 lớp kiến trúc ánh xạ lên mã đã có (cái gì có / cái gì còn thiếu), **(4)** cách hợp nhất hai thân mã mà **không** viết lại.

## Quyết định

### D1 — SmartAI Core ở TẦNG NGƯỜI DÙNG, không kernel, không root thường trực

1. **Không mã model/AI trong kernel.** SmartAI là chương trình userspace (`/usr/local/bin/*`, engine Python ở `/opt/namios` khi đóng gói). Không module kernel, không initramfs/GRUB hook, không unit systemd nằm trên đường boot/recovery.
2. **Không root shell cho model.** Model chỉ phát **ACTION CÓ CẤU TRÚC** (`tool_contract`); mọi đặc quyền đi qua **polkit/pkexec** (hệ thống hỏi mật khẩu). Không sudoers riêng cho AI, không `eval`, không lệnh lấy từ log/web, không `curl|bash`, không tải binary/driver.
3. **AI không là điểm lỗi đơn.** Mạng (NetworkManager), in (CUPS), gõ (fcitx5), cập nhật (Update Center/APT), khôi phục (Timeshift+GRUB) hoạt động **độc lập**. **Tắt/gỡ SmartAI → máy vẫn boot/gõ/in/cập nhật** (đã là bất biến cấu trúc của trợ lý bash — xem `SMARTAI-ORCHESTRATOR.md` §5). Nút "Tắt SmartAI" tức thì, không gián đoạn dịch vụ nền.

### D2 — Sáu hợp đồng không được vi phạm (PL14 §1.1) + mã hiện thực/còn thiếu

| # | Hợp đồng | Hiện thực ở đâu | Còn thiếu |
| --- | --- | --- | --- |
| 1 | **Sự thật** — "đã xong" cần bằng chứng từ dịch vụ + người nhận | bash: `VERIFY_CMD` hiện bằng chứng, không tự nói "đã xong"; engine: `state_machine` chỉ đổi trạng thái từ `ToolResult`, `COMPLETED` chỉ từ `VERIFYING` | Outcome Validator thật nhận `expected_evidence` từ adapter thật (hiện bash kiểm rời, engine mock) |
| 2 | **Quyền** — AI không tự cấp quyền; qua broker/policy/OS auth; có phạm vi/thời hạn/thu hồi | engine: `CapabilityToken`(scope/expires/one_time/revoked) + `policy.evaluate`; bash: `pkexec`/polkit | **Capability Registry + catalog tool đã ký** chạy thật; nối bash qua broker |
| 3 | **Dữ liệu** — chỉ ngữ cảnh được chọn; log/web là dữ liệu không tin cậy | engine: `injection.guard_untrusted`, `memory_scope`, `redaction`; bash: audit đã che | Context Manager thật giới hạn "đã chọn gì"; không quét home/clipboard |
| 4 | **Khả năng quay lại** — preflight + snapshot + kiểm + rollback/không-đảo-ngược-báo-rõ | bash: undo Timeshift (ADR-0014) + nói rõ `cancel -a` không hoàn tác; engine: `rollback_class`, `Capsule` snapshot | `rollback` cụ thể trong `tool_contract`; preflight pin/đĩa (UPD-03) |
| 5 | **Tính khả dụng** — AI không là điểm lỗi đơn | D1.3 (bất biến cấu trúc bash) | test gỡ-phụ-thuộc trên **máy thật** (T-D) |
| 6 | **Minh bạch** — AI đã xem gì, dùng model nào, sẽ làm gì, phần chưa chắc, nút Dừng, lịch sử | bash: banner/guardrail, menu "Lịch sử hành động", mức chắc chắn; engine: `observability.Trace`, `data_sent_to_model` (schema); QML `AIPlanCard` | Health panel (model local/cloud, catalog version, tool permission) chạy thật |

### D3 — Sáu lớp kiến trúc (PL14 §3) ánh xạ lên mã đã có

Quyết định: **giữ kiến trúc 6 lớp của PL14 làm xương sống**, **tái dùng** engine PL04 cho các lớp có-kiểu và trợ lý bash cho lớp hành-động-thật; **không viết lại**.

| Lớp | Thành phần chịu trách nhiệm | Prototype (đã có) | Thật (còn thiếu) |
| --- | --- | --- | --- |
| **L1 Giao diện/ngôn ngữ** | panel tiếng Việt, `--explain`, QML | menu bash + plasmoid + `AIPlanCard.qml`/`ErrorCard.qml` | `Super+Space`, ô hỏi ở Settings/Hub, giọng nói, "Tiếp tục sau reboot" |
| **L2 Context/Task Manager** | task-id + ngữ cảnh đã chọn + trạng thái | `Task`/12 `TaskStatus`/`state_machine` (engine, mock); `correlation_id` (bash) | Task Manager **bền hoá thật** có task-id chạy xuyên reboot |
| **L3 Planner/Model Router** | quy tắc + router local/remote | `planner.build_task` + `intent.ModelProvider` seam (engine); `backend_mode_line` dò có/không (bash) | **Model Router thật** chọn quy-tắc/local/remote theo nhạy-cảm + CPU/RAM/pin/mạng/ngân-sách (gần `absent`) |
| **L4 Policy/Tool Broker** | typed tool + consent + audit | `ToolRegistry` fail-closed + `policy.evaluate` (engine, mock); `confirm_and_run`+audit (bash, thật) | Broker hợp nhất đủ 12 trường §3.1 + **catalog ký** + đối chiếu **trạng thái thật** (xem `SMARTAI-TOOL-BROKER.md`) |
| **L5 Adapter dịch vụ** | NM/BlueZ/CUPS/update/backup/IME/Wine, lỗi cấu trúc | bash gọi lệnh thật argv tĩnh; `route.py`/`capsule.py` (engine) | Adapter trả **lỗi cấu trúc** + đọc precondition cho broker (12/14 tool chưa có) |
| **L6 Outcome Validator + Knowledge/Audit** | validator + catalog + audit đã che | bash audit + kiểm-bằng-chứng (thật); `knowledge_base`/`recipe`/`promotion`/`observability` (engine, mock) | Validator nối adapter thật; catalog app/version/workflow/test/date |

### D4 — Mức tự chủ L0–L4 (PL14 §4) + consent theo action

Chốt ma trận L0–L4 ở `docs/specs/SMARTAI-TOOL-BROKER.md` §4. Bất biến: consent nêu **đối tượng + thao tác + phạm vi + hệ quả** (không gộp "toàn quyền"); R4/L4 cần **xác nhận giao dịch** cụ thể (engine đã mô hình `ConsentRecord.transaction_confirmed` + `idempotency`), và **M0 không thực thi R4** (không bịa biên nhận). Ánh xạ `RiskTier` R0..R4 ⇄ L0..L4.

### D5 — Cách hợp nhất (không viết lại)

AI-0 **chỉ chốt hợp đồng**; hợp nhất mã ở AI-2 theo thứ tự: (a) mở rộng `ToolSpec`/`ToolCall` đủ 12 trường §3.1 + đổi `DEFAULT_TOOLS` sang bộ device-doctor; (b) viết adapter đọc precondition thật; (c) ký catalog + broker từ chối catalog không ký; (d) cho trợ lý bash gọi **qua** broker (giữ `pkexec`/audit/undo). Mỗi bước giữ bất biến D1–D4.

## Các phương án đã cân nhắc

- **(a) Giữ 2 thân mã, chốt hợp đồng nối dần — ĐƯỢC CHỌN.** Tái dùng tối đa (engine có-kiểu + bash hành-động-thật + catalog `NM-*`), rủi ro thấp, nối từng tool. Hại (honest): còn hai nơi cho tới khi hợp nhất xong; dễ lệch nếu không có test parity (đã đặt ở `SMARTAI-40-CASES.md`).
- **(b) Viết lại một Broker Python chạy thật thay bash.** Sạch hơn nhưng vứt bỏ lớp cổng-quyền/audit/undo đã kiểm của bash + rủi ro Python chạm root; chậm; mâu thuẫn "không viết lại".
- **(c) Để bash tự mở rộng thành typed broker.** Bash không hợp để mang schema/capability/registry ký; dễ sai fail-closed.
- **(d) Nhúng model vào dịch vụ nền để proactive.** Vi phạm D1.3 (AI thành điểm lỗi đơn) + §4 (default bảo thủ). Bác.

## Hệ quả

**Tích cực:** kiến trúc 6 lớp + 6 hợp đồng + L0–L4 + schema tool-broker đã chốt bằng tài liệu máy-đọc; hai thân mã có đường hợp nhất rõ; mọi hành động đặc quyền tập trung ở polkit; bất biến "tắt AI máy vẫn chạy" giữ nguyên.

**Tiêu cực / nợ phải trả (honest):**
1. **Chưa có Broker chạy đối chiếu trạng thái thật** — 12/14 tool `detector: specified`.
2. **Model Router gần như `absent`** — mới có seam `ModelProvider`; chưa route theo nhạy-cảm/tài-nguyên.
3. **Catalog tool chưa ký production** (khoá lab placeholder).
4. **Chưa máy/model/HW thật** — không hạng mục nào `completed`; AI-2 "3 workflow máy thật" + §9 là cổng bắt buộc.
5. **Rủi ro double-implementation** oracle ⇄ detector (ghi ở `RELIABILITY-TESTS.md` §1).

**Cổng chặn kế thừa §9:** một ca xoá/ghi tệp trái quyền; AI khuyên tải driver lạ; "đã nộp/đã in" sai; leak tài liệu/token qua cloud; AI treo làm desktop không dùng được; không rollback được action đã hứa → **chặn phát hành**. Pilot chỉ mở theo nhóm máy/app được chứng nhận.

## Tham chiếu

PL14 §1–§4, §7, §9–§11; `docs/spec-package/U14-INVENTORY.md`; `docs/specs/SMARTAI-TOOL-BROKER.md` + `smartai-tools.schema.json`; `docs/specs/EVENT-ERROR-CONTRACT.md`; `docs/specs/SMARTAI-40-CASES.md`; `docs/specs/SMARTAI-ORCHESTRATOR.md`; `docs/specs/RELIABILITY-TESTS.md`; ADR 0014 (rollback), ADR 0017 (Update↔SmartAI). Nguồn ngoài (PL14 §12): NetworkManager/BlueZ/CUPS/XDG portal/OWASP prompt-injection/polkit/NIST AI RMF.
