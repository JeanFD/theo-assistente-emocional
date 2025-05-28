from rest_framework import generics
from .models import RegistroSentimento, RegistroBPM
from .serializers import RegistroSentimentoSerializer, RegistroBPMSerializer
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

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
    user = request.user
    if user.is_authenticated and user.username != 'Teste':
        registros_sentimento = RegistroSentimento.objects.filter(usuario=user)
        registros_bpm = RegistroBPM.objects.filter(usuario=user)
        nome = user.username
        sexo = getattr(user, 'sexo', '-')
        idade = getattr(user, 'idade', '-')
    else:
        registros_sentimento = RegistroSentimento.objects.filter(usuario__isnull=True)
        registros_bpm = RegistroBPM.objects.filter(usuario__isnull=True)
        nome = 'Teste'
        sexo = '-'
        idade = '-'
    return render(request, 'registros.html', {
        'registros_sentimento': registros_sentimento,
        'registros_bpm': registros_bpm,
        'nome': nome,
        'sexo': sexo,
        'idade': idade,
        'user': user
    })

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('listar_registros')
    return redirect('listar_registros')
