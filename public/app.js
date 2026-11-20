/* --- SearchName · interações da landing (nav, reveal, FAQ, busca rápida) --- */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* --- reveal ao entrar na tela --- */
  var revealEls = Array.prototype.slice.call(document.querySelectorAll(".sn-reveal"));

  if (reduced || !("IntersectionObserver" in window)) {
    revealEls.forEach(function (el) { el.setAttribute("data-visible", "true"); });
  } else {
    document.documentElement.setAttribute("data-reveal", "");
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.setAttribute("data-visible", "true");
        io.unobserve(entry.target);
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -5% 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
  }

  /* --- nav com borda depois do topo --- */
  var nav = document.getElementById("nav");
  var ticking = false;

  function syncNav() {
    if (!nav) return;
    nav.setAttribute("data-scrolled", window.scrollY > 12 ? "true" : "false");
  }

  window.addEventListener("scroll", function () {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      ticking = false;
      syncNav();
    });
  }, { passive: true });
  syncNav();

  /* --- FAQ: uma resposta aberta por vez --- */
  var faqItems = Array.prototype.slice.call(document.querySelectorAll(".sn-faq__item"));
  faqItems.forEach(function (item) {
    item.addEventListener("toggle", function () {
      if (!item.open) return;
      faqItems.forEach(function (other) {
        if (other !== item) other.open = false;
      });
    });
  });

  /* --- busca rápida do hero: valida e manda para a ferramenta --- */
  var heroForm = document.getElementById("hero-form");
  if (heroForm) {
    heroForm.addEventListener("submit", function (event) {
      var input = document.getElementById("hero-name");
      var region = document.getElementById("hero-region");
      var nome = input ? input.value.trim() : "";

      if (nome.length < 3) {
        event.preventDefault();
        if (input) {
          input.focus();
          input.setAttribute("aria-invalid", "true");
        }
        return;
      }
      if (input) input.removeAttribute("aria-invalid");
      /* --- o navegador monta ?name=&region= e a ferramenta continua a busca. --- */
      if (region) region.name = "region";
    });

    var heroInput = document.getElementById("hero-name");
    if (heroInput) {
      heroInput.addEventListener("input", function () {
        heroInput.removeAttribute("aria-invalid");
      });
    }
  }

  /* --- ano no rodapé --- */
  var year = document.getElementById("ano");
  if (year) year.textContent = new Date().getFullYear();
})();
