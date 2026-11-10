// Trang /devices.html — nhóm thiết bị theo lớp (In ấn, Quét, Wi-Fi, Bluetooth, Mạng dây, Lưu trữ).
(function () {
  "use strict";
  var C = window.NaMiCompat;

  function deviceCard(dev) {
    var fns = dev.functions ? Object.keys(dev.functions).map(function (k) {
      return "<li>" + C.escapeHtml(k) + ": " + C.resultBadge(dev.functions[k]) + "</li>";
    }).join("") : "";
    return '<article class="card">' +
      "<div style=\"display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap\">" +
      "<h3>" + C.escapeHtml(dev.vendor_model) + "</h3>" + C.transparencyBadge(dev.transparency_status) +
      "</div>" +
      '<p class="card__meta">Kết nối: ' + C.escapeHtml((dev.connection || []).join(", ")) + " · " + C.escapeHtml(dev.kernel_driver_backend) + "</p>" +
      (fns ? '<ul class="stack" style="margin:0;padding-left:18px">' + fns + "</ul>" : "") +
      "<p>" + C.escapeHtml(dev.limitations_vi || "") + "</p>" +
      "</article>";
  }

  function render(data) {
    var byClass = {};
    data.devices.forEach(function (d) {
      byClass[d.class] = byClass[d.class] || [];
      byClass[d.class].push(d);
    });
    var el = document.getElementById("device-groups");
    var html = "";
    Object.keys(byClass).sort().forEach(function (cls) {
      html += "<section class=\"flow\" style=\"margin-bottom:32px\"><h2>" + C.escapeHtml(cls) + "</h2>" +
        '<div class="grid grid--2">' + byClass[cls].map(deviceCard).join("") + "</div></section>";
    });
    el.innerHTML = html || '<p class="text-muted">Chưa có dữ liệu thiết bị.</p>';
  }

  document.addEventListener("DOMContentLoaded", function () {
    var el = document.getElementById("device-groups");
    C.setLoading(el, "Đang tải…");
    C.fetchCompatibility().then(render).catch(function (err) { C.setError(el, err); });
  });
})();
