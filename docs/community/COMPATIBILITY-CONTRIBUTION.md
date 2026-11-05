# Đóng góp hồ sơ tương thích

> NaMiOS mạnh lên nhờ **cộng đồng báo cáo app Windows chạy ra sao trên NaMiOS**. Tài liệu này
> giải thích cách gửi báo cáo cho **có ích và trung thực** — và vì sao một lời "máy mình chạy
> ngon" **không** tự biến thành "đã chứng nhận".
>
> Đây là nơi tính cộng đồng gặp kiến trúc tin cậy: ai cũng góp được dữ liệu, nhưng **chỉ bằng
> chứng thật mới nâng được trạng thái**. (EN summary at the bottom.)

## 1. Bốn tầng nguồn (provenance) — và tầng nào "có giá trị" tới đâu

NaMiOS tách rõ bốn tầng nguồn (xem `namios_smartai.knowledge_base`, SAI-025):

| Tầng | Là gì | Dùng để làm gì | KHÔNG dùng để |
| --- | --- | --- | --- |
| **Chứng nhận NaMiOS** (`namios_cert`) | Lab NaMiOS chạy thật + bằng chứng tool | Khẳng định mức thử: `verified`/`partial`/`failed` | — |
| **Tài liệu chính thức** (`official_doc`) | Hãng/Linux công bố | Tham khảo, cơ sở cho chỉ dẫn cài | Khẳng định "đã chạy trên NaMiOS" |
| **Cộng đồng chưa kiểm** (`community_unverified`) | Báo cáo của bạn | **Gợi ý test case** | Cài driver / kết luận "chạy được" |
| **Suy luận AI** (`ai_inference`) | Mô hình đoán | Gợi ý hướng điều tra | Bất kỳ kết luận nào |

**Hệ quả quan trọng:** khi hỏi "App X bản Y chạy được không?", NaMiOS trả **đúng mức đã thử
của bản Y cụ thể**, hoặc **"chưa kiểm"** — nó **không** suy từ bản khác, và **không** để lời
đồn cộng đồng/AI nâng thành "chạy được".

## 2. Phản hồi của bạn đi đâu (SAI-029)

Khi bạn báo "workflow này đã giải quyết / chưa giải quyết" + mô tả lỗi:

- Phản hồi được ghi nhận **theo vai trò** (người dùng / IT / chuyên gia nghiệp vụ) — đánh giá
  **riêng**, không gộp. Một "đã xong" của người dùng cuối **không** thay cho thẩm định IT/nghiệp vụ.
- Phản hồi **không bao giờ** tự nâng trạng thái lên `workflow_verified`. Dù 1000 người báo "chạy
  ngon", gate vẫn không đổi — chỉ **gợi ý test case mới** để lab kiểm lại.
- Mô tả lỗi của bạn → sinh **gợi ý test case**: chưa-giải-quyết → ca *tái hiện*; đã-giải-quyết →
  ca *hồi quy* (để chắc fix thực sự giữ).

Vì sao chặt vậy? Vì kế toán/thuế/BHXH sai một con số là hậu quả thật. "Mở được" ≠ "đúng dữ liệu".

## 3. Một báo cáo tương thích TỐT gồm gì

Dùng mẫu issue **Compatibility report** (`.github/ISSUE_TEMPLATE/compatibility_report.yml`).
Càng cụ thể, càng dễ biến thành test case:

1. **App + phiên bản chính xác** (vd "MISA SME 2024 R2", không chỉ "MISA"). Mức thử gắn với
   đúng (app, mode, version) — bản khác là chuyện khác.
2. **Mode đã thử:** native Linux / web / Wine / remote Windows / VM.
3. **Workflow đo được** (không chỉ "mở được"): vd "nhập chứng từ → in báo cáo → số tiền khớp Windows".
4. **Kết quả so với Windows:** khớp hay lệch (số tiền, bố cục, bản in, chữ ký). Lệch = `failed`.
5. **Môi trường:** bản NaMiOS, phiên bản Wine/runtime (nếu có), máy in/scanner/token liên quan.
6. **Log — ĐÃ che thông tin nhạy cảm.** Đừng dán CCCD, mã số thuế, mật khẩu, token, chuỗi kết
   nối DB, cookie. (Lớp `namios_security`/`redaction` của hệ cũng tự che, nhưng bạn vẫn nên tự che trước.)

**Tuyệt đối không** gửi: dữ liệu kế toán/khách hàng thật, PIN/khóa ký số, ảnh chụp có thông tin cá nhân.

## 4. Từ báo cáo cộng đồng → chứng nhận (vòng đời)

```
Báo cáo cộng đồng (community_unverified)
  → gợi ý test case (SAI-029)
  → lab NaMiOS dựng ca + chạy thật trên đúng (app, mode, version)
  → bằng chứng tool (pass/fail + fixture hash + môi trường)   ← đây mới là SỰ THẬT
  → promotion gate (SAI-012): + người duyệt + xác nhận nghiệp vụ end-to-end
  → namios_cert: verified / partial / failed   (gắn ngày + có thể hết hạn)
```

Đổi thành phần (Wine/model/bản app/thiết bị) → trạng thái về `needs_retest` trước khi "stable"
(SAI-033). Chứng nhận có hạn: quá hạn → `needs_retest`, không tự gia hạn.

## 5. Đóng góp một "recipe" tương thích (nâng cao)

Nếu bạn tìm được cách làm app chạy, bạn có thể đề xuất một **recipe** (xem `namios_smartai.recipe`):
- Phải có **nguồn tải chính thức** + **hash** + **bước hoàn tác (rollback)** nếu đổi hệ thống.
- Recipe kiến trúc x86 **không** tự áp cho x64.
- Recipe AI đề xuất mặc định `experimental` — chỉ promotion gate mới nâng.
- Kiểm nhanh điều kiện publish: `namios smartai recipe-check <file.json>`.

---

## EN — Contributing compatibility data

NaMiOS grows from the community reporting **how Windows apps actually run on NaMiOS** — but a
"works for me" is **unverified community feedback**, not a certification.

Four provenance tiers (`namios_smartai.knowledge_base`, SAI-025): **NaMiOS certification** (lab +
tool evidence — the only tier that asserts a tested level), **official docs** (reference), **unverified
community** (suggests test cases; never installs drivers or concludes "works"), **AI inference**
(investigation hints only). Asking "does App X version Y work?" returns the actual tested level
**for that exact version** or **"not tested"** — never carried over from another version, never
raised by rumor/AI.

Your feedback (SAI-029) is recorded **per role** (user/IT/business, evaluated separately) and
**never** auto-promotes to `workflow_verified`; it only generates test-case suggestions
(unresolved → repro, resolved → regression). A good report has: exact app+version, mode tried, a
measurable workflow (not just "it opens"), result vs the Windows baseline, environment, and
**redacted** logs (never real accounting/PII/PINs/tokens). Lifecycle: community report → test-case
→ NaMiOS lab run → tool evidence → promotion gate (reviewer + business sign-off) → certified
(dated, expirable; component change → `needs_retest`). Advanced: propose a recipe (official source
+ hash + rollback; x86 ≠ x64; AI recipes default `experimental`) and check it with
`namios smartai recipe-check <file.json>`.
