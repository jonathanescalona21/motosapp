from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from .models import Moto, Sesion
from .forms import MotoForm, MotoEditarForm
from .serializers import MotoSerializer, LoginSerializer, LogoutSerializer
from .decorators import login_requerido_sesion

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from drf_spectacular.utils import extend_schema, OpenApiResponse


# ---------- PÁGINAS HTML ----------

# READ (Lista principal)
@login_requerido_sesion
def lista_motos(request):
    buscar = request.GET.get('buscar', '')
    motos = Moto.objects.all()
    # filtramos por nombre o marca si escribió algo
    if buscar:
        motos = motos.filter(Q(nombre__icontains=buscar) | Q(marca__icontains=buscar))
    return render(request, 'motosapp/lista_motos.html', {'motos': motos, 'buscar': buscar})

# READ (Detalle)
@login_requerido_sesion
def detalle_moto(request, pk):
    moto = get_object_or_404(Moto, pk=pk)
    return render(request, 'motosapp/detalle_moto.html', {'moto': moto})

# CREATE (Crear)
@login_requerido_sesion
def crear_moto(request):
    if request.method == 'POST':
        # request.FILES trae la imagen
        form = MotoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Moto creada correctamente.')
            return redirect('lista_motos')
    else:
        form = MotoForm()
    return render(request, 'motosapp/crear_moto.html', {'form': form})

# UPDATE
@login_requerido_sesion
def editar_moto(request, pk):
    moto = get_object_or_404(Moto, pk=pk)
    if request.method == 'POST':
        form = MotoEditarForm(request.POST, request.FILES, instance=moto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Moto actualizada correctamente.')
            return redirect('lista_motos')
    else:
        form = MotoEditarForm(instance=moto)
    return render(request, 'motosapp/editar_moto.html', {'form': form, 'moto': moto})

# DELETE
@login_requerido_sesion
def eliminar_moto(request, pk):
    moto = get_object_or_404(Moto, pk=pk)
    if request.method == 'POST':
        moto.delete()
        messages.success(request, 'Moto eliminada correctamente.')
        return redirect('lista_motos')
    return render(request, 'motosapp/eliminar_moto.html', {'moto': moto})

def login_pagina(request):
    # si ya tiene la sesión iniciada lo mandamos al catálogo
    if request.user.is_authenticated and request.session.get('sesion_id'):
        return redirect('lista_motos')
    return render(request, 'motosapp/login.html')

def logout_pagina(request):
    if request.method == 'POST':
        sesion_id = request.session.get('sesion_id')
        sesion = Sesion.objects.filter(id=sesion_id).first()
        if sesion is not None:
            cerrar_sesion(sesion)
        # borramos la sesión de Django
        logout(request)
        messages.success(request, 'Cerraste sesión correctamente.')
    return redirect('login_pagina')


# ---------- FUNCIONES DE AYUDA ----------

# crea los tokens y el registro en la tabla Sesion
def crear_sesion(request, usuario):
    refresh = RefreshToken.for_user(usuario)
    sesion = Sesion.objects.create(
        usuario = usuario,
        jti = refresh['jti'],
        ip = request.META.get('REMOTE_ADDR'),
        navegador = request.META.get('HTTP_USER_AGENT', '')[:255],
        fecha_expiracion = timezone.now() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
    )
    return refresh, sesion

# deja la sesión inactiva y manda su refresh token a la blacklist
def cerrar_sesion(sesion):
    sesion.activa = False
    sesion.save()
    token = OutstandingToken.objects.filter(jti=sesion.jti).first()
    if token is not None:
        BlacklistedToken.objects.get_or_create(token=token)


# ---------- API ----------

class LoginAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Login'],
        summary='Iniciar sesión',
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description='Entrega el access y el refresh token'),
            401: OpenApiResponse(description='Usuario o contraseña incorrectos'),
        },
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        usuario = authenticate(
            username = username,
            password = password
        )

        if usuario is not None:
            # sesión de Django para las páginas HTML
            login(request, usuario)
            refresh, sesion = crear_sesion(request, usuario)
            request.session['sesion_id'] = sesion.id

            return Response({
                'mensaje': 'Autenticación correcta',
                'usuario': usuario.username,
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status = status.HTTP_200_OK)
        return Response({
            'error': 'Usuario o contraseña incorrectos'
        }, status=status.HTTP_401_UNAUTHORIZED)

class LogoutAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Login'],
        summary='Cerrar sesión',
        request=LogoutSerializer,
        responses={
            200: OpenApiResponse(description='Sesión cerrada'),
            400: OpenApiResponse(description='Refresh token inválido'),
            401: OpenApiResponse(description='Falta el access token o venció'),
        },
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'Debes enviar el refresh token'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(serializer.validated_data['refresh'])
        except TokenError:
            return Response({'error': 'El refresh token es inválido o ya fue usado'}, status=status.HTTP_400_BAD_REQUEST)

        # buscamos la sesión de ese token y la cerramos
        sesion = Sesion.objects.filter(jti=refresh['jti'], usuario=request.user).first()
        if sesion is None:
            return Response({'error': 'Ese refresh token no es tuyo'}, status=status.HTTP_400_BAD_REQUEST)
        cerrar_sesion(sesion)

        return Response({'mensaje': 'Sesión cerrada correctamente'}, status=status.HTTP_200_OK)

class MotosAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Motos'],
        summary='Listar motos',
        responses={200: MotoSerializer(many=True), 401: OpenApiResponse(description='Token faltante, inválido o vencido')},
    )
    def get(self, request):
        motos = Moto.objects.all()
        serializer = MotoSerializer(motos, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Motos'],
        summary='Crear moto',
        request=MotoSerializer,
        responses={201: MotoSerializer, 400: OpenApiResponse(description='Datos inválidos')},
    )
    def post(self, request):
        serializer = MotoSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                "mensaje" : "Moto creada correctamente",
                "moto" : serializer.data
            }, status = status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MotoDetalleAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Motos'],
        summary='Ver una moto',
        responses={200: MotoSerializer, 404: OpenApiResponse(description='La moto no existe')},
    )
    def get(self, request, id):
        moto = Moto.objects.filter(id=id).first()
        if moto is None:
            return Response({"error": f"No existe una moto con id {id}"}, status=status.HTTP_404_NOT_FOUND)

        serializer = MotoSerializer(moto, context={'request': request})
        return Response(serializer.data, status = status.HTTP_200_OK)

    @extend_schema(
        tags=['Motos'],
        summary='Eliminar moto',
        responses={204: None, 404: OpenApiResponse(description='La moto no existe')},
    )
    def delete(self, request, id):
        moto = Moto.objects.filter(id=id).first()
        if moto is None:
            return Response({"error": f"No existe una moto con id {id}"}, status=status.HTTP_404_NOT_FOUND)

        moto.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=['Motos'],
        summary='Editar moto',
        request=MotoSerializer,
        responses={
            200: MotoSerializer,
            400: OpenApiResponse(description='Datos inválidos'),
            404: OpenApiResponse(description='La moto no existe'),
        },
    )
    def put(self, request, id):
        moto = Moto.objects.filter(id=id).first()
        if moto is None:
            return Response({"error": f"No existe una moto con id {id}"}, status=status.HTTP_404_NOT_FOUND)

        # le pasamos la moto que ya existe para que la actualice
        serializer = MotoSerializer(moto, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                "mensaje": "Moto actualizada correctamente",
                "moto": serializer.data
            }, status = status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
