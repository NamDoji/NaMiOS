# SmartAI Orchestrator — kênh điều phối xử lý sự cố (U13-12)

**Trạng thái:** `specified` — mã nguồn có thật, chạy được ở chế độ TTY (đã
`bash -n` + chạy thử luồng menu/định tuyến/cổng-quyền trên môi trường dev);
**CHƯA xác minh trên máy thật / trong phiên KDE Plasma có `kdialog`** và chưa
chạy qua `lb build`. Theo Phụ lục 13 §5: không có artifact chạy trên máy thật thì
trạng thái vẫn là `specified`, không phải `completed`.
**Ngày:** 09/11/2026.

**Nguồn yêu cầu:**
`docs/spec-package/NaMiOS_Phu_luc_13_Uu_tien_Nang_cap_va_Cong_Phat_hanh.md`
§2 dòng **U13-12** — *"SmartAI giải quyết việc thật: Hỏi tiếng Việt, diagnostic
read-only, plan/permission/rollback, kiểm kết quả"*; cửa kiểm chứng: *"Giải 10
ca mạng/in/IME thường gặp; tắt AI máy vẫn boot, gõ, in và cập nhật."* — và §3:
*"SmartAI không được thay policy bảo mật, không là điều kiện cho boot/recovery
và không tự xác nhận app hoạt động."*

**Tệp hiện thực (nguồn sự thật của hành vi):**
- `distro/live-build/config/includes.chroot/usr/local/bin/namios-smartai`
  — CLI/kdialog assistant tiếng Việt (bash). **Sửa hành vi ở đây** thì phải cập
  nhật tài liệu này cho khớp (không để hai nơi lệch).
- `distro/live-build/config/includes.chroot/usr/local/bin/namios-smartai-policy.sh`
  — thư viện CHÍNH SÁCH được `source` bởi `namios-smartai`: kế hoạch ≤3 bước +
  mức chắc chắn, cổng phân loại thay đổi (`policy_classify`), AUDIT log đã che bí
  mật, correlation_id, và đọc `error-catalog.json` (`catalog_lookup`). Tách ra để
  sửa chính sách KHÔNG phải động vào 10 playbook; nếu file vắng, `namios-smartai`
  tự định nghĩa stub và vẫn chạy (xem §3bis).
- `distro/.../usr/share/namios/error-catalog.json` +
  `docs/specs/EVENT-ERROR-CONTRACT.md` — hợp đồng sự kiện/lỗi máy-đọc mà SmartAI
  tiêu thụ qua `--explain <cause_code>` (nút "Nhờ SmartAI giải thích" của
  ErrorCard).
- `distro/live-build/config/includes.chroot/usr/share/applications/namios-smartai.desktop`
  — launcher trình đơn ứng dụng + đường mở dự phòng cho widget.
- `distro/live-build/config/includes.chroot/usr/share/plasma/plasmoids/org.namios.smartai/contents/ui/main.qml`
  — widget desktop "Hỏi SmartAI"; bấm pill → mở `namios-smartai`.

**Quan hệ với các module khác:**
- Chẩn đoán (phần CHỈ ĐỌC) được **uỷ** cho `namios-chan-doan` (U13-08,
  `docs/support/error-codes.md`) — SmartAI KHÔNG tự chế lại logic quét.
- Hoàn tác hệ thống được **uỷ** cho Timeshift (U13-02,
  `docs/adr/ADR-0014-update-recovery-strategy.md`) — SmartAI KHÔNG tự chế rollback.
- Engine PL04 `src/namios_smartai/*` (intent → plan → policy/consent → typed
  tool broker) là khung tất định M0; CLI này **không phụ thuộc cứng** vào engine
  đó, chỉ dùng khi có mặt để diễn giải câu hỏi tự do (xem §6).
- Hợp đồng sự kiện/lỗi (`docs/specs/EVENT-ERROR-CONTRACT.md` +
  `/usr/share/namios/error-catalog.json`) là **nguồn cause_code**; SmartAI đọc
  catalog để giải thích + lấy `safe_actions`, KHÔNG tự chế mã lỗi (xem §3bis.4).

> **Trạng thái cập nhật 09/11/2026:** bổ sung lớp chính sách tường minh
> (`namios-smartai-policy.sh`): kế hoạch tối đa 3 bước + mức chắc chắn
> (cao/vừa/thấp), AUDIT log đã che bí mật + correlation_id, bước KIỂM kết quả
> (read-only), và đường `--explain <mã>` đọc `error-catalog.json`. 10 playbook cũ
> giữ nguyên; thay đổi là bổ sung + hoàn tác được. Vẫn `specified` (chưa máy thật).

---

## 1. Kiến trúc

```
                 ┌───────────────────────────────┐
  Người dùng ──▶ │ Widget "Hỏi SmartAI" (plasmoid)│  bấm pill
                 └───────────────┬───────────────┘
                                 ▼  engine "executable"
                 ┌───────────────────────────────┐
                 │ /usr/local/bin/namios-smartai  │  (bash, thuần userspace)
                 │  • menu tiếng Việt (kdialog/TTY)│
                 │  • 10 playbook tất định         │
                 │  • cổng QUYỀN trước mọi thay đổi │
                 └───┬───────────────┬─────────────┘
         chỉ đọc ▼               thay đổi ▼ (chỉ sau khi đồng ý)
   ┌──────────────────┐   ┌──────────────────────────────────────┐
   │ namios-chan-doan │   │ nmcli / cups / fcitx5 / pkexec /       │
   │ (U13-08, chẩn    │   │ timeshift-gtk (qua pkexec) — argv tĩnh │
   │  đoán read-only) │   │ policy hệ thống (polkit) vẫn hỏi mật   │
   └──────────────────┘   │ khẩu; SmartAI KHÔNG qua mặt            │
                          └──────────────────────────────────────┘
```

Nguyên tắc dòng chảy: **mô tả sự cố (tiếng Việt) → chọn playbook → trình bày KẾ
HOẠCH các bước → với bước thay đổi: HỎI quyền → chạy lệnh argv tĩnh → báo kết quả
trung thực → nêu cách HOÀN TÁC**. Trạng thái "đã sửa hay chưa" do người dùng tự
kiểm (thử lại việc thật), SmartAI không tự tuyên bố "đã xong".

Lớp giao diện: `kdialog` nếu có (phiên KDE), ngược lại rơi về TTY (stdin/stdout)
— y hệt `namios-chan-doan`; tool không chết vì thiếu `kdialog`.

**Chế độ suy giảm (degrade) & offline:** tool chạy hoàn toàn **offline**, không
gọi mạng. Nếu một công cụ nền thiếu (`nmcli`, `cups`, `fcitx5`, `pkexec`,
`timeshift`...), playbook báo rõ "không có công cụ X nên không chạy bước này" và
hướng người dùng sang cách thủ công — **không bịa** là đã sửa, không suy diễn
"ổn" khi thiếu dữ liệu.

---

## 2. Mười ca thường gặp phải xử lý (cửa kiểm chứng U13-12)

| Mã ca | Nhóm | Tình huống | Playbook (hàm) | Bước thay đổi (cần quyền) |
| --- | --- | --- | --- | --- |
| C1 | Mạng | Mất mạng hoàn toàn (không Wi-Fi/Ethernet) | `playbook_net_down` | `nmcli radio wifi on`; `nmcli networking on` |
| C2 | Mạng | Đã nối nhưng không vào được Internet (DNS/captive portal) | `playbook_net_noinet` | `nmcli networking on`; mở Cài đặt mạng |
| C3 | Mạng | Mạng/Wi-Fi mất sau khi ngủ – thức máy | `playbook_net_resume` | `nmcli networking on` |
| C4 | In | Máy in USB không in, hàng đợi treo | `playbook_print_usb` | `cancel -a`; `pkexec systemctl restart cups` |
| C5 | In | Không tìm thấy máy in mạng | `playbook_print_net` | mở quản lý máy in (thêm theo IP) |
| C6 | In | In ra trang trắng / báo kẹt | `playbook_print_blank` | `cancel -a`; `pkexec systemctl restart cups` |
| C7 | Gõ TV | Không gõ được tiếng Việt (bộ gõ chưa chạy/bật) | `playbook_ime_none` | `fcitx5 -r -d`; mở cấu hình bộ gõ |
| C8 | Gõ TV | Gõ lặp/sai kiểu Telex–VNI trong ứng dụng | `playbook_ime_wrong` | mở cấu hình bộ gõ; `fcitx5 -r -d` |
| C9 | Cập nhật | Cập nhật lỗi → hoàn tác về bản trước | `playbook_update` | `pkexec timeshift-gtk` (người dùng tự chọn điểm) |
| C10 | App Windows | App Windows không mở / mở nhưng không in/ký | `playbook_wine` | mở `winecfg` (KHÔNG xác nhận app chạy được) |

C1–C8 là đúng **"10 ca mạng/in/IME"** theo U13-12 (8 ca chính + C9/C10 bổ sung
đúng danh mục sự cố phổ biến owner nêu: *mạng / in / gõ tiếng Việt / cập nhật /
mở app Windows*). Mỗi playbook: (a) nêu triệu chứng, (b) mời mở Chẩn đoán chỉ
đọc, (c) liệt kê bước đánh dấu `[chỉ đọc]` / `[cần quyền]` / `[tự làm]`.

Người dùng cũng có thể **gõ một câu tiếng Việt** ("không in được", "máy không
vào mạng"...) ở mục 7 — tool định tuyến tất định (khớp từ khoá, có/không dấu)
sang playbook gần nhất; không chắc thì đề nghị mở Chẩn đoán, **không đoán bừa**.

---

## 3. Mô hình QUYỀN + HOÀN TÁC

**Mặc định chỉ đọc.** Không bước nào sửa máy khi chưa được đồng ý.

Mọi bước thay đổi đi qua đúng một trong hai cổng:
- `confirm_and_run` — chạy **đồng bộ** một lệnh argv tĩnh. Trước khi chạy: hiện
  KẾ HOẠCH + đúng dòng lệnh sẽ chạy + câu HOÀN TÁC, rồi hỏi Có/Không. Hủy →
  "KHÔNG có gì thay đổi". Thiếu công cụ → báo rõ, không thay bằng đường khác.
  Sau khi chạy: báo kết quả thật (mã lỗi ≠ 0 → nói "không hoàn tất, thường do
  thiếu quyền/bị chính sách chặn", **không giả vờ thành công**).
- `confirm_and_launch` — mở một GUI chạy **nền** (vd `winecfg`,
  `timeshift-gtk`, Cài đặt) để **người dùng tự thao tác**; SmartAI không bấm thay.

**Cách hoàn tác được nêu theo từng loại thay đổi:**
- Thay đổi **gói/cấu hình hệ thống** → `ROLLBACK_TIMESHIFT`: khôi phục về bản
  trước bằng **Timeshift** (U13-02); Timeshift không đụng `/home`. SmartAI chỉ
  **mở** Timeshift để người dùng tự chọn điểm, **không** tự chạy `--restore`,
  **không** tự chọn điểm hộ (giống `namios-chan-doan`).
- Thay đổi **tạm thời/không lưu lâu dài** (bật/tắt lại Wi-Fi, networking,
  restart `fcitx5`) → `ROLLBACK_NONE`: chỉ việc bật lại trạng thái cũ / đăng
  xuất–đăng nhập lại; không có cấu hình lâu dài để hoàn tác.
- Hành động **không thể hoàn tác nhưng vô hại** (huỷ lệnh in `cancel -a`) → nói
  thẳng "không hoàn tác được lệnh in đã huỷ — chỉ cần In lại", cấu hình máy in
  không đổi.

**Đặc quyền luôn qua `pkexec`** (polkit) — hệ thống tự hỏi mật khẩu; SmartAI
không có và không cần sudoers riêng. Nếu polkit từ chối, tool báo "bị chính sách
hệ thống chặn", đúng guardrail #1.

---

## 3bis. Mô hình KẾ HOẠCH ≤3 BƯỚC + MỨC CHẮC CHẮN + AUDIT + UNDO + CATALOG

Lớp này (hiện thực ở `namios-smartai-policy.sh`, bật trong `confirm_and_run`/
`confirm_and_launch`) làm chặt yêu cầu §D của owner thành bất biến chạy được.

### 3bis.1 Chẩn đoán CHỈ ĐỌC trước (không đổi)

Mỗi playbook vẫn **mời mở Chẩn đoán chỉ đọc** (`namios-chan-doan`,
`offer_diagnostics`) trước khi đề xuất bất kỳ thay đổi nào. SmartAI không tự chế
lại logic quét (uỷ U13-08).

### 3bis.2 KẾ HOẠCH tối đa 3 bước, mỗi bước có bằng chứng + mức chắc chắn

- Helper `smartai_plan_add` **từ chối** bước thứ 4 (bất biến "tối đa 3 bước");
  `smartai_plan_render` in `cao|vừa|thấp` cho từng bước.
- Tại điểm hành động, `confirm_and_run` hiển thị cho MỖI bước có thay đổi:
  `Bằng chứng:` (mặc định "triệu chứng + chẩn đoán chỉ đọc", playbook có thể đặt
  `STEP_EVIDENCE` chính xác hơn, vd trỏ `NM-NET-001/003`) và
  `Mức chắc chắn:` (`STEP_CONFIDENCE`, mặc định `vừa`).
- Mỗi playbook vốn đã chỉ có ≤3 bước `[cần quyền]` (mạng 2, in 2, gõ 1, cập nhật
  1, wine 1) → bất biến giữ được mà không phải cắt playbook.

### 3bis.3 Cổng CHÍNH SÁCH cho hành động thay đổi → xác nhận → KIỂM → AUDIT → UNDO

Mọi hành động **đổi cấu hình / cài backend / reset dịch vụ / xoá queue / cấp
quyền** đi qua `confirm_and_run` (hoặc `confirm_and_launch` cho GUI), nay thêm:

1. **Phân loại** (`smartai_policy_classify`): đặt `POLICY_CLASS` ("reset DỊCH VỤ",
   "XOÁ HÀNG ĐỢI in", "BẬT/TẮT trạng thái mạng (tạm thời)", "CÀI/ĐỔI GÓI", "khởi
   động lại BỘ GÕ"…) + gợi ý hoàn tác chuẩn (`POLICY_UNDO_HINT`). Lệnh đặc quyền
   nhận diện `pkexec` → `POLICY_PRIVILEGED=yes`.
2. **Xác nhận tường minh**: hiện KẾ HOẠCH + **lệnh argv tĩnh** sẽ chạy ("KHÔNG do
   AI tự sinh") + loại thay đổi + cách HOÀN TÁC, rồi hỏi Có/Không. Hủy → "KHÔNG
   có gì thay đổi" + ghi audit `cancelled`.
3. **Chạy** argv tĩnh (không `eval`, không chuỗi động).
4. **KIỂM kết quả** (read-only): nếu playbook đặt `VERIFY_CMD` (argv tĩnh read-
   only, vd `nmcli networking connectivity`, `lpstat -r`), chạy và hiển thị kết
   quả như **bằng chứng** — KHÔNG tự tuyên bố "đã xong" (guardrail #3; người dùng
   tự thử lại việc thật).
5. **AUDIT** (`smartai_audit`): ghi MỘT dòng vào
   `${XDG_STATE_HOME:-~/.local/state}/namios/smartai-audit.log`:
   `ts | corr | tag | status(ran/cancelled/skipped/launched) | rc | class | cmd |
   undo | result`, **đã che bí mật** qua `smartai_redact` (namios_security +
   email/MAC; thiếu python3 → sed dự phòng, cùng nguyên tắc error-codes.md §5).
   `SMARTAI_CORRELATION_ID` nối mọi dòng của một phiên (xem mục 9 menu "Lịch sử
   hành động").
6. **UNDO**: nêu theo loại thay đổi — `ROLLBACK_TIMESHIFT` cho gói/cấu hình/dịch
   vụ hệ thống (U13-02; SmartAI chỉ MỞ Timeshift, không tự `--restore`),
   `ROLLBACK_NONE` cho thay đổi tạm thời, "in lại" cho `cancel -a`.

### 3bis.4 Đọc error-catalog.json qua `--explain <cause_code>`

- Nút "Nhờ SmartAI giải thích" của ErrorCard gọi `namios-smartai --explain <mã>`
  (phiên một-lần). `smartai_catalog_lookup` đọc
  `/usr/share/namios/error-catalog.json` (python3 ưu tiên, jq dự phòng; override
  bằng `NAMIOS_ERROR_CATALOG` khi test) → `phase`, `message_vi`,
  `default_confidence`, `safe_actions`.
- SmartAI giải thích **bước lỗi (phase) + mức chắc chắn + hành động an toàn**,
  nhắc quy tắc CHƯA XÁC ĐỊNH (`*-000` — không bịa), rồi **định tuyến** sang
  playbook theo tiền tố mã: `NM-NET-*`→mạng, `NM-PRN-*`→in (`NM-PRN-005` scan →
  uỷ `namios-ket-noi-thiet-bi`), `NM-BT-*`→uỷ `namios-ket-noi-thiet-bi` (ghép
  nối/profile), khác→mở Chẩn đoán.
- **Degrade:** thiếu catalog/python3/jq, hoặc thiếu cả `namios-smartai-policy.sh`
  → tool vẫn chạy: báo trung thực "chưa đọc được catalog" + hướng dẫn theo nhóm
  (rule-based). AI/LLM offline KHÔNG ảnh hưởng (xem §5, §6).

### 3bis.5 Không AI shell, không tải driver

- Chỉ chạy **argv tĩnh** định sẵn trong script (và `command` trong catalog là
  argv tĩnh, kiểm trong contract test). Không `eval`, không lệnh lấy từ
  log/web/LLM, không `curl|bash`, không `apt-add-repository`/tải driver từ nguồn
  không tin cậy. Phần LLM (nếu có) **chỉ định tuyến** sang playbook, không tự
  sinh rồi chạy lệnh (bất biến PL04).

## 4. Guardrail — ba điều SmartAI KHÔNG BAO GIỜ làm (Phụ lục 13 §3)

Các bất biến này là **thật trong thiết kế**, không chỉ là câu chữ:

1. **KHÔNG thay/nới chính sách bảo mật.**
   - Không có lệnh nào tắt tường lửa, cấp quyền root cho AI, hay bỏ qua hỏi mật
     khẩu. Mọi việc đặc quyền gọi qua `pkexec` → polkit quyết định.
   - Chỉ chạy lệnh **argv tĩnh**; không `eval`, không chạy lệnh lấy từ
     log/web/tài liệu, không `curl|bash` (CLAUDE.md, SAI-019).
   - Phần diễn giải câu hỏi tự do (nếu có engine/LLM) **chỉ định tuyến** sang
     playbook, không bao giờ tự sinh rồi chạy lệnh.

2. **KHÔNG là điều kiện để boot/recovery** — xem §5.

3. **KHÔNG tự xác nhận một ứng dụng "chạy được".**
   - `playbook_wine` nói thẳng: Wine không biến mọi app Windows thành chạy được,
     không biến driver Windows thành driver Linux; app mở được GUI mà không
     in/ký vẫn là "một phần", không "đạt". Việc chứng nhận app/phiên bản/công
     việc là quy trình có kiểm thử + người nghiệp vụ duyệt (M3/M4), không do AI
     tự quyết.
   - Tool không bao giờ in câu "app đã hoạt động".

Banner + mục "Giới thiệu & cam kết an toàn" hiển thị nguyên ba điều trên bằng
tiếng Việt cho người dùng cuối.

---

## 5. Vì sao "tắt AI máy vẫn boot, gõ, in và cập nhật"

Đây là phần cốt lõi của cửa kiểm chứng U13-12 và được bảo đảm bằng **cấu trúc**,
không bằng lời hứa:

- `namios-smartai` là **một tệp chương trình thường** ở `/usr/local/bin`, chạy
  theo yêu cầu (người dùng bấm widget hoặc mở từ trình đơn). **Không** có unit
  systemd, **không** hook boot, **không** nằm trong initramfs/GRUB/recovery nào.
- **Không tiến trình hệ thống nào phụ thuộc nó.** Mạng do NetworkManager, in do
  CUPS, gõ tiếng Việt do fcitx5, cập nhật do Update Center/APT, khôi phục do
  Timeshift + GRUB — tất cả hoạt động độc lập, SmartAI chỉ là lớp **hướng dẫn**
  gọi lại chính các công cụ đó khi người dùng chủ động nhờ.
- Vì vậy: **xoá** `namios-smartai`, **gỡ** plasmoid, hoặc không đặt khoá AI nào
  → máy **vẫn** khởi động, **vẫn** gõ tiếng Việt, **vẫn** in, **vẫn** cập nhật.
- SmartAI cũng chạy **offline** và **không cần khoá AI đám mây**: khi thiếu
  backend, nó dùng playbook tất định (rule-based). Khoá/LLM chỉ là lớp tăng
  cường tuỳ chọn, không phải điều kiện hoạt động.

**Cách chứng minh (test gỡ phụ thuộc):** trên máy thật, `sudo rm
/usr/local/bin/namios-smartai` (hoặc chưa cài), rồi xác nhận 4 việc boot/gõ/in/
cập nhật vẫn chạy — xem T-D ở §7.

---

## 6. Backend LLM tuỳ chọn (không phụ thuộc cứng)

`backend_mode_line` dò các biến môi trường (`NAMIOS_SMARTAI_API_KEY`,
`NAMIOS_SMARTAI_LLM`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) và wrapper `namios`
(engine PL04). Kết quả **chỉ đổi dòng mô tả chế độ** ("hướng dẫn theo quy tắc"
so với "có trợ lý nâng cao khả dụng"); **mọi playbook chạy y hệt**. Thiếu toàn
bộ backend → tool vẫn đầy đủ chức năng. Khi có engine, luồng dự kiến là dùng nó
để *hiểu* câu tiếng Việt (intent) rồi **vẫn** định tuyến sang playbook tất định
— AI đề xuất, không tự hành động; policy + người quyết (bất biến PL04).

---

## 7. Kiểm thử trên máy thật cho cửa U13-12 (10 ca + gỡ phụ thuộc)

Thực hiện trong phiên KDE Plasma thật (có `kdialog`), ghi màn hình + ảnh kết quả
(bản in, ảnh gõ tiếng Việt), log đã che bí mật. Mỗi ca xác nhận: **plan hiện ra
→ hỏi quyền → chỉ chạy khi đồng ý → nêu hoàn tác → kiểm kết quả thật**.

| Test | Dựng tình huống | Kỳ vọng |
| --- | --- | --- |
| **T-C1** | Tắt Wi-Fi phần cứng / rút LAN | Playbook C1 hiện, bật lại Wi-Fi qua `nmcli` sau khi đồng ý, mạng trở lại; hủy thì không đổi gì. |
| **T-C2** | Nối Wi-Fi có captive portal / DNS sai | C2 hướng mở trình duyệt + làm mới IP/DNS; không tự sửa `resolv.conf`. |
| **T-C3** | Suspend rồi resume, Wi-Fi không tự nối | C3 nối lại qua NetworkManager; nếu lặp lại, hướng xuất log gửi hỗ trợ. |
| **T-C4** | In vào máy USB tắt nguồn → hàng đợi treo | C4 xoá hàng đợi + restart CUPS (qua `pkexec`), in lại được 1 trang. |
| **T-C5** | Máy in mạng chưa thêm | C5 mở trình quản lý máy in; xác nhận cùng LAN; không tự thêm hộ. |
| **T-C6** | Gửi lệnh in lỗi → ra trang trắng | C6 xoá hàng đợi + restart CUPS; in lại trang thử ra đúng nội dung. |
| **T-C7** | Vô hiệu bộ gõ / chưa bật | C7 restart `fcitx5` + mở cấu hình; gõ Telex ra tiếng Việt trong Office & trình duyệt. |
| **T-C8** | Đặt sai kiểu (VNI khi muốn Telex) | C8 mở cấu hình đổi kiểu + restart; gõ đúng dấu, không lặp ký tự. |
| **T-C9** | Sau 1 cập nhật hỏng, có snapshot Timeshift | C9 mở Timeshift để **người dùng** chọn điểm khôi phục; SmartAI không tự restore; `/home` còn nguyên. |
| **T-C10** | Một app Windows .exe qua Wine | C10 mở `winecfg`, nêu rõ "không bảo đảm app chạy/in/ký được"; người dùng tự kiểm việc thật. |
| **T-SEC** | Thử ép SmartAI tắt tường lửa / cấp root | Không có đường nào làm được; việc đặc quyền đều rơi vào `pkexec` (hỏi mật khẩu). |
| **T-D** (gỡ phụ thuộc) | Gỡ/đổi tên `namios-smartai` + gỡ plasmoid, **không** đặt khoá AI | Máy vẫn **boot**, **gõ** tiếng Việt, **in**, và **cập nhật** bình thường. |

**Test hợp đồng/đơn vị cho lớp chính sách mới (chưa viết — bước tiếp theo, không
cần máy thật):**

| Test | Kiểm | Kỳ vọng |
| --- | --- | --- |
| **T-PLAN** | `smartai_plan_add` bước thứ 4 | Bị từ chối (ép "tối đa 3 bước"); `smartai_plan_render` in `cao/vừa/thấp`. |
| **T-POLICY** | `smartai_policy_classify` cho pkexec/cancel/nmcli/fcitx5/apt | Đúng lớp + `POLICY_PRIVILEGED=yes` khi `pkexec`. |
| **T-AUDIT** | Chạy 1 bước qua `confirm_and_run` (nmcli giả) | Ghi 1 dòng audit `status=ran`, có `corr`, bí mật (password/IP/email/MAC) bị che. |
| **T-VERIFY** | `VERIFY_CMD` đặt trước bước | Hiện "Kiểm lại (chỉ đọc)" + output, KHÔNG in "app/việc đã xong". |
| **T-EXPLAIN** | `--explain NM-NET-007` / mã `*-000` / mã lạ | Giải thích đúng phase+actions / nói "CHƯA XÁC ĐỊNH" / báo không có trong catalog; đều exit 0. |
| **T-CATALOG-PARITY** | catalog ↔ `error-codes.md` ↔ `namios-chan-doan` | Mọi `cause_code` khớp; `command` là argv tĩnh; `privileged:true ⇒ pkexec`. |
| **T-OFFLINE/DEGRADE** | Gỡ `namios-smartai-policy.sh` hoặc catalog hoặc python3/jq | Tool vẫn chạy (stub), báo trung thực, không sập. |

Các test trên đã **chạy tay smoke** khi dựng (plan ≤3, classify, audit+redact,
catalog lookup, `--explain`, degrade) nhưng **chưa** được đóng thành pytest/bats
trong `tests/` — đó là việc bắt buộc trước khi rời `specified`, cùng với các
contract/integration test ở `EVENT-ERROR-CONTRACT.md` §7 (sự kiện mô phỏng Wi-Fi/
auth/DNS, in/scan, Bluetooth, AI-offline, localization, redaction).

Chỉ khi T-C1…T-C10 + T-SEC + T-D **và** các test hợp đồng/đơn vị trên pass (máy
thật cho nhóm T-C/T-SEC/T-D, CI cho nhóm contract) — với bằng chứng — thì U13-12
mới chuyển từ `specified` sang `completed`.
