from rest_framework.views import exception_handler
from rest_framework.exceptions import NotAuthenticated, AuthenticationFailed


# cambiamos los mensajes 401 de la API a español
def manejar_errores(exc, context):
    respuesta = exception_handler(exc, context)

    if isinstance(exc, NotAuthenticated):
        respuesta.data = {'error': 'Falta el Access Token. Envíalo como: Authorization: Bearer <token>'}
    elif isinstance(exc, AuthenticationFailed):
        respuesta.data = {'error': 'El token es inválido o ya venció. Vuelve a iniciar sesión.'}

    return respuesta
