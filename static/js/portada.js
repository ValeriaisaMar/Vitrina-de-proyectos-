/* Vista previa en vivo de la portada en el formulario del proyecto (spec 009).
   Cambia el color al elegir otro de la paleta, la inicial al escribir el título y muestra la
   imagen elegida antes de subirla. Sin este archivo el formulario funciona igual. */
(function () {
  "use strict";

  var bloque = document.querySelector("[data-portada]");
  if (!bloque) return;
  var color = bloque.querySelector("[data-vista-color]");
  var imagen = bloque.querySelector("[data-vista-imagen]");
  var inicial = bloque.querySelector("[data-vista-inicial]");
  var archivo = bloque.querySelector("input[type=file]");
  var quitar = bloque.querySelector("input[type=checkbox][name=quitar_portada]");
  var titulo = document.getElementById("id_titulo");

  var mostrarImagen = function (si) {
    imagen.classList.toggle("hidden", !si);
    color.classList.toggle("hidden", si);
  };

  bloque.addEventListener("change", function (e) {
    if (e.target.matches("[data-color]")) color.style.backgroundColor = e.target.dataset.color;
  });

  if (archivo) {
    archivo.addEventListener("change", function () {
      var elegido = archivo.files && archivo.files[0];
      if (!elegido) return;
      imagen.src = URL.createObjectURL(elegido);
      mostrarImagen(true);
      if (quitar) quitar.checked = false;
    });
  }
  if (quitar) {
    quitar.addEventListener("change", function () { mostrarImagen(!quitar.checked && !!imagen.getAttribute("src")); });
  }

  // La misma regla que el filtro |inicial: la primera letra o número, con su tilde
  if (titulo && inicial) {
    titulo.addEventListener("input", function () {
      var texto = titulo.value.normalize("NFC");
      var letra = texto.match(/[\p{L}\p{N}]\p{M}*/u);
      inicial.textContent = letra ? letra[0].toUpperCase() : "V";
    });
  }
})();
