from django.contrib import admin
from .models import Registro, Usuario

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sexo', 'idade')
    search_fields = ('nome',)

@admin.register(Registro)
class RegistroAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'sentimento', 'tipo', 'escala', 'bpm', 'data_criacao')
    list_filter = ('sentimento', 'tipo', 'usuario', 'data_criacao')
    search_fields = ('sentimento', 'tipo', 'usuario__nome')

# Se houver outros modelos, registre-os aqui também.
