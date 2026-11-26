# Quickstart: validar la configuración inicial (spec 010)

## Requisitos

- Entorno local con PostgreSQL y el proyecto instalado (README → Instalación local).
- Una base de datos vacía para probar, por ejemplo `DB_NAME=vitrina_prueba_010` en la terminal
  (no en `.env`), creada vacía y migrada con `python manage.py migrate`.

## Pruebas automáticas

```bash
python manage.py test cuentas
python manage.py test           # suite completa (482 + nuevas)
python manage.py makemigrations --check --dry-run
```

## Casos a mano

1. **DEBUG=True + runserver, base vacía**: abrir `/cuentas/entrar/` → aparece "¿Instalación nueva?…";
   abrirlo → la consola de runserver muestra el bloque; pegar el código, crear cuenta nueva → panel
   del admin con "Listo…" y siguientes pasos; volver a Entrar (cerrando sesión) → sin enlace;
   `/configuracion-inicial/` → 404.
2. **DEBUG=False** (`ALLOWED_HOSTS=127.0.0.1,localhost`), base vacía: abrir la configuración → el
   bloque **sí** aparece en la consola.
3. **Comando**: `python manage.py codigo_configuracion_inicial` dos veces → el primer código ya no sirve.
4. **Base con usuarios sin admin**: promover un estudiante → tiene Estudiante y Admin.
5. **Con admin**: URL 404, sin enlace, el comando termina con error "Ya existe un administrador activo".

Contratos: [comando](contracts/comando.md), [página](contracts/pagina.md), [logging](contracts/logging.md).
Modelo: [data-model.md](data-model.md).
