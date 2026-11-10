# 02. Mở tệp, định dạng và mức độ hỗ trợ

## 1. Luật chung

Mỗi định dạng có ma trận **xem / sửa / tạo / xuất / mở lại không mất dữ liệu / in / offline** theo ứng dụng và version. Không gộp “mở được” với “sửa được”. NaMiFiles dò MIME bằng nội dung và cấu trúc, đối chiếu đuôi tên, không mở mã thực thi chỉ vì người dùng đổi đuôi; tệp lạ hiển thị “Không nhận diện được định dạng” cùng tùy chọn an toàn. Trước chuyển đổi hoặc lưu vào định dạng khác, tạo bản sao và cảnh báo nguy cơ mất macro, lớp, liên kết, công thức, font, chú thích hay chữ ký.

| Nhóm | Định dạng P0 xem/mở | Sửa/tạo mặc định | Giới hạn phải nêu |
|---|---|---|---|
| Văn bản | DOCX, DOC, ODT, RTF, TXT, PDF | NaMiWriter cho văn bản; NaMiPDF theo pha | DOCX phức tạp, macro/VBA, chữ ký và font theo corpus |
| Bảng tính | XLSX, XLS, ODS, CSV/TSV | NaMiSheet | Công thức, Pivot, chart, XLSM/XLSB và Power Query theo phiên bản/ma trận |
| Trình chiếu | PPTX, PPT, ODP | NaMiSlides | Animation, video, font và object nhúng có thể khác |
| PDF | PDF thường, PDF/A, biểu mẫu AcroForm | NaMiPDF; sửa nội dung/OCR/ký/redact theo cổng riêng | XFA, DRM, chữ ký, ảnh quét, PDF/UA không suy từ việc xem |
| Ảnh raster | JPEG, PNG, WebP, GIF, BMP, TIFF | NaMiImages: crop/rotate/resize/exposure cơ bản; Save As | EXIF orientation/ICC, animation/frame, alpha, mất dữ liệu do JPEG |
| Ảnh RAW/HEIF/AVIF | Preview theo codec có quyền và test | P1 export/chỉnh cơ bản | Không hứa mọi camera/HEIC 10-bit, metadata/quyền codec |
| Vẽ và vector | SVG, ODG, PDF vector; EPS nếu parser an toàn | NaMiDraw P1 cho SVG/ODG; xem qua renderer sandbox P0 nếu có | CorelDRAW CDR/CDT, Adobe AI/PSD là định dạng riêng, lớp/effect có thể mất |
| Tệp nén | ZIP, 7z, TAR, TAR.GZ, GZ, BZ2, XZ | NaMiArchive tạo ZIP/7z/tar theo engine/test | RAR thường chỉ giải nén và tùy biến thể; không giả định tạo RAR |
| CAD 2D | DXF, DWG theo phiên bản đã thử | NaMiCAD Viewer P1; editor CAD là gói tùy chọn | Xref, font SHX, custom object, plot style và DWG version |
| CAD 3D/BIM | STEP, IGES, STL, IFC theo engine đã chọn | Viewer/ứng dụng tùy chọn P2 | Không suy viewer là AutoCAD/Revit hoặc chỉnh native trọn vẹn |
| Âm thanh | MP3, WAV, FLAC, OGG/Vorbis/Opus, AAC/M4A khi codec hợp pháp | NaMiMedia phát, playlist; converter/editor P1 | Container, codec, DRM và thiết bị xuất âm thanh kiểm riêng |
| Video | MP4, MKV, WebM, MOV, AVI; H.264/H.265/AV1/VP9 theo codec được phân phối | NaMiMedia phát, subtitle SRT/VTT, audio track, fullscreen | MP4 là container; không bảo đảm mọi codec/DRM bên trong |

**“Zar”** trong yêu cầu chưa xác định là phần mở rộng nào. Không tự coi .zar là .rar. NaMiArchive cần nhận diện theo signature/MIME; nếu là định dạng riêng thì ghi nhà tạo và mẫu có quyền trước khi hỗ trợ. Cho phép người dùng chọn một tệp mẫu đã lọc dữ liệu và báo “chưa hỗ trợ” rõ ràng.

## 2. NaMiFiles và lựa chọn ứng dụng

Nhấp đôi mở app mặc định; chuột phải “Mở bằng”, “Chọn ứng dụng khác”, “Luôn dùng ứng dụng này cho loại tệp”, “Xem trước”, “Chia sẻ”, “Nén”, “Giải nén”, “Quét an toàn”, “Thuộc tính”. Hỗ trợ thay mặc định trong Settings và reset mà không làm hỏng hệ thống. Với tệp từ USB/tải về/email: nhãn nguồn, chế độ bảo vệ cho macro/script/link ngoài/đính kèm, thông báo trước mở. Preview chạy trong process sandbox không được quyền ghi file.

Không để một chương trình “chiếm” mặc định hàng trăm MIME không xử lý tốt. Mỗi association kèm mức view/edit và test, người dùng đổi được. Copy/move có progress, pause, conflict rename/replace/skip, kiểm hash khi sao chép vào USB theo lựa chọn; không tuyên bố xong khi thiết bị bị rút giữa chừng. Tên tệp tiếng Việt NFC/NFD/Unicode và path dài phải qua test trên local/SMB/USB.

## 3. NaMiArchive

Danh sách bên trong mà không giải nén, preview tệp an toàn, kéo thả, nén/giải nén có progress và hủy. Giải nén chọn thư mục, kiểm file trùng, bảo vệ path traversal (../, absolute path, symlink/hardlink), archive bomb, kích thước giải nén, số mục, nested archive và malware; không tự chạy chương trình sau giải nén. Password nhập vào UI bảo mật, không log, thuật toán mã hóa/khả năng của ZIP/7z hiển thị đúng. RAR có thể giải nén nếu engine và giấy phép cho phép; đối chiếu version RAR4/RAR5/password/multi-volume. Không gắn badge “tạo RAR” khi engine không làm được.

## 4. NaMiImages, NaMiDraw, NaMiCAD

NaMiImages: zoom/fit, gallery, slideshow, compare, rotate theo EXIF, crop không phá bản gốc, resize theo pixel, color profile, export JPEG/PNG/WebP, xóa metadata vị trí theo lựa chọn. GIF/ảnh động không được lưu thành frame đầu mà không báo. NaMiDraw: SVG/ODG có text/vector/layer, shape, đường, arrow, export PNG/PDF, kiểm font, external resource và script SVG; CDR/AI/PSD chỉ thêm khi importer được kiểm phiên bản cụ thể, mặc định không hứa sửa lớp trọn vẹn.

NaMiCAD Viewer: ưu tiên đọc DXF, đo kích thước, layer on/off, pan/zoom, đơn vị, layout/model space, print to scale, xref/SHX warning; DWG thông qua importer/converter có quyền nếu chọn được. Test bản vẽ nhà xưởng/cơ khí có xref/font tùy chỉnh. Nếu DWG thiếu hỗ trợ, ghi “chưa xác minh bản này” và hướng dẫn DXF/PDF từ người gửi hoặc app chuyên ngành đã chứng nhận; không tự chuyển rồi ghi đè bản thiết kế.

## 5. NaMiMedia

Tách container/codec/audio/subtitle/hardware acceleration/DRM trong diagnostic. Video không chạy phải nói “thiếu codec”, “file lỗi”, “codec bị hạn chế”, “thiết bị xuất âm thanh” hoặc “bản quyền DRM” khi xác định được; SmartAI có thể giải thích, không tìm bộ codec lạ trên mạng. Player có playlist, resume, seek, frame aspect, subtitle tiếng Việt UTF-8/legacy với preview, chọn audio track, playback speed, picture-in-picture khi desktop hỗ trợ, keyboard và screen reader. Codec H.264/H.265/AAC và nội dung có DRM cần audit giấy phép/bằng sáng chế/phân phối theo thị trường trước ISO, không coi FFmpeg hỗ trợ kỹ thuật là quyền phân phối tự động.
