"""
URL configuration for asistencia_qr project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework import routers


# 👇 1. Importa las vistas de tu app 'empleados' 👇
from empleados import views 
from empleados.views import EmpleadoViewSet, AsistenciaViewSet

router = routers.DefaultRouter()
router.register(r'empleados', EmpleadoViewSet)
router.register(r'asistencias', AsistenciaViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
     # 👇 2. AÑADE ESTA LÍNEA PARA LA NUEVA URL DEL QR 👇
    path('qr/empleado/<int:empleado_id>/', views.generar_qr_empleado, name='qr_empleado'),
    # 👇 AÑADE LA URL PARA LA PÁGINA DEL ESCÁNER 👇
    path('scanner/', views.scanner_view, name='scanner_page'),
]
