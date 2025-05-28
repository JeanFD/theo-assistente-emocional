from rest_framework import generics
from .models import RegistroSentimento, RegistroBPM
from .serializers import RegistroSentimentoSerializer, RegistroBPMSerializer
from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

class RegistroSentimentoCreateListAPIView(generics.ListCreateAPIView):
    queryset = RegistroSentimento.objects.all()
    serializer_class = RegistroSentimentoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return RegistroSentimento.objects.filter(usuario=user)
        anon = User.objects.filter(username='Anônimo').first()
        if anon:
            return RegistroSentimento.objects.filter(usuario=anon)
        return RegistroSentimento.objects.none()

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else User.objects.get(username='Anônimo')
        serializer.save(usuario=user)

class RegistroBPMCreateListAPIView(generics.ListCreateAPIView):
    queryset = RegistroBPM.objects.all()
    serializer_class = RegistroBPMSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return RegistroBPM.objects.filter(usuario=user)
        anon = User.objects.filter(username='Anônimo').first()
        if anon:
            return RegistroBPM.objects.filter(usuario=anon)
        return RegistroBPM.objects.none()

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else User.objects.get(username='Anônimo')
        serializer.save(usuario=user)

def listar_registros(request):
    registros_sentimento = RegistroSentimento.objects.select_related('usuario').all()
    registros_bpm = RegistroBPM.objects.select_related('usuario').all()
    return render(request, 'registros.html', {'registros_sentimento': registros_sentimento, 'registros_bpm': registros_bpm})
