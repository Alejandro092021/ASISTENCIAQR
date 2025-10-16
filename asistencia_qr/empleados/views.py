from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone  # Importante para la zona horaria
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
import qrcode
import io

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

    @action(detail=False, methods=['post'])
    def registrar(self, request):
        empleado_id = request.data.get("empleado_id")
        
        try:
            empleado = Empleado.objects.get(id=empleado_id)
        except Empleado.DoesNotExist:
            return Response({"error": "Empleado no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        # --- INICIO DE LA LÓGICA FINAL Y ROBUSTA ---
        
        # Obtenemos el momento actual en la zona horaria correcta
        now = timezone.now()
        
        # Definimos el rango exacto del día de hoy para evitar errores de zona horaria
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Buscamos el último registro DENTRO DEL RANGO de hoy
        ultimo_registro = Asistencia.objects.filter(
            empleado=empleado, 
            fecha_hora__gte=start_of_day,  # gte = mayor o igual que
            fecha_hora__lte=end_of_day    # lte = menor o igual que
        ).order_by('-fecha_hora').first()

        # Determinamos si el nuevo registro es una entrada o una salida
        if ultimo_registro and ultimo_registro.tipo == 'entrada':
            tipo = 'salida'
        else:
            tipo = 'entrada'
            
        # --- FIN DE LA LÓGICA FINAL ---

        # Creamos el nuevo registro de asistencia
        asistencia = Asistencia.objects.create(
            empleado=empleado,
            tipo=tipo,
            fecha_hora=now  # Reutilizamos la variable 'now' para consistencia
        )
        
        # Creamos la respuesta JSON personalizada
        response_data = {
            'message': f'Asistencia de "{tipo.upper()}" registrada con éxito',
            'empleado_id': asistencia.empleado.id,
            'nombre_empleado': asistencia.empleado.nombre,
            'fecha_hora': asistencia.fecha_hora.strftime('%Y-%m-%d %H:%M:%S'),
            'tipo': asistencia.tipo
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


# --- Vistas para las páginas HTML y generación de QR ---
def generar_qr_empleado(request, empleado_id):
    """
    Esta vista genera y devuelve la imagen de un código QR 
    para un ID de empleado específico.
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