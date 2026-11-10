// Trang /namioffice.html — bảng tính năng/giới hạn rút từ compatibility.json (lọc theo lĩnh vực Văn phòng).
(function () {
  "use strict";
  var C = window.NaMiCompat;
  var IDS = ["namioffice-suite", "microsoft-word-desktop", "microsoft-excel-desktop", "namipdf"];

  function row(app) {
    return "<tr><td><strong>" + C.escapeHtml(app.name) + "</strong><div class=\"card__meta\">" + C.escapeHtml(app.vendor) + "</div></td>" +
      "<td>" + C.escapeHtml(C.typeLabel(app.type)) + "</td>" +
      "<td>" + C.resultBadge(app.result) + "</td>" +
      "<td>" + C.transparencyBadge(app.transparency_status) + "</td>" +
      "<td>" + C.escapeHtml(app.limitations_vi || "") + "</td></tr>";
  }

  document.addEventListener("DOMContentLoaded", function () {
    var el = document.getElementById("office-matrix");
    C.setLoading(el, "Đang tải…");
    C.fetchCompatibility().then(function (data) {
      var rows = IDS.map(function (id) { return data.apps.filter(function (a) { return a.id === id; })[0]; }).filter(Boolean);
      if (!rows.length) { C.setEmpty(el); return; }
      el.innerHTML = '<div class="table-wrap"><table><caption>So với công cụ tham chiếu phổ biến (không phải cùng một sản phẩm — xem cột Loại)</caption>' +
        "<thead><tr><th>Ứng dụng</th><th>Loại</th><th>Kết quả</th><th>Minh bạch</th><th>Hạn chế</th></tr></thead><tbody>" +
        rows.map(row).join("") + "</tbody></table></div>";
    }).catch(function (err) { C.setError(el, err); });
  });
})();
