# Hợp đồng sự kiện & lỗi NaMiOS (EVENT-ERROR-CONTRACT)

**Trạng thái:** `specified` — hợp đồng (contract) + catalog máy-đọc có thật trong
repo; **chưa có bất kỳ phát sinh sự kiện/че log/bind UI nào chạy trên máy thật**.
Theo quy ước `docs/STATUS-U13-KIEM-KE.md` §"Quy ước trạng thái": *"Nếu không có
artifact chạy trên máy thật, trạng thái vẫn là `specified`, không phải
`completed`."*
**Ngày:** 09/11/2026.

**Nguồn yêu cầu:** `docs/brand-uiux-v1/04_PROMPT_CLAUDE_CODE.md` §"C. Feedback &
errors" — *"xây event contract và catalog lỗi có `correlation_id`, `phase`,
`cause_code`, `evidence`, `safe_actions`, `result_after_action`; localization
tiếng Việt. Luồng mạng phân biệt radio/SSID/auth/IP/DNS/portal; máy in phân biệt
discovery/backend/queue/device/scan; Bluetooth phân biệt discover/pair/profile/
service. UI phải nói rõ kết nối thành công hay thất bại và lỗi xác định tại bước
nào; lỗi chưa đủ bằng chứng phải nói 'chưa xác định', không bịa nguyên nhân...
Che bí mật trong log."*

**Tệp nguồn sự thật đi kèm:**
- `distro/live-build/config/includes.chroot/usr/share/namios/error-catalog.json`
  — **catalog máy-đọc**, khoá theo `cause_code`. Đây là bản cài được (nằm trong
  ISO ở `/usr/share/namios/error-catalog.json`). Sửa ý nghĩa/hành động của một mã
  thì PHẢI sửa ở đây và giữ khớp với `docs/support/error-codes.md`.
- `docs/support/error-codes.md` — tài liệu người-đọc của tập mã `NM-*` (nguồn sự
  thật cho ý nghĩa/cách xử lý của 8 mã đã có detector trong `namios-chan-doan`;
  §6 mở rộng theo hợp đồng này).
- `distro/.../usr/local/bin/namios-chan-doan` — công cụ CHẨN ĐOÁN chỉ đọc; nơi
  **phát sinh** sự kiện chẩn đoán (hiện in text, phần phát sự kiện có cấu trúc là
  bước tiếp theo — xem §7).
- `distro/.../usr/local/bin/namios-smartai` (+ `namios-smartai-policy.sh`) — nơi
  **tiêu thụ** `cause_code` (nút "Nhờ SmartAI giải thích" ↦ `--explain <mã>`).

> Hai không gian tên tách biệt (giữ nguyên chủ đích cũ): `NM-*` là mã **hướng
> người dùng cuối/IT**; `namios_core.errors.ErrorCode` (`E_*`) là mã máy-đọc cho
> API nội bộ engine Python (`docs/specs/M1-INTERFACES.md`). Hợp đồng này CHỈ nói
> về `NM-*`. Không hợp nhất hai không gian.

---

## 1. Vì sao cần hợp đồng (không chỉ 8 mã cũ)

`namios-chan-doan` (U13-08) đã phân biệt được 4 lớp sự cố ở mức THÔ qua 3 màn
hình (mất mạng / thiếu driver / quyền bị từ chối / app crash) bằng 8 mã `NM-*`.
Yêu cầu §C đòi hỏi mức MỊN hơn cho ba họ thiết bị người dùng chạm tới nhiều
nhất — mạng, máy in, Bluetooth — để UI nói đúng **bước (phase)** nào hỏng thay
vì chỉ "mạng có vấn đề". Hợp đồng này:

1. Định nghĩa **phong bì sự kiện** (event envelope) chuẩn cho mọi sự kiện chẩn
   đoán/lỗi (§2).
2. Định nghĩa **phase chính xác** cho 3 họ (§3) + quy tắc "CHƯA XÁC ĐỊNH" (§4).
3. Ánh xạ phase → `cause_code` trong catalog máy-đọc (§5).
4. Đặc tả **ErrorCard** (panel lỗi) bind vào catalog (§6).
5. Liệt kê test cần có trước khi lên `partial`/`completed` (§7).

Mức mịn mới **không phá** 8 mã cũ: 8 mã giữ nguyên giá trị + ý nghĩa; hợp đồng
thêm mã mới và gán phase cho cả mã cũ.

---

## 2. Phong bì sự kiện (event envelope)

Mỗi sự kiện chẩn đoán/lỗi mang ĐÚNG các trường sau. Catalog (`error-catalog.json`)
cung cấp phần **tĩnh** (theo `cause_code`); công cụ phát sự kiện điền phần
**động** (runtime).

| Trường | Nguồn | Ý nghĩa | Ví dụ |
| --- | --- | --- | --- |
| `correlation_id` | runtime | Khoá liên kết mọi dòng thuộc CÙNG một lần xử lý (chẩn đoán → giải thích → hành động → kiểm kết quả). Dạng `YYYYmmdd-HHMMSS-<pid>-<rand>`. | `20261109-142233-5312-8471` |
| `phase` | catalog | Bước trong pipeline của họ thiết bị nơi lỗi được định vị. Giá trị hợp lệ theo §3. | `dns` |
| `cause_code` | catalog | Mã `NM-*` (khoá catalog). `NM-<NHÓM>-000` = CHƯA XÁC ĐỊNH. | `NM-NET-007` |
| `result` | runtime | Kết quả quan sát: `success` \| `failure` \| `unknown`. UI PHẢI nói rõ thành công hay thất bại; thiếu bằng chứng → `unknown` (không đoán). | `failure` |
| `evidence` | runtime (khuôn: catalog.`needs_evidence`) | Bằng chứng ĐÃ QUAN SÁT (lệnh read-only + trích xuất **đã che bí mật**). Rỗng/không đủ → `cause_code` phải là `*-000`. | `getent hosts example.com → fail; nmcli dev show: DNS trống` |
| `safe_actions` | catalog | Danh sách hành động AN TOÀN gợi ý (đã phân loại `read-only`/`state-change`/`launch`/`manual`, kèm `privileged` + `undo`). | xem catalog |
| `result_after_action` | runtime | Sau khi một `safe_action` chạy: `fixed` \| `unchanged` \| `partial` \| `blocked` \| `unknown`, kèm bằng chứng kiểm lại (read-only, đã che). KHÔNG tự tuyên bố `fixed` nếu không kiểm được — mặc định `unknown`. | `unknown (đã chạy nmcli networking on, người dùng tự thử lại web)` |
| `l10n_key` | catalog | Khoá bản địa hoá ổn định (xem §2.1). | `err.net.dns` |
| `timestamp` | runtime | Thời điểm ISO-8601 local. | `2026-11-09T14:22:33+07:00` |
| `source_tool` | runtime | Công cụ phát: `namios-chan-doan` \| `namios-smartai` \| `error-card`. | `namios-chan-doan` |

**Bất biến:**
- `result ∈ {failure, unknown}` ⇒ UI hiển thị `phase` + `cause_code` + `evidence`.
- `cause_code` kết thúc `-000` ⇔ `phase = unknown` ⇔ UI nói "CHƯA XÁC ĐỊNH".
- `evidence` và `result_after_action` **luôn** đi qua bộ che bí mật trước khi ghi
  log/hiển thị kỹ thuật (§2.2).

### 2.1 Khoá bản địa hoá (localization keys)

- `cause_code → l10n_key`: mỗi entry catalog có `l10n_key` dạng
  `err.<domain>.<phase>` (vd `err.net.radio`, `err.prn.queue`, `err.bt.pair`).
- Chuỗi tiếng Việt hiện nằm **inline** trong `message_vi` của catalog (nguồn sự
  thật ngắn hạn). Khi dựng ErrorCard Qt (follow-up), bind UI theo `l10n_key` và
  nạp chuỗi từ catalog `vi.json`/gettext — giữ `l10n_key` ổn định để không vỡ
  bản dịch khi đổi câu chữ. `en` để trống cho tới khi có bản dịch (nguyên tắc
  "tiếng Anh theo ngôn ngữ máy", VN-001 — không giả vờ đã dịch).
- Nhãn nút UI (Thử lại / Chi tiết kỹ thuật / Nhờ SmartAI giải thích) dùng khoá
  `ui.errorcard.*` (xem §6).

### 2.2 Che bí mật trong log (bắt buộc)

Mọi `evidence`, `result_after_action`, và gói "Chi tiết kỹ thuật" xuất ra PHẢI
che qua `namios_security.redact_text` (+ email + MAC — xem `error-codes.md` §5):
PEM key, `Bearer ...`, `password=`/`token=`/`secret=`/OTP, IP nội bộ RFC1918/
loopback, `/home/<user>`, email, MAC. Thiếu `python3`/`namios_security` → dùng
`sed` dự phòng + **ghi rõ cảnh báo đang ở đường dự phòng** (không che giấu).
`namios-smartai-policy.sh::smartai_redact` dùng đúng nguyên tắc này cho audit log.

---

## 3. Định nghĩa phase (chính xác) cho ba họ

Mỗi họ là một **pipeline có thứ tự**: lỗi được định vị ở bước ĐẦU TIÊN thất bại.
Nếu không đủ bằng chứng để chỉ ra bước nào → `phase = unknown` (`*-000`).

### 3.1 MẠNG — `radio → ssid → auth → ip → dns → portal`

| phase | Nghĩa (bước thất bại) | Bằng chứng read-only điển hình | cause_code |
| --- | --- | --- | --- |
| `radio` | Sóng Wi-Fi tắt (rfkill/chế độ máy bay). | `nmcli radio wifi`=disabled; `rfkill list` blocked | `NM-NET-003` |
| `ssid` | Không thấy mạng (SSID) mong muốn khi quét. | `nmcli -f SSID dev wifi list` thiếu SSID; radio BẬT | `NM-NET-004` |
| `auth` | Xác thực thất bại (sai mật khẩu/WPA-EAP). | NM lặp `need auth`/`authentication failed` | `NM-NET-005` |
| `ip` | Không nhận IP (DHCP hỏng / 169.254). | `ip -4 addr` chỉ link-local; không default route | `NM-NET-006` |
| `dns` | Có IP + route nhưng phân giải tên hỏng. | `getent hosts <domain>` fail; DNS trống | `NM-NET-007` |
| `portal` | Cổng đăng nhập Wi-Fi công cộng / limited. | `nmcli networking connectivity` ∈ {limited,portal,none} | `NM-NET-002` |

Mã thô `NM-NET-001` ("mất mạng hoàn toàn", 8-mã-cũ) = detector hiện có của
`namios-chan-doan` (không giao diện UP / không default route). Trong hợp đồng nó
là **coarse** (`phase=ip`, `refines_to: radio/ssid/auth/ip`): khi có thêm bằng
chứng, làm mịn xuống một trong 4 mã trên; không đủ → giữ thô hoặc `NM-NET-000`.

### 3.2 MÁY IN — `discovery → backend → queue → device → scan`

| phase | Nghĩa | Bằng chứng read-only | cause_code |
| --- | --- | --- | --- |
| `discovery` | Không dò thấy máy in (mạng/USB). | `lpstat -p` trống; `lpinfo -v`/`avahi-browse` không thấy | `NM-PRN-001` |
| `backend` | Dịch vụ in CUPS không chạy/backend lỗi. | `systemctl is-active cups`≠active; `lpstat -r` not running | `NM-PRN-002` |
| `queue` | Hàng đợi treo/giữ, máy in bị pause. | `lpstat -o` tồn đọng; `lpstat -p` disabled/paused | `NM-PRN-003` |
| `device` | Lỗi thiết bị (hết giấy/mực, kẹt, offline). | `lpstat -p` reasons: media-empty/jam/door-open/offline | `NM-PRN-004` |
| `scan` | Không thấy máy quét / quét lỗi (SANE/eSCL). | `scanimage -L` trống | `NM-PRN-005` |

### 3.3 BLUETOOTH — `discover → pair → profile → service`

| phase | Nghĩa | Bằng chứng read-only | cause_code |
| --- | --- | --- | --- |
| `service` | `bluetoothd` không chạy / thiếu bluez (điều kiện nền). | `systemctl is-active bluetooth`≠active; thiếu `bluetoothctl` | `NM-BT-004` |
| `discover` | Không dò thấy thiết bị (adapter tắt/rfkill/chưa vào pairing). | `bluetoothctl show` Powered=no; `rfkill` blocked | `NM-BT-001` |
| `pair` | Ghép nối thất bại (PIN sai/từ chối/timeout). | log `Pairing failed`/`Authentication Failed` | `NM-BT-002` |
| `profile` | Đã ghép nhưng profile không chạy (A2DP/HFP/HID). | Connected=yes nhưng `pactl list cards` không có card BT | `NM-BT-003` |

> Lưu ý thứ tự: `service` là điều kiện nền (kiểm trước); nếu `service` hỏng thì
> không định vị được `discover/pair/profile`.

### 3.4 Các họ còn lại (giữ từ 8 mã cũ)

Driver/đĩa/quyền/ứng dụng giữ nguyên detector đã có trong `namios-chan-doan`,
được gán phase để vào chung phong bì: `firmware`(`NM-DRV-001`),
`driver`(`NM-DRV-002`), `disk`(`NM-DSK-001`), `permission`(`NM-PERM-001/002`),
`app-crash`(`NM-APP-001/002`).

---

## 4. Quy tắc "CHƯA XÁC ĐỊNH" — không bịa nguyên nhân

Đây là bất biến cứng của hợp đồng (§C: *"lỗi chưa đủ bằng chứng phải nói 'chưa
xác định', không bịa nguyên nhân"*):

1. Mỗi họ có một mã sentinel `NM-<NHÓM>-000` (`NM-NET-000`, `NM-PRN-000`,
   `NM-BT-000`) với `phase=unknown`, `default_confidence=thấp`.
2. Công cụ chỉ được gán một `cause_code` cụ thể khi QUAN SÁT đủ `needs_evidence`
   của mã đó (catalog liệt kê). Thiếu → `*-000` + `result=unknown`.
3. Lệnh nền thiếu/bị chặn quyền (vd `kernel.dmesg_restrict`) → báo "không xác
   định được" cho đúng mục đó, **không** suy diễn `success`/`[OK]` (giống nguyên
   tắc đã có ở `namios-chan-doan`: false negative nguy hiểm hơn im lặng).
4. UI với `*-000` hiển thị: "Chưa xác định được nguyên nhân (chưa đủ bằng chứng)"
   + gợi ý mở Chẩn đoán chỉ đọc; **không** hiện danh sách nguyên nhân phỏng đoán.

---

## 5. Ánh xạ phase → cause_code (catalog)

`error-catalog.json` là nguồn máy-đọc. Mỗi entry:

```json
"NM-NET-007": {
  "domain": "mang", "phase": "dns", "cause_code": "NM-NET-007",
  "nm_code": "NM-NET-007", "l10n_key": "err.net.dns",
  "message_vi": "…(bản tiếng Việt hiển thị)…",
  "needs_evidence": ["getent hosts <domain> thất bại …", "nmcli dev show: DNS trống"],
  "safe_actions": [ {"id":"net.renew","label_vi":"…","kind":"state-change",
                     "privileged":false,"command":"nmcli networking on",
                     "undo":"…","playbook":"playbook_net_noinet"}, … ],
  "default_confidence": "vừa",
  "detector": "specified (getent/nmcli DNS — chưa thêm vào namios-chan-doan)"
}
```

- `kind` ∈ {`read-only`, `state-change`, `launch`, `manual`} — ErrorCard và
  SmartAI dùng để quyết định hành động nào cần cổng chính sách (`state-change`)
  và hành động nào chỉ mở GUI cho người dùng (`launch`).
- `privileged: true` ⇒ chạy qua `pkexec` (polkit hỏi mật khẩu) — không có đường
  vòng.
- `playbook` nối mỗi mã về đúng playbook trong `namios-smartai` (hoặc
  `delegate_ket_noi` cho Bluetooth/scan — uỷ sang `namios-ket-noi-thiet-bi`).
- `detector`: `có` = đã có logic quét thật trong `namios-chan-doan` (8 mã cũ);
  `specified` = phase mới theo hợp đồng, detector là bước tiếp theo (§7). Ghi
  thật để không quảng cáo quá năng lực hiện tại.

**Tính nhất quán bắt buộc:** mọi `cause_code` trong catalog phải có mục tương ứng
ở `error-codes.md` (8 mã cũ ở §3; mã mới ở §6) và ngược lại. Test parity (§7) giữ
hai nơi khớp.

---

## 6. UI spec — ErrorCard (panel lỗi)  `[trạng thái: specified — Qt là follow-up]`

> **Đánh dấu rõ:** phần này là **đặc tả component**. Chưa có mã Qt/QML. ErrorCard
> live là việc tiếp theo; dưới đây là hợp đồng để khi dựng không lệch catalog.

ErrorCard là biến thể của `ErrorCard` trong Design System
(`docs/brand-uiux-v1/03_...Design_System.md`; token sáng/tối, focus, zoom 200%,
reduced motion). Nó hiển thị MỘT phong bì sự kiện (§2).

### 6.1 Bố cục

```
┌───────────────────────────────────────────────────────────┐
│  ⚠  <Tiêu đề họ>: <THÀNH CÔNG | THẤT BẠI | CHƯA XÁC ĐỊNH>   │   ← result
│  Bước lỗi: <phase tiếng Việt>   ·  Mã: <cause_code>         │   ← phase + code
│  <message_vi của cause_code>                                │
│                                                             │
│  [ Thử lại ]  [ Chi tiết kỹ thuật ]  [ Nhờ SmartAI giải thích ] │
│  ▸ Lịch sử (n sự kiện cùng correlation_id)                  │
└───────────────────────────────────────────────────────────┘
```

- **Dòng trạng thái**: màu/token theo `result` — `success`→positive,
  `failure`→danger, `unknown`→neutral/warning. Luôn nói RÕ thành công hay thất
  bại (yêu cầu §C). `unknown` → "CHƯA XÁC ĐỊNH" + câu giải thích thiếu bằng chứng.
- **Dòng bước lỗi**: `phase` (bản tiếng Việt từ bảng §3) + `cause_code`. Với
  `*-000` ẩn tên bước cụ thể, chỉ ghi "chưa xác định".

### 6.2 Ba nút + lịch sử (binding vào catalog)

| Nút | l10n_key | Hành vi | Nguồn dữ liệu |
| --- | --- | --- | --- |
| **Thử lại** | `ui.errorcard.retry` | Chạy LẠI phép chẩn đoán read-only cho đúng `phase`/họ (không phải hành động thay đổi). Cập nhật `result`/`evidence`, sinh dòng lịch sử mới cùng `correlation_id`. | `namios-chan-doan` (read-only) |
| **Chi tiết kỹ thuật** | `ui.errorcard.details` | Mở panel phụ hiện `evidence` + `needs_evidence` + lệnh nền đã chạy, **đã che bí mật** (§2.2). Chỉ đọc. | event.`evidence` + catalog.`needs_evidence` |
| **Nhờ SmartAI giải thích** | `ui.errorcard.ask_ai` | Gọi `namios-smartai --explain <cause_code>`. SmartAI tra catalog, giải thích `message_vi` + `safe_actions` + mức chắc chắn, rồi định tuyến sang playbook đúng (state-change luôn qua cổng chính sách + xác nhận). | `namios-smartai-policy.sh::catalog_lookup` |
| **Lịch sử** | `ui.errorcard.history` | Liệt kê các sự kiện cùng `correlation_id` theo thời gian (chẩn đoán → giải thích → hành động → `result_after_action`). Đọc audit log đã che của SmartAI + log chẩn đoán. | audit log (`smartai-audit.log`) |

**Quy tắc binding:**
- ErrorCard KHÔNG tự chạy `safe_action` nào có `kind=state-change`. Nó chỉ:
  (a) chạy read-only ("Thử lại"), (b) hiển thị (details), (c) chuyển quyền hành
  động cho SmartAI qua `--explain` (nơi có cổng chính sách + xác nhận + audit +
  undo). Đây là lý do hành động thay đổi tập trung ở MỘT cổng duy nhất
  (`namios-smartai-policy.sh`), không rải rác trong UI.
- Mọi nhãn/câu chữ lấy theo `l10n_key` (tiếng Việt). Mã `cause_code` hiển thị
  nguyên văn (không dịch — là định danh).
- `*-000` ⇒ nút "Nhờ SmartAI giải thích" vẫn bật nhưng SmartAI sẽ mở Chẩn đoán
  thu thập thêm, không đề xuất hành động thay đổi khi chưa có nguyên nhân.

### 6.3 Mức chắc chắn (confidence) trên UI

Khi hiện `safe_actions`, ErrorCard/SmartAI gắn nhãn **mức chắc chắn**
`cao`/`vừa`/`thấp` (từ catalog `default_confidence`, có thể hạ xuống khi bằng
chứng yếu). Hiển thị để người dùng biết "nên thử" vs "chỉ là khả năng".

---

## 7. Kiểm thử cần có trước khi lên `partial`/`completed`

Theo §C + §"Kiểm thử và báo cáo" của prompt owner. **Chưa có test nào được
viết** (deliverable này chỉ là hợp đồng + catalog). Các test BẮT BUỘC trước khi
rời `specified`:

**Unit/contract (không cần máy thật):**
- `catalog ↔ error-codes.md` parity: mọi `cause_code` có ở cả hai nơi; `phase`
  thuộc đúng tập `phases` của `domain`; mọi `*-000` có `phase=unknown`.
- Schema catalog: mỗi entry đủ trường bắt buộc; `kind` ∈ tập hợp lệ; `command`
  là argv tĩnh (không chứa ký tự shell nguy hiểm `;|&$>` do người dùng điền);
  `privileged:true` ⇒ `command` bắt đầu bằng `pkexec`.
- Localization: mỗi entry có `l10n_key` duy nhất; `message_vi` không rỗng; không
  lẫn tiếng Anh ở chuỗi người dùng (trừ định danh mã/lệnh).
- Phong bì sự kiện: `result=unknown ⇔ cause_code kết thúc -000`; `evidence` rỗng
  ⇒ không được gán mã ≠ `-000`.
- Redaction: `evidence`/`result_after_action` chứa mẫu bí mật mô phỏng (password/
  token/IP nội bộ/email/MAC/`/home/<user>`) đều bị che; đường dự phòng in cảnh báo.

**Integration bằng sự kiện mô phỏng (fixture, không cần phần cứng):**
- MẠNG: fixture cho từng phase radio/ssid/auth/ip/dns/portal ⇒ đúng `cause_code`;
  fixture thiếu bằng chứng ⇒ `NM-NET-000`.
- MÁY IN: discovery/backend/queue/device/scan ⇒ đúng mã; CUPS tắt ⇒ `NM-PRN-002`.
- BLUETOOTH: service tắt ⇒ `NM-BT-004` (và KHÔNG gán discover/pair/profile khi
  service hỏng); pair-fail ⇒ `NM-BT-002`.
- AI-offline: `--explain <mã>` chạy đủ khi KHÔNG có python3/jq (degrade: vẫn mở
  Chẩn đoán + định tuyến playbook theo tiền tố mã), và khi KHÔNG có backend LLM.

**Máy thật (để lên `completed`, chưa làm):** phát sự kiện thật từ 3 adapter
Wi-Fi (bắt từng phase bằng cách dựng tình huống: tắt radio, sai mật khẩu, DNS
sai…), 3 máy in/MFP (in/scan/queue), 2 thiết bị Bluetooth (audio + HID). Ghi
log đã che + ảnh. Đồng bộ với các test T-C/T-SEC/T-D ở `SMARTAI-ORCHESTRATOR.md`.

---

## 8. Tóm tắt bất biến (để reviewer soi nhanh)

1. Mỗi sự kiện mang đủ 10 trường §2; `result` luôn nói rõ thành công/thất bại/
   chưa xác định.
2. `*-000` = CHƯA XÁC ĐỊNH; không bịa nguyên nhân khi thiếu bằng chứng (§4).
3. Phase chính xác cho 3 họ (§3); mã mới `detector: specified` (trung thực).
4. Hành động `state-change` chỉ chạy qua cổng chính sách + xác nhận +
   audit + undo của SmartAI (không rải rác trong UI) (§6.2).
5. Mọi evidence/log đã che bí mật (§2.2).
6. Catalog ↔ error-codes.md phải khớp (test parity §7).
