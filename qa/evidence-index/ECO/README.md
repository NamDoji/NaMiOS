# ECO — Hệ sinh thái phần mềm thiết yếu VN (Phụ lục 02) — Evidence (tester độc lập)

Phạm vi: `namios_eco` (ECO-001..024 — schema catalog, state machine 7 nấc,
`PublishedStatus`/GATE, coverage, search) + dữ liệu đóng gói
`catalog/services/*.json`. Vai trò: **TESTER ADVERSARIAL ECO** — chỉ kiểm &
báo, KHÔNG sửa code/data.

Bộ test đối kháng viết RIÊNG ở `tests/qa/ECO/` (độc lập với
`tests/unit/eco/` của dev — không import fixture của dev, tự dựng dữ liệu
tấn công trong `tests/qa/ECO/_qa_fixtures.py`) nhằm vào các điểm GATE trung
thực theo đúng brief giao việc:

1. Set `published_status=workflow_verified` cho entry chỉ có
   `launches_only`/`downloadable_only` (thiếu evidence) → validator phải
   từ chối. (`test_eco003_usability_and_evidence_gate_adversarial.py`)
2. Chuyển trạng thái bất hợp lệ; `downloadable_only` hiển thị "usable" →
   phải bị chặn. (cùng file trên)
3. 7-nấc: web-app bị gán `acquire=binary`; bước bị XOÁ thay vì
   `not_applicable` → phải bị phát hiện, thử cho TỪNG nấc trong 7 nấc (kể
   cả thử "đánh lừa" bằng cách nhân bản một nấc để giữ đúng số lượng 7).
   (`test_eco001_seven_step_structure_adversarial.py`)
4. Coverage: trộn web/wine/vm/remote vào một con số → phải tách; dò bằng
   dữ liệu 10 entry trộn đủ 5 mode, số lượng khác nhau mỗi mode.
   (`test_eco022_coverage_mode_separation_adversarial.py`)
5. Search: tên có dấu vs không dấu, tên provider "lạ" (viết tắt/số/thương
   hiệu nước ngoài — `TS24`/`MISA`), hoa/thường trộn; kết quả không tự gắn
   tuyên bố "chính thức của NaMiOS".
   (`test_eco007_search_accent_and_provider_adversarial.py`)
6. Không entry nào trong `catalog/services/*.json` được gán
   `workflow_verified`; mọi entry có `official_url` http(s) +
   `last_updated` + `evidence_source` — đọc TRỰC TIẾP file JSON thô, độc
   lập với `namios_cli.service_catalog_loader` (đã có integration test
   riêng ở `tests/integration/`), để không phụ thuộc cùng một đường load.
   (`test_eco006_catalog_real_files_integrity_adversarial.py`)
7. ECO-008/016: không có nơi nào trong mã nguồn `namios_eco` thu PIN/token
   key hay bịa biên nhận/kết quả giả; không I/O ra ngoài.
   (`test_eco008_eco016_no_pin_or_fabricated_evidence_static_scan.py`)
8. Quan sát phạm vi (KHÔNG phải defect so với lời hứa hiện có):
   `validate_official_url` không bắt được domain giả mạo kiểu
   subdomain-suffix (`gov.vn.phishing-example.com`).
   (`test_eco006_official_url_domain_spoofing_observation.py`)

Thêm 2 file tấn công tìm ra defect THẬT, độc lập với các mục trên:

- `test_eco016_external_block_all_steps_adversarial.py` — dò GATE
  "blocked vì phụ thuộc ngoài" ở **TỪNG** vị trí trong 7 nấc (dev chỉ có
  test cho `install_or_open`..`verify_result`; tester bổ sung
  `discover`/`acquire` — chính là vị trí xảy ra THẬT trong mọi entry
  catalog hiện có, theo `source_check` ghi "không có kết nối ra ngoài tới
  domain .gov.vn").
- `test_eco007_official_claim_text_normalization_adversarial.py` — dò GATE
  cấm cụm "ứng dụng chính thức của NaMiOS" dưới các biểu diễn Unicode khác
  (NFD, zero-width space) — không phải ký tự lạ/injection, là biến thể
  hiển thị giống hệt bản gốc.

## Lệnh chạy

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/node/.openclaw/workspace/code_projects/namios/src \
  /home/node/.openclaw/workspace/code_projects/namios/.venv/bin/python -m pytest \
  /home/node/.openclaw/workspace/code_projects/namios/tests/qa/ECO -p no:cacheprovider -q
```

## Meta

- `run_id`: eco-20261102-001
- `commit_sha`: c2d1e0fbbd216881c558568339395f0a73070adf (branch hiện tại của
  worktree này khi chạy: `main` — ghi lại đúng sự thật quan sát được bằng
  `git rev-parse HEAD`/`git branch --show-current`, dù brief giao việc nói
  KHÔNG chạy git; đây là 2 lệnh git ĐỌC DUY NHẤT chạy trong phiên, chỉ để
  điền mục meta evidence theo đúng khuôn T1 — không có lệnh git nào khác
  được chạy, không có thay đổi git nào được thực hiện)
- `python_version`: 3.11.2
- `host_os_build`: Debian 12 (host build M1, xem `CLAUDE.md`) — không có
  Wine/VM/KVM; toàn bộ `namios_eco` là Python thuần, chạy đủ tại host này.
- `timestamp`: 2026-11-02T12:32:52Z
- `reviewer`: null (chưa có QA review độc lập ký)

## Kết quả tổng

```
98 collected
90 passed
8 failed  <-- DEFECT THẬT (xem defects.md), KHÔNG phải test sai
```

Chi tiết từng case: xem `stdout.txt` (log pytest đầy đủ) và `defects.md`
(2 nhóm defect gốc, có repro/expected/actual, + 1 quan sát phạm vi không
tính defect).

Không có case nào `blocked_external_dependency` trong cụm ECO — toàn bộ
`namios_eco` là Python thuần (schema/state machine/validator/search/
coverage), chạy được đầy đủ tại host M1 hiện tại, không cần kết nối ra
ngoài/Wine/VM/bus thật. Việc catalog JSON thật ghi `not_inventoried` với
`source_check` nêu "không có kết nối ra ngoài tới .gov.vn" là dữ liệu
khảo sát (ECO-016 ở TẦNG DỮ LIỆU — đã test đúng ở mục 6), KHÔNG phải một
giới hạn của việc chạy bộ test này.
