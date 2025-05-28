from django.db import models


class Usuario(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    sexo = models.CharField(max_length=20, blank=True, null=True)
    idade = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.nome


class Registro(models.Model):
    SENTIMENTO_CHOICES = [
        ('Feliz', 'Feliz'),
        ('Irritado', 'Irritado'),
        ('Triste', 'Triste'),
        ('Ansioso', 'Ansioso'),
    ]

    TIPO_CHOICES = [
        ('Positivo', 'Positivo'),
        ('Negativo', 'Negativo'),
        ('Não sei', 'Não sei'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='registros')
    sentimento = models.CharField(max_length=20, choices=SENTIMENTO_CHOICES, blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, blank=True, null=True)
    escala = models.IntegerField(blank=True, null=True)
    bpm = models.IntegerField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.nome} - {self.sentimento} - {self.tipo} - {self.escala}"
