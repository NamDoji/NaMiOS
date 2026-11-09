# NaMiOS — Bộ chọn tuyến ứng dụng Windows/.NET (COMPAT-ROUTING)

- **Năng lực:** Phụ lục 13 **U13-09 "Bộ chọn tuyến app Windows"** (P1). Quyết định chiến lược: `docs/adr/ADR-0015-dotnet-windows-compat-strategy.md`.
- **Trạng thái:** `specified` — đây là **đặc tả taxonomy + schema + cây quyết định**, chưa có app nào được chứng nhận chạy thật.
- **Công cụ gợi ý:** `distro/live-build/config/includes.chroot/usr/local/bin/namios-compat-assessor` (chỉ **đề xuất** tuyến; không phải verdict).
- **Quy tắc tối cao (U13-09, §6):** *GUI mở ra ≠ app chạy được.* App mở được cửa sổ nhưng **không in / không ký / không kết nối thiết bị** ⇒ verdict **`partial`** hoặc **`blocked`**, **không bao giờ `ready`**.

## 1. Taxonomy 7 tuyến

| Tuyến | Nghĩa | Khi nào | Cần gì | Rủi ro chính |
| --- | --- | --- | --- | --- |
| `native` | App Linux gốc (gói `.deb`/Flatpak/repo) | Có bản Linux chính thức hoặc tương đương | apt / Flatpak | Hầu như không |
| `web` | Dùng bản web / PWA thay app cài | Dịch vụ có web app đủ dùng (Zalo Web, Office web...) | Trình duyệt | Thiếu tính năng offline/thiết bị |
| `dotnet-native` | **.NET hiện đại** (Core/5–8) chạy native qua `dotnet` | Binary là .NET đa nền tảng (có `*.runtimeconfig.json`/`*.deps.json`) | `dotnet-runtime-8.0` (+ `aspnetcore-runtime-8.0`) | API phụ thuộc Windows (Registry, WinForms/WPF) vẫn lỗi |
| `mono` | **.NET Framework** chạy native qua **Mono**, **không Wine** | App console/WinForms .NET Framework mức vừa | `mono-complete` | **Không WPF**; thiếu vài API Framework + P/Invoke Win32 |
| `wine` | App **Win32 thuần** (native PE, không .NET) chạy qua Wine | `.exe`/`.msi` native PE | `wine` (+ `winetricks`) | Không driver kernel; in/thiết bị có thể hỏng |
| `wine+dotnet-framework` | App **.NET Framework** cần Wine (WPF / Win32 sâu) | Mono không đạt; cần hành vi Windows thật | `wine` + `wine-mono` (hoặc `winetricks dotnet48`) | Nặng, dễ vỡ theo version; phải pin + retest hash |
| `blocked` | Chưa có đường chạy trung thực | Cần driver/token/middleware Windows không có trên Linux | — | Ký số USB token, driver thiết bị, in nghiệp vụ đặc thù |

> **`dotnet-native` vs `mono`:** đây là ranh giới "hai thế giới .NET" (xem ADR-0015). `dotnet-native` = .NET **hiện đại** (Microsoft phát hành bản Linux). `mono` = .NET **Framework** cổ điển (Microsoft chỉ ra cho Windows) chạy nhờ Mono. Nhầm hai cái này là nguồn sai sót phổ biến nhất.

## 2. Cây quyết định (khớp với `namios-compat-assessor`)

```text
Đầu vào: đường dẫn file hoặc URL
│
├─ Là URL (http/https)?
│     └─ CÓ → gợi ý `web` (kiểm xem có bản web/PWA đủ dùng không)
│
├─ Đuôi .deb?
│     └─ CÓ → `native` (cài qua apt/dpkg)
│
├─ Đuôi .msi?
│     └─ CÓ → `wine` (chạy qua msiexec; nếu là bộ cài .NET Framework → `wine+dotnet-framework`)
│
├─ Đuôi .dll?
│     └─ CÓ → KHÔNG tự chạy được: .dll là thư viện, không phải app
│              → xác định .exe chủ gọi nó rồi đánh giá lại (mặc định `blocked`/cần ngữ cảnh)
│
└─ Đuôi .exe (hoặc PE khác) → soi bằng `file` + chuỗi trong binary:
      │
      ├─ Có sibling `*.runtimeconfig.json` hoặc `*.deps.json`? (hoặc chuỗi "runtimeconfig")
      │     └─ CÓ → `dotnet-native`  (.NET hiện đại, chạy qua `dotnet`)
      │
      ├─ `file` báo ".Net assembly" / binary chứa "mscoree"|"mscorlib"|"System."?
      │     ├─ chứa "PresentationFramework"|"WindowsBase"|"System.Xaml" (WPF)?
      │     │     └─ CÓ → `wine+dotnet-framework`  (Mono không làm WPF)
      │     └─ còn lại → `mono`  (thử Mono trước; không đạt thì hạ xuống wine+dotnet-framework)
      │
      ├─ `file` báo PE32/PE32+ native (không .NET)?
      │     └─ CÓ → `wine`  (Win32 thuần)
      │
      └─ Không nhận dạng được → `blocked` (chưa đủ thông tin; cần soi tay / chạy thử)
```

**Sau mọi nhánh, in cảnh báo cố định:** nếu công việc thật cần **in / ký số USB token / kết nối thiết bị**, verdict có thể tụt về `partial`/`blocked` **bất kể** tuyến trên — vì Wine không cấp driver kernel Windows (ADR-0015, Phụ lục 13 §6 [2]).

## 3. Schema hồ sơ từng app (per-app compatibility record)

Mỗi app được đánh giá phải có **một hồ sơ** theo schema dưới. Hồ sơ **không** được ghi `ready` nếu thiếu bằng chứng công việc thật.

```jsonc
{
  "app": "Tên phần mềm",                 // bắt buộc
  "publisher": "Nhà phát hành",          // tùy chọn
  "version": "x.y.z",                    // bắt buộc — verdict gắn với ĐÚNG version này
  "hash_sha256": "…",                    // bắt buộc — hash binary đã test; đổi hash ⇒ retest (U13-10)
  "input_kind": "exe|msi|dll|deb|url",   // loại đầu vào
  "dotnet_world": "none|dotnet-core|dotnet-framework", // thế giới .NET nào (ADR-0015)
  "route": "native|web|dotnet-native|mono|wine|wine+dotnet-framework|blocked", // tuyến đã chọn
  "route_source": "assessor-heuristic|tester-manual", // gợi ý máy hay người test chốt
  "workflow_tested": [                   // CÔNG VIỆC THẬT đã chạy, không phải "mở GUI"
    {
      "task": "VD: xuất hóa đơn PDF rồi IN ra giấy",
      "result": "ok|fail|not-tested",
      "evidence": "đường dẫn ảnh/tờ in/log đã che bí mật trong qa/evidence-index/"
    }
  ],
  "device_needs": [                      // thiết bị phụ thuộc + model thật
    { "type": "printer|usb-token|scanner|other", "model": "…", "status": "ok|partial|fail|not-tested" }
  ],
  "verdict": "ready|partial|blocked",    // THEO quy tắc §4 — không tự nâng
  "verified_on_host": "NO|QEMU-only|real-hardware", // bắt buộc; ready yêu cầu real-hardware
  "qa_independent": "NO|<ai/người QA>",  // U13-09 cần QA độc lập trước khi ready
  "blockers": ["VD: token CKS cần driver vendor Windows → không ký được trên Wine"],
  "notes": "ghi chú trung thực; liệt kê thứ KHÔNG chạy"
}
```

### 3.1 Ví dụ hồ sơ (mẫu — chưa phải dữ liệu thật)

```jsonc
{
  "app": "Phần mềm kế toán (ví dụ)",
  "version": "2024.1",
  "hash_sha256": "<chưa test>",
  "input_kind": "exe",
  "dotnet_world": "dotnet-framework",
  "route": "wine+dotnet-framework",
  "route_source": "assessor-heuristic",
  "workflow_tested": [
    { "task": "Nhập liệu + lưu sổ", "result": "not-tested", "evidence": "" },
    { "task": "Xuất + IN báo cáo", "result": "not-tested", "evidence": "" },
    { "task": "Ký số nộp thuế (USB token)", "result": "not-tested", "evidence": "" }
  ],
  "device_needs": [
    { "type": "printer", "model": "<chưa chọn>", "status": "not-tested" },
    { "type": "usb-token", "model": "<CA vendor>", "status": "not-tested" }
  ],
  "verdict": "blocked",
  "verified_on_host": "NO",
  "qa_independent": "NO",
  "blockers": ["USB token chữ ký số cần driver+middleware Windows của vendor → Wine không cấp driver kernel"],
  "notes": "GUI có thể mở được KHÔNG đồng nghĩa ký/nộp được. Giữ blocked cho tới khi ký thật đối chiếu biên nhận trên MÁY THẬT."
}
```

## 4. Quy tắc gán verdict (BẮT BUỘC — không được lách)

- `ready` **chỉ khi** đủ **tất cả**: (a) `verified_on_host = real-hardware`; (b) **mọi** `workflow_tested` bắt buộc có `result = ok` **kèm** evidence; (c) mọi `device_needs` bắt buộc `status = ok`; (d) `qa_independent` có người/AI độc lập ký.
- `partial` — chạy được **một phần** công việc thật (ví dụ nhập liệu ok nhưng **in thiếu trang**, hoặc chỉ test trong QEMU) → ghi rõ phần nào ok, phần nào chưa.
- `blocked` — có bước thiết yếu **không** chạy (ký số, in bắt buộc, driver thiết bị) hoặc chưa có đường chạy trung thực.
- **Cấm:** nâng lên `ready` chỉ vì "GUI mở ra" / "cài xong" / "test trong máy ảo". Thiếu bằng chứng ⇒ **mặc định tụt về `partial`/`blocked`**, không phải `ready`.
- Đổi `version` hoặc `hash_sha256` ⇒ hồ sơ cũ **không còn giá trị**, phải **retest** (gắn với U13-10 "app đổi hash cần retest").

## 5. Ranh giới trách nhiệm

- **File này + ADR-0015 + `0660` + `namios-compat-assessor`:** chiến lược tuyến, gói nền, schema, công cụ gợi ý — thuộc phạm vi ADR-0015.
- **KHÔNG thuộc phạm vi này:** Wine capsule runner (WINEPREFIX cô lập từng app, quyền file/network/USB hẹp, snapshot, recipe thực thi) = **U13-10, engineer khác**. Assessor chỉ **đề xuất** tuyến; capsule mới là nơi **chạy** app theo tuyến đó một cách cô lập + an toàn.
- **Catalog hồ sơ app** (tập hợp các record §3) sẽ sống ở nơi do U13-09/U13-11 chốt (ví dụ `catalog/`), đồng bộ với App Center (U13-05) để hiển thị nhãn native/web/Wine + nguồn + quyền trung thực.
