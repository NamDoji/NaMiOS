# NaMiOS — Danh mục khóa và chủ sở hữu chuỗi cập nhật (Update Key & Owner Catalog)

**Ngày:** 09/11/2026 · **Mốc:** Phụ lục 15 §4 "Quản lý khóa" — **U15-A**.
**Trạng thái:** `specified` / **DESIGN** — **toàn bộ khóa dưới đây là ĐẶC TẢ, chưa tạo.** Không có khóa thật, không có HSM, không có production key nào trong repo/CI/ISO.
**Đối chiếu:** `docs/spec-package/NaMiOS_Phu_luc_15_Update_Center_Bao_mat_Cap_nhat.md` (§4), `docs/adr/0007-cap-nhat-bao-ve-metadata.md` (SEC-007: key production KHÔNG nằm trong repo/ISO/CI), `docs/adr/ADR-0017-update-service-architecture.md`, `docs/security/UPDATE-THREAT-MODEL.md`.

## 0. Tuyên bố trung thực (đọc trước)

> **Chưa có bất kỳ khóa ký thật nào.** NaMiOS hiện chỉ kế thừa **keyring repo của Debian** (apt GPG upstream) để xác thực gói; **chưa** có khóa phát hành riêng, **chưa** có vai trò TUF, **chưa** có HSM, **chưa** có quy trình tạo/luân chuyển/thu hồi được thực thi. Mọi mục trong danh mục này là **thiết kế để U15-B/C/D hiện thực**. Khi hiện thực giai đoạn đầu (U15-B) sẽ dùng **khóa lab gắn nhãn `dev`/`lab`** cho fixture test, **tách tuyệt đối** khỏi (các) khóa production sau này. **Không** commit khóa private vào repo.

**Nguyên tắc nền (PL15 §4 + ADR 0007):**
- Dùng **triển khai/chứng thư được kiểm định**, KHÔNG tự viết thuật toán chữ ký.
- **root/targets offline hoặc HSM** với quorum; khóa CI **tách quyền + có hạn**.
- **Tách nhiệm vụ (separation of duties):** người build gói **KHÔNG** tự phê duyệt/phát hành một mình.
- rotation/revocation có quy trình; thiết bị nhận **danh sách thu hồi** và chặn metadata quá hạn.
- Diễn tập định kỳ tình huống **khóa bị lộ / CDN bị chiếm**.

## 1. Mô hình vai trò khóa (kiểu TUF)

Thiết kế theo bốn vai trò TUF + vai trò CI, để **không một khóa đơn lẻ nào** vừa neo tin cậy vừa ký nội dung hằng ngày (chống TA3 "khóa CI bị trộm", TA4/TA5 rollback/freeze — xem threat model).

| Vai trò | Ký cái gì | Threshold (đề xuất) | Vị trí khóa | Tần suất dùng | Hạn/rotation (đề xuất) | Chủ sở hữu (vai trò, chưa gán người) |
| --- | --- | --- | --- | --- | --- | --- |
| **root** | Ủy quyền cho các vai trò khác (neo tin cậy); phân phối trong ISO | **3-trong-5** (quorum) | **Offline / HSM**, tách rời, không bao giờ trên máy nối mạng | Rất hiếm (khi lập/rotation vai trò) | 1–2 năm; rotation có nghi thức nhiều người | Ban quản trị khóa (Đỗ Chí Cường + người được ủy quyền) |
| **targets** | Ký danh tính + hash của payload phát hành (gói/ảnh) | **2-trong-3** | Offline / HSM | Mỗi đợt phát hành chính | 6–12 tháng | Chủ trì phát hành (release owner) |
| **snapshot** | Ký một **tập metadata nhất quán theo thời điểm** (chống mix-and-match) | 1 (có thể nâng) | Online có bảo vệ (hạn ngắn) | Mỗi lần cập nhật chỉ mục | Ngắn (tuần) | Dịch vụ phát hành tự động, giám sát bởi release owner |
| **timestamp** | Ký mốc thời gian "metadata còn tươi" (chống freeze) | 1 | Online (hạn rất ngắn) | Thường xuyên (giờ/ngày) | Rất ngắn (giờ–ngày) | Dịch vụ phát hành tự động |
| **CI / build-signing** | Ký artifact build sau khi **gate QA đạt** (provenance) | 1, **có hạn + revocation** | Online trong CI, phạm vi hẹp, **tách khỏi root/targets** | Mỗi build qua gate | Ngắn hạn, cấp lại thường xuyên | Hệ thống CI, không cá nhân giữ |

Ghi chú: **root** chỉ ủy quyền, **không** ký payload trực tiếp → nếu khóa ký hằng ngày (snapshot/timestamp/CI) bị lộ, vẫn **rotation + revocation** được bằng root offline mà không phải dựng lại gốc tin cậy trên toàn bộ máy đã cài.

## 2. apt GPG (tầng 1 — đã có, upstream) vs vai trò TUF (tầng 2 — phải xây)

| | apt GPG keyring (Debian) | Vai trò TUF (release-index NaMiOS) |
| --- | --- | --- |
| Hiện trạng | **có (upstream)** — keyring Debian trong ISO | **DESIGN** — chưa có khóa nào |
| Bảo vệ | Toàn vẹn + nguồn **gói** trong repo đã ký | Quản trị tin cậy cấp **bản phát hành**: vai trò/threshold/thời hạn/revocation/chống rollback-freeze-mix |
| Số khóa | Một tập keyring repo | Nhiều vai trò tách biệt (bảng §1) |
| Threshold | Không (một chữ ký repo là đủ) | Có (quorum cho root/targets) |
| Revocation bản phát hành | Không có | Có (danh sách thu hồi §4) |

**Khoảng cách:** apt GPG là **nền đủ** cho "gói đến từ Debian, không bị sửa", nhưng **thiếu** toàn bộ tầng vai trò/threshold/revocation cấp bản phát hành — đó là việc tầng 2 (TUF-grade) phải lấp, và nó **chưa tồn tại**.

## 3. Tách nhiệm vụ (Separation of Duties) + quy trình phát hành

Chống TA3 (khóa CI bị trộm) và lỗi nội bộ, ký một bản phát hành cần **nhiều vai trò người khác nhau** — không ai tự làm trọn:

1. **Người build** (developer/CI) tạo artifact + SBOM + provenance → **không** giữ khóa targets/root.
2. **Gate QA** (bộ kiểm thử PL15 §9) phải **đạt** trước khi ký — ký **sau** gate, không trước.
3. **Chủ trì phát hành** (release owner) duyệt + kích hoạt ký **targets** (cần quorum 2-trong-3).
4. **Ban quản trị khóa** chỉ can thiệp cho rotation/revocation vai trò (quorum root 3-trong-5), **không** tham gia phát hành hằng ngày.
5. **"Khẩn cấp" KHÔNG phải quyền bỏ kiểm** (PL15 §8): bản vá khẩn vẫn **bắt buộc chữ ký + rollback**, chỉ rút gọn test — không bypass QA cốt lõi, không ký bằng khóa ngoài quy trình.

## 4. Luân chuyển (Rotation) và thu hồi (Revocation)

| Tình huống | Hành động | Mã lỗi tới máy |
| --- | --- | --- |
| **Rotation định kỳ** | Theo hạn bảng §1; root ký ủy quyền khóa mới; máy cập nhật trust qua chuỗi metadata đã ký | — |
| **Khóa snapshot/timestamp/CI bị nghi lộ** | root (offline, quorum) thu hồi + cấp khóa mới; đẩy metadata mới; **không** cần dựng lại root trên máy đã cài | UPD-003 (nếu bản ký bằng khóa lộ bị từ chối) |
| **Khóa targets bị lộ** | Quorum root thu hồi targets, cấp mới; **thu hồi mọi bản** đã ký bằng targets lộ trong cửa sổ nghi ngờ | UPD-009 |
| **Khóa root bị lộ** (thảm họa) | Nghi thức khôi phục root: phân phối root mới **qua kênh ngoài-băng đã ký** (bản cập nhật trust đặc biệt / USB ngoại tuyến của IT); diễn tập trước | UPD-003/UPD-009 |
| **Một bản phát hành bị phát hiện lỗi/độc** | Thêm vào **danh sách thu hồi**; máy dừng rollout/cài, giữ hoặc rollback theo policy | UPD-009 |
| **Clock/NTP sai khiến không xác minh được thời hạn** | Máy báo "không xác minh được thời hạn", **không** âm thầm bỏ kiểm | UPD-004 |

**Danh sách thu hồi (revocation list):** là một phần metadata ký (tầng 2), thời hạn ngắn, đẩy tới mọi máy; máy offline lâu ngày phải **kiểm chain metadata + trạng thái khóa** trước khi lên bản mới (PL15 §8).

## 5. Khóa test/lab (cho U15-B) — tách tuyệt đối khỏi production

- Khi dựng verify-metadata ở U15-B, dùng **khóa lab** sinh tại chỗ, **gắn nhãn rõ** (ví dụ chuỗi `NAMIOS-LAB-DEV-DO-NOT-TRUST` trong tên/comment), **chỉ** dùng cho fixture + server giả.
- Khóa lab **không bao giờ** được phục vụ cho máy thật, **không** chung không gian với production, **không** commit private key vào repo (chỉ có thể commit **public** của khóa lab cho test, hoặc sinh runtime).
- Ca test bắt buộc (PL15 §9 nhóm Bảo mật): gói giả chữ ký, hash sai, metadata cũ/hết hạn, repo bị thay, **khóa thu hồi**, mirror độc hại → **100% bị chặn**, có mã lỗi, không bypass.

## 6. Việc phải làm để rời `specified` (điều kiện lên `partial`/`completed`)

1. **Chọn & kiểm định triển khai TUF** (thư viện/chứng thư được duy trì) — ADR 0007 §spike; ghi ADR phụ nếu chọn khác TUF.
2. **Sinh khóa lab + fixture** cho U15-B; chứng minh fail-closed trên 6 ca phản công.
3. **Thiết kế nghi thức khóa production** (ai giữ, HSM nào, quorum thật, nơi cất offline) — **chỉ làm khi có người + phần cứng thật**; hiện **BLOCKED** (chưa có HSM, chưa gán người cụ thể ngoài vai trò).
4. **Diễn tập** khóa lộ / CDN bị chiếm (U15-D) trước khi ký bản phát hành thật đầu tiên.

> **Nhắc lại:** mọi khóa ở đây là **thiết kế**. Không có khóa thật, không HSM, không production key. Không ghi "đã có quản lý khóa" cho tới khi nghi thức được thực thi + diễn tập trên hạ tầng thật.
