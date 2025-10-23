# empleados/admin.py

from django.contrib import admin
from django.utils.html import mark_safe
from django.urls import reverse
from .models import Empleado, Asistencia 

class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'dni', 'area')
    list_display_links = ('nombre',)
    
    # PLANTILLA PERSONALIZADA: Se usa para AÑADIR y MODIFICAR
    add_form_template = 'admin/empleados/empleado/change_form_photo_capture.html'
    change_form_template = 'admin/empleados/empleado/change_form_photo_capture.html'
    
    readonly_fields = ('qr_code_display',) 

    fieldsets = (
        (None, {
            'fields': ('nombre', 'dni', 'area', 'foto_perfil') # Asegúrate que foto_perfil esté aquí si usas el campo del form.
        }),
        ('Información de Sistema', {
            'fields': ('qr_code_display',) 
        }),
    )

    # 🚨 CRÍTICO: Añade change_view para forzar que el objeto 'opts' esté disponible en el contexto.
    def change_view(self, request, object_id, form_url='', extra_context=None):
        if extra_context is None:
            extra_context = {}
        # Inyecta el objeto de opciones del modelo en el contexto
        extra_context['opts'] = self.model._meta
        extra_context['has_delete_permission'] = self.has_delete_permission(request, self.get_object(request, object_id))
        
        return super().change_view(request, object_id, form_url, extra_context=extra_context)


    def qr_code_display(self, obj):
        # ... (código existente de qr_code_display)
        if obj.id:
            qr_url = reverse('qr_empleado', args=[obj.id]) 
            return mark_safe(f'<a href="{qr_url}" target="_blank"><img src="{qr_url}" width="150" height="150" /></a>')
        return "El QR se generará después de guardar el empleado por primera vez."

    qr_code_display.short_description = "Código QR"

admin.site.register(Empleado, EmpleadoAdmin)
admin.site.register(Asistencia)