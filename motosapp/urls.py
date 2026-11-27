from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('', views.login_pagina, name='login_pagina'),
    path('logout/', views.logout_pagina, name='logout_pagina'),
    path('motos/', views.lista_motos, name='lista_motos'),
    path('moto/<int:pk>/', views.detalle_moto, name='detalle_moto'),
    path('moto/nueva/', views.crear_moto, name='crear_moto'),
    path('moto/<int:pk>/editar/', views.editar_moto, name='editar_moto'),
    path('moto/<int:pk>/eliminar/', views.eliminar_moto, name='eliminar_moto'),

    # login y tokens JWT
    path('api/login/', views.LoginAPIView.as_view(), name='login_api'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/logout/', views.LogoutAPIView.as_view(), name='logout_api'),

    # API de motos
    path('api/motos/', views.MotosAPIView.as_view(), name='api_motos'),
    path('api/motos/<int:id>/', views.MotoDetalleAPIView.as_view(), name ='api_moto_detalle'),

    # documentación Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger'),
]
