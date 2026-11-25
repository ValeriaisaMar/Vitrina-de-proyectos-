# Spec 008, historia 3: cuenta de correo de envío configurable desde la app (una sola fila).

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cuentas', '0004_quitar_rol_unico'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracionCorreo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('servidor', models.CharField(max_length=120, verbose_name='servidor SMTP')),
                ('puerto', models.PositiveIntegerField(default=587, verbose_name='puerto')),
                ('seguridad', models.CharField(choices=[('starttls', 'STARTTLS'), ('ssl', 'SSL/TLS'), ('ninguna', 'Ninguna')], default='starttls', max_length=10, verbose_name='seguridad')),
                ('usuario', models.CharField(max_length=254, verbose_name='usuario o correo de acceso')),
                ('clave_cifrada', models.TextField(blank=True, editable=False, verbose_name='contraseña cifrada')),
                ('nombre_remitente', models.CharField(default='Vitrina de Proyectos UTEQ', max_length=80, verbose_name='nombre del remitente')),
                ('correo_remitente', models.EmailField(blank=True, max_length=254, verbose_name='correo del remitente')),
                ('actualizado_en', models.DateTimeField(auto_now=True, verbose_name='actualizado en')),
                ('ultima_prueba_en', models.DateTimeField(blank=True, null=True, verbose_name='última prueba')),
                ('ultima_prueba_ok', models.BooleanField(blank=True, null=True, verbose_name='última prueba correcta')),
                ('ultima_prueba_mensaje', models.CharField(blank=True, max_length=300, verbose_name='resultado de la última prueba')),
                ('actualizado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='actualizado por')),
            ],
            options={
                'verbose_name': 'configuración de correo',
                'verbose_name_plural': 'configuración de correo',
            },
        ),
    ]
