# NaMiOS — U16-INVENTORY: Kiểm kê trung thực cho tầng tác vụ desktop (SmartAI kiểu osGPT)

**Ngày:** 09/11/2026 · **Người lập:** đội phát triển (Claude Code) · **Mốc:** Phụ lục 16 §10 **OSG-M0** (nền tảng: kiểm kê + ADR + schema task/capability + khung kiểm thử) — **mức THIẾT KẾ/SCHEMA, chưa chạy agent thật.**
**Đối chiếu:** `docs/spec-package/NaMiOS_Phu_luc_16_SmartAI_OSGPT_Tac_vu_Desktop.md`, `docs/spec-package/NaMiOS_Phu_luc_14_SmartAI_Core_Nguoi_Viet.md`, `docs/specs/SMARTAI-ORCHESTRATOR.md`, `docs/specs/EVENT-ERROR-CONTRACT.md`, `docs/adr/ADR-0019-os-agent.md`.

## 0. Tuyên bố trung thực (đọc trước)

> **NaMiOS CHƯA có "agent dùng máy tính" (computer-use agent).** Thứ duy nhất đang chạy hướng về Phụ lục 16 là **NaMiOS SmartAI chế độ "Hỏi tôi" dạng rule-based** — tức công cụ `namios-smartai` (bash): 10 playbook tất định cho mạng/in/gõ tiếng Việt/cập nhật/Wine, có cổng quyền `confirm_and_run`, audit đã che bí mật và đường `--explain <mã lỗi>`. Nó **KHÔNG quan sát giao diện ứng dụng khác, KHÔNG bấm thay người dùng, KHÔNG có task-graph engine**. Mọi thứ còn lại của PL16 (quan sát UI qua AT-SPI/portal, hai chế độ "Hướng dẫn tôi"/"Làm cùng tôi", Capability Registry chạy được, bộ VN-OS Tasks) là **VẮNG MẶT**.
>
> Có một thư viện Python `src/namios_smartai/*` (engine PL04): intent → planner → policy/consent → typed tool broker → state machine → validator, **có unit test**. Nhưng đây là **khung thư viện tất định mức M0**, **chưa nối vào desktop**, **không phải** agent xuyên ứng dụng, **không có** task-GRAPH (chỉ danh sách `PlanStep` tuyến tính), **không có** Capability Registry, **không có** AT-SPI/portal. Nó là **tài sản thiết kế/thư viện**, không phải "SmartAI điều khiển máy".
>
> **"osGPT" là MỤC TIÊU TRẢI NGHIỆM, không phải tính năng đã có.** Tên sản phẩm là **NaMiOS SmartAI**. Không có đoạn nào trong tài liệu này được hiểu là agent đã hoạt động.

**Quy tắc chấm trạng thái** (kế thừa §5 Phụ lục 13, dùng xuyên suốt U13/U15):

- `absent` — không có trong repo.
- `specified` — đã có yêu cầu/thiết kế/schema trong repo, **chưa** có bằng chứng chạy.
- `partial` — có artifact + bằng chứng chạy **một phần**, **chưa** đủ cửa kiểm chứng.
- `completed` — **chỉ** khi chạy trên **máy thật** (pilot) qua đúng cửa kiểm chứng.

**Sự thật nền:** NaMiOS **chưa test trên máy thật nào** cho tầng tác vụ; mọi bằng chứng là unit-test thư viện + review mã bash. Theo quy tắc trên, **không năng lực PL16 nào đạt `completed`.** Ngay cả OSG-M0 cũng chỉ ở mức `specified` sau đợt này (có đủ ADR + schema + khung test, nhưng **chưa** có "demo task giả trên VM" mà §10 đòi làm bằng chứng M0).

## 1. Bản đồ năng lực PL16 ↔ hiện trạng

| # | Năng lực PL16 | Mục | Trạng thái | Bằng chứng / khoảng trống trong repo |
| --- | --- | --- | --- | --- |
| 1 | **Chế độ "Hỏi tôi" (ask_me)** — chỉ đọc trạng thái, chỉ đường tới Settings, giải thích có bằng chứng | §2 | **partial** (rule-based) | `distro/.../usr/local/bin/namios-smartai` + `namios-smartai-policy.sh`; `docs/specs/SMARTAI-ORCHESTRATOR.md`. Thực tế làm HƠN "chỉ đọc": chạy hành động đặc quyền qua `pkexec` **sau khi người dùng đồng ý** — nhưng vẫn trong-phiên, không quan sát/điều khiển app khác. `specified` theo SMARTAI-ORCHESTRATOR (chưa máy thật). |
| 2 | **Chế độ "Hướng dẫn tôi" (guide_me)** — checklist ≤3 bước, highlight nút/tệp trên cửa sổ đã chọn, người dùng tự bấm | §2 | **absent** | Không có quan sát cửa sổ, không overlay highlight, không AT-SPI. `namios-smartai` chỉ hiện văn bản kế hoạch, không trỏ vào control thật của app. |
| 3 | **Chế độ "Làm cùng tôi" (do_with_me)** — thực thi trong phạm vi duyệt, kiểm sau mỗi bước, nhường quyền khi người dùng chạm chuột/bàn phím | §2 | **absent** | Không có vòng lặp quan sát→hành động→kiểm; không có user-takeover; `confirm_and_launch` chỉ *mở* GUI để người dùng tự thao tác (ngược lại với "làm cùng"). |
| 4 | **Đường A — API & dịch vụ OS** (Wi-Fi/BT/máy in/tệp/cập nhật/sao lưu/catalog qua broker) | §3 | **partial** | `namios-smartai` gọi `nmcli`/`cups`/`fcitx5`/`pkexec systemctl`/`timeshift` bằng **argv tĩnh** sau consent — đúng tinh thần đường A nhưng **không** qua một Policy/Tool Broker có schema (typed-tool nằm ở thư viện PL04, chưa nối). Engine PL04 `tools.py`/`policy.py` có typed tool + allowlist (unit-test), chưa chạy trên OS. |
| 5 | **Đường B — Action SDK của ứng dụng** (app khai hành động/schema/quyền/pre-post/evidence, review + ký) | §3, §7 | **absent** | Chưa có app nào đăng ký; registry service chưa có. Schema manifest vừa dựng ở đợt này (mục 2 dưới) là `specified`. |
| 6 | **Đường C — Cây trợ năng AT-SPI** (đọc/điều khiển cửa sổ người dùng chọn) | §3 | **absent** | `grep -rniE 'at-spi\|atspi'` trong `distro/`,`src/` → **không** có tích hợp AT-SPI (chỉ nhắc "accessibility" ở tài liệu UX/design, khác việc). Không có binding `org.a11y.atspi`. |
| 7 | **Đường D — Hình ảnh + input có phiên** (screen capture/remote desktop portal, che vùng nhạy cảm) | §3 | **absent** | `grep -rniE 'remotedesktop\|screencast\|screen.?capture\|remote.?control'` trong `distro/`,`src/` → **không** kết quả. Không dùng `xdg-desktop-portal` RemoteDesktop/ScreenCast. **Không** có (và theo thiết kế **không** được có) tọa độ chuột cố định. |
| 8 | **Tầng tác vụ: Goal contract + Task graph** (task_id/intent/mode/resource/success/allowed/forbidden/consent/pause_on/evidence/state; mỗi bước có dependency/pre/post/idempotency/timeout/retry/rollback) | §4, §4.1 | **specified** (schema mới) | `distro/.../usr/share/namios/task-graph.schema.json` (dựng đợt này, validate bằng `jsonschema` draft 2020-12). **Chưa có engine** đọc/thực thi graph. PL04 có `PlanStep`/`state_machine.py` nhưng là danh sách tuyến tính + enum trạng thái KHÁC (`PROPOSED/AWAITING_CONSENT/.../COMPLETED`), **không** phải DAG và **không** phải enum §4 (`planned/awaiting_user/running/paused/blocked/partial/verified/cancelled`). |
| 9 | **Capability Registry** (manifest: app_id/publisher/version/actions/labels/io-schema/permissions/dry_run/pre-post/idempotency/audit_redaction/test_fixture + mức chứng nhận declared→…→published/stale/revoked) | §7 | **specified** (schema mới) | `distro/.../usr/share/namios/capability-registry.schema.json` (dựng đợt này, validate OK). **Chưa có** registry service, **chưa có** app nào đăng ký, **chưa có** cơ chế review/ký. |
| 10 | **Bề mặt trải nghiệm** (gọi nhanh, bảng kế hoạch, chỉ dẫn trực quan, nút quyền cụ thể, tiến trình Dừng/Tự-làm-tiếp/Hoàn tác, màn kết quả Đã-xong/Một-phần/…) | §5 | **partial** | Có menu kdialog/TTY + "KẾ HOẠCH ≤3 bước" + nút đồng ý/hủy + "Giới thiệu & cam kết an toàn" trong `namios-smartai`. **Thiếu**: panel QML thống nhất brand, chỉ-dẫn-trực-quan (highlight control), nút Hoàn tác/"Tự làm tiếp" theo tác vụ, màn kết quả 4 trạng thái. |
| 11 | **Ranh giới an toàn computer-use** (chống quan sát quá mức, chống prompt-injection, bảo vệ OTP/token/ngân hàng, chống nhầm đối tượng, khôi phục/undo, không-tê-liệt-OS) | §8 | **partial** | Guardrail đã CÓ THẬT trong `namios-smartai`: chỉ argv tĩnh (không eval/curl\|bash), không root cho AI, pkexec/polkit, audit đã che, "tắt AI máy vẫn boot/gõ/in/cập nhật". PL04 có `injection.py`/`redaction.py`/`kill_switch.py` (unit-test). **Thiếu** phần computer-use: chỉ-báo-đang-quan-sát, che vùng OTP khi capture, dừng-ở-lockscreen — vì các đường C/D chưa tồn tại. |
| 12 | **Model Router local/cloud tuỳ chọn** | §5, PL14 §3 | **absent** (sản phẩm) / **partial** (thiết kế) | `namios-smartai` chỉ *dò* biến môi trường khoá LLM để đổi dòng mô tả; **mọi playbook chạy rule-based**. PL04 `planner.py` có khung router nhưng không gọi model thật. Không có router local/cloud hoạt động. |
| 13 | **Event/Audit cho tác vụ** | §4, PL14 §7 | **partial** | `docs/specs/EVENT-ERROR-CONTRACT.md` + `/usr/share/namios/error-catalog.json` là hợp đồng sự kiện/lỗi **cho chẩn đoán** (họ `NM-*`), tái dùng được cho `evidence`/audit của task-graph. **Chưa** có không gian sự kiện riêng cho vòng đời tác vụ xuyên app (focus_change/layout_changed/user_takeover…). |
| 14 | **Bộ VN-OS Tasks (100 ca) + cổng phát hành** | §9 | **absent** (fixtures) / **specified** (khung) | `docs/specs/VN-OS-TASKS.md` (dựng đợt này) là **KHUNG/skeleton**: 10 kịch bản OSG-01..10, cơ cấu 100 ca, danh sách đối kháng, metric. **Mọi ca là TODO fixture**, chưa viết, chưa chạy. `fixtures/smartai/` trống. |

### Chú thích "Hỏi tôi" làm hơn chỉ-đọc

PL16 §2 định nghĩa "Hỏi tôi" là *chỉ đọc trạng thái đã cho phép; không điều khiển cửa sổ hay sửa máy*. `namios-smartai` hiện tại **vượt** định nghĩa đó: sau khi người dùng bấm đồng ý, nó chạy hành động **đổi trạng thái** (bật Wi-Fi, restart CUPS qua pkexec, restart fcitx5…). Về bản chất đây là một trộn lẫn "Hỏi tôi + một phần Làm cùng tôi theo-dịch-vụ (đường A)", nhưng **không** quan sát/điều khiển UI app khác. Khi dựng ADR-0019, ta tách bạch: các hành động đổi-trạng-thái-qua-dịch-vụ-OS này thuộc **đường A của chế độ "Làm cùng tôi" mức L2**, còn "Hỏi tôi" đúng nghĩa là nhánh chỉ-đọc/giải-thích. Hiện trạng gộp trong một tool; M1 sẽ tách panel ba chế độ tường minh.

## 2. Hai schema mới dựng ở OSG-M0 (mức thiết kế)

| Artifact | Vai trò | Trạng thái | Kiểm chứng |
| --- | --- | --- | --- |
| `distro/live-build/config/includes.chroot/usr/share/namios/task-graph.schema.json` (`urn:namios:task-graph:1`) | Hợp đồng mục tiêu/tác vụ §4.1 + task graph §4 (dependency/pre-post/idempotency/timeout/retry/rollback), enum trạng thái `planned/awaiting_user/running/paused/blocked/partial/verified/cancelled` | **specified** | `Draft202012Validator.check_schema` PASS; validate instance mẫu `print_document` PASS; ca âm (trường lạ `ai_granted_root`, `state:"done"`) bị từ chối đúng. |
| `distro/live-build/config/includes.chroot/usr/share/namios/capability-registry.schema.json` (`urn:namios:capability-registry:1`) | Manifest năng lực app §7: actions/labels VI/io-schema/permissions/dry_run/pre-post/idempotency/audit_redaction/test_fixture + mức chứng nhận `declared→sandbox_tested→pilot_verified→published→stale/revoked` | **specified** | `check_schema` PASS; validate instance mẫu (app kế toán: `invoice.preview` L1 + `invoice.issue` L4 cần người-nghiệp-vụ) PASS; ca âm (`grants_root`, `uses_fake_data:false`) bị từ chối đúng. |

Hai schema cố ý đặt `additionalProperties:false` ở mọi object để **chặn trường tự-cấp-quyền** (ví dụ `grants_root`, `ai_autonomy`) lọt vào — fail-closed. **Lưu ý quan trọng:** "schema hợp lệ" KHÔNG phải "được phép chạy". Việc cấp quyền do Policy/Tool Broker + polkit/portal + consent-theo-phiên quyết định (PL14 §3 Lớp 4), **không** phải do manifest/goal-contract tự khai.

## 3. Ánh xạ mốc OSG-M0..M4 — chia done/partial/absent

| Mốc | PL16 đòi gì | Phần ĐÃ làm (đợt này + sẵn có) | Phần THIẾU | Kết luận |
| --- | --- | --- | --- | --- |
| **OSG-M0 — nền tảng** | Kiểm kê repo; ADR stack desktop/compositor/portal/AT-SPI; schema task + capability registry + consent UI + event/audit; **demo task giả trên VM** | Kiểm kê (file này); **ADR-0019** (agent user-space, API-first, 3 chế độ, 4 đường, ranh giới an toàn); **task-graph.schema.json** + **capability-registry.schema.json** (validate OK); khung test **VN-OS-TASKS.md**; tái dùng EVENT-ERROR-CONTRACT cho evidence/audit | **Consent UI ba chế độ** (QML) chưa dựng; **event/audit RIÊNG cho vòng đời tác vụ** chưa tách khỏi họ `NM-*`; **demo task giả trên VM** (bằng chứng M0 mà §10 đòi) **chưa** làm | **partial → `specified`.** Có đủ phần giấy tờ/schema của M0; chưa có demo chạy. |
| **OSG-M1 — API first** | 5 tác vụ ưu tiên qua đường A; panel ba chế độ; verifier; pause/stop; AI offline fallback; test trên VM + 5 máy pilot, "đã xong" có evidence | Nền rời rạc: `namios-smartai` đã làm được net/print/update theo rule-based + offline fallback + audit; engine PL04 có typed-tool/policy/validator (thư viện) | **Toàn bộ M1 như một thể thống nhất chưa có**: chưa có panel 3 chế độ, chưa có engine đọc task-graph, chưa có verifier gắn success_criteria→evidence, chưa test VM/pilot. 5 tác vụ chưa chạy qua đúng hợp đồng §4.1. | **absent** (là **bước dựng được kế tiếp** — xem ADR-0019 §Lộ trình). |
| **OSG-M2 — UI agent** | AT-SPI scoped-window; visual fallback theo phiên; user takeover; stale-state guard; 20 task GUI lab + đối kháng focus/layout, không wrong-target | — (không có gì) | AT-SPI, portal RemoteDesktop/ScreenCast, stale-state guard, user-takeover, 20 ca GUI | **absent.** Cần desktop thật + review an toàn nặng; mở **sau khi** M1 đạt. |
| **OSG-M3 — liên ứng dụng** | App SDK + 3 app mẫu; tệp/Office/in; một Wine capsule có kiểm; 30 task xuyên app; broker policy | Schema capability-registry (thiết kế); PL04 có `capsule.py`/`recipe.py`/`vendorpack.py` (thư viện, chưa chứng nhận workflow nào) | Registry service, 3 app mẫu đăng ký, conformance test, Wine capsule có workflow chứng nhận, 30 ca xuyên app | **absent.** |
| **OSG-M4 — người Việt** | 100 VN-OS Tasks; pilot giáo viên/văn phòng; model router local/cloud; voice tuỳ chọn; báo cáo success/error/resource; danh sách công việc được chứng nhận | Khung 100 ca (skeleton trong VN-OS-TASKS.md) | Mọi fixture thật, pilot người thật, router model chạy, voice, dashboard chất lượng | **absent.** Cần người dùng thật; "không dùng demo đẹp làm bằng chứng độ tin cậy" (§10). |

## 4. Kết luận U16 (phần kiểm kê)

1. **Chỉ có "Hỏi tôi" rule-based tồn tại** (`partial`/`specified`). Hai chế độ "Hướng dẫn tôi"/"Làm cùng tôi" đúng nghĩa computer-use **chưa có một dòng**.
2. **OSG-M0 giao đủ phần thiết kế** ở đợt này: kiểm kê + ADR-0019 + 2 schema (validate) + khung VN-OS Tasks. **Chưa** giao "demo task giả trên VM" → M0 giữ `specified`, **không** tự nâng lên `partial/completed`.
3. **M1 là bước dựng được kế tiếp** (API-first 5 tác vụ qua đường A + panel 3 chế độ + verifier) — làm **trước** khi gắn nhãn "SmartAI điều khiển máy". M2+ (AT-SPI/visual) cần **máy thật + rà soát an toàn nặng** và chỉ mở sau M1.
4. Giữ bất biến xuyên suốt: **user-space, API-first, không root shell cho AI, không toàn-màn-hình mặc định, không tọa độ chuột cố định**, dừng ở focus-change/dialog-lạ/lockscreen/OTP/user-takeover. Tắt AI → OS vẫn boot/gõ/in/cập nhật/khôi phục.

## 5. Việc phải xây tiếp (tham chiếu nhanh)

- **OSG-M0 còn lại:** tách event/audit vòng-đời-tác-vụ khỏi họ `NM-*`; dựng **demo task giả trên VM** (mock adapter, không model) để lấy bằng chứng M0; phác consent UI 3 chế độ (QML, theo ADR-0016 design system).
- **OSG-M1:** engine đọc `task-graph.schema.json` (đường A + mock), verifier success_criteria→evidence, panel ba chế độ với nút quyền cụ thể + Dừng/Tạm dừng, offline fallback; 5 tác vụ `connect_wifi/print_document/switch_bluetooth_audio/update_namios/find_app_or_file`; test VM rồi 5 máy pilot.
- **OSG-M2:** AT-SPI scoped-window đọc-trước-khi-bấm + stale-state guard + user-takeover; visual fallback theo phiên qua portal (che OTP), **không** tọa độ cứng; 20 ca GUI + đối kháng.
- **OSG-M3:** registry service + 3 app mẫu đăng ký qua `capability-registry.schema.json` + conformance test + một Wine capsule có workflow chứng nhận.
- **OSG-M4:** 100 VN-OS Tasks (fixtures thật, dữ liệu giả) + pilot người thật + router model + voice; chỉ công bố danh sách app/version/task/thiết bị **đã kiểm**.

Chi tiết kiến trúc ở `docs/adr/ADR-0019-os-agent.md`; schema ở `.../usr/share/namios/task-graph.schema.json` và `.../capability-registry.schema.json`; khung kiểm thử ở `docs/specs/VN-OS-TASKS.md`.
