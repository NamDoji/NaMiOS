# NaMiOS — Chức năng & Hướng phát triển MỚI (NEW-FUNCTIONS-DIRECTION)

> **Loại tài liệu:** định hướng sản phẩm (Head of Product) — danh mục **CHỨC NĂNG MỚI**
> + **HƯỚNG PHÁT TRIỂN** vượt ra ngoài "bắt kịp Windows/KDE", mỗi mục biến thành **khối
> yêu cầu dev-ready** để đội phát triển nhận việc ngay.
> **Ngày:** 2026-11-11 · **Vai trò người soạn:** Head of Product / chiến lược (đội quan
> trọng nhất — "định hướng thêm chức năng + hướng phát triển mới").
> **Phạm vi:** CHỈ phân tích + đề xuất + viết tài liệu này. KHÔNG sửa code/gói khác,
> KHÔNG build, KHÔNG commit, KHÔNG đụng `.gh-token`.

## 0. Quy ước đọc (bắt buộc — giữ kỷ luật trung thực của repo)

- **`verified_on_host: NO` cho mọi khẳng định "sẽ chạy / sẽ hay" dưới đây.** Toàn hệ mới
  vào được desktop KDE trong QEMU, **chưa có pilot máy thật** (`docs/STATUS.md`, ADR-0011).
  "Khối yêu cầu viết xong" ≠ "tính năng đã chạy". Chỗ suy đoán ghi **[GIẢ ĐỊNH]**.
- **Ranh giới IP (ADR-0011 §3, LIC-004, TRADEMARK doc — ràng buộc cứng):** được bắt chước
  **bố cục + luồng thao tác quen thuộc**; **TUYỆT ĐỐI KHÔNG** chép icon/font/âm thanh/thương
  hiệu độc quyền, không host lại bộ cài của cơ quan/nhà cung cấp khi chưa có quyền, không
  tự dán nhãn "ứng dụng chính thức của NaMiOS" lên sản phẩm bên thứ ba. "**Tested by NaMiOS**"
  ≠ "**Officially supported by vendor**" (ECO-004/021). Chỗ chạm ranh giới ghi **[IP]**.
- **7 điều KHÔNG overclaim** (giữ nguyên từ `NANG-CAP-NHU-CAU-NGUOI-DUNG.md` §4): không
  "chạy mọi phần mềm Windows", không "100% tương thích Office", không "miễn phí mọi phần
  mềm", không "diệt sạch virus", không "tương thích Outlook/Exchange", không gọi LibreOffice
  là "Word/Excel", không "được cơ quan nhà nước chứng nhận" khi chưa có văn bản.
- **Ưu tiên:** **P0** mở khoá giá trị khác-biệt cốt lõi / chặn niềm tin · **P1** cần cho
  trải nghiệm "chọn NaMiOS thay vì Windows" · **P2** đánh bóng/mở rộng.
- **Công sức:** **S** vài ngày/1 wave · **M** 1–2 tuần · **L** nhiều tuần + cần phần
  cứng/build host thật · **XL** cần đối tác/model/pháp lý/hạ tầng-dịch-vụ (ngoài lập trình
  thuần).
- **Đội sở hữu:** **1** = thiết kế/UX · **3** = dev nền tảng/desktop · **5** = Wine/tương
  thích · **6** = SmartAI/AI.
- **Cổng chung #0 (kế thừa):** mọi mục gắn "verify-on-hardware" vẫn khoá sau **build host
  nested-virt** (đã là #1 ở hai tài liệu roadmap trước). Tài liệu này **đánh dấu rõ** mục
  nào **xây-tĩnh-được-ngay** (static-buildable-now, không chờ phần cứng) để giao thẳng cho
  dev — đó là đóng góp chính của bản này.

## 0bis. Tài liệu này KHÁC gì ba roadmap đã có (không lặp)

| Tài liệu đã có | Trả lời câu hỏi | Khung |
| --- | --- | --- |
| `WINDOWS-FEATURE-PARITY.md` | "Bằng Windows chưa?" | **Bắt kịp** (parity) |
| `NANG-CAP-NHU-CAU-NGUOI-DUNG.md` | "Văn phòng/kế toán dùng được chưa?" | **Vá khoảng trống** (gap) |
| `MODERN-FUTURE-UX.md` | "Nhìn có cao cấp không?" | **Đánh bóng** (polish) |
| **`NEW-FUNCTIONS-DIRECTION.md` (bản này)** | "**Vì sao người Việt CHỌN NaMiOS thay vì Windows?**" | **Bứt lên + thuần Việt** (leap + uniquely VN) |

Ba tài liệu kia = "để không thua Windows". Bản này = "để **hơn** ở đúng chỗ người Việt cần,
và có thứ Windows **không có**". Không chép lại backlog parity; chỉ tham chiếu khi một chức
năng mới tái dùng hạ tầng đã phân tích ở đó.

---

## 1. Tầm nhìn điều hành (what NaMiOS is becoming)

> **NaMiOS đang trở thành hệ điều hành đầu tiên "hiểu người Việt": một máy tính quen tay
> như Windows, nhẹ nhàng như macOS, nhưng có ba thứ Windows không bao giờ cho người Việt —
> (1) một TRỢ LÝ AI tiếng Việt ở khắp nơi, biết tự giải thích lỗi, viết/tóm tắt giúp, và
> điều khiển máy bằng câu nói thật; (2) một tầng THUẦN VIỆT bẩm sinh — âm lịch & ngày lễ,
> bộ gõ + chính tả + định dạng tiền/ngày chuẩn Việt, và một "Cổng dịch vụ Việt" dẫn thẳng
> tới thuế/BHXH/dịch vụ công/ký số (ưu tiên ký số từ xa chạy ngay trên trình duyệt); (3)
> sự TRUNG THỰC & AN TOÀN làm mặc định — không quảng cáo quá lời, telemetry tắt, cập nhật
> quay-lui được. Và nó tự cấu hình theo NGHỀ của bạn (học sinh / văn phòng / kế toán) ngay
> lần đầu bật máy. Mục tiêu không phải "một Windows rẻ hơn", mà "chiếc máy tính đầu tiên
> thực sự nói tiếng Việt với bạn" — chạy được cả trên máy yếu, cả khi mất mạng.**

Bốn nguyên tắc chi phối mọi chức năng mới:
1. **Local-first, cloud-optional, honest-about-it** — mặc định chạy offline/rule-based;
   model/khoá đám mây chỉ là lớp tăng cường, luôn nói rõ "cần khoá/model" (không giả vờ AI
   khi chưa có).
2. **Tái dùng hạ tầng đã dựng** — ưu tiên nối các mảnh đã có (PL04 SmartAI engine,
   `error-catalog.json`, `catalog/services/*.json`, `namios_essentials`, Kup/Timeshift,
   `namios-welcome.apply()`) thay vì xây mới từ 0.
3. **Xây-tĩnh-được-ngay trước** — ưu tiên giao dev những mục không chờ phần cứng (QML,
   extension, JSON-driven UI, config) để có giá trị thấy được sớm.
4. **Không overclaim, không clone** — mỗi chức năng tự mang nhãn trạng thái trung thực + tôn
   trọng ranh giới IP.

---

## 2. Năm trụ cột (+ hai trụ bổ sung) & bản đồ chức năng

| Trụ | Khác biệt cốt lõi | Chức năng mới (mã) |
| --- | --- | --- |
| **I. AI là điểm khác biệt** | SmartAI ở khắp nơi, không chỉ chatbot | AI-1 Thanh lệnh ngôn ngữ tự nhiên · AI-2 Viết/tóm tắt trong NaMiOffice · AI-3 Giúp lỗi chủ động · AI-4 Tìm kiếm ngữ nghĩa · AI-5 Đồng hành onboarding · AI-6 Chiến lược model local/cloud |
| **II. Thuần Việt bẩm sinh** | Thứ Windows không làm cho người Việt | VN-1 NaMiLịch (âm lịch + lễ) · VN-2 Cổng Dịch vụ Việt · VN-3 Trung tâm Ký số · VN-4 Gói ngôn ngữ Việt hợp nhất · VN-5 Giọng đọc tiếng Việt (TTS/a11y) · VN-6 Bộ gõ thông minh + macro |
| **III. Tài khoản · đồng bộ · sao lưu** | Chuyển máy không mất gì | ACC-1 Sao lưu ra đám mây của BẠN · ACC-2 Mang-máy-cũ-sang-máy-mới · ACC-3 Tài khoản NaMiOS (tuỳ chọn) |
| **IV. Niềm tin · an toàn · cập nhật** | Trung thực làm mặc định | SEC-1 Trung tâm An toàn hợp nhất · SEC-2 Bảng điều khiển Riêng tư · SEC-3 Cập nhật an toàn + quay lui (Update Center) |
| **V. Gói thiết lập theo nghề** | Máy tự cấu hình theo bạn | PROF-1 Hồ sơ nghề (khung) · PROF-2 Học sinh · PROF-3 Văn phòng · PROF-4 Kế toán |
| **VI. (bổ sung) Bền bỉ offline cho vùng kết nối yếu** | Nông thôn/trường học VN | OFF-1 Trợ giúp + từ điển + AI offline · OFF-2 Gương cập nhật nội bộ (trường/làng) |
| **VII. (bổ sung) Máy dùng chung / gia đình** | Trường, tiệm net, nhà nhiều người | FAM-1 Chế độ khách + hồ sơ nhiều người nhẹ |

---

## 3. Khối yêu cầu dev-ready

> Mỗi khối: **Title · User story · Acceptance criteria (testable) · Tech mechanism ·
> Dependencies · Effort · Priority · Risk + MUST-VERIFY-ON-HARDWARE · Owning team.**
> Nhãn **[tĩnh-ngay]** = xây được không cần phần cứng; **[R&D]** = cược nghiên cứu lớn;
> **[đối tác]** = cần bên ngoài.

### TRỤ I — AI LÀ ĐIỂM KHÁC BIỆT

**Nền tảng hiện có — BA thân mã AI RIÊNG BIỆT, CỐ Ý TÁCH NHAU (sự thật đã xác minh mã nguồn):**
1. **Chatbot `namios_assistant`** (`distro/.../opt/namios/namios_assistant-src/`, PySide6) =
   cửa sổ chat **CHỈ GIẢI THÍCH lỗi** (classify→tra KB offline→giải thích), có **OCR**
   (`tesseract -l vie+eng` dán ảnh lỗi), **không hành động gì lên máy**; LLM đám mây **tuỳ
   chọn** qua endpoint OpenAI-compatible (`NAMIOS_ASSISTANT_API_KEY/_MODEL/_BASE_URL`), **không
   có model local**; mặc định offline rule-based, 19 mục KB tiếng Việt/Anh.
2. **Bash `namios-smartai`** (`usr/local/bin/`) = **10 playbook tất định** (mạng/in/IME/cập
   nhật/wine) **CÓ hành động** qua cổng `pkexec` + undo Timeshift + audit; LLM nếu có **chỉ
   ĐỊNH TUYẾN** sang playbook, không tự sinh-rồi-chạy lệnh.
3. **Engine Python PL04** (`src/namios_smartai/`) = khung tất định typed intent→plan→policy→
   tool-broker, **executor còn MOCK**, **chỉ 4 intent** (`install_app/submit_filing/open_app/
   print_document`), **"Model Router thật CHƯA nối"** (ADR-0021).

**Ba thân mã này CỐ Ý không đụng nhau** (chatbot firewalled khỏi executor). "**tắt wifi**" hôm
nay **KHÔNG được hỗ trợ** (không intent điều khiển thiết bị nào; chỉ có *đọc trạng thái*
read-only + tên-tool-bị-khoá chưa chạy). → Cơ hội lớn nhất của trụ này là **nối + mở rộng** ba
mảnh đã có, giữ nguyên guardrail "AI đề xuất, policy + người quyết".

---

#### AI-0 · Hợp nhất trợ lý: "giải thích lỗi → nhờ SỬA luôn" (bridge chatbot → executor có-cổng-quyền) · [tĩnh-ngay]

- **User story:** *Là người không rành, khi trợ lý đã giải thích lỗi và nêu các bước sửa, tôi
  muốn bấm "Sửa giúp tôi" ngay trong cửa sổ chat để trợ lý thực hiện (có hỏi quyền), thay vì
  phải tự gõ lệnh theo hướng dẫn.*
- **Acceptance criteria:**
  - Khi câu trả lời của chatbot khớp một `cause_code` có playbook an toàn, hiện nút **"Sửa giúp
    tôi"** → **chuyển giao** sang executor bash `namios-smartai --explain/--run <cause_code>`
    (đúng cổng `confirm_and_run`): hiện KẾ HOẠCH ≤3 bước + lệnh argv tĩnh + cách hoàn tác → hỏi
    Có/Không → chạy → kiểm read-only → audit.
  - **Không phá firewall tuỳ tiện:** chatbot vẫn KHÔNG tự chạy lệnh; nó chỉ **mở executor đã
    được kiểm duyệt** với một `cause_code` thuộc danh mục an toàn. Không `cause_code` → không
    có nút (giữ "chỉ giải thích").
  - Giữ mọi guardrail executor (pkexec, argv tĩnh, không `eval`, tắt AI máy vẫn chạy).
  - Test: dán 5 lỗi có playbook → hiện nút → bấm → đúng luồng xác nhận/undo; dán lỗi không có
    playbook → không nút, chỉ giải thích.
- **Tech mechanism:** cầu nối nhỏ giữa `namios_assistant` (#1) và `namios-smartai` (#2) qua
  `cause_code` + `--explain/--run`; chuẩn hoá JSON contract `handle_request` của engine PL04
  (#3, `cli.py`) nếu muốn đi qua engine. **Không viết lại** ba thân mã — chỉ nối.
- **Dependencies:** chatbot (#1), bash SmartAI (#2), `error-catalog.json` (tất cả đã có).
- **Effort: M. Priority: P1** (quick win chiến lược: biến "ba mảnh rời" thành một trợ lý thật).
- **Risk + verify:** nối sai = nới firewall → chỉ cho qua `cause_code` thuộc allowlist có
  playbook. MUST-VERIFY-ON-HARDWARE: **CÓ** (session KDE + kdialog thật). **Owning: 6.**

---

#### AI-1 · Thanh lệnh ngôn ngữ tự nhiên (NaMiAI Command Bar) — điều khiển máy bằng câu nói thật

- **User story:** *Là người ít rành máy tính, tôi muốn gõ/nói "tắt wifi", "mở file tuần
  trước", "tăng cỡ chữ", "chụp màn hình vùng này" và máy làm đúng, để tôi không phải tìm
  trong menu rối rắm.*
- **Acceptance criteria:**
  - Có một **Action Catalog khai báo** (JSON có schema + ký) liệt kê các "động từ hệ thống an
    toàn" (toggle wifi/bluetooth, đổi âm lượng/độ sáng, đổi cỡ chữ KDE, mở thư mục chuẩn, chụp
    màn hình, khoá máy, mở app theo tên) — **mỗi mục là argv tĩnh**, không lệnh động.
  - NL → intent khớp vào Action Catalog; **không khớp chắc chắn → hỏi lại/đề nghị Chẩn đoán**,
    không đoán bừa (giữ hành vi routing tất định hiện có).
  - Mọi hành động **ĐỔI máy** vẫn qua cổng xác nhận + `pkexec` khi cần; hiển thị đúng lệnh sẽ
    chạy + cách hoàn tác; audit đã che bí mật (tái dùng `namios-smartai-policy.sh`).
  - Test: 20 câu tiếng Việt (có/không dấu) → đúng action hoặc "không chắc"; 0 câu nào chạy
    lệnh ngoài Action Catalog; tắt AI vẫn làm được mọi việc bằng tay.
  - Offline: bộ khớp từ khoá tất định chạy không cần model; model/khoá chỉ nâng độ hiểu câu
    phức, **không** mở thêm quyền.
- **Tech mechanism:** mở rộng **typed tool-broker PL04** (`src/namios_smartai/`,
  `SMARTAI-TOOL-BROKER.md`) từ 10 playbook cứng thành Action Catalog JSON-driven; UI = KRunner
  runner tuỳ biến **hoặc** ô lệnh trong widget "Hỏi SmartAI" đã có. Verb nền: `nmcli`,
  `kwriteconfig6` (KScreen scale), `spectacle`, `xdg-open`, `loginctl lock-session`.
- **Dependencies:** PL04 engine (thay MOCK executor bằng broker thật, bounded); `pkexec`
  policy; error-catalog; [tuỳ chọn] model local (AI-6).
- **Effort: L** (khung tĩnh-ngay, nhưng NL hiểu-câu là [R&D]). **Priority: P1.**
- **Risk + verify:** **RỦI RO CAO** — đây là nơi "AI điều khiển máy", dễ phình quyền. Bất
  biến: **chỉ Action Catalog, argv tĩnh, không `eval`, không `curl|bash`** (SAI-019). MUST-
  VERIFY-ON-HARDWARE: **CÓ** (fcitx5 + KDE thật). **Owning: 6 (+3).**

---

#### AI-2 · Viết / tóm tắt / dịch / sửa văn trong NaMiOffice (NaMiAI Writer)

- **User story:** *Là nhân viên văn phòng, tôi muốn bôi đen một đoạn rồi bấm "Tóm tắt",
  "Viết lại trang trọng", "Soạn email từ ý này", "Dịch", "Sửa chính tả Việt" ngay trong
  NaMiWriter/NaMiSheet, để soạn công văn/email nhanh mà không rời máy ra web.*
- **Acceptance criteria:**
  - Panel bên (sidebar) trong LibreOffice: các tác vụ viết lại/tóm tắt/soạn thảo/dịch/sửa
    lỗi; chèn kết quả vào tài liệu hoặc thay đoạn bôi đen (có Undo chuẩn LibreOffice).
  - **Trung thực model:** nếu chưa có model/khoá → panel nói rõ "cần bật trợ lý nâng cao
    (khoá/model)"; **không** bịa nội dung từ engine rule-based cho tác vụ sáng tạo.
  - Dữ liệu: mặc định gửi **chỉ đoạn bôi đen**, hiển thị rõ "văn bản này sẽ được xử lý bởi
    [local model / dịch vụ X]"; chế độ **chỉ-local** không gửi gì ra mạng.
  - Test: 10 mẫu công văn/email VN → kết quả tiếng Việt đúng ngữ cảnh; chế-độ-local không tạo
    kết nối mạng (kiểm bằng log mạng).
- **Tech mechanism:** LibreOffice extension (`.oxt`, UNO API — Python/Basic) gọi backend
  SmartAI (local model qua AI-6 hoặc dịch vụ đám mây tuỳ chọn). Tái dùng lớp redaction +
  consent của SmartAI.
- **Dependencies:** AI-6 (model strategy); NaMiOffice (đã ship); chính sách dữ liệu rõ ràng.
- **Effort: M** (khung extension) **/ L** nếu bó kèm model local. **Priority: P1.**
- **Risk + verify:** rò rỉ dữ liệu nếu mặc định gửi cloud — **phải opt-in + chỉ-đoạn-chọn +
  nhãn rõ**. [IP] không gọi là "Copilot". MUST-VERIFY-ON-HARDWARE: **Không bắt buộc** cho
  khung; **CÓ** cho chất lượng tiếng Việt. **Owning: 6 (+1 cho UX panel).**

---

#### AI-3 · Giúp lỗi CHỦ ĐỘNG (Proactive error help)

- **User story:** *Là người không rành, khi máy báo lỗi (mất mạng, in hỏng, cập nhật lỗi),
  tôi muốn một gợi ý nhẹ "Để tôi giúp?" hiện lên đúng lúc, để không phải tự đi tìm trợ lý.*
- **Acceptance criteria:**
  - Khi một sự kiện lỗi có `cause_code` xảy ra (theo `EVENT-ERROR-CONTRACT.md`), hiện
    **toast không xâm phạm** "Để tôi giúp?" → bấm mở SmartAI `--explain <cause_code>` đúng ca.
  - **Opt-in, im lặng theo mặc định đúng mức:** không spam; có công tắc tắt hẳn; không bao giờ
    tự chạy hành động, chỉ **mời**.
  - Không là điều kiện boot/recovery (guardrail #2); tắt đi máy vẫn báo lỗi bình thường.
  - Test: bơm 5 sự kiện lỗi mô phỏng (Wi-Fi/DNS/in/scan/update) → đúng 5 toast đúng cause_code;
    tắt tính năng → 0 toast.
- **Tech mechanism:** watcher nhẹ userspace nghe DBus/journald/các ErrorCard đã phát (Design
  System A1 có ErrorCard + nút "Nhờ SmartAI giải thích") → KNotification. Tái dùng catalog +
  `--explain` đã có.
- **Dependencies:** `error-catalog.json` + EVENT-ERROR-CONTRACT (đã có); ErrorCard QML (A1).
- **Effort: M. Priority: P2** (nâng P1 nếu pilot thấy người dùng không tự mở trợ lý).
- **Risk + verify:** phiền nhiễu nếu quá nhạy → ngưỡng + gom. MUST-VERIFY-ON-HARDWARE: **CÓ**
  (session KDE thật). **Owning: 6 (+1).**

---

#### AI-4 · Tìm kiếm ngữ nghĩa "mở file tuần trước / hợp đồng có chữ ABC"

- **User story:** *Là người hay quên tên file, tôi muốn tìm bằng mô tả tự nhiên ("file Word
  tuần trước về hợp đồng", "ảnh chụp hoá đơn tháng 10"), để khỏi nhớ chính xác tên/đường dẫn.*
- **Acceptance criteria:**
  - Gõ câu mô tả trong KRunner/ô tìm → trả file theo **thời gian + loại + nội dung** (ví dụ
    "tuần trước" → lọc mtime; "hợp đồng" → full-text).
  - Bậc 1 (tĩnh-ngay): dùng chỉ mục **Baloo** + lọc thời gian/loại bằng NL đơn giản.
  - Bậc 2 [R&D, tuỳ chọn]: chỉ mục embedding **local** cho tìm theo ý nghĩa; chạy offline;
    opt-in; nêu rõ chi phí RAM/đĩa.
  - Quyền riêng tư: chỉ chỉ mục thư mục người dùng; không gửi nội dung ra mạng ở chế độ local.
  - Test: 10 truy vấn mô tả → file đúng trong top-5; tắt → KRunner thường vẫn chạy.
- **Tech mechanism:** KRunner runner tuỳ biến bắc cầu Baloo (`baloosearch6`) + parser thời
  gian tiếng Việt; bậc 2 dùng model embedding local (AI-6).
- **Dependencies:** Baloo (đi kèm Plasma); AI-6 cho bậc 2.
- **Effort: M** (bậc 1) **/ L** (bậc 2). **Priority: P2.**
- **Risk + verify:** Baloo tốn tài nguyên trên máy yếu → cho tắt. MUST-VERIFY-ON-HARDWARE:
  **CÓ.** **Owning: 3 (+6 cho bậc 2).**

---

#### AI-5 · Đồng hành onboarding bằng AI (first-run companion + tour)

- **User story:** *Là người lần đầu dùng Linux, tôi muốn một trợ lý dẫn tôi làm "4 việc đầu
  tiên" và trả lời "làm sao gõ tiếng Việt / in PDF / nối Wi-Fi", để không bơ vơ phút đầu.*
- **Acceptance criteria:**
  - Sau wizard `namios-welcome`, mở **tour 3–5 việc đầu tiên** (mở Văn phòng, gõ tiếng Việt,
    lưu, in PDF, nối Wi-Fi) + ô "Hỏi gì cũng được" nối SmartAI.
  - Mỗi bước **hiện "Đã áp dụng ✓"** ngay (tái dùng `RuntimeApplyOutcome` của firstrun.py —
    xem MODERN-FUTURE-UX #8), không chỉ báo ở cuối.
  - Chạy-1-lần + mở lại được từ NaMiHelp; offline hoàn toàn.
  - Test: hoàn thành tour → 4 marker trạng thái đúng; mở lại tour từ Help được.
- **Tech mechanism:** mở rộng `src/namios_welcome/ui.py` (PySide6) + nối SmartAI; tái dùng
  `apply_runtime_desktop_settings()` đã có.
- **Dependencies:** namios-welcome (đã có apply()); SmartAI CLI.
- **Effort: M. Priority: P1.**
- **Risk + verify:** thấp. MUST-VERIFY-ON-HARDWARE: **CÓ** (các lệnh apply chạy đúng trên
  trixie thật). **Owning: 1 (+3).**

---

#### AI-6 · Chiến lược model local-first / cloud-optional (ADR mới + runtime)

- **User story:** *Là chủ dự án, tôi muốn một chiến lược rõ ràng để AI chạy được offline trên
  máy yếu nhưng mạnh hơn khi có model/khoá, để không hứa quá và không khoá người dùng vào một
  nhà cung cấp.*
- **Acceptance criteria:**
  - **ADR "SmartAI model runtime"** chốt: (a) rule-based luôn là lưới an toàn; (b) model
    **local tuỳ chọn** (ví dụ GGUF qua `llama.cpp`/`ollama`) — nêu RÕ yêu cầu RAM/đĩa, **không
    bật mặc định trên máy yếu**; (c) **cloud tuỳ chọn** qua khoá người dùng tự nhập; (d) bất
    biến "AI đề xuất, không tự hành động".
  - Trạng thái model hiển thị trung thực ("đang dùng: quy tắc / model local / dịch vụ X");
    `backend_mode_line` đã dò biến môi trường — chuẩn hoá thành cài đặt có UI.
  - Không tải model/khoá tự động; không `curl|bash`; model đóng gói (nếu có) phải có ADR
    nguồn-gói (CLAUDE.md).
  - Test: gỡ mọi model/khoá → mọi tính năng AI hạ cấp sạch (rule-based/"cần bật"), 0 crash.
- **Tech mechanism:** lớp cấu hình trong `namios_smartai` + KCM/cài-đặt; đóng gói runtime tuỳ
  chọn (không vào ISO alpha nếu chưa có ADR nguồn-gói).
- **Dependencies:** nền AI-1/2/4; quyết định hạ tầng (đóng gói model là XL nếu bundle).
- **Effort: M** (ADR + runtime switch) **/ XL** nếu bundle model local vào ISO. **Priority:
  P0** (là cổng quyết định cho AI-1/2/4).
- **Risk + verify:** model local nặng, chất lượng tiếng Việt chưa chắc → đo trước khi hứa.
  [R&D]. MUST-VERIFY-ON-HARDWARE: **CÓ.** **Owning: 6.**

---

### TRỤ II — THUẦN VIỆT BẨM SINH

#### VN-1 · NaMiLịch — Âm lịch + ngày lễ Việt (không có trong Windows mặc định) · [tĩnh-ngay]

- **User story:** *Là người Việt, tôi muốn thấy NGÀY ÂM LỊCH, can chi, ngày lễ/giỗ và nhắc
  việc theo âm lịch ngay trên lịch của máy, để không phải tra lịch giấy hay app điện thoại.*
- **Acceptance criteria:**
  - Lịch của đồng hồ Plasma hiển thị **song song dương + âm lịch** (ngày/tháng âm, can chi,
    tháng nhuận đúng theo thuật toán âm lịch VN múi giờ GMT+7).
  - Đánh dấu **ngày lễ VN** (Tết Nguyên đán, Giỗ Tổ 10/3 ÂL, 30/4, 1/5, 2/9…) + lễ theo âm
    lịch; cho phép thêm **nhắc giỗ theo âm lịch** lặp hằng năm.
  - Widget "Hôm nay" nhỏ: dương + âm + lễ sắp tới.
  - **Chính xác là tiêu chí nghiệm thu:** so 50 mốc âm-dương với nguồn đối chiếu công khai →
    khớp 100% (đặc biệt tháng nhuận + giao thừa).
  - Offline hoàn toàn; không cần mạng.
- **Tech mechanism:** **Plasma calendar plugin** (QML, loại `org.kde.plasmacalendarplugins`)
  cài âm lịch + nguồn sự kiện lễ VN; thuật toán âm lịch (Hồ Ngọc Đức/giải thuật công khai) hiện
  thực trong plugin. Có thể kèm applet "NaMiLịch" riêng.
- **Dependencies:** Plasma calendar (đi kèm); không cần dịch vụ ngoài.
- **Effort: M. Priority: P1.**
- **Risk + verify:** sai thuật toán âm lịch = mất uy tín → **giám khảo đối chiếu 50 mốc**.
  MUST-VERIFY-ON-HARDWARE: **CÓ** (render trong digital-clock thật). **Owning: 3 (+1 UX).**

---

#### VN-2 · Cổng Dịch vụ Việt (VN Services Hub) — dẫn thẳng tới thuế/BHXH/DVC/ký số · [tĩnh-ngay]

- **User story:** *Là người dân/kế toán, tôi muốn gõ "khai thuế", "bảo hiểm", "học bạ", "hoá
  đơn" (có hay không dấu) và được dẫn đúng chỗ + biết rõ "chạy được tới đâu trên máy này", để
  không mò mẫm giữa chục cổng khác nhau.*
- **Acceptance criteria:**
  - App desktop đọc **`catalog/services/*.json` + `catalog/compat/*.json` đã có** (thuế/kế
    toán/BHXH/hành chính/giáo dục/ngành dọc) và hiển thị: nhà cung cấp, **mode** (web/wine/vm/
    remote), **trạng thái 7-nấc** (ECO-001/003), token/đăng nhập cần gì, **ngày kiểm**, giới hạn.
  - **Tìm không dấu** (ECO-007): "khai thue" = "khai thuế".
  - Bấm → mở đúng tuyến: **web** mở đúng tên miền chính thức qua NaMiBrowser (cảnh báo khi
    redirect lạ); **wine/vm** trỏ đúng; **không tự đăng nhập, không host lại bộ cài** (ECO-006).
  - Nhãn trung thực: "**Đã kiểm bởi NaMiOS**" ≠ "nhà cung cấp hỗ trợ chính thức" (ECO-004);
    `downloadable_only/launches_only` **không** hiển thị "dùng được" (ECO-003).
  - **Tự kiểm môi trường** trước khi bắt đầu (ECO-008): trình duyệt/chứng thư/token/popup/
    font/PDF/giờ hệ thống — chỉ kết luận phần quan sát được, **không thu PIN/khoá**.
  - Test: 12 dịch vụ trong catalog hiển thị đúng trạng thái; chèn 1 mục `downloadable_only` →
    UI không bao giờ gọi nó là "workflow_verified".
- **Tech mechanism:** app QML/Qt **JSON-driven** (schema đã có trong `catalog/`); tái dùng
  `namios_essentials` (labels/trạng thái) + anti-impersonation; env-check gọi công cụ chẩn đoán
  read-only. Có thể là một mặt của menu "nhóm việc" (DESIGN-SYSTEM §7).
- **Dependencies:** `catalog/services` + `catalog/compat` (ĐÃ CÓ dữ liệu); NaMiBrowser; env-check.
- **Effort: M. Priority: P1** (một trong những differentiator mạnh nhất, dữ liệu đã sẵn).
- **Risk + verify:** nếu để lộ nhãn sai → overclaim; test chặn `downloadable→verified` là bắt
  buộc. MUST-VERIFY-ON-HARDWARE: **Một phần** (UI tĩnh-ngay; env-check cần desktop thật).
  **Owning: 3 (+1).**

---

#### VN-3 · Trung tâm Ký số — ưu tiên KÝ SỐ TỪ XA (SmartCA/MySign) chạy ngay trên trình duyệt

- **User story:** *Là kế toán, tôi muốn ký PDF/tờ khai trên NaMiOS mà không bị chặn vì USB
  token không có driver Linux, để chuyển máy chính được.*
- **Acceptance criteria:**
  - Hub ký số trình bày **3 tuyến theo thứ tự thực tế** (bằng chứng: `docs/wine/KY-SO-PKCS11-
    RESEARCH.md`): **(1) Ký số từ xa** (VNPT SmartCA / Viettel MySign / tương đương) — **web,
    không cần Wine**, duyệt trên app điện thoại; hướng dẫn tiếng Việt + mở đúng cổng. **(2) Ký
    PDF bằng chứng thư mềm `.p12/PKCS#12`** sẵn trong Okular/LibreOffice + hướng dẫn. **(3) USB
    token PKCS#11** — thử phát hiện (`pkcs11-tool --list-slots`) và **công bố trung thực
    `blocked`/`unknown`** nếu không có middleware Linux (3 CA lớn hiện chưa có bằng chứng).
  - **Không giả lập plugin ký để vượt kiểm tra nền tảng**, không tự can thiệp trang/chữ ký
    (ECO-010); private key luôn ở token/HSM; audit không lưu PIN.
  - Không đóng gói công cụ ký bên thứ ba chưa duyệt (MacSigner) vào ISO alpha (cần ADR nguồn-gói).
  - Test: ký `.p12` một PDF thử ra chữ ký hợp lệ (verify bằng `pdfsig`); tuyến remote mở đúng
    cổng; tuyến token báo đúng trạng thái khi không có middleware.
- **Tech mechanism:** tuyến (1) = shortcut web + guide (NaMiBrowser, **tĩnh-ngay**); tuyến (2)
  = Okular/LibreOffice digital signature đã hỗ trợ sẵn + wrapper tiếng Việt; tuyến (3) =
  OpenSC/`pkcs11-tool` phát hiện + verdict theo `COMPAT-ROUTING.md`.
- **Dependencies:** Okular/LibreOffice (đã ship); Firefox (đã ship); [đối tác] xác nhận
  SmartCA/MySign hỗ trợ trình duyệt NaMiOS (ECO-011, quyết định hợp đồng của đơn vị).
- **Effort: M** (web + .p12 tĩnh-ngay) **/ L** (token thật cần phần cứng) **/ XL** (hợp tác CA).
  **Priority: P0** (điểm nghẽn số 1 của kế toán; tuyến remote + .p12 gỡ được ngay một phần).
- **Risk + verify:** token vật lý **có thể blocked cứng** — nói thẳng, đẩy remote/.p12 làm
  tuyến chính. [IP] không tuyên bố "được CA chứng nhận". MUST-VERIFY-ON-HARDWARE: **CÓ** cho
  token; **Không** cho web/.p12 khung. **Owning: 5 (+3).**

---

#### VN-4 · Gói ngôn ngữ Việt hợp nhất (chính tả + ngữ + định dạng + tự sửa "quen tay") · [tĩnh-ngay]

- **User story:** *Là người Việt, tôi muốn máy GẠCH ĐỎ lỗi chính tả tiếng Việt, hiểu "1.234,56
  ₫" và "25/12/2026", và tự sửa viết tắt phổ biến, để soạn thảo nhanh và đúng chuẩn Việt.*
- **Acceptance criteria:**
  - **Chính tả tiếng Việt** bật sẵn trong NaMiOffice + NaMiMail (gói `hunspell-vi` **đã có
    trong package-lists** — việc là **nối + bật mặc định + verify**, không phải thêm mới).
  - **Định dạng vùng Việt chuẩn** system-wide: tiền `1.234.567 ₫`, số thập phân dấu phẩy,
    ngày `dd/MM/yyyy`, tuần bắt đầu Thứ Hai — áp qua locale `vi_VN` + mẫu LibreOffice.
  - **Từ điển đồng nghĩa (thesaurus)** + **gạch nối (hyphenation)** tiếng Việt nếu có gói hợp
    quyền; nếu không → ghi `unknown`, không bịa.
  - **Tự sửa "quen tay"** (tuỳ chọn): bảng autocorrect viết tắt phổ biến → chuẩn (ví dụ "ko" →
    "không") — **mặc định TẮT** để không phiền người đánh máy nhanh; bật được.
  - Test: mở .docx có lỗi chính tả → gạch đỏ đúng; nhập "1234567" định dạng tiền → "1.234.567 ₫".
- **Tech mechanism:** nối `hunspell-vi` vào LibreOffice/Thunderbird; `/etc/skel` registry
  LibreOffice đặt locale số/tiền/ngày; bảng autocorrect VN đóng gói vào
  `/usr/share/namios/office/`.
- **Dependencies:** `hunspell-vi` (đã khai ở `0400`/`0405`); NaMiOffice.
- **Effort: S–M. Priority: P1.**
- **Risk + verify:** chất lượng từ điển hunspell-vi + glyph Inter dấu tiếng Việt chưa đo →
  verify. MUST-VERIFY-ON-HARDWARE: **CÓ** (gạch đỏ hiện trong LO thật). **Owning: 1 (+3).**

---

#### VN-5 · Giọng đọc tiếng Việt (TTS) + đọc màn hình · [R&D nhẹ]

- **User story:** *Là người thị lực kém / người lớn tuổi, tôi muốn máy ĐỌC văn bản/PDF bằng
  giọng tiếng Việt, để dùng máy mà không phải nhìn sát màn hình.*
- **Acceptance criteria:**
  - Nút "Đọc văn bản này" (chọn đoạn → nghe) trong NaMiPDF/NaMiOffice bằng **giọng tiếng Việt**
    tự nhiên, offline.
  - Tích hợp đọc-màn-hình (Orca/accessibility) với giọng Việt cho người khiếm thị.
  - Giọng dùng **model mở, hợp quyền phân phối** (ví dụ Piper vi) — audit license trước khi vào
    ISO; nếu chưa đạt chất lượng/quyền → ghi `đang phát triển`, không ship nửa vời.
  - Test: đọc 1 đoạn tiếng Việt có dấu → phát âm đúng thanh điệu ở mức nghe hiểu được.
- **Tech mechanism:** Piper (TTS neural offline) + Speech Dispatcher + Orca; đóng gói voice vi
  (cần ADR nguồn-gói).
- **Dependencies:** [R&D] chất lượng + giấy phép voice; hạ tầng a11y.
- **Effort: L. Priority: P2.**
- **Risk + verify:** giọng Việt mở chất lượng không chắc → đo trước khi hứa. MUST-VERIFY-ON-
  HARDWARE: **CÓ.** **Owning: 3 (+1 a11y).**

---

#### VN-6 · Bộ gõ thông minh + macro văn bản (gõ tắt, emoji, chèn MST/địa chỉ) · [tĩnh-ngay]

- **User story:** *Là người gõ nhiều, tôi muốn gõ tắt để chèn nhanh địa chỉ công ty, mã số
  thuế, chữ ký email, và chèn emoji, để đỡ lặp lại.*
- **Acceptance criteria:**
  - Bảng **macro gõ tắt** người dùng tự định nghĩa (ví dụ `@mst` → mã số thuế), hoạt động mọi
    ô nhập qua Fcitx5; **không can thiệp ô mật khẩu**.
  - Bộ chọn **emoji** + ký tự đặc biệt tiếng Việt; không phá Telex/VNI.
  - Mặc định rỗng/opt-in; không đổi hành vi gõ cơ bản.
  - Test: định nghĩa 3 macro → chèn đúng; ô mật khẩu không bị can thiệp.
- **Tech mechanism:** Fcitx5 quick-phrase/table addon + cấu hình; tái dùng hạ tầng NaMiType.
- **Dependencies:** fcitx5-unikey (đã ship).
- **Effort: S. Priority: P2.**
- **Risk + verify:** thấp. MUST-VERIFY-ON-HARDWARE: **CÓ** (gõ thật). **Owning: 3.**

---

### TRỤ III — TÀI KHOẢN · ĐỒNG BỘ · SAO LƯU

#### ACC-1 · Sao lưu ra đám mây của BẠN (không khoá người dùng) · [tĩnh-ngay phần lớn]

- **User story:** *Là người dùng, tôi muốn sao lưu tài liệu + cấu hình lên ổ ngoài HOẶC đám
  mây của chính tôi (Google Drive/OneDrive/Nextcloud/WebDAV), để đổi máy/hỏng máy không mất
  gì, mà không bị khoá vào dịch vụ của NaMiOS.*
- **Acceptance criteria:**
  - Kup (đã ship, versioned/dedup bằng bup) + thêm **đích đám mây tuỳ chọn** qua `rclone`
    (người dùng tự nối tài khoản của họ); **mặc định vẫn là ổ ngoài** (U13-03, tách quyền).
  - **Xem trước khi khôi phục** (restore preview), không ghi đè âm thầm (đã là yêu cầu U13-03).
  - Mã hoá at-rest tuỳ chọn cho đích đám mây; nói rõ dữ liệu đi đâu.
  - Test: sao lưu → khôi phục 10 file đúng hash; đích cloud nối bằng tài khoản người dùng.
- **Tech mechanism:** Kup/bup (đã có) + `rclone` remotes + UI chọn đích; không tự tạo tài
  khoản NaMiOS.
- **Dependencies:** Kup/bup (đã khai `0620`); rclone.
- **Effort: M. Priority: P1.**
- **Risk + verify:** gửi dữ liệu nhạy cảm lên cloud bên thứ ba → nhãn rõ + mã hoá tuỳ chọn.
  MUST-VERIFY-ON-HARDWARE: **CÓ** (chu kỳ backup/restore thật). **Owning: 3.**

---

#### ACC-2 · "Mang máy cũ sang máy mới" (profile export/import) · [tĩnh-ngay]

- **User story:** *Là người đổi máy, tôi muốn mang cấu hình + tài liệu + danh sách app từ máy
  NaMiOS cũ sang máy mới trong vài bước, để không phải cài lại từ đầu.*
- **Acceptance criteria:**
  - Xuất "hồ sơ NaMiOS" (cài đặt desktop, bộ gõ, app đã ghim, mẫu, đích backup) ra 1 gói; nhập
    trên máy mới khôi phục lại.
  - Tái dùng/khái quát `migrate.py` (hiện **nhập từ Windows**) sang **NaMiOS→NaMiOS**.
  - Không gồm bí mật/khoá ký; nêu rõ cái gì được mang.
  - Test: export máy A → import máy B → desktop/bộ gõ/app ghim khớp.
- **Tech mechanism:** mở rộng `src/namios_welcome/migrate.py`; gói tar + manifest.
- **Dependencies:** namios-welcome.
- **Effort: M. Priority: P2.**
- **Risk + verify:** mang nhầm bí mật → loại trừ tường minh. MUST-VERIFY-ON-HARDWARE: **CÓ.**
  **Owning: 3.**

---

#### ACC-3 · Tài khoản NaMiOS (tuỳ chọn) + đồng bộ cài đặt · [R&D / đối tác — cược hạ tầng]

- **User story:** *Là người dùng nhiều máy, tôi muốn (tuỳ chọn) một tài khoản để đồng bộ cài
  đặt + khôi phục thiết bị, để trải nghiệm liền mạch — nhưng tôi không bắt buộc phải có.*
- **Acceptance criteria:**
  - Tài khoản **hoàn toàn tuỳ chọn**; máy dùng được đầy đủ khi **không** đăng nhập (local-first).
  - Đồng bộ **chỉ cài đặt desktop** (không file nhạy cảm mặc định); mã hoá đầu-cuối; telemetry
    vẫn tắt.
  - **Trung thực hạ tầng:** đây cần một **dịch vụ backend thật** (chi phí vận hành, bảo mật,
    pháp lý dữ liệu cá nhân VN) — là **cược lớn**, không làm trước khi có pilot + quyết định
    kinh doanh. Có thể thay bằng ACC-1/ACC-2 (không cần backend) cho 90% nhu cầu.
  - Test: tắt tài khoản → không mất chức năng nào.
- **Tech mechanism:** backend đồng bộ (self-host/đối tác) + E2E; HOẶC tầng mỏng trên Nextcloud.
- **Dependencies:** [đối tác/hạ tầng] backend; pháp lý dữ liệu cá nhân.
- **Effort: XL. Priority: P2** (khuyến nghị **hoãn** — ưu tiên ACC-1/ACC-2 trước).
- **Risk + verify:** trách nhiệm pháp lý + bảo mật dữ liệu cá nhân → cân nhắc rất kỹ.
  MUST-VERIFY-ON-HARDWARE: **CÓ.** **Owning: 3 (+pháp lý).**

---

### TRỤ IV — NIỀM TIN · AN TOÀN · CẬP NHẬT

#### SEC-1 · Trung tâm An toàn hợp nhất (NaMiSecurity thành MỘT app) · [tĩnh-ngay]

- **User story:** *Là người quen "có phần mềm diệt virus", tôi muốn MỘT màn hình nói rõ máy
  đang được bảo vệ thế nào (cập nhật, tường lửa, quét tệp, sao lưu) và một nút "Quét thư mục
  này", để yên tâm mà không bị lừa bởi lời hứa suông.*
- **Acceptance criteria:**
  - Một app gom: trạng thái **cập nhật bảo mật**, **tường lửa (ufw)**, **AppArmor**, **quét
    tệp ClamAV on-demand** (nút "Quét thư mục này"), **trạng thái sao lưu** (Kup).
  - **Giáo dục kỳ vọng, KHÔNG overclaim:** giải thích mô hình bảo vệ Linux; **không hứa "chặn
    100% mã độc"** (VN09-030); nêu rõ ClamAV là on-demand, không realtime (và vì sao).
  - Hiển thị "**Tuyên bố giới hạn trung thực**" (7 điều không-overclaim) ở mục Giới thiệu.
  - Test: bấm "Quét thư mục này" → ClamAV chạy + báo kết quả thật; không có câu "an toàn tuyệt
    đối" ở bất kỳ đâu.
- **Tech mechanism:** app Qt/QML gom KCM + gọi `ufw`/`aa-status`/`clamscan`/Kup; tái dùng
  `namios_essentials` cho trạng thái.
- **Dependencies:** ufw/clamav/apparmor/Kup (đã ship `0630`/`0635`/`0620`).
- **Effort: M. Priority: P1.**
- **Risk + verify:** biến "giáo dục" thành "overclaim" → review câu chữ. MUST-VERIFY-ON-
  HARDWARE: **CÓ.** **Owning: 1 (nội dung) + 3 (app).**

---

#### SEC-2 · Bảng điều khiển Riêng tư (Privacy Dashboard) — biến "trung thực" thành tính năng · [tĩnh-ngay]

- **User story:** *Là người lo bị theo dõi, tôi muốn thấy RÕ máy KHÔNG gửi dữ liệu của tôi đi
  đâu, ứng dụng nào đang kết nối mạng, và tự quyết cho phép gì, để tin tưởng NaMiOS.*
- **Acceptance criteria:**
  - Hiển thị: **telemetry = TẮT** (SUP-001), danh sách kết nối mạng đang mở (read-only), app
    nào xin quyền gì; công tắc "chế độ riêng tư".
  - Không tự bật bất kỳ thu thập nào; mọi thứ opt-in + giải thích.
  - Đây là **biến điểm mạnh trung thực của repo thành lợi thế marketing hợp pháp** (không
    overclaim — chỉ hiển thị sự thật).
  - Test: cài mới → telemetry tắt; dashboard phản ánh đúng kết nối thật (đối chiếu `ss`/`netstat`).
- **Tech mechanism:** app đọc trạng thái hệ thống read-only (`ss`, systemd, polkit); không
  thêm agent nền.
- **Dependencies:** none nặng.
- **Effort: S–M. Priority: P2** (nâng P1 khi làm marketing/niềm tin).
- **Risk + verify:** hiển thị sai = phản tác dụng. MUST-VERIFY-ON-HARDWARE: **CÓ.** **Owning:
  1 (+3).**

---

#### SEC-3 · Cập nhật an toàn + quay-lui (Update Center nối thật) 

- **User story:** *Là người sợ "update xong hỏng máy", tôi muốn cập nhật có thể QUAY LUI một
  nút khi hỏng, để không mất máy giữa chừng.*
- **Acceptance criteria:**
  - **Update Center** (ADR-0017, logic đã có ở `src/namios_essentials/update_center.py` +
    `update_txn.py` + `rings.py`) nối với APT + `needrestart` + snapshot Timeshift **trước**
    update + đường rollback rõ.
  - Diễn tập `apt upgrade → needrestart → snapshot → rollback` trên VM (U15-C staged + fault-
    injection mất điện); help tiếng Việt "cập nhật an toàn + cách quay lui".
  - Trung thực: Timeshift là rsync (không A/B nguyên tử) — nêu rõ rủi ro mất-điện còn lại.
  - Test: mô phỏng update hỏng → rollback về bản trước, `/home` nguyên vẹn.
- **Tech mechanism:** nối `namios_essentials` Update Center ↔ Discover/APT/Timeshift; UI
  Update Center (`UPDATE-CENTER-UI.md`).
- **Dependencies:** essentials (đã có); Timeshift (đã có); build host để diễn tập.
- **Effort: M. Priority: P1.**
- **Risk + verify:** rollback phải thật. MUST-VERIFY-ON-HARDWARE: **CÓ** (diễn tập trên VM/
  máy thật). **Owning: 6 (+3).**

---

### TRỤ V — GÓI THIẾT LẬP THEO NGHỀ (điểm tích hợp tất cả) · [tĩnh-ngay]

#### PROF-1 · Hồ sơ nghề (khung) — máy tự cấu hình theo BẠN ở lần đầu

- **User story:** *Là người mới cài, tôi muốn chọn "Tôi là Học sinh / Nhân viên văn phòng /
  Kế toán" và máy tự cài đặt app, mẫu, phím tắt, cổng dịch vụ phù hợp, để dùng được ngay mà
  không phải tự chỉnh.*
- **Acceptance criteria:**
  - Trong `namios-welcome`, bước "Bạn dùng máy để làm gì?" → chọn **hồ sơ nghề**; `apply()` áp
    **gói cấu hình khai báo** (app ghim, mẫu, nhóm việc menu, cổng dịch vụ liên quan, font,
    tuyến ký số).
  - Hồ sơ là **JSON khai báo** (không hard-code), mở rộng được; **bỏ qua được** (chọn "cơ bản").
  - Không cài gì nặng ngoài ý muốn; nêu rõ mỗi hồ sơ thay đổi gì.
  - Test: chọn mỗi hồ sơ → đúng tập cấu hình áp; chọn "cơ bản" → không đổi gì thừa.
- **Tech mechanism:** mở rộng `apply_runtime_desktop_settings()` đọc profile JSON; tái dùng
  user-places/mimeapps/ghim app.
- **Dependencies:** namios-welcome apply() (đã có); VN-2 Services Hub; VN-4 language pack;
  mẫu Office.
- **Effort: M. Priority: P1** (điểm "wow" đầu tiên + buộc chặt các chức năng VN lại với nhau).
- **Risk + verify:** áp sai gây rối → mỗi hồ sơ phải hoàn tác được. MUST-VERIFY-ON-HARDWARE:
  **CÓ.** **Owning: 1 (nội dung hồ sơ) + 3 (apply).**

---

#### PROF-2 · Hồ sơ Học sinh · PROF-3 Hồ sơ Văn phòng · PROF-4 Hồ sơ Kế toán

- **User story:** *Là [học sinh / nhân viên / kế toán], tôi muốn một máy đã có sẵn đúng công
  cụ nghề tôi, để bắt đầu học/làm ngay.*
- **Acceptance criteria (ví dụ theo hồ sơ):**
  - **Học sinh (PROF-2):** từ điển offline + NaMiOffice + trình duyệt + web giáo dục (ghim),
    [tuỳ chọn] công cụ học (GeoGebra nếu hợp quyền), chế độ chữ to; **không** cài nặng.
  - **Văn phòng (PROF-3):** mẫu công văn/biên bản/báo giá (từ §1.3 NANG-CAP), NaMiMail, chính
    tả Việt bật, in/PDF sẵn, cụm "Cài đặt nhanh".
  - **Kế toán (PROF-4):** mẫu bảng lương/hoá đơn/phiếu thu-chi, NaMiSheet (font metric-compat
    Carlito/Caladea, công thức Excel A1), **Cổng Dịch vụ Việt** trỏ thuế/BHXH/hoá đơn, **Trung
    tâm Ký số** (tuyến remote/.p12), cảnh báo trung thực "MISA/HTKK/token xem mục tương thích".
  - Mỗi hồ sơ nêu rõ **việc nào chưa đạt** (ví dụ kế toán: token USB có thể blocked) — không
    hứa trọn gói.
  - Test: mỗi hồ sơ áp đúng tập; mở 1 mẫu nghề ra không lỗi.
- **Tech mechanism:** profile JSON (PROF-1) + mẫu `/usr/share/namios/templates/` + ghim services.
- **Dependencies:** PROF-1; mẫu Office (NANG-CAP §1.3); VN-2; VN-3; VN-4.
- **Effort: M (mỗi hồ sơ S). Priority: P1 (Kế toán/Văn phòng) / P2 (Học sinh).**
- **Risk + verify:** hồ sơ kế toán dễ overclaim "làm được kế toán" → nhãn giới hạn rõ.
  MUST-VERIFY-ON-HARDWARE: **CÓ.** **Owning: 1 (+3).**

---

### TRỤ VI — BỀN BỈ OFFLINE (vùng kết nối yếu) · [tĩnh-ngay]

#### OFF-1 · Trợ giúp + từ điển + AI đều chạy offline

- **User story:** *Là người ở nơi mạng chập chờn, tôi muốn trợ giúp, từ điển, và trợ lý sửa
  lỗi vẫn dùng được khi KHÔNG có mạng, để không bị kẹt.*
- **Acceptance criteria:**
  - NaMiHelp (hướng dẫn xử lý lỗi), từ điển chính tả, SmartAI rule-based + `--explain` **chạy
    offline** (đã là thiết kế — việc là **đóng gói nội dung offline đầy đủ + verify**).
  - Không có chức năng cốt lõi nào chết khi mất mạng (chỉ các "dịch vụ web" mới cần mạng, và
    gắn nhãn rõ "Cần mạng").
  - Test: ngắt mạng → Help/từ điển/SmartAI vẫn mở + giải thích được 10 ca.
- **Tech mechanism:** đóng gói docs/catalog offline; SmartAI offline (đã có).
- **Dependencies:** SmartAI; NaMiHelp (đang phát triển).
- **Effort: S–M. Priority: P2.**
- **Risk + verify:** thấp. MUST-VERIFY-ON-HARDWARE: **Một phần.** **Owning: 1 (+6).**

---

#### OFF-2 · Gương cập nhật nội bộ (trường/làng/doanh nghiệp) · [R&D nhẹ / đối tác]

- **User story:** *Là quản trị phòng máy trường học, tôi muốn một máy tải cập nhật rồi các máy
  khác lấy từ nó qua LAN, để không nghẽn mạng và tiết kiệm băng thông.*
- **Acceptance criteria:**
  - Tài liệu + công cụ dựng **APT mirror/cache nội bộ** (apt-cacher-ng) cho cụm máy NaMiOS.
  - Catalog/metadata cập nhật lấy từ gương nội bộ khi cấu hình; vẫn kiểm chữ ký (không hạ
    bảo mật).
  - Test: 1 máy làm gương → máy thứ 2 cập nhật qua LAN thành công.
- **Tech mechanism:** apt-cacher-ng + hướng dẫn; tùy chọn trong Update Center.
- **Dependencies:** Update Center; hạ tầng LAN.
- **Effort: M. Priority: P2.**
- **Risk + verify:** cấu hình sai hạ bảo mật → giữ verify chữ ký. MUST-VERIFY-ON-HARDWARE:
  **CÓ** (cụm máy). **Owning: 3.**

---

### TRỤ VII — MÁY DÙNG CHUNG / GIA ĐÌNH · [tĩnh-ngay]

#### FAM-1 · Chế độ khách + hồ sơ nhiều người nhẹ

- **User story:** *Là gia đình/trường/tiệm net dùng chung một máy, tôi muốn tạo nhanh tài
  khoản cho từng người + một "chế độ khách" sạch sau mỗi lần dùng, để riêng tư và gọn.*
- **Acceptance criteria:**
  - Tạo người dùng mới trong vài bước (UI tiếng Việt thân thiện hơn KDE mặc định); **chế độ
    khách** xoá dữ liệu phiên khi đăng xuất.
  - Chuyển người dùng nhanh; mỗi người giữ cài đặt/bộ gõ riêng.
  - Test: tạo user + đăng nhập khách → phiên khách sạch sau logout.
- **Tech mechanism:** bọc `accountsservice`/KDE user management + guest session; UI tiếng Việt.
- **Dependencies:** KDE user mgmt (đi kèm).
- **Effort: M. Priority: P2.**
- **Risk + verify:** guest-session trên Wayland/X11 khác nhau → verify. MUST-VERIFY-ON-
  HARDWARE: **CÓ.** **Owning: 3.**

---

## 4. Trung thực: cược R&D lớn vs win nhanh, và việc KHÔNG nên làm

**Win nhanh, xây-tĩnh-được-ngay, giá trị cao (giao dev được liền):** VN-2 Cổng Dịch vụ Việt
(dữ liệu catalog đã có), VN-1 NaMiLịch âm lịch, VN-4 gói ngôn ngữ Việt, PROF-1..4 hồ sơ nghề,
SEC-1 Trung tâm An toàn, SEC-2 Riêng tư, VN-3 tuyến remote/.p12, AI-5 onboarding, VN-6 macro gõ.

**Cược R&D / cần đo trước khi hứa:** AI-1 (NL→action tổng quát — mở rộng quyền, phải rất cẩn
trọng), AI-6 (model local chất lượng tiếng Việt + RAM), AI-4 bậc-2 (embedding local), VN-5
(giọng Việt mở chất lượng + giấy phép).

**Cần đối tác/pháp lý/phần cứng (ngoài lập trình thuần):** VN-3 token USB PKCS#11 (có thể
blocked cứng — đẩy remote), ACC-3 tài khoản+sync (backend + pháp lý dữ liệu cá nhân — **khuyến
nghị hoãn**, dùng ACC-1/ACC-2 thay thế), hợp tác CA/nhà cung cấp (ECO-019/021), codec/giấy
phép media (đã nêu ở NANG-CAP).

**KHÔNG nên làm (giữ phạm vi + trung thực):**
- Không hứa "ký số USB token chạy mọi CA" — bằng chứng hiện tại là `blocked`/`unknown`; nói
  thẳng, ưu tiên ký số từ xa.
- Không bundle công cụ ký bên thứ ba chưa duyệt (MacSigner) vào ISO alpha.
- Không bật AI model local mặc định trên máy yếu; không tải model/khoá tự động.
- Không làm tài khoản+đồng bộ (ACC-3) trước khi có pilot + quyết định kinh doanh + pháp lý.
- Không dán "NaMi" lên dịch vụ bên thứ ba (Zalo/MISA/ngân hàng) — gây nhầm nguồn gốc (TRADEMARK).
- Không để "AI điều khiển máy" vượt Action Catalog tĩnh (không `eval`, không chạy lệnh từ LLM).

---

## 5. TOP-12 LÀM NGAY (xếp hạng: nhanh-nhất × giá-trị-cao-nhất trước)

> Cột **Sẵn sàng:** `TĨNH-NGAY` = giao dev không chờ phần cứng · `CẦN-HW` = phải verify máy
> thật · `R&D`/`ĐỐI-TÁC` = cược lớn/ngoài lập trình.

| # | Chức năng (dev nhận việc ngay) | Trụ | P | Effort | Sẵn sàng | Đội |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **VN-2 Cổng Dịch vụ Việt** — app JSON-driven đọc `catalog/services`+`catalog/compat` (ĐÃ CÓ dữ liệu), tìm-không-dấu, trạng thái 7-nấc trung thực, mở đúng tuyến. Differentiator mạnh nhất, dữ liệu sẵn. | II | P1 | M | **TĨNH-NGAY** (env-check cần HW) | 3(+1) |
| 2 | **VN-1 NaMiLịch — âm lịch + lễ Việt** — Plasma calendar plugin QML; thứ Windows không có; giám khảo đối chiếu 50 mốc. | II | P1 | M | **TĨNH-NGAY** (render cần HW) | 3(+1) |
| 3 | **VN-3 Trung tâm Ký số (tuyến remote + .p12 trước)** — gỡ điểm nghẽn kế toán số 1 bằng ký số từ xa (web, không Wine) + ký `.p12` trong Okular/LO. | II | P0 | M | **TĨNH-NGAY** (token cần HW) | 5(+3) |
| 4 | **VN-4 Gói ngôn ngữ Việt hợp nhất** — nối `hunspell-vi` (đã đóng gói) + định dạng tiền/ngày/số chuẩn Việt + autocorrect tuỳ chọn. | II | P1 | S–M | **TĨNH-NGAY** | 1(+3) |
| 5 | **SEC-1 Trung tâm An toàn hợp nhất** — một app: cập nhật/tường lửa/AppArmor/"Quét thư mục này"/backup + tuyên bố giới hạn trung thực. | IV | P1 | M | **TĨNH-NGAY** | 1(+3) |
| 6 | **AI-0 Hợp nhất trợ lý "giải thích lỗi → nhờ SỬA luôn"** — nối chatbot (#1) ↔ executor có-cổng-quyền (#2) qua `cause_code`; biến BA mảnh AI rời thành một trợ lý thật. Quick win chiến lược. | I | P1 | M | **TĨNH-NGAY** (verify HW) | 6 |
| 7 | **PROF-1 Hồ sơ nghề (khung) + PROF-4 Kế toán + PROF-3 Văn phòng** — máy tự cấu hình theo nghề ở first-run; buộc chặt VN-2/3/4 lại. | V | P1 | M | **TĨNH-NGAY** (apply cần HW) | 1(+3) |
| 8 | **AI-5 Đồng hành onboarding + tour "4 việc đầu tiên"** + hiện "Đã áp dụng ✓" ngay mỗi bước (tái dùng firstrun.apply()). | I | P1 | M | **TĨNH-NGAY** (apply cần HW) | 1(+3) |
| 9 | **AI-6 ADR + runtime model local-first/cloud-optional** — cổng quyết định cho mọi AI; chuẩn hoá `backend_mode_line`/config chatbot thành cài đặt có UI, trung thực "cần khoá/model". | I | P0 | M | **TĨNH-NGAY** (bundle model = XL) | 6 |
| 10 | **AI-2 Viết/tóm tắt/dịch/sửa văn trong NaMiOffice (.oxt)** — khung extension + consent/redaction; tái dùng đường cấu hình LLM OpenAI-compatible đã có ở chatbot; chất lượng cần model (AI-6). | I | P1 | M | **TĨNH-NGAY** (khung) / **R&D** (chất lượng) | 6(+1) |
| 11 | **SEC-3 Cập nhật an toàn + quay-lui (Update Center nối thật)** — nối `namios_essentials` update_center/txn/rings ↔ APT/Timeshift; diễn tập rollback. | IV | P1 | M | **CẦN-HW** (diễn tập VM) | 6(+3) |
| 12 | **AI-1 Thanh lệnh ngôn ngữ tự nhiên (Action Catalog)** — mở rộng tool-broker PL04 từ 10 playbook → Action Catalog argv-tĩnh có-cổng-quyền; "tắt wifi/mở file tuần trước" (nay CHƯA hỗ trợ). | I | P1 | L | **TĨNH-NGAY** (khung) / **R&D** (hiểu câu) | 6(+3) |

> **Ngoài Top-12 nhưng xây-tĩnh-ngay, giá trị cao:** **ACC-1** (sao lưu ra đám mây của BẠN,
> Kup/bup + rclone) + **ACC-2** (mang-máy-cũ-sang-máy-mới) — khuyến nghị làm ngay sau Top-12;
> **SEC-2** (bảng Riêng tư), **VN-6** (macro gõ), **AI-3** (giúp lỗi chủ động).

**Gợi ý thứ tự khởi công cho dev (giá trị thấy sớm):** #1 → #2 → #4 (ba mục thuần-Việt
tĩnh-ngay, dữ liệu/gói đã có) chạy song song; **#6 (nối trợ lý)** là quick win AI rẻ nhất vì
ba mảnh đã có; #9 (ADR model) mở khoá nhánh AI sinh nội dung; #3 (ký số remote/.p12) gỡ nghẽn
kế toán; rồi #5/#7/#8 gói lại thành trải nghiệm "mở máy là dùng được theo nghề". #11/#12 cần
build host/đo thêm.

---

## 6. Nguồn bằng chứng (đọc trong repo, phiên 2026-11-11)

- `docs/roadmap/WINDOWS-FEATURE-PARITY.md`, `docs/roadmap/NANG-CAP-NHU-CAU-NGUOI-DUNG.md`,
  `docs/design/MODERN-FUTURE-UX.md` (ba roadmap đã có — tài liệu này **không lặp**, chỉ bổ sung
  tầng "bứt lên + thuần Việt").
- `docs/apps/NAMI-APP-CATALOG.md` (trạng thái app thật, nhãn NaMiAI partial + chatbot chưa nối).
- **AI — ba thân mã đã xác minh mã nguồn (cố ý tách nhau):** (#1 chatbot giải thích)
  `distro/.../opt/namios/namios_assistant-src/**` (PySide6, OCR tesseract vie+eng, LLM đám mây
  tuỳ chọn OpenAI-compatible, không model local) + `.../usr/share/namios/docs/SMARTAI-ASSISTANT.md`;
  (#2 executor có-quyền) `.../usr/local/bin/namios-smartai{,-policy.sh}` + `SMARTAI-ORCHESTRATOR.md`;
  (#3 engine PL04 mock, 4 intent, model-router chưa nối) `src/namios_smartai/**` +
  `SMARTAI-TOOL-BROKER.md` + `ADR-0018/0021`. `src/namios_essentials/**` (update_center/txn/
  rings/cert_workflow/labels/anti_impersonation) = Update Center + governance đã có để mở rộng.
- `docs/wine/KY-SO-PKCS11-RESEARCH.md` (ký số từ xa web-first vs USB token blocked) +
  `docs/wine/WINE-COMPAT-MATRIX.md`.
- `docs/specs/PHU-LUC-02-HE-SINH-THAI-VN.md` (ECO-001..024: service-catalog, 7-nấc, sign-center,
  Windows-bridge) + **`catalog/services/*.json` + `catalog/compat/*.json` ĐÃ CÓ dữ liệu**.
- `src/namios_welcome/{firstrun.py,ui.py,migrate.py}` (apply() thật + import Windows để khái quát).
- `distro/live-build/config/package-lists/*` (đã có: `hunspell-vi`, `libreoffice-l10n-vi`,
  Kup/bup, Carlito/Caladea, ClamAV/ufw/AppArmor, Timeshift; **chưa có**: âm lịch, TTS Việt,
  Services-Hub app, Sign-Center app).
- `docs/adr/0011-...` (ranh giới IP familiar-not-clone), `docs/branding/TRADEMARK-LICENSE-
  COMPLIANCE.md`, `docs/design/DESIGN-SYSTEM.md` §7 (nhóm việc).

*Hết tài liệu. Mọi khối trên là **đề xuất dev-ready**; chưa khối nào `verified_on_host`. Giao
các mục **TĨNH-NGAY** trong Top-12 cho dev trước — chúng không chờ phần cứng.*
