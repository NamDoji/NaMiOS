# Phụ lục 07 (ODC-001–048) — Ma trận: yêu cầu → module hiện có → thay đổi → test

> Bắt buộc theo §8: map để **tránh viết chồng** Document Broker / Route Matrix /
> Fidelity Gate / Device Hub / Office-Device Doctor. Nguyên tắc: TÁI DÙNG
> `namios_pra` (Office route/fidelity + device per-function + Doctor), `namios_sys`
> (data_authority), `namios_smartai` (promotion pattern); chỉ thêm hợp đồng O0
> engine-agnostic còn thiếu vào package mới `namios_odc`. Chọn engine thật = ADR 0013.

## O0 — Quyết định engine + hợp đồng (buildable NGAY; đợt này làm phần code)

| ODC | Yêu cầu | Module | Thay đổi | Test | Buildable |
| --- | --- | --- | --- | --- | --- |
| ODC-002/003/004 | Đánh giá engine + license/branding audit | `docs/adr/0013-office-engine-evaluation.md` | rubric 8 tiêu chí + 15-fixture plan + audit checklist; MỌI ô đo = "chưa đo" | — | ✅ (ADR) — đo thật BLOCKED |
| ODC-007 | Document Broker | **`namios_odc.document_broker`** (tái dùng `sys.data_authority` + `pra.fidelity_gate`) | inspect→explain→open_copy→verify_save; nội dung tài liệu không cấp quyền; không tự upload | `test_odc_route.py` | ✅ |
| ODC-008 | Office Route Matrix 6-mode | **`namios_odc.route_matrix`** (tái dùng `pra.OfficeNeed`) | 6 mode + TÁCH 4 trục mở≠sửa≠in≠macro; macro chỉ Windows; web+nhạy-cảm cần xác nhận | `test_odc_route.py` | ✅ |
| ODC-006/014 | Định dạng mặc định + fidelity gate | `document_broker.open_as_copy`/`verify_save` (tái dùng `pra` fidelity) | file ngoại/nhạy-cảm → mở bản sao; sai dữ liệu nghĩa → chặn lưu/in | `test_odc_route.py` | ✅ (so file thật = O1) |
| ODC-015/017 | Macro + tệp nhạy cảm | `route_matrix` + `document_broker.may_auto_upload` | VBA không web/bundled macro-pass; Wine không nhận macro-pass; auto_upload luôn False | `test_odc_route.py` | ✅ |
| ODC-001/020/033 | Tách gói + vòng đời + recheck | **`namios_odc.lifecycle`** | rollback riêng; Office lỗi không chặn OS; đổi 1 thành phần chỉ kiểm lại vùng ảnh hưởng | `test_odc_cert_lifecycle.py` | ✅ |
| ODC-022/041/047 | Chứng nhận thiết bị per-function | **`namios_odc.device_cert`** (tái dùng ý `pra.device_hub` + `sai.promotion`) | 10 trục chức năng + state machine reported→lab→pilot→published; cộng đồng/AI không nâng; hỗ trợ chỉ khi published | `test_odc_cert_lifecycle.py` | ✅ |
| ODC-048 | Chỉ số thành công | **`namios_odc.metrics`** | user-weighted coverage + mẫu số thật; catalog ≠ đã-hỗ-trợ; không bịa >100% | `test_odc_cert_lifecycle.py` | ✅ |
| ODC-037/038/039 | Device/Office Doctor + offline | **tái dùng** `namios_pra.doctor`/`support` (PRA-028/030/035 đã có) | Device Doctor (4 lỗi 4 cách), Office fidelity-diff, offline lõi vẫn chạy | (đã test ở PRA) | ✅ (đã có) |
| ODC-009/045 | Giao diện Office quen thuộc + theme | `docs/design/DESIGN-SYSTEM.md` (tái dùng) + mockup Office (làm tiếp) | File/Home/Insert… + theme NaMiOS chung | — | một phần (mockup) — làm tiếp |

## O1–O4 (cần Office/thiết bị/pilot THẬT — BLOCKED đúng §7)

| Mốc | ODC | Lý do BLOCKED |
| --- | --- | --- |
| O0 chốt engine | ODC-002 đo thật | 15 fixture Office thật đã khử dữ liệu + máy Windows đối chứng |
| O1 Office dùng được | ODC-005–019 evidence | engine thật đóng gói + fidelity round-trip trên file thật |
| O2 thiết bị phổ biến | ODC-021–034 | lab ≥3 laptop/2 desktop/2 MFP/router/BT thật + firmware vendor có nguồn |
| O3 SmartAI xuyên suốt | ODC-035–040 pilot | 10 người pilot + 3 persona thật xác nhận |
| O4 Release | ODC-042–048 scorecard | go/no-go theo persona trên thiết bị/Office/pilot thật |

## Chốt phạm vi đợt này

Làm **O0 phần code+ADR được-tại-chỗ** (§8 "Bắt đầu O0 và O1: … broker, route matrix,
fidelity gate … package/version/rollback"): package mới `namios_odc` = Document Broker
(ODC-007) · Office Route Matrix 6-mode (ODC-008) · lifecycle/recheck (ODC-001/020/033) ·
device cert per-function (ODC-022/047) · chỉ-số (ODC-048), **tái dùng** `namios_pra`/
`namios_sys`, KHÔNG fork + ADR 0013 (ODC-002/004). Office/Device Doctor + offline =
đã có sẵn ở `namios_pra`. Còn O0: mockup giao diện Office (ODC-009) = làm tiếp. O1–O4 =
BLOCKED chờ engine/Office/thiết bị/pilot thật (§7).
