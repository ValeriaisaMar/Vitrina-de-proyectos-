# Imagen de la Vitrina de Proyectos: Django + gunicorn, con los estáticos servidos por WhiteNoise.
FROM python:3.13-slim

# Sin archivos .pyc y con la salida de Python sin búfer (los logs salen al momento en `docker compose logs`)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primero solo las dependencias: si no cambian, Docker reutiliza esta capa y el build es más rápido
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# settings.py exige SECRET_KEY y DB_NAME; valores de relleno solo para juntar los estáticos
RUN SECRET_KEY=solo-para-construir DB_NAME=x DB_USER=x python manage.py collectstatic --noinput

# Usuario sin privilegios; media/ es suya para poder guardar las imágenes subidas
RUN useradd --create-home appuser && mkdir -p /app/media && chown -R appuser /app/media
USER appuser

EXPOSE 8000

# Al arrancar: aplica las migraciones y levanta gunicorn (3 procesos; el log de peticiones a la consola)
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --access-logfile -"]
