// NaMiOS website — hành vi dùng chung cho mọi trang (điều hướng, focus, footer year).
(function () {
  "use strict";

  function initNav() {
    var toggle = document.querySelector("[data-nav-toggle]");
    var nav = document.getElementById("main-nav");
    if (!toggle || !nav) return;

    toggle.addEventListener("click", function () {
      var isOpen = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
      if (isOpen) {
        var firstLink = nav.querySelector("a");
        if (firstLink) firstLink.focus();
      }
    });

    // Đóng menu di động khi nhấn Escape hoặc chọn một liên kết.
    nav.addEventListener("keydown", function (evt) {
      if (evt.key === "Escape") {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });
    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        if (window.matchMedia("(max-width: 860px)").matches) {
          nav.classList.remove("is-open");
          toggle.setAttribute("aria-expanded", "false");
        }
      });
    });

    // Đóng khi click ra ngoài.
    document.addEventListener("click", function (evt) {
      if (!nav.classList.contains("is-open")) return;
      if (nav.contains(evt.target) || toggle.contains(evt.target)) return;
      nav.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    });
  }

  function markCurrentNavLink() {
    var path = window.location.pathname.split("/").pop() || "index.html";
    document.querySelectorAll(".main-nav__list a[href]").forEach(function (a) {
      var href = a.getAttribute("href").split("/").pop();
      if (href === path) {
        a.setAttribute("aria-current", "page");
      }
    });
  }

  function setFooterYear() {
    var el = document.querySelector("[data-year]");
    if (el) el.textContent = String(new Date().getFullYear());
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNav();
    markCurrentNavLink();
    setFooterYear();
  });
})();
