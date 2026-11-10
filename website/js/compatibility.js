// Trang /compatibility.html — ma trận ứng dụng + thiết bị, tìm kiếm/lọc, bảng minh bạch.
(function () {
  "use strict";
  var C = window.NaMiCompat;
  var state = { data: null, tab: "apps", q: "", category: "", type: "", transparency: "" };

  function normalize(str) {
    return String(str || "")
      .toLowerCase()
      .normalize("NFD").replace(/[̀-ͯ]/g, ""); // bỏ dấu để tìm không dấu
  }

  function matchesApp(app) {
    var q = normalize(state.q);
    if (q && normalize(app.name + " " + app.vendor + " " + (app.workflows || []).join(" ")).indexOf(q) === -1) return false;
    if (state.category && app.category !== state.category) return false;
    if (state.type && app.type !== state.type) return false;
    if (state.transparency && app.transparency_status !== state.transparency) return false;
    return true;
  }

  function matchesDevice(dev) {
    var q = normalize(state.q);
    if (q && normalize(dev.vendor_model + " " + dev.class).indexOf(q) === -1) return false;
    if (state.transparency && dev.transparency_status !== state.transparency) return false;
    return true;
  }

  function renderLegend(legend) {
    var el = document.getElementById("legend-grid");
    if (!el) return;
    var order = ["verified", "unverified", "cannot_publish"];
    el.innerHTML = order.map(function (key) {
      var l = legend[key];
      return '<div class="legend-card">' +
        '<h4>' + C.transparencyBadge(key) + '</h4>' +
        '<p class="text-muted">' + C.escapeHtml(l.description_vi) + '</p></div>';
    }).join("");
  }

  function renderCounts(apps, devices) {
    var el = document.getElementById("transparency-counts");
    if (!el) return;
    var all = apps.concat(devices);
    var counts = { verified: 0, unverified: 0, cannot_publish: 0 };
    all.forEach(function (r) { if (counts[r.transparency_status] != null) counts[r.transparency_status]++; });
    el.innerHTML =
      '<div class="table-wrap"><table><caption>Tổng số bản ghi theo trạng thái minh bạch (toàn bộ ' + all.length + ' ứng dụng + thiết bị trong dữ liệu hiện tại)</caption>' +
      "<thead><tr><th>Trạng thái</th><th>Số bản ghi</th></tr></thead><tbody>" +
      ["verified", "unverified", "cannot_publish"].map(function (k) {
        return "<tr><td>" + C.transparencyBadge(k) + "</td><td>" + counts[k] + "</td></tr>";
      }).join("") + "</tbody></table></div>";
  }

  function appRow(app) {
    return "<tr>" +
      "<td><strong>" + C.escapeHtml(app.name) + "</strong><div class=\"card__meta\">" + C.escapeHtml(app.vendor) + "</div></td>" +
      "<td>" + C.escapeHtml(app.category) + "</td>" +
      "<td>" + C.escapeHtml(C.typeLabel(app.type)) + "</td>" +
      "<td>" + C.resultBadge(app.result) + "</td>" +
      "<td>" + C.transparencyBadge(app.transparency_status) + "</td>" +
      "<td>" + C.escapeHtml(app.last_tested || "chưa có ngày") + "</td>" +
      "<td>" + C.escapeHtml(app.limitations_vi || "") + "</td>" +
      "</tr>";
  }

  function deviceRow(dev) {
    var fns = dev.functions ? Object.keys(dev.functions).map(function (k) {
      return C.escapeHtml(k) + ": " + C.escapeHtml(C.RESULT_LABEL[dev.functions[k]] || dev.functions[k]);
    }).join(", ") : "—";
    return "<tr>" +
      "<td><strong>" + C.escapeHtml(dev.vendor_model) + "</strong><div class=\"card__meta\">" + C.escapeHtml(dev.class) + " · " + C.escapeHtml((dev.connection || []).join("/")) + "</div></td>" +
      "<td>" + C.escapeHtml(dev.kernel_driver_backend) + "</td>" +
      "<td>" + fns + "</td>" +
      "<td>" + C.resultBadge(dev.result) + "</td>" +
      "<td>" + C.transparencyBadge(dev.transparency_status) + "</td>" +
      "<td>" + C.escapeHtml(dev.limitations_vi || "") + "</td>" +
      "</tr>";
  }

  function render() {
    var container = document.getElementById("result-table");
    if (!state.data) return;
    var list = state.tab === "apps"
      ? state.data.apps.filter(matchesApp)
      : state.data.devices.filter(matchesDevice);

    if (!list.length) { C.setEmpty(container, "Không có " + (state.tab === "apps" ? "ứng dụng" : "thiết bị") + " phù hợp bộ lọc. Thử bỏ bớt điều kiện tìm."); return; }

    if (state.tab === "apps") {
      container.innerHTML = '<div class="table-wrap"><table>' +
        '<caption>Ma trận ứng dụng (' + list.length + ' kết quả)</caption>' +
        "<thead><tr><th>Ứng dụng</th><th>Lĩnh vực</th><th>Loại</th><th>Kết quả</th><th>Minh bạch</th><th>Ngày kiểm</th><th>Hạn chế</th></tr></thead>" +
        "<tbody>" + list.map(appRow).join("") + "</tbody></table></div>";
    } else {
      container.innerHTML = '<div class="table-wrap"><table>' +
        '<caption>Ma trận thiết bị (' + list.length + ' kết quả)</caption>' +
        "<thead><tr><th>Thiết bị</th><th>Driver/backend</th><th>Chức năng theo trục</th><th>Kết quả</th><th>Minh bạch</th><th>Hạn chế</th></tr></thead>" +
        "<tbody>" + list.map(deviceRow).join("") + "</tbody></table></div>";
    }
  }

  function populateCategoryFilter(apps) {
    var sel = document.getElementById("filter-category");
    if (!sel) return;
    var cats = Array.from(new Set(apps.map(function (a) { return a.category; }))).sort();
    cats.forEach(function (c) {
      var opt = document.createElement("option");
      opt.value = c; opt.textContent = c;
      sel.appendChild(opt);
    });
  }

  function wireControls() {
    var tabApps = document.getElementById("tab-apps");
    var tabDevices = document.getElementById("tab-devices");
    var categoryWrap = document.getElementById("category-filter-wrap");
    var typeWrap = document.getElementById("type-filter-wrap");

    function setTab(tab) {
      state.tab = tab;
      tabApps.setAttribute("aria-selected", tab === "apps" ? "true" : "false");
      tabDevices.setAttribute("aria-selected", tab === "devices" ? "true" : "false");
      categoryWrap.hidden = tab !== "apps";
      typeWrap.hidden = tab !== "apps";
      render();
    }
    tabApps.addEventListener("click", function () { setTab("apps"); });
    tabDevices.addEventListener("click", function () { setTab("devices"); });

    document.getElementById("filter-q").addEventListener("input", function (e) { state.q = e.target.value; render(); });
    document.getElementById("filter-category").addEventListener("change", function (e) { state.category = e.target.value; render(); });
    document.getElementById("filter-type").addEventListener("change", function (e) { state.type = e.target.value; render(); });
    document.getElementById("filter-transparency").addEventListener("change", function (e) { state.transparency = e.target.value; render(); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var container = document.getElementById("result-table");
    C.setLoading(container, "Đang tải ma trận tương thích…");
    C.fetchCompatibility().then(function (data) {
      state.data = data;
      document.querySelectorAll("[data-last-updated]").forEach(function (el) { el.textContent = data.last_updated; });
      renderLegend(data.legend);
      renderCounts(data.apps, data.devices);
      populateCategoryFilter(data.apps);
      wireControls();
      render();
    }).catch(function (err) { C.setError(container, err); });
  });
})();
