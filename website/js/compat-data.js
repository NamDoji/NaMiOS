// NaMiOS website — tiện ích dùng chung để tải và hiển thị data/compatibility.json.
// Dùng ở compatibility.html, apps.html, devices.html, namioffice.html.
// Lưu ý: fetch() đọc file cục bộ có thể bị trình duyệt chặn khi mở trực tiếp bằng
// file:// (CORS). Hãy chạy một local server — xem website/README.md.
(function (global) {
  "use strict";

  var DATA_URL = "data/compatibility.json";
  var MANIFEST_URL = "data/release-manifest.json";

  var TRANSPARENCY_LABEL = {
    verified: "Đã xác minh",
    unverified: "Chưa xác minh",
    cannot_publish: "Không thể công bố"
  };
  var TRANSPARENCY_CLASS = {
    verified: "badge--verified",
    unverified: "badge--unverified",
    cannot_publish: "badge--cannot"
  };
  var RESULT_LABEL = {
    pass: "Đạt",
    partial: "Đạt một phần",
    fail: "Không đạt",
    not_tested: "Chưa thử"
  };
  var TYPE_LABEL = {
    native: "Cài sẵn (native)",
    official_web: "Trang web chính thức",
    wine_tested: "Qua Wine — đã thử",
    windows_only: "Chỉ có bản Windows — chưa thử qua Wine"
  };

  function fetchJSON(url) {
    return fetch(url, { cache: "no-store" }).then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status + " khi tải " + url);
      return res.json();
    });
  }

  function fetchCompatibility() { return fetchJSON(DATA_URL); }
  function fetchManifest() { return fetchJSON(MANIFEST_URL); }

  function escapeHtml(str) {
    return String(str == null ? "" : str).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function transparencyBadge(status) {
    var cls = TRANSPARENCY_CLASS[status] || "badge--info";
    var label = TRANSPARENCY_LABEL[status] || status;
    return '<span class="badge ' + cls + '">' + escapeHtml(label) + "</span>";
  }

  function resultBadge(result) {
    var map = { pass: "badge--verified", partial: "badge--unverified", fail: "badge--cannot", not_tested: "badge--info" };
    var cls = map[result] || "badge--info";
    return '<span class="badge ' + cls + '">' + escapeHtml(RESULT_LABEL[result] || result) + "</span>";
  }

  function typeLabel(type) { return TYPE_LABEL[type] || type; }

  function setLoading(container, message) {
    container.innerHTML =
      '<div class="stack" role="status" aria-live="polite">' +
      '<span class="visually-hidden">' + escapeHtml(message || "Đang tải dữ liệu…") + "</span>" +
      '<div class="skeleton" style="width:100%"></div>' +
      '<div class="skeleton" style="width:85%"></div>' +
      '<div class="skeleton" style="width:92%"></div>' +
      "</div>";
  }

  function setError(container, err) {
    container.innerHTML =
      '<div class="error-state alert alert--error" role="alert">' +
      "<div><strong>Không tải được dữ liệu tương thích.</strong>" +
      "<p>" + escapeHtml(err && err.message ? err.message : String(err)) + "</p>" +
      "<p>Nếu bạn đang mở file này trực tiếp (file://), trình duyệt có thể chặn đọc JSON cục bộ. " +
      "Hãy chạy một local server — xem hướng dẫn trong <code>website/README.md</code> (ví dụ: " +
      "<code>python3 -m http.server</code> trong thư mục <code>website/</code>).</p></div></div>";
  }

  function setEmpty(container, message) {
    container.innerHTML = '<div class="empty-state">' + escapeHtml(message || "Không có kết quả phù hợp với bộ lọc hiện tại.") + "</div>";
  }

  global.NaMiCompat = {
    fetchCompatibility: fetchCompatibility,
    fetchManifest: fetchManifest,
    escapeHtml: escapeHtml,
    transparencyBadge: transparencyBadge,
    resultBadge: resultBadge,
    typeLabel: typeLabel,
    setLoading: setLoading,
    setError: setError,
    setEmpty: setEmpty,
    TRANSPARENCY_LABEL: TRANSPARENCY_LABEL,
    RESULT_LABEL: RESULT_LABEL
  };
})(window);
