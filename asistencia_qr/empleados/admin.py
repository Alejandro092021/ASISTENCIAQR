# empleados/admin.py
from django.contrib import admin
from django.utils.html import mark_safe
from django.urls import reverse
from .models import Empleado, Asistencia

class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'dni', 'area')
    list_display_links = ('nombre',)
    
    # Definimos los campos que se mostrarán en el formulario de edición
    readonly_fields = ('qr_code_display',)

    def qr_code_display(self, obj):
        """
        Genera el HTML para mostrar la imagen del QR en el admin.
        'obj' es la instancia del modelo Empleado.
        """
        if obj.id:
            # Creamos la URL a nuestra vista usando el 'name' que definimos en urls.py
            qr_url = reverse('qr_empleado', args=[obj.id])
            # Devolvemos una etiqueta de imagen HTML
            return mark_safe(f'<a href="{qr_url}" target="_blank"><img src="{qr_url}" width="150" height="150" /></a>')
        return "El QR se generará después de guardar el empleado por primera vez."

    # Renombramos la cabecera de la columna en el admin
    qr_code_display.short_description = "Código QR"

# Registramos el modelo con la clase personalizada
admin.site.register(Empleado, EmpleadoAdmin)
admin.site.register(Asistencia)