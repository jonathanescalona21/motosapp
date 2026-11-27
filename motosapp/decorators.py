from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.utils import timezone
from .models import Sesion


def login_requerido_sesion(vista):
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        # revisamos que el usuario haya iniciado sesión
        sesion_id = request.session.get('sesion_id')
        if sesion_id is None or not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para entrar.')
            return redirect('login_pagina')

        # buscamos la sesión en la tabla y vemos que siga activa
        sesion = Sesion.objects.filter(id=sesion_id, activa=True).first()
        if sesion is None or sesion.fecha_expiracion < timezone.now():
            # si ya venció la dejamos inactiva
            if sesion is not None:
                sesion.activa = False
                sesion.save()
            logout(request)
            messages.error(request, 'Tu sesión expiró o fue cerrada. Inicia sesión de nuevo.')
            return redirect('login_pagina')

        # todo bien, mostramos la página
        return vista(request, *args, **kwargs)
    return envoltura
