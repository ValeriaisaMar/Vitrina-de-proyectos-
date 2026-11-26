"""Perfil público de cada persona (spec 009, historia 4).

Aquí vive la lógica del perfil para que las vistas queden cortas:
- crear_perfil(): el perfil de una cuenta nueva, con un slug estable.
- normalizar_github / normalizar_linkedin / normalizar_orcid: validan y dejan los enlaces en una
  sola forma (por ejemplo, "octocat" → "https://github.com/octocat").
- personas_relacionadas(): coautores y docentes o estudiantes con los que trabajó, solo en
  proyectos aprobados, con pocas consultas.
- buscar_personas(): perfiles cuyo nombre coincide con la búsqueda de Explorar.
"""

import re

from django.core.exceptions import ValidationError
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.utils.text import slugify
from django.utils.translation import gettext as _

from cuentas.models import Perfil, Rol, Usuario

# --------------------------------------------------------------------------- Crear


def slug_unico(usuario):
    """Slug a partir del nombre ("ana-perez"); si ya existe, "ana-perez-2". Nunca el correo ni el id."""
    base = slugify(f"{usuario.nombres} {usuario.apellidos}")[:80] or "persona"
    slug, n = base, 2
    while Perfil.objects.filter(slug=slug).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


def crear_perfil(usuario):
    """Devuelve el perfil de la persona y lo crea si no lo tiene."""
    perfil = Perfil.objects.filter(usuario=usuario).first()
    if perfil is None:
        perfil = Perfil.objects.create(usuario=usuario, slug=slug_unico(usuario))
    return perfil


# --------------------------------------------------------------------------- Enlaces

_USUARIO_GITHUB = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")
_URL_GITHUB = re.compile(r"^(?:https?://)?(?:www\.)?github\.com/([^/?#\s]+)/?$", re.I)
_URL_LINKEDIN = re.compile(r"^(?:https?://)?(?:[a-z]{2,3}\.)?linkedin\.com/in/([A-Za-z0-9\-_%]{3,100})/?$", re.I)
_ORCID = re.compile(r"^(?:https?://)?(?:www\.)?(?:orcid\.org/)?(\d{4}-?\d{4}-?\d{4}-?\d{3}[\dXx])/?$")


def normalizar_github(valor):
    """Acepta "usuario" o "https://github.com/usuario". Devuelve la URL completa o lanza ValidationError."""
    valor = (valor or "").strip()
    if not valor:
        return ""
    coincidencia = _URL_GITHUB.match(valor)
    usuario = coincidencia.group(1) if coincidencia else valor.lstrip("@")
    if not _USUARIO_GITHUB.match(usuario):
        raise ValidationError(_("Escribe tu usuario de GitHub o un enlace como https://github.com/usuario."), code="github")
    return f"https://github.com/{usuario}"


def normalizar_linkedin(valor):
    """Exige un perfil personal: https://www.linkedin.com/in/<id>."""
    valor = (valor or "").strip()
    if not valor:
        return ""
    coincidencia = _URL_LINKEDIN.match(valor)
    if not coincidencia:
        raise ValidationError(_("Escribe el enlace de tu perfil de LinkedIn, como https://www.linkedin.com/in/tu-nombre."), code="linkedin")
    return f"https://www.linkedin.com/in/{coincidencia.group(1)}"


def digito_verificador_orcid(base):
    """Dígito verificador de un ORCID (norma ISO 7064 11,2) a partir de sus primeros 15 dígitos."""
    total = 0
    for digito in base:
        total = (total + int(digito)) * 2
    resultado = (12 - total % 11) % 11
    return "X" if resultado == 10 else str(resultado)


def normalizar_orcid(valor):
    """Acepta "0000-0002-1825-0097" (o el enlace de orcid.org) y comprueba el dígito verificador."""
    valor = (valor or "").strip()
    if not valor:
        return ""
    coincidencia = _ORCID.match(valor)
    if not coincidencia:
        raise ValidationError(_("El ORCID tiene la forma 0000-0000-0000-000X."), code="orcid")
    digitos = coincidencia.group(1).replace("-", "").upper()
    if digito_verificador_orcid(digitos[:15]) != digitos[15]:
        raise ValidationError(_("Ese ORCID no es válido: revisa los números (el último es un dígito de control)."), code="orcid_digito")
    return "-".join(digitos[i:i + 4] for i in range(0, 16, 4))


# --------------------------------------------------------------------------- Consultas


def perfiles_visibles():
    """Perfiles que se pueden mostrar: cuenta activa con rol estudiante o profesor."""
    return Perfil.objects.filter(
        usuario__is_active=True, usuario__roles_asignados__rol__in=[Rol.ESTUDIANTE, Rol.PROFESOR],
    ).distinct()


def personas_relacionadas(usuario):
    """Personas con las que trabajó en proyectos APROBADOS, con el número de proyectos en común.

    - Coautores de sus proyectos.
    - Si es estudiante: los profesores que revisaron sus proyectos.
    - Si es profesor: los estudiantes autores de los proyectos que revisó.
    Hace cuatro consultas, sin importar cuántos proyectos haya: tres traen solo parejas
    (persona, proyecto) y la cuarta trae los perfiles. Una persona que aparece por dos caminos
    cuenta una sola vez, con el total de proyectos distintos. Devuelve una lista ordenada de dicts.
    """
    from proyectos.models import Autoria, Estado, Proyecto  # cuentas no depende de proyectos al cargar

    aprobados = Proyecto.objects.filter(estado=Estado.APROBADO)
    mios = aprobados.filter(autorias__usuario=usuario).values("pk")
    proyectos_por_persona = {}

    def sumar(parejas):
        for persona_id, proyecto_id in parejas:
            if persona_id and persona_id != usuario.pk:
                proyectos_por_persona.setdefault(persona_id, set()).add(proyecto_id)

    sumar(Autoria.objects.filter(proyecto__in=mios).values_list("usuario_id", "proyecto_id"))
    if usuario.tiene_rol(Rol.ESTUDIANTE):
        sumar(aprobados.filter(pk__in=mios).values_list("revisor_id", "pk"))
    if usuario.tiene_rol(Rol.PROFESOR):
        sumar(Autoria.objects.filter(proyecto__in=aprobados.filter(revisor=usuario)).values_list("usuario_id", "proyecto_id"))
    if not proyectos_por_persona:
        return []

    perfiles = (
        perfiles_visibles().filter(usuario_id__in=proyectos_por_persona)
        .select_related("usuario").prefetch_related("usuario__roles_asignados")
    )
    tarjetas = [{"perfil": p, "en_comun": len(proyectos_por_persona[p.usuario_id])} for p in perfiles]
    return sorted(tarjetas, key=lambda t: (-t["en_comun"], t["perfil"].usuario.nombre_completo.casefold()))


def buscar_personas(texto, limite=6):
    """Perfiles visibles cuyo nombre completo coincide con el texto (para el bloque "Personas")."""
    texto = " ".join((texto or "").split())
    if len(texto) < 2:
        return []
    return list(
        perfiles_visibles()
        .annotate(nombre_completo=Concat("usuario__nombres", Value(" "), "usuario__apellidos"))
        .filter(Q(nombre_completo__icontains=texto) | Q(usuario__apellidos__icontains=texto))
        .select_related("usuario").prefetch_related("usuario__roles_asignados")
        .order_by("usuario__apellidos", "usuario__nombres")[:limite]
    )


def usuarios_por_nombre(texto):
    """Ids de usuarios cuyo nombre completo contiene el texto (para buscar proyectos por autor)."""
    return (
        Usuario.objects.annotate(nombre_completo=Concat("nombres", Value(" "), "apellidos"))
        .filter(nombre_completo__icontains=" ".join(texto.split()))
        .values("pk")
    )


# --------------------------------------------------------------------------- Edición en la misma página


def formularios_de_edicion(perfil, ligado=None):
    """Formularios de cada sección del perfil, sin datos. `ligado` = (nombre, form con errores)."""
    from cuentas import forms as f

    formularios = {
        "foto": f.FormularioFoto(),
        "descripcion": f.FormularioDescripcion(instance=perfil, prefix="descripcion"),
        "aptitudes": f.FormularioAptitudes(prefix="aptitudes", initial={"aptitudes": ", ".join(a.nombre for a in perfil.aptitudes.all())}),
        "enlaces": f.FormularioEnlaces(instance=perfil, prefix="enlaces"),
        "experiencia": f.FormularioExperiencia(prefix="experiencia"),
        "estudio": f.FormularioEstudio(prefix="estudio"),
    }
    if perfil.usuario.tiene_rol(Rol.PROFESOR):
        formularios["asignaturas"] = f.FormularioAsignaturasImparte(instance=perfil, prefix="asignaturas")
    if ligado:
        formularios[ligado[0]] = ligado[1]
    return formularios


def editar_seccion(perfil, seccion, datos, archivos):
    """Guarda una sección del perfil. Devuelve (True, mensaje) o (False, (sección, form con errores)).

    Las vistas solo llaman aquí después de comprobar que quien edita es el dueño del perfil.
    """
    from config.imagenes import TAM_FOTO, convertir_a_webp
    from cuentas import forms as f

    if seccion == "foto":
        form = f.FormularioFoto(datos, archivos)
        if not form.is_valid():
            return False, ("foto", form)
        anterior = perfil.foto.name
        contenido = convertir_a_webp(form.cleaned_data["foto"], TAM_FOTO)
        perfil.foto.save(contenido.name, contenido, save=False)  # nombre aleatorio: <uuid>.webp
        perfil.save(update_fields=["foto"])
        if anterior:
            perfil.foto.storage.delete(anterior)
        return True, _("Actualizamos tu foto.")

    if seccion == "quitar_foto":
        if perfil.foto:
            perfil.foto.delete(save=False)
            perfil.foto = ""
            perfil.save(update_fields=["foto"])
        return True, _("Quitamos tu foto.")

    if seccion == "quitar_experiencia" or seccion == "quitar_estudio":
        relacion = perfil.experiencias if seccion == "quitar_experiencia" else perfil.estudios
        borrados, _detalle = relacion.filter(pk=datos.get("pk") or 0).delete()  # solo las suyas
        return True, _("Quitamos el elemento.") if borrados else _("No encontramos ese elemento.")

    clases = {
        "descripcion": (f.FormularioDescripcion, True),
        "enlaces": (f.FormularioEnlaces, True),
        "asignaturas": (f.FormularioAsignaturasImparte, True),
        "aptitudes": (f.FormularioAptitudes, False),
        "experiencia": (f.FormularioExperiencia, False),
        "estudio": (f.FormularioEstudio, False),
    }
    if seccion not in clases or (seccion == "asignaturas" and not perfil.usuario.tiene_rol(Rol.PROFESOR)):
        return False, None
    clase, es_del_perfil = clases[seccion]
    form = clase(datos, prefix=seccion, **({"instance": perfil} if es_del_perfil else {}))
    if not form.is_valid():
        return False, (seccion, form)
    if seccion == "aptitudes":
        form.guardar(perfil)
    elif es_del_perfil:
        form.save()
    else:
        elemento = form.save(commit=False)
        elemento.perfil = perfil
        elemento.save()
    return True, _("Guardamos los cambios de tu perfil.")
