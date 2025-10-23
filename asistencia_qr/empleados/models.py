from django.db import models
from django.utils.timezone import localtime

# Create your models here.

class Empleado(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    area = models.CharField(max_length=150, blank=True)
    # 🚨 SOLUCIÓN 1: Agregamos el campo 'foto_perfil' al modelo
    foto_perfil = models.ImageField(upload_to='fotos_empleados/', blank=True, null=True, verbose_name='Foto de Perfil')

    def __str__(self):
        return self.nombre


class Asistencia(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField()
    tipo = models.CharField(max_length=10, choices=[('entrada', 'Entrada'), ('salida', 'Salida')])

    def __str__(self):
        # --- CORRECCIÓN APLICADA AQUÍ ---
        # Convierte la fecha_hora guardada en UTC a la zona horaria local para mostrarla.
        local_time = localtime(self.fecha_hora).strftime('%Y-%m-%d %H:%M:%S')
        return f"{self.empleado.nombre} - {self.tipo} - {local_time}"