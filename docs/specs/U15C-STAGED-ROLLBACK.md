# U15-C — Staged deployment, boot-health và auto-rollback (NaMiOS Update Center)

- **Ngày:** 09/11/2026 · **Năng lực:** Phụ lục 15 — **U15-C "Transaction/rollback"** (PL15 §5, §9).
- **Trạng thái thực thi:** `partial` — **PROTOTYPE/SIMULATION mức VM/thư-mục, chạy + test được bằng pytest; CHƯA nối bootloader/apt thật, CHƯA chạy trên phần cứng.**
- **Mã nguồn:** `tools/update-center-prototype/` — `staged_deploy.py`, `boot_health.py`, `fault_inject.py`, `tests/test_u15c_staged_rollback.py` (dựng trên U15-B: `update_contract.py`, `update_service.py`, `sign_test_repo.py`).
- **Liên quan:** ADR 0014 (snapshot Timeshift + rollback + health check), ADR 0017 (kiến trúc Update Service + ranh giới UI/Service/SmartAI), ADR 0007 (ký metadata fail-closed), PL15 §5/§7/§9.

Tài liệu này mô tả MÔ HÌNH staged/boot-health/rollback/migration đã hiện thực trong prototype, cách nó ÁNH XẠ vào thực tế Debian + Timeshift, và **khoảng trống trung thực** còn lại trước khi được coi là "đã có".

---

## 1. Chạy và kiểm thử

```bash
cd tools/update-center-prototype
python3 -m pytest -q                 # 66 pass: 33 (U15-B) + 33 (U15-C)
python3 fault_inject.py              # in bảng fault-injection + luồng sạch + health-fail
python3 update_service.py            # demo luồng U15-B (hợp lệ + payload bị sửa → UPD-003)
```

Không dùng khóa sản phẩm: repo test sinh cặp khóa ed25519 dùng-một-lần (`sign_test_repo.py`, nhãn TEST-ONLY).

---

## 2. Mô hình staged deployment (`staged_deploy.py`)

### 2.1 Nguyên tắc (PL15 §5)

> *"Trình cài **staged** vào phiên bản mới thay vì ghi nửa vời lên hệ đang chạy. ... không xóa deployment cũ cho tới khi bản mới qua cửa kiểm."*

`DeploymentStore` mô phỏng một tập deployment A-B trên thư mục:

```
root/
  deployments/<dep_id>/payload           # ảnh hệ điều hành của bậc đó
  deployments/<dep_id>/deployment.json    # {build, hash, confirmed, failed, created_ns}
  default                                 # CON TRỎ (1 dòng dep_id) — đổi NGUYÊN TỬ
  data/                                   # mô phỏng /home — staging KHÔNG đụng
```

Ba bất biến then chốt:

1. **Chuẩn bị tách biệt, không ghi nửa vời.** `prepare()` chép payload đã-xác-thực vào thư mục `.staging-*` tạm, fsync, rồi **đổi tên nguyên tử** (`os.replace`) sang `deployments/<dep_id>`. Thư mục deployment THẬT chỉ xuất hiện khi đã đủ byte + hash khớp. Mất điện giữa prepare ⇒ chỉ còn `.staging` dở → `recover()` dọn → **không bao giờ có deployment-thật-nửa-vời**.
2. **Đổi con trỏ default nguyên tử.** `set_default()` ghi file `default` qua `tmpfile + fsync + os.replace` (rename POSIX nguyên tử). Con trỏ luôn trỏ tới một deployment HOÀN CHỈNH; không có trạng thái con-trỏ-nửa. `set_default` **từ chối** trỏ sang deployment chưa hoàn chỉnh.
3. **Giữ bản cũ tới khi bản mới qua cửa kiểm.** `prepare`/`arm_switch`/`rollback`/`confirm` **không bao giờ xóa** deployment nào. `confirm()` chỉ đánh dấu `confirmed=True`. Việc dọn bản rất cũ là `prune_old(keep_last_confirmed>=2)` riêng, luôn giữ default + bản confirmed gần nhất làm đường quay lui.

### 2.2 Luồng (nối tiếp hợp đồng §7)

```
verified ──prepare()──▶ staged ──arm_switch()──▶ reboot_pending ──boot_health──▶ completed
   │  (deployment mới riêng,   (ĐỔI con trỏ default                     │
   │   default vẫn = bản cũ)    nguyên tử sang bản mới,                  └─(health fail)─▶ rolled_back
   │                            GIỮ bản cũ confirmed)
   └─(migration không an toàn)─▶ blocked (UPD-010)
```

- `arm_switch` chuyển `staged → reboot_pending` và đặt `default = bản mới` (chưa `confirmed`). Vì bản cũ vẫn còn + `confirmed`, mọi đường khôi phục/rollback luôn có đích về.
- "`completed` chỉ tới từ `boot_check`" được giữ nguyên từ U15-B — **không tự nâng `completed` vì một tool trả success** (PL15 §7).

### 2.3 Khôi phục sau mất điện (`recover()`)

Chạy khi "bật máy lại": (a) dọn mọi `.staging-*`/`.tmp-*`; (b) đọc `default`; (c) nếu default trỏ tới bản **chưa `confirmed`** hoặc **không hoàn chỉnh** → tự đổi về **bản `confirmed` gần nhất** (rollback kiểu greenboot/boot-counter), đánh dấu bản dở là `failed`. Hệ quả: nếu mất điện ngay sau khi flip con trỏ sang bản mới nhưng trước khi xác nhận health, máy boot lại bằng bản cũ confirmed.

### 2.4 Migration guard (PL15 §5 — dữ liệu)

> *"Rollback OS không đồng nghĩa rollback dữ liệu cá nhân. ... migration phải versioned, có thử dry-run, tương thích tiến/lùi hoặc kế hoạch phục hồi riêng."*

`MigrationGuard.assess(migration, backup)` **fail-closed**. CHO đi tiếp CHỈ KHI:
1. Có `BackupProof` đã **tạo** VÀ `restore_verified=True` (dry-run restore ra đúng hash) — không chấp nhận "đã tạo backup" mà chưa kiểm khôi phục.
2. Migration có `dry_run_ok=True`.
3. Nếu migration **một chiều** (không `forward_backward_compatible`, không `reversible`) thì backup phải **phủ** đúng `data_paths` (đường phục hồi duy nhất).

Thiếu bất kỳ điều kiện nào ⇒ `MigrationDecision(allowed=False, error_code="UPD-010")`. `StagedDeployer.prepare` khi đó trả contract `blocked` + `UPD-010`, đặt `preflight.backup="fail"`, và **KHÔNG tạo deployment** (giữ bản hiện tại) — đúng PL15 §7 bảng mã lỗi: *"UPD-010 — Migration dữ liệu không an toàn → Chặn update, yêu cầu backup và kế hoạch chuyển đổi."* Không migration (None) ⇒ an toàn, không cần backup.

---

## 3. Boot health-check (`boot_health.py`)

### 3.1 Bộ probe (PL15 §5)

`{kernel_up, login_ok, data_mount, basic_network, ui_not_crash_loop, update_service_responds}`.

- **Probe tới hạn** (hỏng bất kỳ → fail ngay): `kernel_up`, `login_ok`, `data_mount`, `update_service_responds`.
- **Ngưỡng điểm:** số probe đạt ≥ `pass_threshold` (mặc định 5/6).
- **UI crash-lặp luôn fail** dù điểm cao.
- **Ngưỡng số lần boot:** cho boot lại tối đa `max_boot_attempts` (mặc định 3, kiểu boot-counter/greenboot); hết lần mà chưa "healthy" ⇒ health FAIL.

### 3.2 Ánh xạ kết quả

- **Đạt** → `confirm(bản mới)` + contract `boot_check → completed`; **bản cũ KHÔNG bị xóa** (vẫn là rollback target).
- **Fail** → `rollback_to_previous(bản mới)` (đổi con trỏ default về bản trước, đánh dấu bản mới `failed`, **không xóa**) + contract `boot_check → rolled_back`. Mã **UPD-008** nằm ở `HealthReport.error_code` / lớp báo cáo, **không** gắn vào contract (vì `error_code` chỉ đi cùng `blocked` theo §7 — `rolled_back` là kết quả bình thường của cửa kiểm, không phải lỗi an ninh).

**Không bao giờ** tự nâng `completed` khi health chưa đạt. Một boot-check fail luôn cho `rolled_back`, không bao giờ `completed`.

---

## 4. Fault-injection harness (`fault_inject.py`)

`UpdateCampaign` dựng: repo ký giả + `UpdateService` (U15-B) + `DeploymentStore` A-B (bản cũ confirmed) + 3 tệp dữ liệu thử có hash + `StagedDeployer` + `BootHealthChecker`. "Mất điện" = **dừng đột ngột** (bỏ trạng thái RAM) rồi **dựng lại store/service TỪ ĐĨA + `recover()` + resume journal** — đúng như máy mất điện rồi bật lại.

Ma trận đã hiện thực (13 ca), phủ **mất điện ở TỪNG pha** + đầy ổ + kill updater + đứt mạng:

| Pha tiêm sự cố | Sự cố | Kết cục sau khôi phục |
| --- | --- | --- |
| download | power_loss / network_drop / killed_updater / disk_full | giữ `.part`, hệ đang chạy (bản cũ) boot được; resume được |
| verify | power_loss / killed_updater | chưa chuẩn bị deployment nào; bản cũ boot được |
| stage | power_loss / disk_full / killed_updater | còn `.staging` dở → recover dọn; deployment thật chưa xuất hiện; bản cũ boot được |
| deployment-switch | power_loss / killed_updater | con trỏ có thể đã sang bản mới (chưa confirmed) → recover quay về **bản cũ confirmed** |
| boot_check | power_loss / killed_updater | bản mới chưa confirmed → recover quay về **bản cũ confirmed** |

**Mọi ca** kết thúc thỏa (kiểm trong test `test_fault_recovers_bootable_data_intact_no_half_install`):
- `bootable == True` (default trỏ tới deployment hoàn chỉnh), bản mới HOẶC bản trước;
- `data_intact == True` (3 tệp `data/` giữ đúng hash — staged KHÔNG đụng `/home` mô phỏng);
- `half_installed == False` (không deployment-thật-dở, không `.staging` sót).

### 4.1 "Không bao giờ nửa cài / luôn boot được / dữ liệu đúng hash" được bảo đảm thế nào

- **Không nửa cài:** deployment thật chỉ ra đời bằng **rename nguyên tử** của thư mục `.staging` đã-đủ-byte-và-đúng-hash; `has_half_installed()` coi là vi phạm nếu còn `.staging` hoặc có deployment thật mà `sha256(payload) ≠ hash đã ghi`. `recover()` dọn `.staging` trước khi kết luận.
- **Luôn boot được:** con trỏ `default` chỉ đổi qua `os.replace` (nguyên tử) và chỉ sang bản hoàn chỉnh; bản cũ `confirmed` **không bị xóa** cho tới khi bản mới qua health; `recover()` tự fallback về bản `confirmed` gần nhất khi default chưa qua kiểm.
- **Dữ liệu đúng hash:** mô hình staged OS **không ghi vào vùng dữ liệu** (`data/`); thay đổi dữ liệu chỉ qua `MigrationGuard` (chặn nếu thiếu backup kiểm-khôi-phục). Test `test_data_files_never_touched_by_staging` chốt hash trước/sau = nhau.

---

## 5. Ánh xạ vào thực tế Debian + Timeshift (ADR 0014 / 0017)

Prototype là **mô hình trừu tượng**; trên NaMiOS alpha (Debian 13 + KDE Plasma 6, ext4, Calamares) nó ánh xạ thế này:

| Khái niệm prototype | Hiện thực thật trên NaMiOS (ADR 0014/0017) |
| --- | --- |
| "Deployment riêng" (A-B slot) | **Timeshift snapshot (rsync, hardlink cho ext4)** trước-update + `apt` staged-apply. **KHÔNG phải A-B nguyên tử thật** (ADR 0014: apt không nguyên tử). |
| `set_default()` đổi con trỏ nguyên tử | Đặt **GRUB default entry** + boot-counter kiểu greenboot; mục GRUB "NaMiOS — Khôi phục (recovery)" cho hệ đã cài (ADR 0014 §GRUB recovery). |
| `recover()` fallback về bản confirmed | Boot vào snapshot trước-update / `dpkg --configure -a` / `timeshift --restore`; health-check lúc boot (`namios-health-check.service`). |
| `BootHealthChecker` probe | `namios-health-check.sh`: `dpkg --audit`, `systemctl is-system-running`, `mountpoint /home`, ping gateway, đếm restart `plasmashell`, D-Bus ping `namios-update-service`. |
| `MigrationGuard` + `BackupProof` | Backup `/home` bằng **Kup + bup** (tách quyền, U13-03) + snapshot hệ thống; dry-run restore phải kiểm thật. |
| `StagedDeployer`/`UpdateService` | Daemon đặc quyền **`namios-update-service`** polkit-gated, argv tĩnh (ADR 0017); Update Center chỉ là UI; SmartAI chỉ-đọc. |
| Repo ký + verify (U15-B) | apt GPG (gói) + **release-index kiểu TUF** (quản trị tin cậy cấp bản phát hành) — còn là thiết kế, chưa có khóa thật (ADR 0017 §Hai tầng tin cậy). |

**Khác biệt bản chất phải nhớ:** prototype mô phỏng **A-B nguyên tử** (hai slot + con trỏ rename); NaMiOS alpha thực tế là **snapshot + rollback mức ảnh**, KHÔNG nguyên tử. Mất điện giữa một transaction `dpkg` thật có thể để gói ở trạng thái half-configured; đường phục hồi là snapshot trước-update, **không** phải "bật lại A-B tức thì". Prototype cố tình mạnh hơn thực tế ở điểm này để đặc tả hành vi ĐÍCH; không được đọc ngược thành "NaMiOS đã có A-B nguyên tử".

---

## 6. Khoảng trống trung thực — còn lại cho U15-C/D trên MÁY THẬT

**Đây là SIMULATION. KHÔNG có gì được kiểm trên phần cứng.** Để U15-C được coi là đạt (PL15 §9 hàng "Độ tin cậy" + cửa gate §9), còn phải:

1. **Nối probe + staged thật:** viết `namios-update-service` thật bọc apt + Timeshift + GRUB; viết probe health đọc trạng thái hệ thật (dpkg/systemd/mount/mạng/plasmashell/D-Bus); nối rollback vào GRUB default + `timeshift --restore`.
2. **Fault-injection trên VM thật:** chạy lại ma trận §4 trên máy ảo QEMU với `apt upgrade` thật + cắt nguồn ảo ở từng pha; kiểm `dpkg --audit` sạch sau phục hồi và hash `/home` còn nguyên.
3. **5 máy pilot (PL15 §5, §9):** máy cũ, NVMe/SATA, ổ mã hóa, dual-boot Windows, mạng chậm, pin yếu — gồm **RÚT ĐIỆN THẬT** giữa update, đổ đầy ổ, và gói hỏng; quay **video rollback** làm bằng chứng.
4. **Timeshift chưa cấu hình:** honest-case khi máy chưa chọn ổ snapshot → KHÔNG có điểm rollback lần đó; health-check phải cho người dùng thấy, update bảo mật vẫn không bị chặn (ADR 0014 §Trung thực).
5. **Migration thật:** guard hiện là lớp QUYẾT ĐỊNH (chặn/cho), chưa thực thi migration; cần nối backup Kup/bup thật + dry-run restore thật trước khi cho một migration chạy trên dữ liệu người dùng.
6. **Hai tầng metadata (apt GPG + release-index TUF):** release-index nhiều vai trò/threshold/revocation vẫn là thiết kế; phải test ca lệch-đồng-bộ giữa hai tầng.

Chừng nào chưa chạy đủ fault-injection trên VM rồi 5 máy pilot (gồm mất điện thật), U15-C vẫn là `partial` — **không** được ghi `completed`, **không** được quảng cáo "rollback nguyên tử" hay "updater đã có" (PL15 §10, ADR 0014 §"Điều kiện để lên completed").
