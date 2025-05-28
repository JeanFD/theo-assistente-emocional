from django.db import models
from django.contrib.auth.models import User


class RegistroSentimento(models.Model):
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

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registros_sentimento', blank=True, null=True)
    sentimento = models.CharField(max_length=20, choices=SENTIMENTO_CHOICES)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    escala = models.IntegerField()
    data_criacao = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.escala < 1:
            self.escala = 1
        elif self.escala > 5:
            self.escala = 5
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.usuario.username if self.usuario else 'Anônimo'} - {self.sentimento} - {self.tipo} - {self.escala}"


class RegistroBPM(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registros_bpm', blank=True, null=True)
    bpm = models.IntegerField()
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username if self.usuario else 'Anônimo'} - {self.bpm} bpm"
