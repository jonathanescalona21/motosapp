from django.contrib import admin
from .models import Moto, Sesion

admin.site.register(Moto)


# tabla de sesiones con las columnas más importantes
class SesionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'ip', 'navegador', 'fecha_inicio', 'fecha_expiracion', 'activa']
    list_filter = ['activa']

admin.site.register(Sesion, SesionAdmin)
