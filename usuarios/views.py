from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages, auth
from django.contrib.messages import constants
from django.urls import reverse


def cadastro(request):
    if request.method == "GET":
        return render(request, 'cadastro.html')
    elif request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        confirmar_senha = request.POST.get('confirmar_senha')

        if not senha == confirmar_senha:
            # para enviar uma mensagem de erro, deve-se colocar a requisição,
            # o tipo de erro e a mensagem que vai ser exibida
            messages.add_message(request, constants.ERROR, 'As senhas não coincidem.')
            return redirect(reverse('usuarios:cadastro'))
        
        # TODO: validar força da senha

        user = User.objects.filter(username=username)

        if user.exists():
            # para enviar uma mensagem de erro, deve-se colocar a requisição,
            # o tipo de erro e a mensagem que vai ser exibida
            messages.add_message(request, constants.ERROR, 'Usuário já existe.')
            return redirect(reverse('usuarios:cadastro'))

        user = User.objects.create_user(
            username=username,
            email=email,
            password=senha
        )
        messages.add_message(request, constants.SUCCESS, 'Usuário salvo com sucesso!')
        print(username, email, senha, confirmar_senha)
        return redirect(reverse('usuarios:login'))
    

def login(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    elif request.method == 'POST':
        username = request.POST.get('username')
        senha = request.POST.get('senha')

        # user - verifica se usuário existe. ele não loga no sistema
        user = auth.authenticate(username=username, password=senha)

        if not user:
            messages.add_message(request, constants.ERROR, 'Usuário ou Senha inválidos.')
            return redirect(reverse('usuarios:login'))
        
        auth.login(request, user)
        return redirect('/eventos/novo_evento/')