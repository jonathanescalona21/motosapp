from datetime import date
from rest_framework import serializers
from .models import Moto


class MotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Moto
        fields = ['id', 'nombre', 'marca', 'anio', 'cilindrada', 'precio', 'imagen']

    # mismas validaciones que el MotoForm
    def validate_anio(self, anio):
        if anio < 1900 or anio > date.today().year + 1:
            raise serializers.ValidationError('Ingresa un año válido (entre 1900 y el próximo año).')
        return anio

    def validate_cilindrada(self, cilindrada):
        if cilindrada <= 0:
            raise serializers.ValidationError('La cilindrada debe ser mayor que cero.')
        return cilindrada

    def validate_precio(self, precio):
        if precio <= 0:
            raise serializers.ValidationError('El precio debe ser mayor que cero.')
        return precio


# datos que pide el login
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


# datos que pide el logout
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
