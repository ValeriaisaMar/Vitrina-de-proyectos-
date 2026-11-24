/*
  Tema claro/oscuro y menú móvil.

  - El tema ya se aplicó antes de pintar con el script corto de base.html (sin destello).
    Aquí solo se maneja el botón y se guarda la elección en el navegador.
  - El menú móvil es un <details>, así que funciona aunque este archivo no cargue.
    Aquí solo se cierra al tocar fuera o al pulsar Escape.
*/
(function () {
  "use strict";

  var raiz = document.documentElement;

  function guardar(tema) {
    try { localStorage.setItem("tema", tema); } catch (e) { /* navegador sin almacenamiento */ }
  }

  function actualizarBotones() {
    var oscuro = raiz.classList.contains("dark");
    document.querySelectorAll("[data-boton-tema]").forEach(function (boton) {
      boton.setAttribute("aria-pressed", oscuro ? "true" : "false");
      boton.setAttribute("aria-label", oscuro ? boton.dataset.textoClaro : boton.dataset.textoOscuro);
      boton.setAttribute("title", boton.getAttribute("aria-label"));
    });
  }

  document.addEventListener("click", function (evento) {
    var boton = evento.target.closest("[data-boton-tema]");
    if (boton) {
      var oscuro = raiz.classList.toggle("dark");
      guardar(oscuro ? "oscuro" : "claro");
      actualizarBotones();
      return;
    }
    // Cerrar el menú móvil si se toca fuera de él
    document.querySelectorAll("details[data-menu][open]").forEach(function (menu) {
      if (!menu.contains(evento.target)) menu.removeAttribute("open");
    });
  });

  document.addEventListener("keydown", function (evento) {
    if (evento.key !== "Escape") return;
    document.querySelectorAll("details[data-menu][open]").forEach(function (menu) {
      menu.removeAttribute("open");
      var resumen = menu.querySelector("summary");
      if (resumen) resumen.focus();
    });
  });

  actualizarBotones();
})();
