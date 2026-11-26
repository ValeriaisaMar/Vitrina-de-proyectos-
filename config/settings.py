"""Configuración de Django para Vitrina de Proyectos.

Los valores secretos o que cambian entre equipos se leen del archivo .env (ver .env.example).
Documentación de cada ajuste: https://docs.djangoproject.com/en/6.1/ref/settings/
"""

from pathlib import Path

from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

from config.entorno import booleano, lista, variable

BASE_DIR = Path(__file__).resolve().parent.parent

# Carga .env en las variables de entorno (si no existe, no pasa nada: se usan las del sistema).
load_dotenv(BASE_DIR / ".env")


# ---------------------------------------------------------------------------
# Seguridad básica
# ---------------------------------------------------------------------------

SECRET_KEY = variable("SECRET_KEY", obligatoria=True)
DEBUG = booleano("DEBUG", defecto=False)
ALLOWED_HOSTS = lista("ALLOWED_HOSTS", "127.0.0.1,localhost")


# ---------------------------------------------------------------------------
# Aplicaciones
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Apps del proyecto (constitución, principio I)
    "cuentas",
    "proyectos",
    "comunidad",
    "vitrina",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Español por defecto: ignora el idioma del navegador; solo cuenta la elección ES/EN.
    "config.middleware.EspanolPorDefectoMiddleware",
    # Activa el idioma de cada petición según la cookie del selector. Va después de sesiones.
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Rol con el que actúa la persona (spec 008). Va después de AuthenticationMiddleware.
    "config.middleware.RolActivoMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Plantillas compartidas (base, componentes, errores). Cada app tiene además las suyas.
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "config.contexto.marca",
                "config.contexto.roles",
                "config.contexto.periodo_actual",
                "config.contexto.menu_cuenta",
            ],
            # Etiquetas disponibles en todas las plantillas sin {% load %}: {% icono %} y |inicial (spec 009)
            "builtins": ["vitrina.templatetags.iconos"],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# ---------------------------------------------------------------------------
# Base de datos: PostgreSQL en todos los entornos (constitución, principio I)
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": variable("DB_NAME", obligatoria=True),
        "USER": variable("DB_USER", obligatoria=True),
        "PASSWORD": variable("DB_PASSWORD", ""),
        "HOST": variable("DB_HOST", "localhost"),
        "PORT": variable("DB_PORT", "5432"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Usuarios y autenticación
# ---------------------------------------------------------------------------

# Usuario propio: entra con su correo y tiene un rol. Debe existir antes de la primera migración.
AUTH_USER_MODEL = "cuentas.Usuario"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Los enlaces de activación y de recuperación vencen en 24 horas (constitución, principio IV).
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24

LOGIN_URL = "cuentas:entrar"
LOGIN_REDIRECT_URL = "vitrina:panel"  # cada rol llega a su panel (módulo 006)
LOGOUT_REDIRECT_URL = "vitrina:inicio"


# Caché: guarda los intentos fallidos de inicio de sesión (cuentas/limite.py).
# En memoria basta para un solo proceso; en producción con varios, usar una caché compartida.
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "vitrina"},
}

# Las pruebas vacían la caché antes de cada caso (config/pruebas.py), así ninguna hereda datos de otra.
TEST_RUNNER = "config.pruebas.Ejecutor"


# ---------------------------------------------------------------------------
# Idioma y zona horaria (constitución, principio XI)
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "es"
LANGUAGES = [
    ("es", _("Español")),
    ("en", _("Inglés")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True

TIME_ZONE = "America/Guayaquil"
USE_TZ = True


# ---------------------------------------------------------------------------
# Archivos estáticos y de usuarios
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# Servir media/ desde Django cuando no hay nginx delante (por ejemplo, Docker en tu equipo)
SERVIR_MEDIA = booleano("SERVIR_MEDIA", defecto=False)

# Dirección base para los QR de verificación (opcional). Sirve cuando el servidor se ve desde
# otros equipos con una dirección distinta, por ejemplo en la demo: http://192.168.1.20:8000
SITIO_URL = variable("SITIO_URL", "").rstrip("/")

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# ---------------------------------------------------------------------------
# Correo (spec 008, historia 3)
#
# 1. Si un admin configuró el correo de envío en la app (Mi panel → Correo de envío), se usa ese.
# 2. Si no, Gmail con la contraseña de aplicación del .env.
# 3. Sin contraseña en el .env, los correos salen en la consola.
# config/correo.py decide en cada envío; aquí solo se le pasa el respaldo (2 o 3).
# ---------------------------------------------------------------------------

EMAIL_REMITENTE = variable("EMAIL_HOST_USER", "vitrinadeproyectosuteq@gmail.com")
_CLAVE_CORREO = variable("EMAIL_HOST_PASSWORD", "")

if _CLAVE_CORREO:
    _RESPALDO_CORREO = {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": "smtp.gmail.com",
            "port": 587,
            "username": EMAIL_REMITENTE,
            "password": _CLAVE_CORREO,
            "use_tls": True,
            "timeout": 20,
        },
    }
else:
    _RESPALDO_CORREO = {"BACKEND": "django.core.mail.backends.console.EmailBackend"}

MAILERS = {
    "default": {
        "BACKEND": "config.correo.CorreoConfigurableBackend",
        "OPTIONS": {"respaldo": _RESPALDO_CORREO, "timeout": 20},
    },
}

DEFAULT_FROM_EMAIL = f"Vitrina de Proyectos UTEQ <{EMAIL_REMITENTE}>"
SERVER_EMAIL = EMAIL_REMITENTE

# Clave Fernet con la que se cifra la contraseña del correo guardada desde la app (cuentas/cifrado.py).
# Si falta, la app no deja guardar una contraseña nueva, pero el correo del .env sigue funcionando.
CLAVE_CIFRADO = variable("CLAVE_CIFRADO", "")


# ---------------------------------------------------------------------------
# Logs (spec 010)
#
# Con DEBUG=False, la configuración por defecto de Django no escribe sus mensajes en la consola, y
# Docker o systemd solo guardan lo que el proceso escribe en stdout/stderr. Por eso se define aquí
# un handler "consola" sin el filtro require_debug_true: los avisos de la app (por ejemplo el código
# de la configuración inicial) se ven en `docker compose logs`, `journalctl` o la consola de runserver.
# Nunca se registran contraseñas ni códigos introducidos por el usuario.
# ---------------------------------------------------------------------------

NIVEL_LOG_DJANGO = (variable("NIVEL_LOG_DJANGO", "INFO") or "INFO").upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,  # no apaga los loggers que ya existen (Django, librerías)
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "formatters": {
        "simple": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        # StreamHandler escribe en stderr, que Docker y systemd guardan igual que stdout
        "consola": {"class": "logging.StreamHandler", "formatter": "simple"},
        # El mismo envío de errores por correo que trae Django (solo si ADMINS tiene direcciones)
        "correo_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "cuentas": {"handlers": ["consola"], "level": "INFO", "propagate": False},
        "django": {"handlers": ["consola", "correo_admins"], "level": NIVEL_LOG_DJANGO, "propagate": False},
    },
}


# ---------------------------------------------------------------------------
# Endurecimiento para producción (solo cuando DEBUG es False)
# ---------------------------------------------------------------------------

SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"

if not DEBUG:
    # False solo para probar por http://localhost; True en el servidor real (con HTTPS)
    SESSION_COOKIE_SECURE = booleano("COOKIES_SEGURAS", defecto=True)
    CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
    # Detrás de nginx o Cloudflare: le dice a Django que la petición llegó por HTTPS
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    CSRF_TRUSTED_ORIGINS = lista("CSRF_TRUSTED_ORIGINS", "")
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
