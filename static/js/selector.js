/* Buscador para los <select data-buscable> (spec 009): por ejemplo, la asignatura de un proyecto,
   agrupada por plan y semestre. Agrega un campo de búsqueda encima del select y deja a la vista
   solo las opciones que coinciden (sin distinguir mayúsculas ni tildes). Sin JavaScript queda el
   select normal, que sigue funcionando. */
(function () {
  "use strict";

  function sinTildes(texto) {
    return texto.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }

  document.querySelectorAll("select[data-buscable]").forEach(function (select) {
    var buscador = document.createElement("input");
    buscador.type = "search";
    buscador.className = "campo-control mb-2";
    buscador.placeholder = select.dataset.textoBuscar || (document.documentElement.lang === "en" ? "Search…" : "Buscar…");
    buscador.setAttribute("aria-label", buscador.placeholder);
    buscador.setAttribute("aria-controls", select.id);
    select.parentNode.insertBefore(buscador, select);

    buscador.addEventListener("input", function () {
      var texto = sinTildes(buscador.value.trim());
      select.querySelectorAll("optgroup").forEach(function (grupo) {
        var grupoCoincide = sinTildes(grupo.label).indexOf(texto) !== -1;
        var visibles = 0;
        grupo.querySelectorAll("option").forEach(function (opcion) {
          var coincide = !texto || grupoCoincide || sinTildes(opcion.textContent).indexOf(texto) !== -1;
          opcion.hidden = !coincide;
          opcion.disabled = !coincide && !opcion.selected;
          if (coincide) visibles += 1;
        });
        grupo.hidden = visibles === 0;
      });
    });
  });
})();
