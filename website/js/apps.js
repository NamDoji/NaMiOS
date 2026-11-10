// Trang /apps.html — thẻ ứng dụng cài sẵn (native) và dịch vụ web rút gọn (official_web).
(function () {
  "use strict";
  var C = window.NaMiCompat;

  function appCard(app) {
    return '<article class="card">' +
      "<div style=\"display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap\">" +
      "<h3>" + C.escapeHtml(app.name) + "</h3>" + C.transparencyBadge(app.transparency_status) +
      "</div>" +
      '<p class="card__meta">' + C.escapeHtml(app.vendor) + " · " + C.escapeHtml(C.typeLabel(app.type)) + "</p>" +
      "<p>" + C.escapeHtml(app.limitations_vi || "") + "</p>" +
      '<p class="card__meta">Ngày kiểm gần nhất: ' + C.escapeHtml(app.last_tested || "chưa có") + "</p>" +
      (app.evidence_url ? '<a class="btn btn--text" href="' + C.escapeHtml(app.evidence_url) + '">Xem bằng chứng</a>' : "") +
      "</article>";
  }

  function render(data) {
    var native = data.apps.filter(function (a) { return a.type === "native"; });
    var web = data.apps.filter(function (a) { return a.type === "official_web"; });

    var nativeEl = document.getElementById("native-apps");
    var webEl = document.getElementById("web-apps");
    nativeEl.innerHTML = native.length ? native.map(appCard).join("") : '<p class="text-muted">Chưa có dữ liệu.</p>';
    webEl.innerHTML = web.length ? web.map(appCard).join("") : '<p class="text-muted">Chưa có dữ liệu.</p>';
  }

  document.addEventListener("DOMContentLoaded", function () {
    var nativeEl = document.getElementById("native-apps");
    var webEl = document.getElementById("web-apps");
    C.setLoading(nativeEl, "Đang tải…");
    C.setLoading(webEl, "Đang tải…");
    C.fetchCompatibility().then(render).catch(function (err) {
      C.setError(nativeEl, err);
      webEl.innerHTML = "";
    });
  });
})();
