from rest_framework import serializers
from django.contrib.auth.models import User
from .models import RegistroSentimento, RegistroBPM

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class RegistroSentimentoSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='usuario', write_only=True)

    class Meta:
        model = RegistroSentimento
        fields = ['id', 'usuario', 'usuario_id', 'sentimento', 'tipo', 'escala', 'data_criacao']

class RegistroBPMSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='usuario', write_only=True)

    class Meta:
        model = RegistroBPM
        fields = ['id', 'usuario', 'usuario_id', 'bpm', 'data_criacao']
