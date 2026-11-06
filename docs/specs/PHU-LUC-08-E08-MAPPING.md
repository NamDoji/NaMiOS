# Phụ lục 08 (E08-001–040) — Ma trận: yêu cầu → module hiện có → thay đổi → test

> Bắt buộc theo §8: map để **tránh viết hệ trạng thái thứ hai**. Nguyên tắc: TÁI DÙNG
> `namios_pra` (DotnetKind/route, device per-function, progress, Doctor, support/offline),
> `namios_sys` (data_authority, action broker), `namios_smartai` (triage/repair/promotion/
> knowledge_base), `namios_odc` (device cert); chỉ thêm hợp đồng I0 còn thiếu vào package
> mới `namios_e08`. KHÔNG dùng Windows driver/INF; KHÔNG hứa mọi .NET native; KHÔNG root
> shell cho AI; KHÔNG tự firmware-flash/ký/nộp; KHÔNG dùng log/tài liệu làm lệnh.

## I0 — Contract + fake (buildable NGAY; đợt này làm phần code)

| E08 | Yêu cầu | Module | Thay đổi | Test | Buildable |
| --- | --- | --- | --- | --- | --- |
| E08-001/027 | Device event bus + correlation | **`namios_e08.event_bus`** | `coalesce_events` debounce → 1 thiết bị = 1 incident (20 event → 1); cap gọi AP | `test_e08_core.py` (D02/A05) | ✅ |
| E08-002 | Driver Match Service | **`namios_e08.driver_match`** | ghép theo hardware-ID + thứ tự tier; KHÔNG theo tên gần giống; lạ → unsupported | `test_e08_core.py` (D01) | ✅ |
| E08-003 | Provenance | `driver_match.provenance_ok` | cần official + hash + chữ ký; thiếu → không tin, bỏ qua (không cài) | `test_e08_core.py` (D04) | ✅ (nguồn thật = I1) |
| E08-004/037 | Device states theo chức năng + schema | **`namios_e08._types`** (DeviceState/DeviceIncident/AiAction) | 12 trạng thái theo-chức-năng; in verified ≠ scan firmware_missing | `test_e08_core.py` (D01) | ✅ |
| E08-005 | Cài/đổi driver có giao dịch | **`namios_e08.install_txn`** | stage→check→snapshot→apply→test→commit/rollback; hỏng→rollback; chưa snapshot→không apply | `test_e08_core.py` (D03) | ✅ (thực thi = action broker SYS) |
| E08-017/018/025 | .NET runtime fingerprint + 2 tuyến | **tái dùng** `namios_pra.classify_dotnet` + `AppRuntimeProfile` (observed/inferred/unknown) | WPF không native; thiếu metadata → unknown | (đã test ở PRA dotnet) | ✅ |
| E08-020/031 | Windows dependency graph + outcome | **`namios_e08.depgraph`** | DAG → mở GUI≠dùng được; DB mất→partial, cổng→blocked; tool-ok≠workflow-ok | `test_e08_core.py` (N02/A02) | ✅ |
| E08-030 | Bounded actuator | **`namios_e08.actuator`** (tái dùng `sys.data_authority`) | log/tài-liệu không thành lệnh; thay-đổi cần rollback; cấm root/shell/binary/flash/ký | `test_e08_core.py` (A01) | ✅ |
| E08-033 | Knowledge provenance | **tái dùng** `namios_smartai.knowledge_base` (SAI-025) | 4 tầng nguồn; community/AI chưa kiểm không thành lời khuyên chắc | (đã test ở SAI) | ✅ |
| E08-035 | Manual operation / offline | **tái dùng** `namios_pra.support.offline_capabilities` (PRA-035) | model tắt → lõi in/scan/Wi-Fi/app offline vẫn chạy | (đã test ở PRA) | ✅ |
| E08-037 | Schema + map vào ECO/COMP/SAI/SYS | `namios_e08._types` | device_incident/app_runtime_profile/ai_action — KHÔNG thêm nguồn trạng thái mới | — | ✅ |

## I1–I4 (cần thiết bị/.NET/pilot THẬT — BLOCKED đúng §7)

| Pha | E08 | Lý do BLOCKED |
| --- | --- | --- |
| I1 driver/thiết bị | E08-006–014, D01–D05 lab | USB/máy in/card mạng/firmware vendor THẬT + máy rollback được |
| I2 .NET/Wine | E08-021/022/024/026, N01–N04 | Wine prefix thật + 3 .NET fixture + máy Windows đối chứng + DB test |
| I3 SmartAI vận hành | E08-029/032/034/036, A01–A05 pilot | model thật + người dùng pilot |
| I4 pilot + release | E08-038(I4)/039/040 | 1 trường + 1 DN: 3 máy/2 MFP/2 card/2 BT/3 app thật + 10 việc/nhóm |

## Chốt phạm vi đợt này

Làm **I0 phần code** (§8 "Thực hiện I0: schema, event bus có debounce, fake device/.NET
fixtures, Device Hub…"): `namios_e08` = event-bus debounce (E08-001/027) · driver-match +
provenance (E08-002/003) · device-state schema (E08-004/037) · install-transaction
(E08-005) · windows-dependency-graph + outcome (E08-020/031) · bounded-actuator (E08-030).
.NET fingerprint / knowledge / offline = **tái dùng** PRA/SAI (không dựng lại). I1–I4 =
BLOCKED chờ thiết bị/.NET/pilot thật (§7).
