from django.urls import path
from .views import RegistroSentimentoCreateListAPIView, RegistroBPMCreateListAPIView, logout_view
from . import views

urlpatterns = [
    path('registro-sentimento/', RegistroSentimentoCreateListAPIView.as_view(), name='registro-sentimento'),
    path('registro-bpm/', RegistroBPMCreateListAPIView.as_view(), name='registro-bpm'),
    path('logout/', logout_view, name='logout'),
    path('', views.listar_registros, name='listar_registros'),
]
