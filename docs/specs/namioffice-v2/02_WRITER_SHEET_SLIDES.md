# 02. Yêu cầu chức năng NaMiWriter, NaMiSheet, NaMiSlides

## A. NaMiWriter — soạn thảo và xuất bản

| Mức | Nhóm | Yêu cầu nghiệm thu |
|---|---|---|
| F0 | Văn bản | Style đoạn/ký tự, font/màu, căn lề, tab, thụt đầu dòng, danh sách đa cấp; dán không định dạng; tìm/thay thế, navigation theo heading; đếm từ; Unicode không mất dấu |
| F0 | Trang và in | A4/A3, lề, cột, section/page break, header/footer, số trang, xem trước, vùng in, PDF có bookmark và liên kết; 10 mẫu hành chính in ra không cắt chữ |
| F0 | Bảng/ảnh | Chèn/gộp/tách ô, lặp dòng tiêu đề, độ rộng cố định/tự động, border/shading, ảnh crop/alt text, caption; round-trip DOCX không rớt đối tượng |
| F1 | Biên tập | Comments, tracked changes nhiều tác giả, accept/reject theo vùng, compare/merge hai bản, tìm sửa đồng loạt, version history và conflict resolution |
| F1 | Tài liệu dài | TOC, foot/endnote, cross-reference, bibliography/citation, index, equations MathML, fields, mail merge, templates và styles |
| F1 | Biểu mẫu | Content controls/checkbox/date/dropdown, khóa vùng, nhập liệu, field mapping và export; khi không giữ được tương tác, chuyển chỉ xem hoặc cảnh báo |
| F2 | Đối tượng phức tạp | Drawing groups/SmartArt/OLE, advanced typography, embedded media, publisher layout; có preview/fallback và cấm Save phá cấu trúc |

Tệp DOCX được đối chiếu bằng cả nội dung và ảnh render từng trang ở cùng font; kiểm pagination, bảng qua trang, chú thích, header/footer, track changes, hyperlink, alt text. Tệp hợp đồng/chữ ký số không tự sửa metadata hay gỡ chữ ký; sau thay đổi, yêu cầu ký lại. Tài liệu nhiều tác giả phải hiển thị tên theo quyền riêng tư và thay đổi có thể hoàn tác.

## B. NaMiSheet — Excel cho công việc thật

**F0 giao diện bảng:** tối thiểu nhập/sửa/paste theo vùng, autofill, flash fill tương đương nếu làm được, sort/filter multi-column, conditional formatting, data validation, named ranges, freeze panes, split, hide/unhide, group/outline, table với structured references, print area, print titles, page setup, CSV import có preview encoding/delimiter. Undo cả thao tác kéo công thức/chèn cột, có kiểm dữ liệu.

**F0 công thức:** các họ SUM/SUMIFS/COUNTIFS/AVERAGEIFS, IF/IFS/IFERROR, INDEX/MATCH/XLOOKUP, text/date/round/financial thường dùng, tham chiếu tương đối/tuyệt đối, tên vùng, cross-sheet, array cũ và lỗi Excel. Tách formula expression khỏi cached result và format; kiểm conversion số/chuỗi, locale vi-VN, dấu thập phân, ngày 1900/1904, precision và circular refs. Danh sách chi tiết có ở v1; ở v2 thêm registry theo version Excel, telemetry lỗi opt-in và 100 fixture riêng từ bảng điểm, hóa đơn, báo cáo kế toán.

**F1 mảng động:** FILTER/SORT/UNIQUE/SEQUENCE/XLOOKUP mảng, LET/LAMBDA và nhóm BYROW/MAP khi engine đủ; spill range, #SPILL!, implicit intersection, vùng nghẽn, tham chiếu A1#, thay đổi kích thước mảng. Cấp C0 chỉ khi công thức lưu lại và tính đúng trong ứng dụng đích; trả cached values không được giả là có engine.

**F1 bảng và phân tích:** table object (header, total row, calculated column, structured references), PivotTable/PivotChart, refresh, grouping, calculated fields, slicer/timeline theo khả năng, conditional formatting nâng cao, data validation dependent list, Goal Seek, Solver, scenario, charts thường và combo/secondary axis, sparklines. Pivot refresh phải giữ nguồn; nguồn không truy cập được thì nêu kết quả cũ và thời điểm.

**F2 nhập và mô hình dữ liệu:** Get & Transform tương đương gồm kết nối nguồn CSV/JSON/SQL/web có quyền, type inference có thể sửa, filter/merge/append/unpivot, bước biến đổi có thể tái lập, lịch sử, cache, secret vault và refresh. Data Model gồm quan hệ nhiều bảng, measures, DAX subset chỉ khi có implementation và differential test; không tự nhận “hỗ trợ Power Query/Power Pivot” chỉ vì có CSV import hoặc Pivot đơn bảng. Chặn truy vấn ngoài mạng khi mở tệp, yêu cầu consent nguồn và chỉ rõ dữ liệu sẽ gửi.

**F1/F2 biểu đồ:** column/bar/line/area/pie/scatter/bubble, combo, stacked, secondary axis, data labels, error bars, trendline, pivot chart, histogram, waterfall, treemap, sunburst, box plot, funnel, stock, map chart nếu có nguồn bản đồ hợp lệ. Chart có data binding, chỉnh sửa, keyboard accessibility, màu đọc được, round-trip; loại chưa thể chỉnh giữ preview và cảnh báo. Không thay dữ liệu bằng ảnh chụp mà báo “biểu đồ chỉnh sửa được”.

**Kiểm soát kế toán/thuế F0:** bảng so sánh số liệu trước và sau mở/lưu: số ô công thức, ô lỗi, ô đổi kiểu, ô làm tròn, liên kết ngoài, tổng đối chiếu; xuất báo cáo để người dùng quyết định. Không tự nộp hoặc ký chứng từ. Tệp mẫu phải được ẩn danh/có quyền sử dụng.

## C. NaMiSlides — trình chiếu và giảng dạy

| Mức | Nhóm | Yêu cầu nghiệm thu |
|---|---|---|
| F0 | Biên tập | Theme, master, layout, text, shape, hình ảnh, icon hợp pháp, alignment, layer/group, table, chart; chọn nhiều đối tượng, copy/paste từ Sheet |
| F0 | Trình chiếu | Slide sorter, notes, presenter view, dual display, laser/pen, tỉ lệ 4:3/16:9/tùy ý, xuất PDF/ảnh; không lộ notes trên màn chiếu |
| F1 | Chuyển động | Transition, animation/timing, trigger, video/audio với codec có quyền, phụ đề, record slide show và xuất video khi có pipeline |
| F1 | Làm việc nhóm | Comment, compare versions, share/export, template cho bài giảng và báo cáo, accessibility checker |
| F2 | Nâng cao | Morph/3D, diagram phức tạp, chart nhúng có dữ liệu, tương tác, kiosk; fallback hiển thị với thông báo khi không sửa được |

Thử PPTX gốc → sửa một slide → lưu → mở bằng PowerPoint có giấy phép và NaMiSlides; so văn bản, vị trí, font, master, animation order, media, notes. Xuất video chỉ công bố khi đồng bộ audio/timing đã test.

## D. Tương tác xuyên ứng dụng

Copy table/chart từ Sheet sang Writer/Slides với ba tùy chọn rõ: ảnh tĩnh, đối tượng có thể chỉnh, liên kết dữ liệu. Khi dữ liệu nguồn thay đổi, thông báo và chọn refresh; không tự truy cập path mạng hoặc cloud. File picker, print/PDF, phím tắt, theme, kiểm lỗi, Help, update, autosave và SmartAI có trải nghiệm thống nhất. CSV/XLSX đính kèm mail mở trong sandbox, không auto-run macro.
