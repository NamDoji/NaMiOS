# ADR 0019 — OS agent user-space, API-first cho NaMiOS SmartAI (tầng tác vụ desktop, Phụ lục 16)

- **Trạng thái:** proposed · **Mức thực thi:** `specified` (chưa có engine tác vụ; chỉ "Hỏi tôi" rule-based tồn tại, chưa máy thật)
- **Ngày:** 09/11/2026
- **Năng lực:** Phụ lục 16 — **OSG-M0 "nền tảng"** (kiểm kê + ADR stack desktop/portal/AT-SPI + schema task/capability + ranh giới consent/audit). Cửa kiểm chứng của chuỗi (OSG-M1→M4): *"'đã xong' chỉ khi có evidence; wrong-target = 0; permission-violation = 0; false-completion = 0 cho in/ký/nộp/thanh toán; tắt AI máy vẫn dùng được bằng tay."*
- **Liên quan:** PL14 SmartAI Core (ADR này là tầng tác vụ **trên** nó), ADR 0005 (tách chế độ ứng dụng), ADR 0008 (chứng nhận theo tác vụ), ADR 0014 (snapshot/rollback), ADR 0016 (design system cho UI), ADR 0017 (ranh giới Update Center/Service/SmartAI — tái dùng mô hình polkit-gated). Kiểm kê nền: `docs/spec-package/U16-INVENTORY.md`. Hợp đồng sự kiện/lỗi: `docs/specs/EVENT-ERROR-CONTRACT.md`.

## Bối cảnh

Phụ lục 16 yêu cầu một **tầng tác vụ xuyên ứng dụng**: người dùng nói "Kết nối máy in, mở bài giảng và in hai mặt", NaMiOS hiểu việc, tìm đúng app/tệp/thiết bị, hiện kế hoạch, thao tác **trong quyền được cấp**, rồi kiểm chứng kết quả. Đây là lớp mạnh hơn hẳn trợ lý hỏi-đáp: nó **quan sát giao diện và hành động** trên desktop.

Kiểm kê U16 (`docs/spec-package/U16-INVENTORY.md`) xác nhận **sự thật nền**:

- **Đã có (rule-based, `partial`/`specified`):** `namios-smartai` (bash) — chế độ "Hỏi tôi" + 10 playbook mạng/in/gõ-TV/cập-nhật/Wine, cổng quyền `confirm_and_run` (argv tĩnh + consent + audit đã che + pkexec/polkit), offline fallback. Thư viện PL04 `src/namios_smartai/*` (intent→planner→policy→typed-tool→state-machine→validator) có unit-test nhưng **chưa nối vào desktop**.
- **CHƯA có:** engine task-GRAPH; Capability Registry chạy được; tích hợp **AT-SPI**; dùng **portal RemoteDesktop/ScreenCast**; panel ba chế độ; bộ VN-OS Tasks. (grep `at-spi`/`atspi`/`remotedesktop`/`screencast`/`screencapture` trong `distro/`,`src/` → **rỗng**.)

Vì đây là năng lực **rủi ro cao** (một agent bấm nhầm có thể gửi nhầm người, in nhầm, ký/nộp sai, xoá dữ liệu), ADR phải chốt **kiến trúc + ranh giới an toàn TRƯỚC**, đúng tinh thần PL16 §10: *"hoàn thành M0/M1 trước khi gắn nhãn 'SmartAI điều khiển máy'."* Nghiên cứu agent dùng-máy-tính (UFO, OSWorld, Operator system card) cho thấy khả năng điều khiển UI vẫn **hạn chế thực tế**; không được hứa làm mọi việc, phải **đo và nói đúng tỷ lệ thành công**.

## Quyết định

Dựng NaMiOS SmartAI tầng-tác-vụ là một **agent USER-SPACE, API-FIRST**, với **ba chế độ** + **bốn đường thực hiện ưu tiên** + **ranh giới an toàn cứng**. **Không** đưa model vào kernel, **không** cấp root shell cho AI.

### 1. Ba chế độ (mặc định an toàn nhất)

| Chế độ | `mode` | Người dùng thấy | AI được làm |
| --- | --- | --- | --- |
| **Hỏi tôi** (mặc định) | `ask_me` | Câu trả lời, đường tới Settings, nguyên nhân có bằng chứng | **Chỉ đọc** trạng thái đã cho phép; không điều khiển cửa sổ, không sửa máy. |
| **Hướng dẫn tôi** | `guide_me` | Checklist ≤3 bước, đánh dấu nút/tệp trên cửa sổ đã chọn; người dùng tự bấm | Quan sát cửa sổ đã chọn trong phiên; **chỉ ra** bước, **không bấm thay**. |
| **Làm cùng tôi** | `do_with_me` | Kế hoạch + tiến trình + nút Tạm dừng/Dừng/Tự-làm-tiếp | Thực thi **trong phạm vi tác vụ được duyệt**, kiểm sau mỗi bước, **nhường điều khiển** ngay khi người dùng chạm chuột/bàn phím. |

**Mặc định `ask_me`.** `do_with_me` bật **cho từng tác vụ/ứng dụng**, có **thời hạn + phạm vi** (`consent_scope` hữu hạn, ví dụ `one_task_10_minutes`). **KHÔNG tồn tại công tắc "AI toàn quyền máy tính".** Trẻ em/máy tổ chức có hồ sơ policy chặt hơn, mặc định bảo thủ nhất.

### 2. Bốn đường thực hiện, ưu tiên đáng-tin → linh-hoạt

| Đường | `path` | Dùng khi | Giới hạn bắt buộc |
| --- | --- | --- | --- |
| **A. API & dịch vụ OS** | `A_service_api` | Wi-Fi, Bluetooth, máy in, tệp, cập nhật, sao lưu, app catalog | **Ưu tiên tuyệt đối** vì có trạng thái/mã lỗi cấu trúc; chỉ gọi qua policy broker. Đây là đường **duy nhất** của M1. |
| **B. Action SDK của app** | `B_app_action_sdk` | App NaMiOS/bên-thứ-ba hợp tác đã đăng ký `capability-registry.schema.json` | App khai action/schema/quyền/pre-post/evidence; **phải review + ký**; mức chứng nhận ≥ published mới dùng không-nhãn-thử-nghiệm. |
| **C. Cây trợ năng AT-SPI** | `C_atspi_scoped` | App GUI không có Action SDK nhưng có nút/nhãn/vai trò trợ năng | **Chỉ** đọc/điều khiển **cửa sổ người dùng đã chọn**; **kiểm element còn đúng trước mỗi lần bấm** (stale-state guard). |
| **D. Hình ảnh + input có phiên** | `D_visual_input` | GUI cũ, Wine, canvas, control không nhãn trợ năng | **Chỉ sau** consent screen/remote-control qua portal, **che vùng nhạy cảm**; độ tin cậy thấp hơn → gắn nhãn **"thử nghiệm"**; dừng khi layout đổi hoặc không chắc. |

**Quy tắc chuyển đường:** khi một đường thất bại, agent chuyển đường khác **chỉ nếu** quyền còn hợp lệ **và** giải thích cho người dùng. Với app Wine/.NET, ưu tiên API/workflow **đã chứng nhận**; nếu chỉ có quan sát GUI, trạng thái là **"thử nghiệm"** cho tới khi đạt test. **TUYỆT ĐỐI KHÔNG dùng tọa độ chuột cố định làm nền tảng chung** — hành động phải neo vào element/role (C) hoặc nội dung quan sát theo phiên (D), không phải (x,y) tuyệt đối.

Trên Linux/Wayland: AT-SPI (`org.a11y.atspi`) cung cấp cây đối tượng trợ năng; XDG Desktop Portal có phiên cho ScreenCast/RemoteDesktop. **Việc dùng thật phụ thuộc compositor + desktop stack NaMiOS (KDE Plasma 6 trên trixie) và cần spike riêng ở M2** — ADR này **chưa** khẳng định hai cơ chế đó đã chạy trên bản NaMiOS.

### 3. Tầng tác vụ: hợp đồng, không phải câu văn của model

- **Goal contract** (`task-graph.schema.json`, §4.1): `task_id`/`intent`/`mode`/`requester`/`risk_tier`/`selected_resources`/`success_criteria`/`allowed_actions`/`forbidden_actions`/`consent_scope`/`pause_on`/`evidence`/`state`.
- **Task graph** (`steps[]`): mỗi bước có `depends_on` (DAG), `preconditions`, `action`+`path`, `postconditions`, `idempotency_key`, `timeout_seconds`, `max_retries`, `rollback`, `evidence`, `state`.
- **Trạng thái** là enum dịch-vụ-OS: `planned/awaiting_user/running/paused/blocked/partial/verified/cancelled` — **không** phải chữ tự do của model. `verified` **chỉ** khi evidence (do adapter trả) khớp `success_criteria`.
- **Vòng lặp an toàn:** quan sát → chọn một action → **kiểm vẫn ở đúng cửa sổ/tệp** → thực hiện → đọc lại trạng thái → so postcondition → tiếp/dừng. Retry có giới hạn; mọi bước ghi audit đã che.

**Broker đối chiếu, không phải model tự xác nhận.** Model chỉ phát ra **action có cấu trúc** (`ToolCall`); Policy/Tool Broker (PL14 §3 Lớp 4, tái dùng `policy.py`/`tools.py` của PL04) đối chiếu handle/owner/app_id/phiên/policy rồi mới cho chạy. Model **không** tự tạo `task_id`/`consent_scope`/`allowed_actions`. Nội dung web/tài liệu/log/tên-tệp/nút-app là **dữ liệu không tin cậy** — không thể tạo quyền mới (chống prompt-injection).

### 4. Ranh giới an toàn (cứng, fail-closed)

1. **Không root shell cho AI.** Mọi đặc quyền qua `pkexec`/polkit (hệ thống tự hỏi mật khẩu) hoặc portal; chỉ **argv tĩnh**, không `eval`, không `curl|bash`, không chạy lệnh/script lấy từ metadata/log/web. (Tái dùng mô hình `namios-smartai-policy.sh` + ADR 0017.)
2. **Không toàn-màn-hình mặc định.** Không quay màn hình liên tục; chỉ **một cửa sổ/vùng** khi đã cho phép; có **chỉ báo đang quan sát**; dừng tức thì. Dữ liệu hình ảnh lưu phiên ngắn theo policy, **không** tự đưa lên cloud.
3. **Không tọa độ chuột cố định.** Hành động neo element/role (C) hoặc nội dung theo phiên (D). Nếu layout đổi/không-khớp → **dừng**, không bấm theo (x,y) cũ.
4. **Tạm dừng bắt buộc** (`pause_on`) khi: `user_input`, `focus_change`, `unknown_dialog`, `permission_expired`, `lockscreen`, `otp_field`/`password_field`, `network_change`, `file_version_changed`, `app_crash`, `layout_changed`. Trên khoá màn hình / nhập mật khẩu-PIN-OTP / USB token / chữ ký số / app ngân hàng-thuế: agent **dừng quan sát & thao tác**, người dùng tự tiếp tục rồi nhấn "Tôi đã xong" để AI đọc trạng thái kết quả được phép.
5. **Chống nhầm đối tượng.** Trước gửi/chia sẻ/in/ký/nộp: UI hiện tên tệp + người-nhận/đích + thiết bị + preview; người dùng xác nhận **hành động cụ thể**. **Không** dùng "đã đồng ý một lần" cho giao dịch khác; không tự đổi máy-in/người-nhận/tệp.
6. **Khôi phục.** Action đổi có preflight + undo/snapshot khi khả thi (Timeshift cho thay đổi hệ thống, ADR 0014). Không đảo ngược được (`rollback.kind=none_irreversible`) PHẢI nói trước và **chờ người dùng** thực hiện. Có nút **Dừng khẩn** + nhật ký đã che.
7. **Không tê liệt OS.** AI chạy user-space, bị giới hạn CPU/RAM/pin, có thể tắt; **mạng/File/Office/máy in/Update Center vẫn dùng bằng tay** khi model lỗi. SmartAI **không** là điều kiện cho boot/recovery.
8. **SmartAI không tự thay người làm việc nhạy cảm:** không gửi tin/email/chia-sẻ-tệp/ký/nộp/mua-hàng/thanh-toán cho người khác nếu chưa có quyền **và** màn hình xem lại cụ thể đối tượng/nội dung. False-completion mục tiêu **= 0** cho in/ký/nộp/thanh toán (gửi-lệnh ≠ đã-xong).

### 5. Sự thật hôm nay (không quảng cáo quá)

- **Chỉ đường A của "Hỏi tôi" tồn tại** (rule-based, `namios-smartai`), và nó còn trộn một phần hành-động-qua-dịch-vụ sau consent. **Hai chế độ "Hướng dẫn tôi"/"Làm cùng tôi" đúng nghĩa computer-use CHƯA có.**
- **Chưa có** engine task-graph, Capability Registry service, AT-SPI, portal screen/remote-control, panel 3 chế độ, VN-OS Tasks chạy được.
- ADR này là `specified`. **Không** tuyên bố "NaMiOS SmartAI điều khiển được máy".

## Các phương án đã cân nhắc

### (a) User-space, API-first, 3 chế độ, 4 đường ưu tiên A→B→C→D — **ĐƯỢC CHỌN**

- Tận dụng dịch vụ OS có mã lỗi cấu trúc (NetworkManager/BlueZ/CUPS/portal) và registry do app khai + ký; chỉ rơi xuống AT-SPI/visual khi buộc phải, có stale-guard + nhãn thử-nghiệm.
- **Lợi:** đáng tin nhất ở đường A (làm được ngay ở M1 mà **không cần model lớn**); an toàn phân tầng; đo được tỷ lệ thành công theo đường; không rời user-space.
- **Hại (honest):** đường C/D phụ thuộc compositor/portal + cần rà soát an toàn nặng (M2); registry (B) cần hệ sinh thái app Việt tham gia (M3) — chậm, không có đường tắt.

### (b) Visual-first computer-use agent (model nhìn màn hình + bấm tọa độ) — **TỪ CHỐI**

- Giống Operator/UFO: model xem screenshot rồi phát (x,y)+click. **Giá:** độ tin cậy thấp & dễ nhầm đối tượng; quay toàn màn hình (lộ OTP/token/tài liệu); phụ thuộc model mạnh/cloud; đúng thứ PL16 §8 cấm làm nền tảng. Chỉ giữ **mảnh D** (có phiên, che vùng nhạy cảm, nhãn thử-nghiệm) làm **phương án cuối**, không phải trục chính.

### (c) Macro/script cố định (ghi-phát thao tác, tọa độ cứng) — **TỪ CHỐI**

- Rẻ nhưng gãy ngay khi layout/độ phân giải/ngôn ngữ đổi; không kiểm được "đúng cửa sổ/tệp"; vi phạm "không tọa độ cố định". Không dùng.

### (d) Mở rộng engine PL04 thành trục chính luôn — **MỘT PHẦN, không đủ**

- PL04 cho nền tốt (typed-tool/policy/consent/injection-guard/redaction/state-machine) và **nên tái dùng** làm broker + guard. Nhưng PL04 **không** có task-GRAPH (chỉ `PlanStep` tuyến tính), enum trạng thái **khác** §4, và **không** có AT-SPI/portal/registry. Vì vậy PL04 là **thành phần**, không phải toàn bộ agent; M1 phải thêm engine đọc `task-graph.schema.json` + adapter đường A + verifier + panel 3 chế độ.

## Lộ trình (bước dựng được kế tiếp)

| Mốc | Làm gì | Không cần |
| --- | --- | --- |
| **OSG-M0** (đợt này) | Kiểm kê (U16-INVENTORY) + ADR này + `task-graph.schema.json` + `capability-registry.schema.json` + khung VN-OS Tasks. Còn thiếu: event/audit vòng-đời-tác-vụ riêng + **demo task giả trên VM** | Model lớn |
| **OSG-M1 — API first (bước kế)** | 5 tác vụ qua **đường A** (`connect_wifi/print_document/switch_bluetooth_audio/update_namios/find_app_or_file`); engine đọc task-graph; **panel ba chế độ**; verifier `success_criteria→evidence`; pause/stop; offline fallback. Test VM → 5 máy pilot; "đã xong" có evidence | Cloud AI, tương thích mọi app |
| **OSG-M2 — UI agent** | **AT-SPI scoped-window** (đọc-trước-khi-bấm + stale-state guard) + **visual fallback theo phiên** qua portal (che OTP) + **user-takeover**; 20 task GUI lab + đối kháng focus/layout; **wrong-target = 0** | — |
| **OSG-M3 — liên ứng dụng** | Registry service + 3 app mẫu đăng ký + conformance test; tệp/Office/in; một Wine capsule có workflow **chứng nhận**; 30 task xuyên app | Driver Windows chạy trên Linux |
| **OSG-M4 — người Việt** | 100 VN-OS Tasks (dữ liệu giả) + pilot giáo viên/văn phòng + model router local/cloud tuỳ chọn + voice tuỳ chọn; dashboard chất lượng; công bố **chỉ** app/version/task/thiết bị đã kiểm | — |

**Ưu tiên khả thi:** hoàn thành **M0/M1 trước** khi gắn nhãn "SmartAI điều khiển máy". **M2/M3 chỉ mở với app & tác vụ đã thử**, cần **desktop/máy thật + rà soát an toàn nặng** (AT-SPI/portal là bề mặt tấn công mới: che OTP, chỉ-báo-quan-sát, stale-guard, chống prompt-injection từ nội dung app). **M4 cần người dùng thật**; không dùng demo đẹp làm bằng chứng độ tin cậy.

## Trung thực về quy mô M1–M4

**Agent dùng-máy-tính thật là một nỗ lực LỚN, nhiều pha.** M1 (đường A, 5 tác vụ) là phần "nhẹ" nhất và **đã có nền rời rạc** — nhưng vẫn cần engine task-graph + verifier + panel 3 chế độ + pilot 5 máy thật. **M2 trở đi là phần khó thật sự:** quan sát UI qua AT-SPI (phụ thuộc chất lượng cây trợ năng của từng app), fallback hình-ảnh qua portal (bề mặt rủi ro quyền-riêng-tư + prompt-injection + nhầm đối tượng), stale-state guard, user-takeover — mỗi thứ cần **máy thật, compositor thật, và rà soát an toàn độc lập**. M3 phụ thuộc **hệ sinh thái app Việt** chịu đăng ký + chịu được review/ký (ngoài tầm kiểm soát của một mình đội OS). M4 cần **pilot người thật** (giáo viên/văn phòng) với dữ liệu giả + rubric chấm kết quả thật. **Không có đường tắt**: không build M2–M4 trong môi trường này; đợt này dừng đúng ở OSG-M0 mức thiết kế/schema.

## Hệ quả

- M1 hiện thực engine đọc `task-graph.schema.json` (đường A + mock adapter) + panel 3 chế độ + verifier; tái dùng broker/guard của PL04 + `pkexec`/polkit + audit đã che (EVENT-ERROR-CONTRACT).
- M2 spike AT-SPI + portal trên VM KDE Plasma, thêm stale-guard + user-takeover + prompt-injection tests; **không** bấm tọa độ cứng.
- M3 dựng registry service + 3 app mẫu + conformance theo `capability-registry.schema.json`.
- M4 bộ 100 VN-OS Tasks + pilot + router + voice.
- Giữ bất biến PL14/PL16: user-space, API-first, không root shell cho AI, không toàn-màn-hình mặc định, không tọa độ cố định, dừng ở lockscreen/OTP/user-takeover, tắt-AI-máy-vẫn-dùng-được. Nếu sau này đổi compositor/desktop stack, **mở lại** ADR này cho đường C/D.

## Nguồn

- [1] UFO — UI-Focused Agent for Windows OS Interaction: https://arxiv.org/abs/2402.07939
- [2] OSWorld — benchmark máy tính thật, kiểm kết quả thực thi: https://arxiv.org/abs/2404.07972
- [3] XDG Desktop Portal RemoteDesktop/ScreenCast + security model: https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html ; https://flatpak.github.io/xdg-desktop-portal/docs/security-model.html
- [4] GNOME AT-SPI accessibility API: https://gnome.pages.gitlab.gnome.org/at-spi2-core/devel-docs/doc-org.a11y.atspi.Accessible.html
- [5] OpenAI Computer-Using Agent system card (hạn chế + an toàn computer use): https://openai.com/index/operator-system-card/
- ADR 0014 (snapshot/rollback), ADR 0016 (design system), ADR 0017 (polkit-gated service, ranh giới UI/Service/SmartAI). Kiểm kê: `docs/spec-package/U16-INVENTORY.md`. Schema: `.../usr/share/namios/task-graph.schema.json`, `.../usr/share/namios/capability-registry.schema.json`. Khung test: `docs/specs/VN-OS-TASKS.md`.

> Nguồn nghiên cứu là **cơ sở tham khảo kiến trúc & đánh giá**, KHÔNG phải chứng nhận SmartAI của NaMiOS đã hoạt động. "osGPT" là mục tiêu trải nghiệm; sản phẩm dùng tên **NaMiOS SmartAI**, giữ khả năng thay model và bảo vệ người dùng Việt khỏi phụ thuộc một dịch vụ duy nhất.
