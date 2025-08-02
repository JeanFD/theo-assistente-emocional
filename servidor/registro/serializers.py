from rest_framework import serializers
from django.contrib.auth.models import User
from .models import RegistroSentimento, RegistroBPM

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class RegistroSentimentoSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)

    class Meta:
        model = RegistroSentimento
        fields = '__all__'

class RegistroBPMSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)

    class Meta:
        model = RegistroBPM
        fields = '__all__'
