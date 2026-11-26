# Quickstart: probar la spec 009

## Preparación

```bash
git pull
.venv/Scripts/python.exe -m pip install -r requirements.txt   # sin dependencias nuevas
.venv/Scripts/python.exe manage.py migrate
.venv/Scripts/python.exe manage.py compilemessages             # o el script propio en Windows
.venv/Scripts/python.exe manage.py test
.venv/Scripts/python.exe manage.py makemigrations --check --dry-run
.venv/Scripts/python.exe manage.py runserver
```

Usuarios de ejemplo (créalos desde "Usuarios" del admin o `createsuperuser`): **ana** (estudiante),
**pablo** y **rosa** (profesores), **admin** (admin). Activa las cuentas y dale a pablo la asignatura
del proyecto en su perfil.

## Escenarios

1. **Período actual** — Admin → Periodos → "Marcar como período actual" en otro período → confirma.
   Ana envía un borrador: toma ese período. Quita el actual (marca uno y bórralo no se puede) → Ana ve
   "No hay un período académico activo…". El pie muestra el período a todos.
2. **Correo** — Admin → Correo de envío: Gmail / Outlook / Personalizado cambian las instrucciones.
3. **Tildes** — Crea "Diseño de ñandúes: Árbol, pingüino y «más» ¿sí?" sin imagen: portada y PDF bien.
4. **Guardados** — En un proyecto publicado, "Guardar" → aparece en Guardados; `/comunidad/favoritos/` redirige.
5. **Plan de estudios** — Admin → Plan de estudios: crea "Plan 2026" con dos asignaturas; aparecen
   en el formulario de proyecto agrupadas; desactiva una y sigue en los proyectos que la usan.
6. **Perfil** — Ana completa descripción, una aptitud y GitHub; ábrelo sin sesión; ORCID inválido da
   error; un admin solo da 404. Busca "Ana" en Explorar: bloque Personas + sus proyectos.
7. **Revisor** — Ana envía y elige a pablo (sugerido "Imparte …"). Pablo → Solicitudes → No acepta
   recomendando a rosa → Ana recibe correo y ve a rosa destacada → elige a rosa → rosa acepta y
   pide cambios → Ana reenvía → vuelve a rosa sin elegir. Admin → reasigna a pablo. Revisa el historial.
8. **Menú** — Con cada rol activo abre el avatar (teclado: Tab, Enter, Esc). Visitante: engranaje.
9. **Portada** — Sube una portada (se ve 16:9 en la tarjeta), quítala, elige color; agrega demo y video.
