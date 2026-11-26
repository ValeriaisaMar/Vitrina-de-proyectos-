/* Menú de la cuenta (spec 009).

   Sin JavaScript, el avatar es un enlace a "Mi cuenta". Aquí se convierte en un botón de menú:
   - aria-expanded dice si está abierto; aria-haspopup ya viene en el HTML;
   - al abrir, el foco va al primer ítem; flechas arriba/abajo recorren los ítems;
   - Esc cierra y devuelve el foco al avatar; un clic fuera también cierra.
   En celular el panel se abre como hoja de ancho completo (lo hacen las clases de Tailwind). */
(function () {
  "use strict";

  document.querySelectorAll("[data-menu-desplegable]").forEach(function (contenedor) {
    var boton = contenedor.querySelector("[data-menu-boton]");
    var panel = contenedor.querySelector("[data-menu-panel]");
    if (!boton || !panel) return;

    boton.setAttribute("role", "button");
    boton.setAttribute("aria-expanded", "false");

    var items = function () {
      return Array.prototype.filter.call(panel.querySelectorAll("[data-menu-item]"), function (el) {
        return !el.disabled && el.offsetParent !== null;
      });
    };
    var abierto = function () { return !panel.hidden; };

    var abrir = function () {
      panel.hidden = false;
      boton.setAttribute("aria-expanded", "true");
      var primero = items()[0];
      if (primero) primero.focus();
    };
    var cerrar = function (devolverFoco) {
      if (!abierto()) return;
      panel.hidden = true;
      boton.setAttribute("aria-expanded", "false");
      if (devolverFoco) boton.focus();
    };

    boton.addEventListener("click", function (e) {
      e.preventDefault();
      if (abierto()) cerrar(false); else abrir();
    });
    boton.addEventListener("keydown", function (e) {
      // Un enlace no se activa con la barra espaciadora: como ahora es un botón, sí
      if (e.key === " " || e.key === "ArrowDown") { e.preventDefault(); abrir(); }
    });
    panel.addEventListener("keydown", function (e) {
      var lista = items();
      var i = lista.indexOf(document.activeElement);
      if (e.key === "ArrowDown") { e.preventDefault(); (lista[i + 1] || lista[0]).focus(); }
      if (e.key === "ArrowUp") { e.preventDefault(); (lista[i - 1] || lista[lista.length - 1]).focus(); }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && abierto()) cerrar(true);
    });
    document.addEventListener("click", function (e) {
      if (abierto() && !contenedor.contains(e.target)) cerrar(false);
    });
  });
})();
