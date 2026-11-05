# Kiến trúc NaMiOS — bản đồ cho người đóng góp

> Tài liệu này là **mô hình tư duy** để một người mới đọc hiểu NaMiOS trong ~15 phút,
> biết code nằm ở đâu, quy tắc bất biến nào không được phá, và ranh giới nào đang
> `BLOCKED` (chưa làm được vì thiếu hạ tầng, **không phải vì lười hay giấu**).
>
> English summary at the bottom. Đặc tả đầy đủ: [`specs/DAC_TA_HE_DIEU_HANH.md`](specs/DAC_TA_HE_DIEU_HANH.md).

## 1. NaMiOS là gì (một câu)

Một bản phân phối Linux (Debian 13 + KDE) tiếng Việt, **cộng thêm một lớp phần mềm Python**
giúp người Việt chạy các tác vụ Windows thiết yếu (Word/Excel, Zalo, MISA, app .NET) theo
**hồ sơ tương thích được kiểm chứng** — chứ không hứa suông "chạy mọi app Windows".

## 2. Nguyên tắc BẤT BIẾN (đọc trước khi viết dòng code đầu tiên)

Mọi module đều phải giữ các bất biến sau. Test đối kháng trong `tests/security/` tồn tại
để **cố tình phá** chúng — nếu bạn làm gãy một bất biến, CI sẽ đỏ.

1. **LỜI AI ≠ SỰ THẬT.** Trạng thái chỉ cập nhật từ **kết quả tool** (`ToolResult`), không
   từ văn bản mô hình. AI *đề xuất*; policy + evidence + con người *quyết định*.
2. **Không nhãn "đạt" khi chưa có bằng chứng.** Thiếu môi trường/bộ cài → ghi `blocked`,
   không bịa. Không có ISO giả, không có biên nhận giả, không "verified" không bằng chứng.
3. **Metadata một mình không bao giờ nâng trạng thái.** Gate chỉ **HẠ**, không **NÂNG**
   dựa trên nhãn tự khai (xem `namios_eco`, `namios_compat`, `namios_smartai.promotion`).
4. **Fail-closed.** Không biết → coi là chưa an toàn/chưa xác nhận, không phải mặc định "ok".
5. **An toàn mặc định.** I/O nhạy cảm đi qua `namios_security` (không shell, không eval,
   không `open()` theo chuỗi — dùng `open_within`; redact secret/PII trước khi log/gửi).
6. **Song ngữ qua một nguồn.** Chuỗi người đọc đi qua `namios_i18n` (`t(key, lang)`),
   KHÔNG hard-code; trường dữ liệu `*_vi` luôn tiếng Việt.

## 3. Bản đồ module (`src/namios_*`)

Lớp nền dùng chung:

| Package | Vai trò |
| --- | --- |
| `namios_core` | Hợp đồng dùng chung M1: envelope, `ExitCode`/`ErrorCode`, state machine, `AppMode`/`CompatStatus`, paths, brand/about, các `Protocol` chia sẻ. Mọi module khác tham chiếu một nguồn sự thật ở đây. |
| `namios_i18n` | Lớp common song ngữ VN/EN — catalog + `t(key, lang)`, đổi ngôn ngữ qua `--lang`/`NAMIOS_LANG`. "Sửa một chỗ → cả hệ thống đổi." |
| `namios_security` | Primitive an toàn: redaction (secret/PII), `safe_path`/`open_within` (chống traversal/symlink/TOCTOU), ranh giới không-shell. |

Lõi phần mềm M1 (tác vụ cài/kiểm trên máy):

| Package | Vai trò |
| --- | --- |
| `namios_manifest` | Schema + validator cho app manifest (quét injection, khóa thực thi). |
| `namios_catalog` | Catalog ứng dụng + tìm kiếm có/không dấu tiếng Việt. |
| `namios_planner` | Lập kế hoạch cài/hành động (digest, các bước dự kiến). |
| `namios_recipe` | Mô hình recipe cấp M1 + `dry_run` (liệt kê hành động, KHÔNG thực thi). |
| `namios_helper` | Ranh giới helper đặc quyền: chỉ chạy **plan đã duyệt sẵn** (allowlist), không `RunCommand` tự do. |
| `namios_evidence` | Mô hình evidence + gate ngữ nghĩa tầng 2 (provenance, người duyệt, môi trường). |
| `namios_txstate` | Trạng thái giao dịch/tác vụ bền + journal (durable, round-trip). |
| `namios_doctor` | Thu thập capability report host THẬT (không bịa, không secret) — lệnh `namios doctor`. |
| `namios_dotnet` | Phân tích PE/.NET **tĩnh** (không chạy binary), an toàn với file dị dạng. |
| `namios_cli` | Console-script `namios` (argparse subcommand + dispatch) — lớp WIRING tích hợp mọi module. |
| `namios_welcome` | Wizard chạy-lần-đầu + chuyển dữ liệu Windows an toàn (DATA-002: không ghi đè/không xoá bản gốc). |

Các trung tâm lớn (theo phụ lục):

| Package | Phụ lục | Vai trò |
| --- | --- | --- |
| `namios_eco` | 02 | Hệ sinh thái phần mềm VN: mô hình **7 nấc quy trình** + gate trạng thái trung thực (`downloadable_only`/`launches_only` **không bao giờ** = "dùng được"; `workflow_verified` cần bằng chứng nộp/nhận) + danh bạ ngành. |
| `namios_compat` | 03 | Trung tâm tương thích: resolver "chạy app Windows kiểu nào" (native→web→wine→remote→vm), schema chống metadata giả, evidence gate chỉ-HẠ, classifier .NET/PE, device registry, workflow pack. |
| `namios_smartai` | 04 | "Linh hồn" điều phối: khung an toàn (state machine/policy-as-code/tool broker/injection defense) + chẩn đoán + tự-sửa-có-giới-hạn (sandbox) + quản trị (kill-switch/admin/vendor-pack/idempotency) + an-toàn-dữ-liệu + **Knowledge Base có nguồn** + **Human Feedback**. |

## 4. Dòng chảy một tác vụ (ví dụ: "cài và chạy MISA")

```
Người dùng (tiếng Việt)
  → namios_smartai.intent         (ý định có cấu trúc; thiếu thông tin → HỎI, không đoán)
  → namios_smartai.planner        (plan hữu hình; bước rủi ro gắn cờ cần consent)
  → namios_smartai.policy         (policy-as-code: R4 ký/nộp cần xác nhận GIAO DỊCH)
  → namios_compat.resolver        (chọn route; .NET không tự thành native; đổi version → vô hiệu route)
  → namios_smartai.tools (broker) (typed, fail-closed, capability token scoped)
  → ToolResult = SỰ THẬT          (orchestrator cập nhật trạng thái TỪ đây, không từ lời AI)
  → namios_smartai.promotion      (chỉ evidence tool-pass + người duyệt + nghiệp vụ → published)
```

Điều gì **chặn** tác vụ (trung thực, không bịa hoàn thành):
- Phụ thuộc bắt buộc chưa sẵn sàng (`namios_smartai.depgraph`) → app mở được ≠ hoàn thành.
- Giao dịch thật R4 (ký/nộp/thanh toán) → dừng ở `blocked_external_dependency`, chờ cổng/sandbox thật.
- Chứng nhận quá hạn / nguồn giả → `needs_retest`, không tạo pass.

## 5. Ranh giới BLOCKED (vì sao chưa làm — không giấu)

| Hạng mục | Cần gì để mở |
| --- | --- |
| M2-host (chạy Wine thật trên app OSS) | Linux host có nested-virt; engine + `TrialExecutor` đã sẵn, chỉ thay executor. |
| M3 pilot (vendor/CA/thiết bị/portal) | Sandbox thật + người nghiệp vụ duyệt R3/R4. |
| M4 phát hành (community-learning, dashboard, release-ring) | Hạ tầng phát hành + ký/thu hồi. |
| Model AI thật (SAI-027/028) | Nhà cung cấp model; seam `ModelProvider` + budget đã có. |
| Compat Phase B/C/D | Vendor + build host + DB thật + pilot. |
| Bridge ký số (ECO-009/010/011) | Tài liệu + quyền tích hợp từ CA/vendor. |

Mọi phần BLOCKED đều **đã có khung/interface** để cắm vào khi hạ tầng sẵn sàng — xem các
`Protocol`/seam trong module tương ứng.

## 6. Kiểm thử & cổng chất lượng

- `tests/unit/` — đơn vị, tất định.
- `tests/integration/`, `tests/system/` — ghép nối, end-to-end CLI.
- `tests/security/` — **đối kháng**: cố tình phá bất biến an toàn/trung thực (mỗi trung tâm có một bộ).
- `qa/evidence-index/` — xác minh độc lập của tester.

Cổng (CI tự chạy mọi push/PR qua `.github/workflows/ci.yml`, phải xanh trước khi merge):
`ruff check src tests` · `black --check src tests` · `mypy src/namios_core` · `pytest`.
Chi tiết trong [`../CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## English summary

NaMiOS = a Vietnamese Debian 13 + KDE distro **plus** a pure-Python software layer that runs
essential Windows tasks (Office, Zalo, MISA, .NET apps) via **verified compatibility profiles**,
never by promising "runs every Windows app".

Non-negotiable invariants every module keeps (adversarial tests in `tests/security/` exist to
break them): **AI words ≠ truth** (state updates only from `ToolResult`); **no "pass" label
without real evidence** (missing infra → `blocked`, never fabricated); **metadata alone never
promotes** (gates only downgrade); **fail-closed**; **safe-by-default I/O** via `namios_security`;
**one bilingual source** via `namios_i18n`.

Package map: shared base (`namios_core`, `namios_i18n`, `namios_security`); M1 core
(`namios_manifest`, `namios_catalog`, `namios_planner`, `namios_recipe`, `namios_helper`,
`namios_evidence`, `namios_txstate`, `namios_doctor`, `namios_dotnet`, `namios_cli`,
`namios_welcome`); big centers (`namios_eco` = VN software ecosystem / 7-step honest gate;
`namios_compat` = compatibility resolver; `namios_smartai` = AI orchestration "soul"). What is
`BLOCKED` and why is listed in §5 — all blocked parts already expose the interface to plug real
infrastructure into. Quality gate: ruff + black + mypy + pytest (see `CONTRIBUTING.md`).
