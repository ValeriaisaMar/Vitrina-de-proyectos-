/* Elegir profesor revisor (spec 009): filtros al instante y resumen del perfil en un diálogo.
   Todo funciona sin este archivo (los filtros recargan la página y el nombre abre el perfil en
   otra pestaña); esto solo lo hace más rápido y sin perder la elección en curso. */
(function () {
  "use strict";

  var lista = document.querySelector("[data-lista-profesores]");
  var filtros = document.querySelector("[data-filtros-profesores]");

  // ---------------------------------------------------------------- Filtros y orden
  if (lista && filtros) {
    document.querySelectorAll("[data-sin-js]").forEach(function (el) { el.hidden = true; });
    var contador = document.querySelector("[data-contador-profesores]");
    var valor = function (nombre) { return filtros.querySelector("[data-filtro='" + nombre + "']"); };
    var sinTildes = function (t) { return t.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); };

    var aplicar = function () {
      var texto = sinTildes(valor("q").value.trim());
      var asignatura = valor("asignatura").value;
      var semestre = valor("semestre").value;
      var soloDisponibles = valor("disponibles").checked;
      var orden = valor("orden").value;
      var tarjetas = Array.prototype.slice.call(lista.querySelectorAll("[data-profesor]"));
      var visibles = 0;
      tarjetas.forEach(function (t) {
        var ok = (!texto || sinTildes(t.dataset.nombre).indexOf(texto) !== -1)
          && (!asignatura || (" " + t.dataset.asignaturas).indexOf(" " + asignatura + " ") !== -1)
          && (!semestre || (" " + t.dataset.semestres).indexOf(" " + semestre + " ") !== -1)
          && (!soloDisponibles || t.dataset.disponible === "1");
        t.hidden = !ok;
        if (ok) visibles += 1;
      });
      tarjetas.sort(function (a, b) {
        if (orden === "pendientes") return (a.dataset.pendientes - b.dataset.pendientes) || a.dataset.nombre.localeCompare(b.dataset.nombre);
        if (orden === "relevancia") return (b.dataset.imparte - a.dataset.imparte) || a.dataset.nombre.localeCompare(b.dataset.nombre);
        return a.dataset.nombre.localeCompare(b.dataset.nombre);
      }).forEach(function (t) { lista.appendChild(t); });
      if (contador) {
        var en = document.documentElement.lang === "en";
        contador.textContent = visibles + (en ? (visibles === 1 ? " teacher" : " teachers") : (visibles === 1 ? " profesor" : " profesores"));
      }
    };
    filtros.addEventListener("input", aplicar);
    filtros.addEventListener("change", aplicar);
    // Enter en el buscador no debe enviar la elección
    valor("q").addEventListener("keydown", function (e) { if (e.key === "Enter") e.preventDefault(); });
  }

  // ---------------------------------------------------------------- Resumen del perfil
  var dialogo = document.getElementById("resumen-profesor");
  if (dialogo && typeof dialogo.showModal === "function") {
    var contenido = dialogo.querySelector("[data-contenido-resumen]");
    var origen = null;
    document.addEventListener("click", function (e) {
      var enlace = e.target.closest("[data-resumen]");
      if (!enlace) return;
      var plantilla = document.getElementById(enlace.dataset.resumen);
      if (!plantilla) return; // sin resumen: el enlace abre el perfil completo
      e.preventDefault();
      origen = enlace;
      contenido.replaceChildren(plantilla.content.cloneNode(true));
      dialogo.showModal();
    });
    dialogo.querySelector("[data-cerrar-resumen]").addEventListener("click", function () { dialogo.close(); });
    dialogo.addEventListener("click", function (e) { if (e.target === dialogo) dialogo.close(); }); // clic fuera
    dialogo.addEventListener("close", function () { if (origen) origen.focus(); });
  }
})();
