"""
URL configuration for asistencia_qr project.
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from empleados import views 
from empleados.views import EmpleadoViewSet, AsistenciaViewSet

router = routers.DefaultRouter()
router.register(r'empleados', EmpleadoViewSet)
router.register(r'asistencias', AsistenciaViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    
    # === VISTAS DEL FLUJO DE ASISTENCIA (QR -> FACIAL -> REGISTRO) ===
    
    # 1. Vista que recibe el dato del QR (POST) y redirige a la validación facial.
    path('procesar_qr/', views.procesar_qr, name='procesar_qr'), 
    
    # 2. Vista que muestra la interfaz de cámara para la validación facial (GET).
    path('validacion_facial/<int:empleado_id>/', views.validacion_facial_view, name='validacion_facial'),
    
    # 3. Vista que recibe la confirmación AJAX (POST) y registra la asistencia final.
    path('registrar_asistencia_final/<int:empleado_id>/', views.registrar_asistencia_final, name='registrar_asistencia_final'),
    
    # === VISTAS DE UTILIDAD ===
    
    # URL para generar la imagen del código QR (usada en el Admin)
    path('qr/empleado/<int:empleado_id>/', views.generar_qr_empleado, name='qr_empleado'),
    
    # URL para la página de inicio del escáner (si aplica)
    path('scanner/', views.scanner_view, name='scanner_page'),
]
