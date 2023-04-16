from django.urls import path
from . import views


app_name = 'cliente'

urlpatterns = [
    path('meus_certificados/', views.meus_certificados, name='meus_certificados'),
]