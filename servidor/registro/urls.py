from django.urls import path
from .views import RegistroCreateAPIView, UsuarioUpdateAPIView
from . import views

urlpatterns = [
    path('registro/', RegistroCreateAPIView.as_view(), name='registro-create'),
    path('usuario/', UsuarioUpdateAPIView.as_view(), name='usuario-update'),
    path('', views.listar_registros, name='listar_registros'),
]
