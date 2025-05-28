from django.urls import path
from .views import RegistroSentimentoCreateListAPIView, RegistroBPMCreateListAPIView
from . import views

urlpatterns = [
    path('registro-sentimento/', RegistroSentimentoCreateListAPIView.as_view(), name='registro-sentimento'),
    path('registro-bpm/', RegistroBPMCreateListAPIView.as_view(), name='registro-bpm'),
    path('', views.listar_registros, name='listar_registros'),
]
