/* ============================================================
   Bazaar — dependency-free vanilla JS. Guard-claused module inits.
   ============================================================ */
(function () {
  "use strict";
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- toast helper ---------- */
  function toast(msg) {
    var wrap = document.getElementById("toastWrap");
    if (!wrap) return;
    var t = document.createElement("div");
    t.className = "bz-toast";
    t.setAttribute("role", "status");
    t.innerHTML =
      '<span class="ti"><svg class="svg-ico" viewBox="0 0 24 24" aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg></span><span>' +
      msg + "</span>";
    wrap.appendChild(t);
    requestAnimationFrame(function () { t.classList.add("show"); });
    setTimeout(function () {
      t.classList.remove("show");
      setTimeout(function () { t.remove(); }, 260);
    }, 2600);
  }

  /* ---------- mobile nav ---------- */
  function initMobileNav() {
    var toggle = document.getElementById("navToggle");
    var panel = document.getElementById("mnav");
    var backdrop = document.getElementById("mnavBackdrop");
    var closeBtn = document.getElementById("mnavClose");
    if (!toggle || !panel || !backdrop) return;
    function open() {
      panel.classList.add("open"); backdrop.classList.add("open");
      toggle.setAttribute("aria-expanded", "true");
      document.body.style.overflow = "hidden";
    }
    function close() {
      panel.classList.remove("open"); backdrop.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
      document.body.style.overflow = "";
    }
    toggle.addEventListener("click", open);
    backdrop.addEventListener("click", close);
    if (closeBtn) closeBtn.addEventListener("click", close);
    panel.querySelectorAll("a").forEach(function (a) { a.addEventListener("click", close); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });
  }

  /* ---------- hero deal carousel ---------- */
  function initHeroCarousel() {
    var root = document.getElementById("dealCarousel");
    if (!root) return;
    var slides = Array.prototype.slice.call(root.querySelectorAll(".deal-slide"));
    var dotsWrap = root.querySelector(".deal-dots");
    if (slides.length < 2) return;
    var i = 0, timer = null;
    var dots = slides.map(function (_, idx) {
      var b = document.createElement("button");
      b.type = "button";
      b.setAttribute("aria-label", "Go to deal " + (idx + 1));
      b.addEventListener("click", function () { go(idx); reset(); });
      dotsWrap.appendChild(b);
      return b;
    });
    function go(n) {
      i = (n + slides.length) % slides.length;
      slides.forEach(function (s, idx) { s.classList.toggle("active", idx === i); });
      dots.forEach(function (d, idx) { d.setAttribute("aria-selected", idx === i ? "true" : "false"); });
    }
    function next() { go(i + 1); }
    function prev() { go(i - 1); }
    function reset() { if (timer) { clearInterval(timer); start(); } }
    function start() { if (reduceMotion) return; timer = setInterval(next, 5500); }
    var nextBtn = root.querySelector(".deal-arrow.next");
    var prevBtn = root.querySelector(".deal-arrow.prev");
    if (nextBtn) nextBtn.addEventListener("click", function () { next(); reset(); });
    if (prevBtn) prevBtn.addEventListener("click", function () { prev(); reset(); });
    root.addEventListener("mouseenter", function () { if (timer) clearInterval(timer); });
    root.addEventListener("mouseleave", function () { start(); });
    go(0); start();
  }

  /* ---------- flash-sale countdown ---------- */
  function initCountdown() {
    var el = document.getElementById("countdown");
    if (!el) return;
    var hEl = el.querySelector('[data-cd="h"]');
    var mEl = el.querySelector('[data-cd="m"]');
    var sEl = el.querySelector('[data-cd="s"]');
    if (!hEl || !mEl || !sEl) return;
    // target: next time the clock hits an 8h boundary from load (stable demo countdown)
    var end = Date.now() + (7 * 3600 + 42 * 60 + 15) * 1000;
    function pad(n) { return n < 10 ? "0" + n : "" + n; }
    function tick() {
      var diff = Math.max(0, end - Date.now());
      var s = Math.floor(diff / 1000);
      hEl.textContent = pad(Math.floor(s / 3600));
      mEl.textContent = pad(Math.floor((s % 3600) / 60));
      sEl.textContent = pad(s % 60);
      if (diff <= 0) clearInterval(iv);
    }
    tick();
    var iv = setInterval(tick, 1000);
  }

  /* ---------- flash stock bars from data-stock ---------- */
  function initStockBars() {
    document.querySelectorAll(".fi-bar > i[data-fill]").forEach(function (bar) {
      var v = parseInt(bar.getAttribute("data-fill"), 10) || 0;
      bar.style.width = Math.max(4, Math.min(100, v)) + "%";
    });
    document.querySelectorAll(".rs-bar .track > i[data-fill]").forEach(function (bar) {
      var v = parseInt(bar.getAttribute("data-fill"), 10) || 0;
      bar.style.width = Math.max(0, Math.min(100, v)) + "%";
    });
  }

  /* ---------- cart + add-to-cart ---------- */
  function initCart() {
    var count = 0;
    var badges = document.querySelectorAll('[data-cart-count]');
    var cartBtn = document.querySelector(".hact.cart");
    function render() {
      badges.forEach(function (b) { b.textContent = count; });
      if (cartBtn) {
        cartBtn.classList.add("pop");
        setTimeout(function () { cartBtn.classList.remove("pop"); }, 340);
      }
    }
    // seed a starting count so the badge isn't 0 on first paint
    count = badges.length ? (parseInt(badges[0].textContent, 10) || 0) : 0;
    document.querySelectorAll("[data-add-cart]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        count += 1;
        render();
        toast((btn.getAttribute("data-name") || "Item") + " added to cart");
      });
    });
  }

  /* ---------- wishlist ---------- */
  function initWishlist() {
    var badges = document.querySelectorAll('[data-wish-count]');
    var count = badges.length ? (parseInt(badges[0].textContent, 10) || 0) : 0;
    document.querySelectorAll(".wish").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var on = btn.getAttribute("aria-pressed") === "true";
        btn.setAttribute("aria-pressed", on ? "false" : "true");
        count += on ? -1 : 1;
        if (count < 0) count = 0;
        badges.forEach(function (b) { b.textContent = count; });
        toast(on ? "Removed from wishlist" : "Saved to wishlist");
      });
    });
  }

  /* ---------- best-sellers filter ---------- */
  function initFilter() {
    var tabs = document.querySelectorAll("[data-filter]");
    if (!tabs.length) return;
    var cards = document.querySelectorAll("[data-category]");
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        tabs.forEach(function (t) { t.setAttribute("aria-selected", "false"); });
        tab.setAttribute("aria-selected", "true");
        var f = tab.getAttribute("data-filter");
        cards.forEach(function (c) {
          var show = f === "all" || c.getAttribute("data-category") === f;
          c.classList.toggle("is-hidden", !show);
        });
      });
    });
  }

  /* ---------- newsletter validation ---------- */
  function initNewsletter() {
    var form = document.getElementById("nlForm");
    if (!form) return;
    var input = form.querySelector('input[type="email"]');
    var msg = document.getElementById("nlMsg");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var ok = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test((input.value || "").trim());
      if (!ok) {
        form.classList.add("err");
        if (msg) msg.textContent = "Please enter a valid email address.";
        input.focus();
        return;
      }
      form.classList.remove("err");
      if (msg) { msg.style.color = "#fff"; msg.textContent = "You're in! Check your inbox for a 15% welcome code."; }
      input.value = "";
      toast("Subscribed — welcome to Bazaar");
    });
    input.addEventListener("input", function () {
      form.classList.remove("err");
      if (msg) msg.textContent = "";
    });
  }

  /* ---------- scroll reveal ---------- */
  function initReveal() {
    var els = document.querySelectorAll(".reveal");
    if (!els.length) return;
    if (reduceMotion || !("IntersectionObserver" in window)) {
      els.forEach(function (el) { el.classList.add("in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    els.forEach(function (el) { io.observe(el); });
  }

  /* ---------- back to top ---------- */
  function initBackTop() {
    var btn = document.getElementById("backTop");
    if (!btn) return;
    window.addEventListener("scroll", function () {
      btn.classList.toggle("show", window.scrollY > 640);
    }, { passive: true });
    btn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
    });
  }

  /* ---------- PDP: gallery ---------- */
  function initGallery() {
    var main = document.getElementById("galleryMain");
    if (!main) return;
    var img = main.querySelector("img");
    var thumbs = document.querySelectorAll(".gallery-thumbs button");
    thumbs.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var src = btn.getAttribute("data-full");
        if (src && img) img.src = src;
        thumbs.forEach(function (t) { t.setAttribute("aria-current", "false"); });
        btn.setAttribute("aria-current", "true");
      });
    });
  }

  /* ---------- PDP: variant option buttons ---------- */
  function initVariants() {
    document.querySelectorAll("[data-variant]").forEach(function (group) {
      var opts = group.querySelectorAll(".opt-btn, .swatch");
      var out = group.querySelector("[data-variant-out]");
      opts.forEach(function (o) {
        o.addEventListener("click", function () {
          if (o.disabled) return;
          opts.forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
          o.setAttribute("aria-pressed", "true");
          if (out) out.textContent = o.getAttribute("data-value") || o.textContent.trim();
        });
      });
    });
  }

  /* ---------- PDP: quantity stepper ---------- */
  function initQty() {
    document.querySelectorAll(".qty-stepper").forEach(function (st) {
      var input = st.querySelector("input");
      var dec = st.querySelector('[data-qty="dec"]');
      var inc = st.querySelector('[data-qty="inc"]');
      if (!input) return;
      var min = parseInt(input.getAttribute("min"), 10) || 1;
      var max = parseInt(input.getAttribute("max"), 10) || 99;
      function clamp() {
        var v = parseInt(input.value, 10);
        if (isNaN(v) || v < min) v = min;
        if (v > max) v = max;
        input.value = v;
      }
      if (dec) dec.addEventListener("click", function () { input.value = (parseInt(input.value, 10) || min) - 1; clamp(); });
      if (inc) inc.addEventListener("click", function () { input.value = (parseInt(input.value, 10) || min) + 1; clamp(); });
      input.addEventListener("change", clamp);
    });
  }

  /* ---------- PDP: tabs ---------- */
  function initTabs() {
    var nav = document.querySelector(".tab-nav");
    if (!nav) return;
    var tabs = nav.querySelectorAll("button");
    var panels = document.querySelectorAll(".tab-panel");
    function activate(id) {
      tabs.forEach(function (t) { t.setAttribute("aria-selected", t.getAttribute("data-tab") === id ? "true" : "false"); });
      panels.forEach(function (p) { p.classList.toggle("active", p.id === "tab-" + id); });
    }
    tabs.forEach(function (t) {
      t.addEventListener("click", function () { activate(t.getAttribute("data-tab")); });
    });
    // deep-link to reviews
    document.querySelectorAll('[data-jump="reviews"]').forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        activate("reviews");
        var el = document.querySelector(".pdp-tabs");
        if (el) el.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
      });
    });
  }

  /* ---------- boot ---------- */
  document.addEventListener("DOMContentLoaded", function () {
    initMobileNav();
    initHeroCarousel();
    initCountdown();
    initStockBars();
    initCart();
    initWishlist();
    initFilter();
    initNewsletter();
    initReveal();
    initBackTop();
    initGallery();
    initVariants();
    initQty();
    initTabs();
  });
})();
