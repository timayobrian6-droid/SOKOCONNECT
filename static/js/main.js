/* ============================================================
   SokoConnect — dependency-free vanilla JS. Guard-claused module inits.
   ============================================================ */
(function () {
  "use strict";
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- server helpers ---------- */
  function csrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) return meta.content;
    var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }

  function post(url, data) {
    var body = new FormData();
    Object.keys(data || {}).forEach(function (k) { body.append(k, data[k]); });
    return fetch(url, {
      method: "POST",
      body: body,
      credentials: "same-origin",
      headers: { "X-CSRFToken": csrfToken(), "X-Requested-With": "XMLHttpRequest", Accept: "application/json" }
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (json) {
        json._status = res.status;
        if (res.status === 401 && json.login_url) {
          window.location.href = json.login_url;
        }
        return json;
      });
    });
  }

  function formatKsh(n) {
    var v = Number(n) || 0;
    return "KSh " + v.toLocaleString("en-KE", { maximumFractionDigits: v % 1 ? 2 : 0 });
  }

  function setBadges(selector, n) {
    document.querySelectorAll(selector).forEach(function (b) {
      b.textContent = n;
      b.hidden = !n;
    });
  }

  /* ---------- toast helper ---------- */
  function toast(msg) {
    var wrap = document.getElementById("toastWrap");
    if (!wrap) return;
    var t = document.createElement("div");
    t.className = "bz-toast";
    t.setAttribute("role", "status");
    t.innerHTML =
      '<span class="ti"><svg class="svg-ico" viewBox="0 0 24 24" aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg></span><span>' +
      escapeHtml(msg) + "</span>";
    wrap.appendChild(t);
    requestAnimationFrame(function () { t.classList.add("show"); });
    setTimeout(function () {
      t.classList.remove("show");
      setTimeout(function () { t.remove(); }, 260);
    }, 2600);
  }

  function escapeHtml(str) {
    var d = document.createElement("div");
    d.textContent = str == null ? "" : String(str);
    return d.innerHTML;
  }

  /* ---------- Django messages -> toasts ---------- */
  function initMessages() {
    var el = document.getElementById("django-messages");
    if (!el) return;
    try {
      JSON.parse(el.textContent).forEach(function (m, i) {
        setTimeout(function () { toast(m.text); }, i * 350);
      });
    } catch (e) { /* ignore malformed payload */ }
  }

  /* ---------- account dropdown ---------- */
  function initAccountMenu() {
    var toggle = document.getElementById("accountToggle");
    var menu = document.getElementById("accountDropdown");
    if (!toggle || !menu) return;
    toggle.addEventListener("click", function (e) {
      if (window.matchMedia("(hover: none)").matches || e.detail === 0) {
        e.preventDefault();
      } else {
        return;
      }
      var open = menu.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("click", function (e) {
      if (!menu.contains(e.target) && !toggle.contains(e.target)) {
        menu.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
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
    // deals refresh twice a day: count down to the next 12:00 / 00:00 boundary
    var now = new Date();
    var end = new Date(now);
    end.setHours(now.getHours() < 12 ? 12 : 24, 0, 0, 0);
    end = end.getTime();
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
    var cartBtn = document.querySelector(".hact.cart");
    function pop() {
      if (!cartBtn) return;
      cartBtn.classList.add("pop");
      setTimeout(function () { cartBtn.classList.remove("pop"); }, 340);
    }
    document.querySelectorAll("[data-add-cart]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        var id = btn.getAttribute("data-add-cart");
        if (!id) return;
        e.preventDefault();
        var qty = 1;
        var qtySel = btn.getAttribute("data-qty-input");
        if (qtySel && document.querySelector(qtySel)) qty = parseInt(document.querySelector(qtySel).value, 10) || 1;
        btn.disabled = true;
        post("/cart/add/" + id + "/", { quantity: qty }).then(function (res) {
          btn.disabled = false;
          if (res.ok) {
            setBadges("[data-cart-count]", res.count);
            pop();
          }
          if (res.message) toast(res.message);
        }).catch(function () {
          btn.disabled = false;
          toast("Could not reach the server. Please try again.");
        });
      });
    });
  }

  /* ---------- cart page: live quantity updates ---------- */
  function initCartPage() {
    var page = document.querySelector("[data-cart-page]");
    if (!page) return;
    function apply(res) {
      if (!res.ok) { if (res.message) toast(res.message); return; }
      setBadges("[data-cart-count]", res.count);
      page.querySelectorAll("[data-cart-row]").forEach(function (row) {
        var item = res.items[row.getAttribute("data-cart-row")];
        if (!item) { row.remove(); return; }
        var input = row.querySelector('input[name="quantity"]');
        if (input) input.value = item.quantity;
        var line = row.querySelector("[data-line-total]");
        if (line) line.textContent = formatKsh(item.line_total);
      });
      var set = function (sel, v) { var el = page.querySelector(sel); if (el) el.textContent = v; };
      set("[data-subtotal]", formatKsh(res.subtotal));
      set("[data-delivery]", res.delivery ? formatKsh(res.delivery) : "Free");
      set("[data-total]", formatKsh(res.total));
      if (!res.count) {
        page.remove();
        var empty = document.querySelector("[data-cart-empty]");
        if (empty) empty.hidden = false;
      }
    }
    page.querySelectorAll("form[data-cart-update]").forEach(function (form) {
      var input = form.querySelector('input[name="quantity"]');
      var timer = null;
      function send() {
        clearTimeout(timer);
        timer = setTimeout(function () {
          post(form.action, { quantity: input.value }).then(apply);
        }, 250);
      }
      input.addEventListener("change", send);
      form.addEventListener("submit", function (e) { e.preventDefault(); send(); });
    });
    page.querySelectorAll("form[data-cart-remove]").forEach(function (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        post(form.action, {}).then(function (res) { apply(res); if (res.message) toast(res.message); });
      });
    });
  }

  /* ---------- wishlist ---------- */
  function initWishlist() {
    document.querySelectorAll("[data-wish]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        var id = btn.getAttribute("data-wish");
        post("/wishlist/toggle/" + id + "/", {}).then(function (res) {
          if (!res.ok) return;
          document.querySelectorAll('[data-wish="' + id + '"]').forEach(function (b) {
            b.setAttribute("aria-pressed", res.saved ? "true" : "false");
          });
          setBadges("[data-wish-count]", res.count);
          toast(res.message);
        });
      });
    });
  }

  /* ---------- small form helpers ---------- */
  function initFormHelpers() {
    document.querySelectorAll("[data-autosubmit]").forEach(function (el) {
      el.addEventListener("change", function () { if (el.form) el.form.submit(); });
    });
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
      form.addEventListener("submit", function (e) {
        if (!window.confirm(form.getAttribute("data-confirm"))) e.preventDefault();
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
      var btn = form.querySelector('button[type="submit"]');
      if (btn) btn.disabled = true;
      post(form.action, { email: input.value.trim() }).then(function (res) {
        if (btn) btn.disabled = false;
        if (!res.ok) {
          form.classList.add("err");
          if (msg) msg.textContent = res.message || "Something went wrong. Please try again.";
          return;
        }
        if (msg) { msg.style.color = "#fff"; msg.textContent = res.message; }
        input.value = "";
        toast("Subscribed — welcome to SokoConnect");
      }).catch(function () {
        if (btn) btn.disabled = false;
        if (msg) msg.textContent = "Could not reach the server. Please try again.";
      });
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
      var input = st.querySelector("input[type=number]");
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
      function bump(d) {
        var before = input.value;
        input.value = (parseInt(input.value, 10) || min) + d;
        clamp();
        if (input.value !== before) input.dispatchEvent(new Event("change"));
      }
      if (dec) dec.addEventListener("click", function () { bump(-1); });
      if (inc) inc.addEventListener("click", function () { bump(1); });
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
    initMessages();
    initAccountMenu();
    initMobileNav();
    initHeroCarousel();
    initCountdown();
    initStockBars();
    initCart();
    initCartPage();
    initWishlist();
    initFormHelpers();
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
