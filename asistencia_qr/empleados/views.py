from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response as DRFResponse # Renombramos para evitar conflicto
from rest_framework import status
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse # <-- Usamos JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt 
from django.utils.decorators import method_decorator
import qrcode
import io
import json

from .models import Empleado, Asistencia
from .serializers import EmpleadoSerializer, AsistenciaSerializer


# --- ViewSet para la API de Empleados ---
class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer


# --- ViewSet para la API de Asistencias ---
class AsistenciaViewSet(viewsets.ModelViewSet):
    queryset = Asistencia.objects.all().order_by("-fecha_hora")
    serializer_class = AsistenciaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        empleado_id = self.request.query_params.get("empleado")
        if empleado_id:
            try:
                empleado_id = int(empleado_id)
                queryset = queryset.filter(empleado_id=empleado_id)
            except ValueError:
                pass
        return queryset


# =========================================================
# === VISTAS PARA EL FLUJO QR -> FACIAL -> REGISTRO ===
# =========================================================

# VISTA 1: Maneja el escaneo del QR y redirige a la validación facial.
def procesar_qr(request):
    """
    Busca al empleado por el dato del QR y redirige a la página de validación facial.
    """
    if request.method == 'POST':
        qr_data = None
        
        # 1. Intentamos obtener el dato de un formulario estándar primero
        qr_data = request.POST.get('qr_data')

        # 2. Si no es un formulario, intentamos obtener el dato desde JSON
        if not qr_data and request.body:
            try:
                data = json.loads(request.body)
                qr_data = data.get('qr_data')
            except json.JSONDecodeError:
                pass
            
        if not qr_data:
            return HttpResponse("Error: Datos QR no recibidos.", status=400)
        
        # 1. Buscar al empleado por ID (asumiendo que el QR tiene el ID)
        try:
            empleado_id = int(qr_data)
            empleado = Empleado.objects.get(id=empleado_id)
        except (ValueError, Empleado.DoesNotExist):
            return HttpResponse(f"Error: Empleado con ID/DNI '{qr_data}' no encontrado.", status=404)

        # 2. Redirigir a la vista que activa la validación facial
        return redirect(reverse('validacion_facial', args=[empleado.id]))
    
    # Si el método no es POST
    return render(request, 'empleados/scanner.html')


# VISTA 2: Muestra la interfaz para la validación facial.
def validacion_facial_view(request, empleado_id):
    """
    Muestra la interfaz (HTML/JS) para que el empleado active la cámara 
    y realice la validación facial.
    """
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    context = {
        'empleado': empleado,
        # La clave 'registro_url' se pasa al template
        'registro_url': reverse('registrar_asistencia_final', args=[empleado.id])
    }
    # *************************************************************************
    # * CORRECCIÓN FINAL: La ruta de la plantilla debe ser 'admin/empleados/validacion_facial.html'
    # * porque está en templates/admin/empleados/
    # *************************************************************************
    return render(request, 'admin/empleados/validacion_facial.html', context)


# VISTA 3: Registra la asistencia SOLO después de la validación facial exitosa.
@csrf_exempt 
def registrar_asistencia_final(request, empleado_id):
    """
    Registra la asistencia (Entrada/Salida) DESPUÉS de una validación facial exitosa.
    """
    if request.method != 'POST':
        return HttpResponse("Método no permitido.", status=405)
        
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    # --- Lógica de Entrada/Salida Robusta ---
    now = timezone.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    ultimo_registro = Asistencia.objects.filter(
        empleado=empleado, 
        fecha_hora__gte=start_of_day, 
    ).order_by('-fecha_hora').first()

    if ultimo_registro and ultimo_registro.tipo == 'entrada':
        tipo = 'salida'
    else:
        tipo = 'entrada'
            
    # Creamos el nuevo registro de asistencia
    Asistencia.objects.create(
        empleado=empleado,
        tipo=tipo,
        fecha_hora=now
    )
    
    # Devolvemos una respuesta JSON limpia y con el mensaje de texto correcto.
    return JsonResponse({
        'success': True,
        'message': f"Asistencia de {empleado.nombre} registrada como {tipo.upper()}.",
        'nombre': empleado.nombre,
        'tipo': tipo
    }, status=200) # Usamos status 200 (OK) para éxito


# --- Vistas de Utilidad (se mantienen) ---
def generar_qr_empleado(request, empleado_id):
    """
    Genera y devuelve la imagen de un código QR.
    """
    empleado = get_object_or_404(Empleado, pk=empleado_id)
    qr_content = str(empleado.id)
    
    img = qrcode.make(qr_content)
    
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)

    return HttpResponse(buf, content_type='image/png')


def scanner_view(request):
    """
    Esta vista muestra la página del escáner (scanner.html).
    """
    return render(request, 'empleados/scanner.html')
