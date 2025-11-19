from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response as DRFResponse
from rest_framework import status
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt 
from django.utils.decorators import method_decorator
import qrcode
import io
import json
import base64

# 🚨 NUEVAS IMPORTACIONES PARA RECONOCIMIENTO FACIAL
import face_recognition
import numpy as np

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
        'registro_url': reverse('registrar_asistencia_final', args=[empleado.id])
    }
    # La ruta de la plantilla debe ser correcta según tu estructura de carpetas
    return render(request, 'admin/empleados/validacion_facial.html', context)


# VISTA 3: Registra la asistencia SOLO después de la validación facial exitosa.
@csrf_exempt 
def registrar_asistencia_final(request, empleado_id):
    """
    Registra la asistencia (Entrada/Salida) DESPUÉS de una validación facial exitosa,
    verificando la imagen capturada contra la imagen guardada usando face_recognition.
    """
    if request.method != 'POST':
        return HttpResponse("Método no permitido.", status=405)
        
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    # Validar que el empleado tenga foto de perfil base
    if not empleado.foto_perfil:
        return JsonResponse({'success': False, 'message': 'El empleado no tiene una foto de perfil registrada para comparar.'}, status=400)

    try:
        # 1. Intentamos cargar los datos JSON
        data = json.loads(request.body)
        foto_base64 = data.get('foto_capturada', None)
        
        # 2. Decodificar la imagen Base64
        if not foto_base64:
            return JsonResponse({'success': False, 'message': 'No se recibió la imagen capturada para la validación.'}, status=400)
            
        # Limpiamos y decodificamos el Base64
        try:
            if ';base64,' in foto_base64:
                _, imgstr = foto_base64.split(';base64,') 
            else:
                imgstr = foto_base64
            
            foto_bytes = base64.b64decode(imgstr) # Imagen capturada en bytes
        except Exception:
             return JsonResponse({'success': False, 'message': 'Formato de imagen Base64 inválido o corrupto.'}, status=400)


        # =================================================================
        # 3. 🚨 LÓGICA DE VALIDACIÓN FACIAL REAL 🚨
        # =================================================================
        
        # A) Procesar la IMAGEN DEL PERFIL (Referencia guardada en BD)
        try:
            # Cargamos la imagen desde la ruta del archivo guardado
            imagen_referencia = face_recognition.load_image_file(empleado.foto_perfil.path)
            encodings_referencia = face_recognition.face_encodings(imagen_referencia)
        except Exception as e:
            print(f"Error leyendo foto perfil: {e}")
            return JsonResponse({'success': False, 'message': 'Error al leer la foto de perfil del sistema. Verifique el archivo.'}, status=500)

        if len(encodings_referencia) == 0:
            return JsonResponse({'success': False, 'message': 'No se detectó ningún rostro en la foto de perfil guardada (Admin).'}, status=400)
        
        encoding_bd = encodings_referencia[0] # Tomamos el primer rostro encontrado

        # B) Procesar la IMAGEN CAPTURADA (Webcam / Live)
        try:
            # Convertimos los bytes a un objeto tipo archivo
            imagen_live = face_recognition.load_image_file(io.BytesIO(foto_bytes))
            encodings_live = face_recognition.face_encodings(imagen_live)
        except Exception as e:
            print(f"Error procesando foto webcam: {e}")
            return JsonResponse({'success': False, 'message': 'Error procesando la imagen de la cámara.'}, status=400)

        if len(encodings_live) == 0:
            return JsonResponse({'success': False, 'message': 'No se detectó ningún rostro en la cámara. Mejore la iluminación.'}, status=400)
        
        encoding_camara = encodings_live[0]

        # C) COMPARAR LOS ROSTROS
        # tolerance=0.5 es un buen equilibrio (0.6 es default, más tolerante)
        # Si devuelve True, es la misma persona.
        resultados = face_recognition.compare_faces([encoding_bd], encoding_camara, tolerance=0.5)
        
        validacion_exitosa = resultados[0]

        if not validacion_exitosa:
            # Si el algoritmo dice que no son la misma persona
            distancia = face_recognition.face_distance([encoding_bd], encoding_camara)[0]
            print(f"Validación fallida. Distancia: {distancia} (Umbral 0.5)")
            return JsonResponse({'success': False, 'message': 'Rostro no reconocido. La validación biométrica ha fallado.'}, status=403)
            
        # =================================================================
        # 4. Lógica de Asistencia (Entrada/Salida) - SOLO si pasó validación
        # =================================================================
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
        
        # 5. Devolvemos respuesta de éxito
        return JsonResponse({
            'success': True,
            'message': f"Identidad Verificada. Asistencia de {empleado.nombre} registrada como {tipo.upper()}.",
            'nombre': empleado.nombre,
            'tipo': tipo
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Datos JSON inválidos.'}, status=400)
    except Exception as e:
        print(f"Error interno al registrar asistencia: {e}")
        return JsonResponse({'success': False, 'message': f'Error interno del servidor: {str(e)}'}, status=500)


# --- Vistas de Utilidad ---
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