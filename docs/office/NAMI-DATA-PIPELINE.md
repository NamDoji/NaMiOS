# NaMi Data Pipeline — prototype "Get & Transform tương đương" (M4)

Tài liệu này mô tả TRUNG THỰC một prototype dev ở `tools/namios-data/`: nó
chứng minh được khái niệm "pipeline biến đổi dữ liệu tái lập, có nguồn cục
bộ + cổng consent cho nguồn mạng" — KHÔNG phải là tính năng NaMiSheet, KHÔNG
phải "hỗ trợ Power Query", và KHÔNG nối vào bất kỳ UI nào.

Theo đúng:
- `docs/specs/namioffice-v2/02_WRITER_SHEET_SLIDES.md` §B, đoạn "F2 nhập và
  mô hình dữ liệu": *"Get & Transform tương đương gồm kết nối nguồn
  CSV/JSON/SQL/web có quyền, type inference có thể sửa, filter/merge/
  append/unpivot, bước biến đổi có thể tái lập, lịch sử, cache, secret vault
  và refresh. Data Model gồm quan hệ nhiều bảng, measures, DAX subset chỉ khi
  có implementation và differential test; **không tự nhận "hỗ trợ Power
  Query/Power Pivot" chỉ vì có CSV import hoặc Pivot đơn bảng**. Chặn truy
  vấn ngoài mạng khi mở tệp, yêu cầu consent nguồn và chỉ rõ dữ liệu sẽ
  gửi."*
- `docs/office/COMPAT-MATRIX.md`:
  - `SH-F2-01` (Power Query / Get & Transform) — **C3**: *"Calc KHÔNG có
    Power Query... không phải pipeline M-steps"* → *"Cần pipeline ETL mở
    riêng (engine/sản phẩm) — không khả thi bằng fork"*. Ghi chú gate:
    *"Không tự nhận 'hỗ trợ Power Query' chỉ vì có CSV import"*.
  - `SH-F2-02` (Data Model / Power Pivot / DAX) — **C3**: *"Calc KHÔNG có
    Data Model/DAX"* → *"Engine mô hình dữ liệu riêng — không khả thi bằng
    fork"*.
  - `SH-F2-03` (chặn truy vấn mạng khi mở + consent nguồn dữ liệu) — **C2**,
    **Gate P0**: *"không mở kết nối ngoài ngoài ý muốn"*.

Prototype này **không nâng hạng C3 nào lên C-cao-hơn** (NaMiSheet/Calc vẫn
KHÔNG có Power Query/Power Pivot thật) — nó chỉ chứng minh phần "pipeline ETL
mở riêng" mà COMPAT-MATRIX nói là hướng khả thi duy nhất, và implement thật
luôn phần Gate P0 (SH-F2-03) ở mức logic lõi (chưa nối UI mở-tệp thật, vì
NaMiSheet/Calc chưa tồn tại).

## 1. Prototype làm được gì (ĐÃ CHẠY + CÓ TEST)

Code ở `tools/namios-data/` (7 module thuần Python + 1 demo + bộ pytest):

| Module | Vai trò |
|---|---|
| `table.py` | `Table` bất biến: cột theo thứ tự + dtype/cột + dòng; `content_hash()` để so "giống hệt" |
| `typeinfer.py` | Suy luận dtype (int/float/bool/date/str) từ dữ liệu thô CSV/JSON, **ghi đè được** qua `type_overrides` |
| `consent.py` | Cổng đồng ý: nguồn cục bộ (csv/json) luôn qua; nguồn mạng (sql/web) **chặn mặc định**, thông báo nêu đúng dữ liệu sẽ gửi/nhận |
| `sources.py` | Đọc CSV/JSON cục bộ thành `Table` đã ép kiểu; gọi `consent.check_consent` trước khi đọc bất kỳ nguồn nào |
| `steps.py` | 7 bước biến đổi THUẦN, tự JSON hoá: `FilterStep`, `SelectStep`, `RenameStep`, `MergeStep` (join inner/left), `AppendStep` (union), `UnpivotStep` (melt), `GroupByStep` (sum/count/avg/min/max) |
| `pipeline.py` | `Pipeline`: 1 nguồn chính + N nguồn phụ đặt tên + danh sách bước có thứ tự; `run()`/`refresh()` (alias — đọc lại nguồn + replay toàn bộ bước); `to_json()`/`from_json()`; `history` (ts + số dòng + hash mỗi lần chạy) |
| `xlsx_writer.py` | Ghi `Table` kết quả ra MỘT sheet `.xlsx` (openpyxl, giữ kiểu ngày/số thật) |
| `demo.py` | Chạy tay end-to-end: sinh 2 CSV đơn hàng theo tháng + 1 JSON tra cứu ngành hàng → filter → append → merge → group_by, cộng một pipeline unpivot riêng; ghi `.xlsx`; tự so hash sau khi serialize→reload→replay |

### Luồng "Get & Transform tương đương" thật sự chạy được

1. **Get**: đọc CSV/JSON **cục bộ** (không ra mạng bao giờ với 2 loại này).
2. **Type inference có thể sửa**: tự đoán dtype theo cột (ưu tiên
   bool > int > float > date > str, chỉ nhận một dtype nếu MỌI giá trị
   không-rỗng đều hợp lệ với nó); người dùng override bất kỳ cột nào qua
   `SourceSpec(type_overrides={...})` TRƯỚC khi ép kiểu thật — ví dụ giữ mã
   học sinh `"001"` là chuỗi thay vì bị đoán thành số `1` (mất số 0 đầu).
3. **Transform**: filter / select / rename / merge (join) / append (union)
   / unpivot (melt) / group-by (sum/count/avg/min/max) — mỗi bước là một
   dataclass bất biến, hàm `apply()` THUẦN (không sửa input, luôn trả object
   mới).
4. **Bước có thể tái lập + lịch sử**: `Pipeline.to_json()` ghi lại TOÀN BỘ
   định nghĩa (nguồn + nguồn phụ + danh sách bước, đúng thứ tự) ra JSON;
   `Pipeline.from_json()` nạp lại thành một `Pipeline` **object hoàn toàn
   mới**; gọi `.run()` trên object đó phải ra **đúng cùng nội dung** (so bằng
   `content_hash()` SHA-256 trên cột+dtype+từng dòng theo thứ tự) như lần
   chạy gốc. `Pipeline.history` là danh sách các lần `run()` thật (thời
   điểm, số dòng, hash) — khác với `Pipeline.steps` (định nghĩa bước).
5. **Refresh**: `refresh` là alias trực tiếp của `run` — đọc lại nguồn từ
   đĩa (bắt được thay đổi nếu file nguồn đổi) rồi replay lại toàn bộ bước.
   Không có "trạng thái cache ngầm" nào khác biệt refresh với run-lần-đầu,
   vì mọi bước là hàm thuần.
6. **Consent nguồn mạng**: `SourceSpec(kind="sql"|"web", ...)` luôn đi qua
   `consent.check_consent()` trước khi đọc; thiếu `consent=True` tường minh
   ⇒ `ConsentRequiredError` kèm nguyên văn "sẽ gửi gì / sẽ nhận gì" (xem mục
   3). Một pipeline có MỘT nguồn phụ mạng mà `Pipeline.consent=False` (mặc
   định) thì `run()` ném lỗi ngay, KHÔNG chạy lọt bước nào — test
   `test_pipeline_run_propagates_consent_gate_for_aux_network_source`.

### Kết quả test

```
$ python3 -m pytest tools/namios-data/tests -v
...
tools/namios-data/tests/test_build_pipeline.py::test_build_pipeline_filter_select_rename PASSED
tools/namios-data/tests/test_build_pipeline.py::test_type_inference_is_editable_via_override PASSED
tools/namios-data/tests/test_consent_gate.py::test_local_sources_never_require_consent PASSED
tools/namios-data/tests/test_consent_gate.py::test_network_source_blocked_without_consent PASSED
tools/namios-data/tests/test_consent_gate.py::test_web_source_blocked_without_consent PASSED
tools/namios-data/tests/test_consent_gate.py::test_consent_notice_names_exact_data_sent_and_received PASSED
tools/namios-data/tests/test_consent_gate.py::test_read_source_sql_blocked_end_to_end_without_consent PASSED
tools/namios-data/tests/test_consent_gate.py::test_read_source_sql_with_consent_is_still_not_wired_to_a_real_client PASSED
tools/namios-data/tests/test_consent_gate.py::test_pipeline_run_propagates_consent_gate_for_aux_network_source PASSED
tools/namios-data/tests/test_replay.py::test_serialize_reload_replay_identical PASSED
tools/namios-data/tests/test_replay.py::test_run_twice_same_pipeline_object_is_also_identical PASSED
tools/namios-data/tests/test_replay.py::test_refresh_picks_up_changed_source PASSED
tools/namios-data/tests/test_transforms.py::test_unpivot_correctness PASSED
tools/namios-data/tests/test_transforms.py::test_unpivot_rejects_unknown_column PASSED
tools/namios-data/tests/test_transforms.py::test_merge_inner_correctness PASSED
tools/namios-data/tests/test_transforms.py::test_merge_left_keeps_unmatched_with_nulls PASSED
tools/namios-data/tests/test_transforms.py::test_merge_rejects_unknown_aux_table PASSED
tools/namios-data/tests/test_transforms.py::test_merge_then_groupby_pipeline_end_to_end PASSED
tools/namios-data/tests/test_transforms.py::test_append_requires_matching_schema PASSED
tools/namios-data/tests/test_transforms.py::test_filter_select_rename_pure_do_not_mutate_input PASSED

============================== 20 passed in 0.12s ==============================
```

20/20 PASS, bao đủ 4 yêu cầu test trong đề bài: (a) dựng pipeline trên CSV
mẫu + assert output (`test_build_pipeline.py`), (b) serialize→reload→replay
→giống hệt (`test_replay.py`, cả khi nguồn KHÔNG đổi và khi nguồn CÓ đổi —
refresh phải đọc lại đúng), (c) unpivot + merge đúng (`test_transforms.py`,
kèm append/group_by/filter/select/rename từng bước riêng để không tuyên bố
"7 bước hoạt động" mà thiếu test), (d) consent-gate chặn nguồn mạng
(`test_consent_gate.py`, cả khi KHÔNG đồng ý và một chú ý quan trọng: kể cả
KHI đồng ý, sql/web vẫn `NotImplementedError` vì chưa có client thật — xem
mục 2).

### Demo chạy tay (không phải test, để xem bằng mắt)

```
$ python3 tools/namios-data/demo.py
=== sales_by_category ===
Category | TotalAmount | OrderCount
Văn phòng | 1290000 | 3
Điện tử | 1350000 | 2
-> wrote tools/namios-data/out/sales_by_category.xlsx
replay hash khớp: 94ea0ac65d2b966e...

=== sales_unpivoted ===
Region | Quarter | Sales
Bắc | Q1 | 100
...
-> wrote tools/namios-data/out/sales_unpivoted.xlsx
```

`sales_by_category.xlsx` sinh từ: 2 CSV đơn hàng theo tháng (filter Qty>0 →
append gộp 2 tháng) → merge với JSON tra cứu ngành hàng → group-by theo
ngành hàng (sum Amount, count đơn). Số liệu đã kiểm tay: Văn phòng =
900.000+260.000+130.000=1.290.000 (3 đơn), Điện tử = 450.000+900.000=
1.350.000 (2 đơn) — khớp output.

## 2. KHÔNG phải (ranh giới trung thực)

- **KHÔNG phải Power Query / ngôn ngữ M**: không có cú pháp M, không có UI
  "Query Editor" kéo-thả, không đọc/viết được file `.pq`/`Section1.m`. 7
  loại bước ở `steps.py` là một tập CỐ ĐỊNH do code Python định nghĩa —
  không cho viết biểu thức M tuỳ ý (Power Query cho phép công thức M bất kỳ,
  bao gồm cả custom function). Đây là lựa chọn CÓ CHỦ Ý để giữ mọi bước
  thuần/an toàn/replay được mà không cần xây một engine ngôn ngữ đầy đủ —
  không phải một thiếu sót tạm thời sẽ "thêm sau cho giống Power Query".
  → Giữ nguyên phân loại **C3** của `SH-F2-01`.

- **KHÔNG phải Power Pivot / Data Model / DAX**: không có khái niệm quan hệ
  nhiều bảng dạng mô hình (star schema), không có measures, không có engine
  DAX, không differential test đối chiếu DAX với Excel thật. `MergeStep`
  trong prototype là join MỘT-LẦN sinh ra MỘT bảng kết quả phẳng (giống
  `JOIN` SQL), không phải một "relationship" sống có thể dùng trong nhiều
  measure khác nhau. → Giữ nguyên phân loại **C3** của `SH-F2-02`. Theo đúng
  câu gốc trong spec kit: *"không tự nhận 'hỗ trợ Power Query/Power Pivot'
  chỉ vì có CSV import hoặc Pivot đơn bảng"* — prototype này có CSV import
  **và** một dạng "Pivot đơn bảng" (group-by), nên theo đúng câu đó, **VẪN
  KHÔNG được gọi là "hỗ trợ Power Query/Power Pivot"**.

- **KHÔNG có client SQL/web thật**: `SourceSpec(kind="sql"|"web")` đi qua
  được cổng consent (nếu `consent=True`) nhưng `sources.read_source()` ném
  `NotImplementedError` ngay sau đó — chưa có bất kỳ thư viện HTTP/DB driver
  nào được nối. Cố ý làm vậy để KHÔNG lặng lẽ trả về `Table` rỗng/giả như
  thể đã kết nối thành công. Nếu sau này nối thật, phải: (a) chọn + ghim
  version driver, (b) viết test có fixture/stub mạng (không gọi Internet
  thật trong CI), (c) mở secret vault riêng (hiện CHƯA có — xem mục dưới).

- **KHÔNG có secret vault**: spec kit nhắc "secret vault" cho nguồn cần
  thông tin đăng nhập. Vì sql/web chưa có client thật, cũng chưa có secret
  nào cần lưu — `SourceSpec.options` là dict JSON thường (không mã hoá),
  **không được dùng để lưu mật khẩu/token thật**. Thêm secret vault là việc
  CẦN LÀM TRƯỚC khi nối sql/web thật, không phải sau.

- **KHÔNG có cache đĩa riêng**: nguồn cục bộ đọc lại rất rẻ nên `refresh()`
  luôn đọc lại từ đĩa; không có tầng cache "giữ bản cũ khi nguồn không truy
  cập được" (spec kit F1 có nhắc yêu cầu này cho Pivot refresh — prototype
  M4 này KHÔNG implement nó).

- **KHÔNG nối vào NaMiSheet/Calc UI**: đây là module Python độc lập trong
  `tools/namios-data/`, chạy bằng dòng lệnh/pytest. KHÔNG có UI Query Editor,
  KHÔNG có nút "Refresh" trong một spreadsheet, KHÔNG đọc/viết `.xlsx` có
  "Query" object native của Excel (`xl/queries/*.xml`,
  `customXml/item*.xml`) — `xlsx_writer.py` chỉ ghi GIÁ TRỊ tĩnh ra một
  sheet, không kèm định nghĩa truy vấn nào trong file. Mở file `.xlsx` xuất
  ra bằng Excel/Calc sẽ thấy một bảng số liệu bình thường, KHÔNG thấy
  "Queries & Connections".

- **KHÔNG kiểm thử bằng soffice/Excel thật**: toàn bộ test là unit test
  Python đối chiếu logic Python (giống self-check của
  `tools/office-compat/README.md`, không phải round-trip qua LibreOffice
  Calc/Microsoft Excel). File `.xlsx` xuất ra CHƯA được mở lại bằng
  LibreOffice/Excel thật để xác nhận mở được — chỉ xác nhận mở lại được bằng
  `openpyxl.load_workbook()` (xem mục 1).

## 3. Quy tắc consent nguồn dữ liệu + "chỉ rõ dữ liệu sẽ gửi"

Theo yêu cầu `SH-F2-03` (Gate P0) + câu "yêu cầu consent nguồn và chỉ rõ dữ
liệu sẽ gửi" trong spec kit:

1. **Nguồn cục bộ (csv/json) không bao giờ cần consent** — vì không có gì
   rời khỏi máy. `consent.describe("csv", path)` trả về thông báo nói rõ
   `"(không có gì — nguồn cục bộ, không ra mạng)"`.
2. **Nguồn mạng (sql/web) bị chặn theo mặc định** (`consent=False` là giá
   trị default của cả `read_source()` và `Pipeline.consent`) — không có cờ
   toàn cục "luôn đồng ý"; mỗi `Pipeline`/mỗi lệnh đọc phải tự đặt
   `consent=True` một cách tường minh.
3. **Thông báo consent nêu CHÍNH XÁC** (không nói mơ hồ "sẽ kết nối
   Internet"): `ConsentNotice.will_send` ghi rõ địa chỉ/chuỗi kết nối +
   câu truy vấn (nếu có) sẽ RỜI khỏi máy; `will_receive` ghi rõ đây là "dữ
   liệu trả về từ nguồn mạng đó (không kiểm soát được nội dung)" — không
   giả vờ biết trước nội dung trả về.
4. **Một pipeline hỗn hợp (nguồn chính cục bộ + nguồn phụ mạng) vẫn bị chặn
   đúng ở nguồn phụ** nếu thiếu consent — không có "đường tắt" nào bỏ qua
   cổng chỉ vì nguồn mạng không phải nguồn chính (test
   `test_pipeline_run_propagates_consent_gate_for_aux_network_source`).
5. **Dù có consent, sql/web vẫn chưa hoạt động thật** (mục 2) — consent chỉ
   mở cổng LOGIC, không tự động nghĩa là có kết nối mạng chạy được. Đây là
   khác biệt quan trọng cần giữ khi tài liệu hoá: "có consent-gate" ≠ "có
   kết nối mạng/SQL hoạt động".

## 4. Việc cần làm tiếp (ngoài phạm vi M4, không tự nhận đã xong)

- Nối `tools/namios-data/` vào một UI thật khi NaMiSheet có khung ứng dụng
  (không có trong phạm vi hiện tại — "môi trường build hiện tại... M4 (app
  thương mại) BLOCKED" theo `CLAUDE.md`).
- Nếu quyết định mở sql/web thật: chọn driver, viết test có stub mạng (CI
  không gọi Internet thật), dựng secret vault, và PHẢI retest lại toàn bộ
  cổng consent với client thật (test hiện tại chỉ test cổng, không test
  client vì client chưa tồn tại).
- Data Model/DAX (`SH-F2-02`) là một hạng mục HOÀN TOÀN khác — cần một engine
  tính toán quan hệ nhiều bảng + differential test với Excel/Power BI thật,
  không phải mở rộng từ `MergeStep`/`GroupByStep` hiện tại (chúng sinh bảng
  phẳng một lần, không phải relationship sống).
- Ngôn ngữ M / UI Query Editor kéo-thả (nếu một ngày muốn gần Power Query
  hơn) là một hạng mục engine riêng, không phải thêm bước vào `steps.py`.

## 5. Chạy lại để tự kiểm chứng

```bash
cd /home/node/.openclaw/workspace/code_projects/namios
python3 -m pytest tools/namios-data/tests -v   # 20 passed
python3 tools/namios-data/demo.py               # in kết quả + ghi .xlsx
```
