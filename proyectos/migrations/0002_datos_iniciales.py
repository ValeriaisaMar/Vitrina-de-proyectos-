"""Datos iniciales: malla de Ingeniería de Software de la UTEQ y tecnologías comunes.

Fuente de la malla: imagen "Malla curricular Software" del sitio oficial de la UTEQ
(https://www.uteq.edu.ec/grado/carrera/software). Se omiten los niveles de inglés.

Una migración de datos usa RunPython: la función recibe "apps" y obtiene los modelos con
apps.get_model(...) (la versión histórica del modelo, no la importada), así sigue funcionando
aunque el modelo cambie en el futuro.
"""

from django.db import migrations

MALLA = {
    1: ["Álgebra lineal", "Algoritmos y lógica de programación", "Cálculo diferencial",
        "Enfoque a la ingeniería de software", "Estructuras discretas I"],
    2: ["Arquitectura de computadoras", "Cálculo integral", "Estructuras discretas II",
        "Fundamentos de física para la ingeniería", "Metodología de la investigación",
        "Programación orientada a objetos"],
    3: ["Base de datos", "Estructura de datos", "Métodos numéricos", "Modelamiento de software",
        "Probabilidad y estadística", "Redacción técnica"],
    4: ["Dinámica de grupo y comunicación", "Fundamentos de contabilidad y finanzas",
        "Ingeniería de requerimientos", "Interacción hombre-máquina", "Investigación de operaciones",
        "Sistemas operativos"],
    5: ["Administración de bases de datos", "Aplicaciones web", "Diseño y arquitectura de software",
        "Modelos matemáticos y simulación", "Verificación y validación de software"],
    6: ["Administración de plataformas de software", "Aplicaciones móviles", "Construcción de software",
        "Proceso de software", "Redes de datos"],
    7: ["Aplicaciones distribuidas", "Calidad del software", "Inteligencia de negocios",
        "Mantenimiento de software", "Seguridad informática"],
    8: ["Deontología informática", "Gestión de la configuración de software", "Herramientas de programación",
        "Ingeniería económica para software", "Modelos de decisión y optimización"],
    9: ["Ciencia, tecnología, sociedad e innovación", "Formulación del trabajo de titulación",
        "Gestión de tecnologías de la información",
        "Realidad socioeconómica, cultural y ecológica del Ecuador y el mundo", "Sistemas inteligentes"],
    10: ["Desarrollo del trabajo de titulación II", "Legislación informática", "Liderazgo y emprendimiento",
         "Programación en la nube", "Redacción de documentos científicos"],
}

TECNOLOGIAS = [
    "Python", "Django", "Flask", "FastAPI", "Java", "Spring Boot", "Kotlin", "JavaScript", "TypeScript",
    "Node.js", "Express", "React", "Angular", "Vue", "PHP", "Laravel", "C#", ".NET", "C++", "Dart",
    "Flutter", "Swift", "HTML", "CSS", "Tailwind CSS", "Bootstrap", "PostgreSQL", "MySQL", "SQL Server",
    "SQLite", "MongoDB", "Firebase", "Docker", "Git", "Linux", "AWS", "Arduino", "ESP32", "IoT",
    "Machine Learning", "TensorFlow", "Power BI",
]


def cargar(apps, schema_editor):
    Asignatura = apps.get_model("proyectos", "Asignatura")
    Tecnologia = apps.get_model("proyectos", "Tecnologia")
    for semestre, nombres in MALLA.items():
        for nombre in nombres:
            Asignatura.objects.get_or_create(nombre=nombre, defaults={"semestre": semestre})
    for nombre in TECNOLOGIAS:
        Tecnologia.objects.get_or_create(nombre=nombre)


def descargar(apps, schema_editor):
    """Permite deshacer la migración (migrate proyectos 0001)."""
    apps.get_model("proyectos", "Asignatura").objects.filter(
        nombre__in=[n for lista in MALLA.values() for n in lista], proyectos__isnull=True
    ).delete()
    apps.get_model("proyectos", "Tecnologia").objects.filter(nombre__in=TECNOLOGIAS, proyectos__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("proyectos", "0001_initial")]
    operations = [migrations.RunPython(cargar, descargar)]
