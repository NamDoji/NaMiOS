// Trang /download.html — mọi CTA/nội dung đọc từ data/release-manifest.json.
// QUY TẮC CỨNG: status=pre_release => KHÔNG được render bất kỳ nút/link tải ISO nào.
(function () {
  "use strict";
  var C = window.NaMiCompat;

  var STATE_LABEL = { pre_release: "Tiền phát hành (pre-release)", beta: "Bản thử nghiệm (beta)", stable: "Bản ổn định (stable)" };
  var FEATURE_STATE_LABEL = {
    released: "Đã có trên bản phát hành",
    verified_specific: "Đã thử nghiệm trên thiết bị/phiên bản cụ thể",
    trial: "Bản thử nghiệm",
    in_development: "Đang phát triển"
  };

  function renderStateBanner(manifest) {
    var el = document.getElementById("release-state-banner");
    var label = STATE_LABEL[manifest.status] || manifest.status;
    el.innerHTML =
      '<span class="release-state"><span aria-hidden="true">●</span> Trạng thái hiện tại: ' + C.escapeHtml(label) + "</span>";
  }

  function renderCTA(manifest) {
    var el = document.getElementById("download-cta");
    if (manifest.status === "pre_release") {
      el.innerHTML =
        '<div class="btn-row">' +
        '<a class="btn btn--primary btn--lg" href="#notify-form">Nhận thông báo khi có bản thử nghiệm</a>' +
        '<a class="btn btn--secondary btn--lg" href="about.html#tien-do">Xem tiến độ</a>' +
        "</div>" +
        '<p class="text-muted" style="margin-top:12px">NaMiOS chưa có bản ISO nào được phê duyệt phát hành. Sẽ không có nút tải ở đây cho tới khi có bản build đã ký, có mã băm SHA-256 và ghi chú phát hành — xem checklist bên dưới.</p>';
      return;
    }
    if (manifest.status === "beta" || manifest.status === "stable") {
      if (!manifest.downloads || !manifest.downloads.length) {
        el.innerHTML = '<div class="alert alert--warning"><div><strong>Thiếu dữ liệu file tải.</strong><p>Manifest báo trạng thái "' + C.escapeHtml(manifest.status) + '" nhưng mảng downloads rỗng — đây là lỗi dữ liệu, trang sẽ không tự suy ra nút tải.</p></div></div>';
        return;
      }
      var label = manifest.status === "beta" ? "Tải bản thử nghiệm miễn phí" : "Tải NaMiOS miễn phí";
      el.innerHTML = '<div class="btn-row">' + manifest.downloads.map(function (d) {
        return '<a class="btn btn--primary btn--lg" href="' + C.escapeHtml(d.url) + '">' + label + " — " + C.escapeHtml(d.architecture) + "</a>";
      }).join("") + '</div><p class="text-muted" style="margin-top:12px">Kiểm tra máy trước khi tải. Luôn xác minh SHA-256 và chữ ký trước khi chạy.</p>';
    }
  }

  function renderMeta(manifest) {
    var el = document.getElementById("release-meta");
    var rows = [
      ["Kênh", manifest.channel],
      ["Phiên bản", manifest.version + (manifest.status === "pre_release" ? " (ví dụ minh họa cấu trúc dữ liệu — không phải bản build có thật)" : "")],
      ["Ngày phát hành", manifest.release_date || "chưa có"],
      ["Kiến trúc", (manifest.architectures && manifest.architectures.length) ? manifest.architectures.join(", ") : "chưa có bản build nào"],
      ["Cập nhật manifest lần cuối", manifest.last_updated]
    ];
    el.innerHTML = '<div class="table-wrap"><table><caption class="visually-hidden">Thông tin phát hành hiện tại</caption><tbody>' +
      rows.map(function (r) { return "<tr><th scope=\"row\">" + C.escapeHtml(r[0]) + "</th><td>" + C.escapeHtml(r[1]) + "</td></tr>"; }).join("") +
      "</tbody></table></div>";
  }

  function renderSigning(manifest) {
    var el = document.getElementById("signing-info");
    var s = manifest.signing || {};
    el.innerHTML =
      '<div class="alert alert--info"><div><strong>Khóa ký và xác minh</strong>' +
      "<p>" + C.escapeHtml(s.note || "Chưa công bố khóa ký.") + "</p>" +
      (s.key_catalog_url ? '<p><a href="' + C.escapeHtml(s.key_catalog_url) + '">Xem danh mục khóa (key catalog)</a></p>' : "") +
      "</div></div>";
  }

  function renderFeatures(manifest) {
    var el = document.getElementById("feature-claims");
    if (!manifest.features || !manifest.features.length) { el.innerHTML = '<p class="text-muted">Chưa có claim tính năng nào trong manifest.</p>'; return; }
    el.innerHTML = '<div class="table-wrap"><table><caption>Tuyên bố tính năng và trạng thái thật (từ release manifest)</caption>' +
      "<thead><tr><th>Tính năng</th><th>Trạng thái</th><th>Kiểm lần cuối</th><th>Bằng chứng</th></tr></thead><tbody>" +
      manifest.features.map(function (f) {
        return "<tr><td>" + C.escapeHtml(f.text_vi) + "</td><td><span class=\"badge badge--info\">" + C.escapeHtml(FEATURE_STATE_LABEL[f.state] || f.state) + "</span></td><td>" + C.escapeHtml(f.last_verified || "chưa có") + "</td><td>" +
          (f.evidence_url ? '<a href="' + C.escapeHtml(f.evidence_url) + '">nguồn</a>' : "—") + "</td></tr>";
      }).join("") + "</tbody></table></div>";
  }

  function renderKnownIssues(manifest) {
    var el = document.getElementById("known-issues");
    if (!manifest.known_issues || !manifest.known_issues.length) { el.innerHTML = '<p class="text-muted">Chưa có mục nào.</p>'; return; }
    el.innerHTML = manifest.known_issues.map(function (k) {
      return '<div class="alert alert--warning"><div><strong>[' + C.escapeHtml(k.severity) + '] ' + C.escapeHtml(k.id) + '</strong><p>' + C.escapeHtml(k.text_vi) + "</p>" +
        (k.workaround_vi ? "<p class=\"text-muted\">Hướng xử lý/theo dõi: " + C.escapeHtml(k.workaround_vi) + "</p>" : "") + "</div></div>";
    }).join("");
  }

  function wireNotifyForm(manifest) {
    var form = document.getElementById("notify-form");
    var result = document.getElementById("notify-result");
    var noteEl = document.getElementById("notify-demo-note");
    if (noteEl) noteEl.textContent = (manifest.notify && manifest.notify.note_vi) || "";

    if (!form) return;
    form.addEventListener("submit", function (evt) {
      evt.preventDefault();
      var emailInput = form.querySelector("#notify-email");
      var email = emailInput.value.trim();
      var valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
      emailInput.setAttribute("data-touched", "true");
      if (!valid) {
        result.innerHTML = '<p class="error-text" role="alert">Email chưa đúng định dạng. Vui lòng kiểm tra lại.</p>';
        emailInput.focus();
        return;
      }
      if (manifest.notify && manifest.notify.mode === "demo") {
        result.innerHTML =
          '<div class="alert alert--success" role="status"><div><strong>Đây là bản xem trước (demo).</strong>' +
          "<p>Form chưa nối dịch vụ gửi email thật. NaMiOS KHÔNG gửi đi, không lưu lại và không xử lý địa chỉ email bạn vừa nhập. " +
          "Khi có dịch vụ gửi tin thật và chính sách quyền riêng tư được ký duyệt, chế độ demo này sẽ được thay bằng form thật có double opt-in.</p></div></div>";
        form.reset();
        return;
      }
      result.innerHTML = '<p>Đã ghi nhận. Cảm ơn bạn.</p>';
      form.reset();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    C.fetchManifest().then(function (manifest) {
      renderStateBanner(manifest);
      renderCTA(manifest);
      renderMeta(manifest);
      renderSigning(manifest);
      renderFeatures(manifest);
      renderKnownIssues(manifest);
      wireNotifyForm(manifest);
    }).catch(function (err) {
      var el = document.getElementById("download-cta");
      C.setError(el, err);
    });
  });
})();
