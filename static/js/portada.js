/* Vista previa en vivo de la portada en el formulario del proyecto (spec 009).
   Cambia el color al elegir otro de la paleta, el título de la portada al escribirlo y muestra la
   imagen elegida antes de subirla. Sin este archivo el formulario funciona igual. */
(function () {
  "use strict";

  var bloque = document.querySelector("[data-portada]");
  if (!bloque) return;
  var color = bloque.querySelector("[data-vista-color]");
  var imagen = bloque.querySelector("[data-vista-imagen]");
  var tituloPortada = bloque.querySelector("[data-vista-titulo]");
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
  // Si el formulario volvió con errores, la vista previa toma el color que quedó marcado
  var marcado = bloque.querySelector("[data-color]:checked");
  if (marcado) color.style.backgroundColor = marcado.dataset.color;

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

  // El título de la portada se escribe tal cual (con tildes, ñ y signos), como en la página del proyecto
  if (titulo && tituloPortada) {
    titulo.addEventListener("input", function () {
      var texto = titulo.value.normalize("NFC").trim();
      tituloPortada.textContent = texto || tituloPortada.dataset.porDefecto;
    });
  }
})();
