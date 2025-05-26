from rest_framework import generics
from .models import Registro
from .serializers import RegistroSerializer

class RegistroCreateAPIView(generics.CreateAPIView):
    queryset = Registro.objects.all()
    serializer_class = RegistroSerializer
