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
| PRA-028–031,033,034 | Doctor thiết bị/mạng/Office/WindowsApp + hướng dẫn + quyền | **tái dùng** `namios_smartai.diagnose`/`triage` + `namios_sys.goal`/`data_authority` | taxonomy lỗi theo vùng (làm tiếp D0/D3) | — | một phần (logic); chạy thật = D1/D2 |
| PRA-009/012 | Network/Bluetooth Center | NetworkManager/BlueZ (hệ) + UI | contract + UI | — | BLOCKED (thiết bị thật) |
| PRA-036–039 | Design system + 5 màn hình + ngôn ngữ VN | `docs/design/` (mockup SVG→PNG như login/desktop) | tokens + 5 screen | — | ✅ (mockup) — **làm tiếp** |

## D1–D4 (cần hạ tầng/thiết bị/pilot THẬT — BLOCKED đúng §10)

| Giai đoạn | PRA | Lý do BLOCKED |
| --- | --- | --- |
| D1 thiết bị/mạng | PRA-002–015 | 3 laptop/2 desktop/2 máy in/2 headset/2 router THẬT (bài P01–P06) |
| D2 Office/Windows | PRA-018–021,024–027 | file Office thật đã khử dữ liệu + .NET fixtures + máy Windows đối chứng + token/portal (P07–P10) |
| D3 SmartAI & người dùng | pilot 3 persona | người dùng thật xác nhận (P11–P13) |
| D4 Release | PRA-041–044 | ma trận phần cứng/ứng dụng thật + gate chuyển máy chính |

## Chốt phạm vi đợt này

Làm **D0 phần code honest-core**: `namios_pra` = device-capability-per-function (PRA-001) ·
Office route+fidelity (PRA-016/017) · .NET classifier+route (PRA-022/023) · progress-vocabulary
(PRA-032) — tái dùng SYS/eco/dotnet, **không fork**. Còn D0: Doctor-taxonomy (nối SmartAI) +
design-system/5-screen mockup = làm tiếp. D1–D4 = BLOCKED chờ thiết bị/Office/.NET/pilot thật
(§10) — chưa có chứng nhận trên thiết bị/phần mềm thật, đúng §12 giới hạn.
