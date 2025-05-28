from rest_framework import generics
from .models import Registro, Usuario
from .serializers import RegistroSerializer, UsuarioSerializer
from django.shortcuts import render

class RegistroCreateAPIView(generics.CreateAPIView):
    queryset = Registro.objects.all()
    serializer_class = RegistroSerializer

class UsuarioUpdateAPIView(generics.UpdateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def get_object(self):
        return Usuario.objects.latest('id')

def listar_registros(request):
    registros = Registro.objects.select_related('usuario').all()
    return render(request, 'registros.html', {'registros': registros})
