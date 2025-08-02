from django.contrib import admin
from .models import RegistroSentimento, RegistroBPM

@admin.register(RegistroSentimento)
class RegistroSentimentoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'sentimento', 'tipo', 'escala', 'data_criacao')
    list_filter = ('sentimento', 'tipo', 'usuario', 'data_criacao')
    search_fields = ('sentimento', 'tipo', 'usuario__username')

@admin.register(RegistroBPM)
class RegistroBPMAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'bpm', 'data_criacao')
    list_filter = ('usuario', 'data_criacao')
    search_fields = ('usuario__username',)

# Se houver outros modelos, registre-os aqui também.
