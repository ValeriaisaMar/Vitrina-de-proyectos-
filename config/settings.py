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
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Español por defecto: ignora el idioma del navegador; solo cuenta la elección ES/EN.
    "config.middleware.EspanolPorDefectoMiddleware",
    # Activa el idioma de cada petición según la cookie del selector. Va después de sesiones.
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
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
            ],
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
LOGIN_REDIRECT_URL = "vitrina:inicio"
LOGOUT_REDIRECT_URL = "vitrina:inicio"


# Caché: guarda los intentos fallidos de inicio de sesión (cuentas/limite.py).
# En memoria basta para un solo proceso; en producción con varios, usar una caché compartida.
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "vitrina"},
}


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

# Dirección base para los QR de verificación (opcional). Sirve cuando el servidor se ve desde
# otros equipos con una dirección distinta, por ejemplo en la demo: http://192.168.1.20:8000
SITIO_URL = variable("SITIO_URL", "").rstrip("/")

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# ---------------------------------------------------------------------------
# Correo: Gmail con contraseña de aplicación; sin contraseña, los correos salen en la consola
# ---------------------------------------------------------------------------

EMAIL_REMITENTE = variable("EMAIL_HOST_USER", "vitrinadeproyectosuteq@gmail.com")
_CLAVE_CORREO = variable("EMAIL_HOST_PASSWORD", "")

if _CLAVE_CORREO:
    MAILERS = {
        "default": {
            "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "OPTIONS": {
                "host": "smtp.gmail.com",
                "port": 587,
                "username": EMAIL_REMITENTE,
                "password": _CLAVE_CORREO,
                "use_tls": True,
                "timeout": 20,
            },
        },
    }
else:
    MAILERS = {
        "default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"},
    }

DEFAULT_FROM_EMAIL = f"Vitrina de Proyectos UTEQ <{EMAIL_REMITENTE}>"
SERVER_EMAIL = EMAIL_REMITENTE


# ---------------------------------------------------------------------------
# Endurecimiento para producción (solo cuando DEBUG es False)
# ---------------------------------------------------------------------------

SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
