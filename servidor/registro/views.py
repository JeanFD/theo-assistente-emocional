from rest_framework import generics
from .models import RegistroSentimento, RegistroBPM
from .serializers import RegistroSentimentoSerializer, RegistroBPMSerializer
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class RegistroSentimentoCreateListAPIView(generics.ListCreateAPIView):
    queryset = RegistroSentimento.objects.all()
    serializer_class = RegistroSentimentoSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return RegistroSentimento.objects.all()

    def perform_create(self, serializer):
        # Cria um novo dict apenas com os campos relevantes para RegistroSentimento
        data = serializer.validated_data
        novo_json = {
            'sentimento': data.get('sentimento'),
            'tipo': data.get('tipo'),
            'escala': data.get('escala'),
        }
        serializer.save(**novo_json)

@method_decorator(csrf_exempt, name='dispatch')
class RegistroBPMCreateListAPIView(generics.ListCreateAPIView):
    queryset = RegistroBPM.objects.all()
    serializer_class = RegistroBPMSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return RegistroBPM.objects.all()

    def perform_create(self, serializer):
        # Cria um novo dict apenas com os campos relevantes para RegistroBPM
        data = serializer.validated_data
        novo_json = {
            'bpm': data.get('bpm'),
        }
        serializer.save(**novo_json)

def listar_registros(request):
    registros_sentimento = RegistroSentimento.objects.all()
    registros_bpm = RegistroBPM.objects.all()
    nome = '-'
    sexo = '-'
    idade = '-'
    return render(request, 'registros.html', {
        'registros_sentimento': registros_sentimento,
        'registros_bpm': registros_bpm,
        'nome': nome,
        'sexo': sexo,
        'idade': idade,
        'user': request.user
    })

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('listar_registros')
    return redirect('listar_registros')
