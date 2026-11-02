# T5 — Evidence / compat-gate / catalog — evidence (02/11/2026)

**Tester:** T5 (độc lập, không phải dev WP9/WP4). **Phạm vi:** MAN-04 (gate
"không task_verified khi thiếu evidence/QA approval"), UX-03 (tìm kiếm tiếng
Việt accent-insensitive, tên gốc giữ nguyên, revocation). Nhắm vào
`namios_evidence` (WP9) và `namios_catalog` (WP4).

**Test file:** `tests/qa/T5/test_t5_adversarial.py` (19 test, viết độc lập
với `tests/unit/evidence/*` và `tests/unit/catalog/*` của dev — không sao
chép case, không sửa file dev).

## Lệnh chạy

```
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/node/.openclaw/workspace/code_projects/namios/src \
/home/node/.openclaw/workspace/code_projects/namios/.venv/bin/python -m pytest \
  /home/node/.openclaw/workspace/code_projects/namios/tests/qa/T5 \
  -p no:cacheprovider -q
```

## Kết quả (commit `b0a96d6`, Python 3.11.2, Debian 12)

```
14 passed, 5 failed in ~0.3s
```

Không flaky (chạy lặp lại nhiều lần cho kết quả giống nhau — test không phụ
thuộc timing/race, chỉ logic thuần + filesystem thật trong `tmp_path`).

### Bất biến ĐANG ĐÚNG (14 test PASS)

- Gate KHÔNG tin field `decision` tự khai báo trong report khi `tests` thực
  tế chưa đủ (`not_run` hoặc toàn bộ `skipped`) — tính lại đúng từ dữ liệu
  `tests`/`qa_reviewer` thật, không phải từ nhãn tự xưng.
- Report có `tests=()` (hoàn toàn rỗng, không chỉ "không có required") →
  `untested`, không suy diễn ngầm là đã đủ.
- Case đối chứng traversal: `..` quay lại ĐÚNG trong cây cho phép (không
  thoát ra ngoài thật) vẫn đọc được bình thường — xác nhận các case FAIL ở
  dưới là do thoát ra ngoài thật, không phải do test chặn quá tay.
- Schema tier 1 chặn đúng unknown key ở các object LỒNG: `environment.*`,
  `qa_approval.*`, từng phần tử `tests[]` (dev mới test unknown key ở
  top-level).
- Type confusion: `required: "true"` (string) và `result: 1` (int) đều bị
  schema từ chối, không bị coerce ngầm.
- Catalog: `app_id` là khóa IDENTITY phân biệt hoa/thường (`"App-ABC"` ≠
  `"app-abc"`) — tách biệt đúng với tầng fold chỉ dùng cho SEARCH; revoke 1
  biến thể không ảnh hưởng biến thể khác.
- Catalog: file evidence quá khổ (> 2 MiB, nhồi qua `known_issues`) bị
  `read_text_safe` từ chối dù là JSON hợp lệ 100% — DoS-by-size được chặn
  TRƯỚC khi parse.
- Catalog: query Unicode dạng NFD (decomposed — xảy ra thật với một số
  bàn phím/IME) khớp đúng entry đã index ở dạng NFC (precomposed) — `fold_vn`
  xử lý đúng cả 2 chiều chuẩn hoá Unicode.
- Catalog: entry bị revoke vẫn trả về từ `list()`/`search()` (ghi nhận là
  THIẾT KẾ đã công bố trong docstring `InMemoryCatalogStore.revoke` — caller
  phải tự gọi `is_revoked()` — không phải lỗi mới phát hiện).

### Defects thật (5 test FAIL — xem `defects.md`)

1. **D1 — Path traversal `..` đọc được file NGOÀI phạm vi khi không có
   symlink nào tham gia** (2 test: trực tiếp `read_text_safe` và qua
   `EvidenceValidatorImpl.load`) — vi phạm trực tiếp CLAUDE.md "chống
   traversal ... không chỉ check '..'".
2. **D2 — Gate `compute_allowed_status` cấp `task_verified` cho
   `qa_reviewer=""` hoặc `"   "` (rỗng/chỉ khoảng trắng, không phải
   `None`)** (2 test) — gate không tự phòng thủ, chỉ an toàn nhờ schema
   tier-1 (`minLength:1`) chặn trước; vi phạm nguyên tắc "schema hợp lệ ≠ an
   toàn" áp ngược lại cho chính gate khi `EvidenceReport` được dựng trực
   tiếp (không qua `load()`).
3. **D3 — `InMemoryCatalogStore.search()` không chuẩn hoá khoảng trắng
   trong query** (1 test) — query có khoảng trắng kép/lỗi gõ phổ biến
   không khớp được entry mà query 1-khoảng-trắng khớp được; mức độ: chất
   lượng tìm kiếm (UX-006), không phải an toàn.

## Không chạy được tại đây (not applicable trong phạm vi T5)

Không có dòng `blocked_external_dependency`. Toàn bộ MAN-04 (gate) và UX-03
(search/revocation) chạy được bằng logic thuần + filesystem thật ngay tại
host này (Debian 12), không cần VM/Wine/bus thật.
