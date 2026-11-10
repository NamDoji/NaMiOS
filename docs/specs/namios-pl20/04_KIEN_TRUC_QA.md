# 04. Kiến trúc, bảo mật, cập nhật và nghiệm thu

## 1. File routing và plugin contract

NaMiFiles dùng shared-mime-info/desktop entries/mimeapps theo chuẩn Linux để nối loại tệp với ứng dụng; nội dung được sniff trước preview, đuôi chỉ là gợi ý. Registry có MIME, extension, magic, app id, action view/edit/create/export, offline, support_level, priority, version, test fixture, permission, owner, last_verified. “Mở bằng…” và app mặc định là quyền lựa chọn của người dùng, thay đổi khi update app không được reset im lặng.

API cho viewer/editor: OpenRequest(file portal handle, source trust, intended action), CapabilityReport(format variant, features, unknowns, warnings), SavePlan(output, lossy features, signature status), Result(error code, safe next actions). File từ USB/email/browser vào sandbox; preview không chạy script/macro. Không cho fallback tự gửi file qua dịch vụ online chỉ vì app local không hỗ trợ.

## 2. Bảo mật định dạng

Archives: ngăn zip slip/path traversal, symlink escape, bomb, file count/size, nested depth, encrypted ambiguity. SVG/PDF/CAD: chặn script, external reference/network fetch và embedded executable mặc định. Ảnh/media: decoder sandbox và fuzz, time/resource quota; thumbnail riêng quyền. Document Office: macro chặn mặc định, Save Safety theo NaMiOffice. Không coi việc quét malware là đủ thay parser sandbox. Cập nhật codec/importer/renderer nhanh qua NaMiUpdates có chữ ký, test hồi quy định dạng và rollback app.

## 3. Manifest ứng dụng và bản phát hành

Mỗi app trong ISO có id/tên/nhà phát hành, package hash/version, license/notice/source, icon provenance, MIME, quyền, offline status, update channel, hardware support, test date. Mỗi web shortcut có domain chính thức, nhãn bên thứ ba, không kèm cookie, browser requirement và link hết hạn kiểm lại. Build ISO tự sinh danh mục “Ứng dụng của tôi”; website chỉ công bố danh mục từ cùng manifest đã ký. Khi bỏ một codec/app vì giấy phép, release notes và ma trận MIME cập nhật đồng bộ.

Nguồn upstream cần được pin, audit và theo dõi CVE. FFmpeg/GStreamer hoặc player có thể hỗ trợ kỹ thuật một codec nhưng quyền phân phối có thể khác theo cấu hình/địa bàn; legal review từng codec/binary. Libarchive/7-Zip/RAR có điều kiện giấy phép từng phần; không phân phối gói thương mại trái phép. CAD DWG dùng importer/converter theo version, bản quyền và test; không coi FreeCAD hỗ trợ file là chứng nhận AutoCAD workflow.

## 4. Corpus thử nghiệm P0

| ID | Tệp và thao tác | Gate |
|---|---|---|
| F20-01 | DOCX/XLSX/PPTX/ODF từ tác vụ Việt Nam | Đúng app, báo tính năng rủi ro, save bản sao, round-trip |
| F20-02 | PDF có chữ ký, ảnh quét, form | NaMiPDF báo đúng trạng thái, không làm hỏng chữ ký/bản gốc |
| F20-03 | ZIP/7z/tar, RAR4/RAR5 và password/multi-volume | Giải nén đúng hoặc cảnh báo; không escape/bomb |
| F20-04 | Tệp tên tiếng Việt, đuôi giả, path dài, USB mất kết nối | MIME/sniff đúng, không chạy tệp giả, file copy an toàn |
| F20-05 | JPEG/PNG/WebP/GIF/TIFF và EXIF/ICC | Xem đúng orientation/color/animation, export không mất âm thầm |
| F20-06 | MP3/FLAC/WAV/AAC, MP4/MKV/WebM với codec khác | Phát/seek/subtitle đúng theo matrix, lỗi codec rõ |
| F20-07 | SVG/ODG/DXF/DWG có font/xref | View/edit đúng cấp, thiếu đối tượng có warning |
| F20-08 | Gõ Telex/VNI vào Office/PDF/CAD/browser, tên tệp | Không mất dấu, không lộ phím mật khẩu |
| F20-09 | Mạng tắt, app web được ghim | Native app dùng offline; web nói cần mạng, không quay loading mãi |
| F20-10 | Update browser/media/Office, đổi app mặc định | MIME người dùng giữ nguyên; rollback khi regression |
| F20-11 | Mã độc thử nghiệm, SVG external, archive traversal | Sandbox chặn, không chạm file ngoài đích |
| F20-12 | Người mới tìm app và xử lý lỗi phổ biến | Hoàn thành workflow bằng UI/keyboard, lỗi có next action |

Gate trước ISO: P0 app thật cài và chạy offline theo manifest; không đánh dấu app web là native; file thường mở bằng nhấp đôi; không có parser cho tệp không tin cậy chạy với quyền rộng; không mất tệp gốc khi save/chuyển đổi; không có lỗ hổng nghiêm trọng chưa xử lý. Theo dõi hiệu năng, crash, dung lượng ISO, bộ nhớ trên máy baseline và thời gian mở tệp; không đưa số giả trong marketing.

## 5. Nguồn chính thức đối chiếu

- Freedesktop MIME associations: https://specifications.freedesktop.org/mime-apps/latest-single/
- Shared MIME database: https://specifications.freedesktop.org/shared-mime-info/latest-single/
- Libarchive supported formats: https://www.libarchive.org/
- 7-Zip licensing và 7z: https://www.7-zip.org/ ; https://www.7-zip.org/7z.html
- FreeCAD features/formats: https://www.freecad.org/features
- FFmpeg legal/license: https://www.ffmpeg.org/legal.html

Tại thời điểm triển khai phải pin phiên bản và kiểm nguồn thật, không suy khả năng từ danh sách định dạng trên website upstream.
