from django.urls import path
from .views import RegistroCreateAPIView

urlpatterns = [
    path('registro/', RegistroCreateAPIView.as_view(), name='registro-create'),
]
