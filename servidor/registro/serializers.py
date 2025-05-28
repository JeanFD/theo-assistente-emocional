from rest_framework import serializers
from .models import Registro, Usuario

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'

class RegistroSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all(), source='usuario', write_only=True)

    class Meta:
        model = Registro
        fields = ['id', 'usuario', 'usuario_id', 'sentimento', 'tipo', 'escala', 'bpm', 'data_criacao']
