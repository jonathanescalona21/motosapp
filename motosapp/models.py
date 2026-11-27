from django.db import models
from django.contrib.auth.models import User

class Moto(models.Model):
    nombre = models.CharField(max_length=100)
    marca = models.CharField(max_length=100)
    anio = models.IntegerField()
    cilindrada = models.IntegerField()
    precio = models.IntegerField()
    imagen = models.ImageField(upload_to='motos/', blank=True)

    def __str__(self):
        return f'{self.marca} {self.nombre}'


# guarda cada inicio de sesión del usuario
class Sesion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    jti = models.CharField(max_length=255, unique=True)  # id del refresh token
    ip = models.GenericIPAddressField(null=True, blank=True)
    navegador = models.CharField(max_length=255, blank=True)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.usuario.username} - {self.fecha_inicio:%d/%m/%Y %H:%M}'
