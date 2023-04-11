from django.urls import path
from . import views


app_name = 'eventos'

urlpatterns = [
    path('novo_evento/', views.novo_evento, name='novo_evento'),
]