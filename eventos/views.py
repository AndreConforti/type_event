from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages import constants
from django.urls import reverse
from django.conf import settings

from .models import Evento
import csv, os
from secrets import token_urlsafe


# A view novo_evento, só pode ser acessada por usuário logado. 
# é criado um decorator para essa permissão
@login_required
def novo_evento(request):
    if request.method == 'GET':
        return render(request, 'novo_evento.html')
    elif request.method == 'POST':
        nome           = request.POST.get('nome')
        descricao      = request.POST.get('descricao')
        data_inicio    = request.POST.get('data_inicio')
        data_termino   = request.POST.get('data_termino')
        carga_horaria  = request.POST.get('carga_horaria')
        cor_principal  = request.POST.get('cor_principal')
        cor_secundaria = request.POST.get('cor_secundaria')
        cor_fundo      = request.POST.get('cor_fundo')  

        logo           = request.FILES.get('logo')
        
        evento = Evento(
            criador=request.user,
            nome=nome,
            descricao=descricao,
            data_inicio=data_inicio,
            data_termino=data_termino,
            carga_horaria=carga_horaria,
            cor_principal=cor_principal,
            cor_secundaria=cor_secundaria,
            cor_fundo=cor_fundo,
            logo=logo,
        )
    
        evento.save()
        
        messages.add_message(request, constants.SUCCESS, 'Evento cadastrado com sucesso')
        return redirect(reverse('eventos:novo_evento'))
    

@login_required
def gerenciar_evento(request):
    if request.method == "GET":
        # cria uma variável para pegar o título do evento na busca
        nome = request.GET.get('nome') 
        # cria uma variável para receber os dados dos eventos que foram cadastrados
        # pelo usuário que está logado
        eventos = Evento.objects.filter(criador=request.user)
        
        if nome:
            # filtra entre todos os eventos do usário logado, onde no nome,
            # CONTENHA os dados enviados na variável de busca
            eventos = eventos.filter(nome__contains=nome)

        return render(request, 'gerenciar_evento.html', {'eventos':eventos})
    

@login_required
def inscrever_evento(request, id):
    # buscando na tabela Evento pelo id passado como parâmetro
    # se não encontrar, devolva uma "página não encontrada" 
    evento = get_object_or_404(Evento,id=id)
    if request.method == "GET":
        return render(request, 'inscrever_evento.html', {'evento':evento})
    elif request.method == "POST":
        # O campo ManyToManyField permite adicionar (fazer uma relação entre outros campos)
        # nesse caso co-realaciona o id do usuário logado ao id do evento selecionado

        # TODO: validar se o usuário já é um participante
        
        evento.participantes.add(request.user)
        evento.save()
        messages.add_message(request, constants.SUCCESS, 'Inscriçao realizada com sucesso!')
        # return redirect(f"/eventos/inscrever_evento/{evento.id}/") 
        return redirect(reverse('eventos:inscrever_evento', kwargs={'id':id}))
    

def participantes_evento(request, id):
    # buscando na tabela Evento pelo id passado como parâmetro
    # se não encontrar, devolva uma "página não encontrada" 
    evento = get_object_or_404(Evento,id=id)
    # verifica se o evento pertence ao criador do evento
    if not evento.criador == request.user:
        raise Http404('Esse evento não é seu')

    if request.method == "GET":
        # o evento tem o campo participantes, então é só acessá-lo
        participantes = evento.participantes.all()[:3]
        return render(request, 'participantes_evento.html', {'evento': evento,
                                                             'participantes':participantes,})


def gerar_csv(request, id):
    # buscando na tabela Evento pelo id passado como parâmetro
    # se não encontrar, devolva uma "página não encontrada" 
    evento = get_object_or_404(Evento,id=id)
    # verifica se o evento pertence ao criador do evento
    if not evento.criador == request.user:
        raise Http404('Esse evento não é seu')
    
    # para gerar um csv com todos os participantes, é necessário buscar todos eles
    participantes = evento.participantes.all()

    # token vai gerar um nome aleatório de 6 caracteres, toda vez que for gerado um arquivo .csv
    token = f"{token_urlsafe(6)}.csv"
    # mostra o caminho onde vai ser armazenado esse arquivo, junto com o seu nome
    path = os.path.join(settings.MEDIA_ROOT, token)
    # cria o csv (para escrita)
    with open(path, 'w') as arq:
        writer = csv.writer(arq, delimiter=';')
        for participante in participantes:
            x = (participante.username, participante.email)
            writer.writerow(x)
    
    return redirect(f"/media/{token}")
    