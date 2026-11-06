# Phụ lục 06 (PRA-001–044) — Ma trận: yêu cầu → module hiện có → thay đổi → test

> Bắt buộc theo §11: map để **tránh viết chồng** app catalog / Device Hub / action
> broker / tool broker. Nguyên tắc: TÁI DÙNG `namios_sys`/`namios_eco`/`namios_compat`/
> `namios_dotnet`/`namios_smartai`; chỉ thêm hợp đồng + logic trung thực còn thiếu vào
> package mới `namios_pra`. Cột "Buildable" phân biệt code-được-ngay với **BLOCKED**
> (thiết bị/Office/.NET/pilot THẬT — §10, bài P01–P13).

## D0 — Contract & UX (buildable NGAY; đợt này làm phần code)

| PRA | Yêu cầu | Module | Thay đổi | Test | Buildable |
| --- | --- | --- | --- | --- | --- |
| PRA-001 | Năng lực thiết bị TỪNG chức năng (in/scan/copy/fax riêng) | **`namios_pra.device_hub`** (tái dùng `namios_sys.DeviceFunctionStatus`; Device Hub UI sau nối `namios_compat.device_registry`) | `DeviceCapability` + `can_copy` chặn suy-diễn | `test_pra_device_hub.py` | ✅ (logic) |
| PRA-016 | Office Route Resolver theo nhu cầu | **`namios_pra.office_route`** (tái dùng `WindowsMode` ý niệm) | macro/add-in → không web; sign → Windows | `test_pra_office_route.py` | ✅ |
| PRA-017 | Document Fidelity Gate | `namios_pra.office_route.fidelity_gate` | sai số tiền/trang/chữ ký (BLOCKING) → chặn lưu/in | ⟪ | ✅ (so file thật = D2) |
| PRA-022 | .NET Classifier có chứng cứ | **`namios_pra.dotnet_classify`** (tái dùng `namios_dotnet` đọc PE tĩnh) | taxonomy 8 kind + trait; unknown khi thiếu metadata | `test_pra_dotnet.py` | ✅ (logic; PE thật = D2) |
| PRA-023 | .NET Runtime Strategy | `namios_pra.dotnet_classify` | WPF/WinUI/WinForms/legacy → windows_only; modern→native; com/webview2→wine | ⟪ | ✅ |
| PRA-032 | Theo dõi kết quả trung thực | **`namios_pra.progress`** (nối `namios_sys.goal` + SAI-022) | queued≠in-xong≠đã-nhận; ký≠nộp≠biên-nhận | `test_pra_progress.py` | ✅ |
| PRA-028/029/030/031 | Doctor thiết bị/mạng/Office/WindowsApp | **`namios_pra.doctor`** (tái dùng `smartai.triage`/`ErrorCategory` + `device_hub`/`office_route`) | 5 lỗi thiết bị khác nhau · 8 lỗi mạng mỗi lỗi 1 cách sửa · macro không web · DB mất→partial · portal→blocker · thử N lần→dừng | `test_pra_doctor.py` + `test_pra_doctor_adversarial.py` | ✅ (logic; chạy thật D1/D2) |
| PRA-033/034/035 | Hướng dẫn tiếp-tục-được · quyền rõ · offline | **`namios_pra.support`** (tái dùng `namios_sys.data_authority`) | checklist ≤3 bước + checkpoint · nguồn-không-tin-cậy không cấp quyền + giao dịch cần xác nhận · cloud tắt lõi vẫn chạy | `test_pra_support.py` | ✅ |
| PRA-009/012 | Network/Bluetooth Center | NetworkManager/BlueZ (hệ) + UI | contract + UI | — | BLOCKED (thiết bị thật) |
| PRA-036/037/039/040 | Design system + 5 màn hình + ngôn ngữ VN + tiếp cận | `docs/design/DESIGN-SYSTEM.md` + `docs/design/mockups/` (SVG→PNG) | tokens màu/chữ/spacing/trạng-thái/tương-phản-AA + từ-vựng VN + 5 màn hình (Desktop/Ứng dụng/Thiết bị/Mạng/SmartAI) | render PNG | ✅ (mockup) |
| PRA-038 | Bảng điều khiển tác vụ SmartAI | `docs/design/mockups/namios-smartai.*` (nối `progress`/`support`) | "Tôi muốn làm gì" + thang tiến-độ trung-thực + quyền + nguồn + hoàn tác + chi-tiết-KTV | mockup | ✅ (mockup) |

## D1–D4 (cần hạ tầng/thiết bị/pilot THẬT — BLOCKED đúng §10)

| Giai đoạn | PRA | Lý do BLOCKED |
| --- | --- | --- |
| D1 thiết bị/mạng | PRA-002–015 | 3 laptop/2 desktop/2 máy in/2 headset/2 router THẬT (bài P01–P06) |
| D2 Office/Windows | PRA-018–021,024–027 | file Office thật đã khử dữ liệu + .NET fixtures + máy Windows đối chứng + token/portal (P07–P10) |
| D3 SmartAI & người dùng | pilot 3 persona | người dùng thật xác nhận (P11–P13) |
| D4 Release | PRA-041–044 | ma trận phần cứng/ứng dụng thật + gate chuyển máy chính |

## Chốt phạm vi

**D0 XONG trọn phần code+UX được-tại-chỗ** (§8 "D0 — Contract & UX"):
- Honest-core: device-capability-per-function (PRA-001) · Office route+fidelity (PRA-016/017) ·
  .NET classifier+route (PRA-022/023) · progress-vocabulary (PRA-032).
- Doctor-taxonomy: `doctor.py` (PRA-028/029/030/031) + `support.py` (PRA-033/034/035) — tái dùng
  `smartai.triage`/`device_hub`/`office_route`/`sys.data_authority`, **không fork**.
- Design: `DESIGN-SYSTEM.md` (PRA-036/037/039/040) + 5 màn hình mockup (PRA-036/038).

Tất cả tái dùng SYS/eco/dotnet/smartai, không dựng hệ song song (đúng §11). D1–D4 = BLOCKED
chờ thiết bị/Office/.NET/pilot thật (§10, bài P01–P13) — chưa có chứng nhận trên thiết bị/phần
mềm thật, đúng §12 giới hạn.
