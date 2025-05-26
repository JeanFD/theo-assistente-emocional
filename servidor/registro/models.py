from django.db import models


class Registro(models.Model):
    SENTIMENTO_CHOICES = [
        ('Feliz', 'Feliz'),
        ('Neutro', 'Neutro'),
        ('Triste', 'Triste'),
        ('Ansioso', 'Ansioso'),
    ]
    TIPO_CHOICES = [
        ('Positivo', 'Positivo'),
        ('Negativo', 'Negativo'),
        ('Não sei', 'Não sei'),
    ]

    sentimento = models.CharField(max_length=20, choices=SENTIMENTO_CHOICES)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, blank=True, null=True)
    escala = models.IntegerField()
    bpm = models.IntegerField(blank=True, null=True)
    sexo = models.CharField(max_length=20, blank=True, null=True)
    idade = models.IntegerField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sentimento} - {self.tipo} - {self.escala}"
