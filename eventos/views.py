from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages import constants
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.paginator import Paginator

from .models import Evento, Certificado
import csv, os, sys
from secrets import token_urlsafe
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


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
        data = {}
        data['evento'] = evento
        # o evento tem o campo participantes, então é só acessá-lo
        data['participantes'] = evento.participantes.all()
        all = evento.participantes.all()
        # seleciona quantos participantes vão ser mostrados em cada página
        paginator = Paginator(all, 2)
        pages = request.GET.get('page')
        data['paginas'] = paginator.get_page(pages)
        return render(request, 'participantes_evento.html', data)


def gerar_csv(request, id):
    # buscando na tabela Evento pelo id passado como parâmetro
    # se não encontrar, devolva uma "página não encontrada" 
    evento = get_object_or_404(Evento,id=id)
    # verifica se o evento pertence ao criador do evento
    if not evento.criador == request.user:
        raise Http404('Esse evento não é seu')
    
    # para gerar um csv com todos os participantes, é necessário buscar todos eles
    participantes = evento.participantes.all()

    # token vai gerar um nome aleatório de 8 bites, toda vez que for gerado um arquivo .csv
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
    

def certificados_evento(request, id):
    # buscar o evento no banco
    evento = get_object_or_404(Evento, id=id)
    # verifica se o evento pertence ao criador do evento
    if not evento.criador == request.user:
        raise Http404('Esse evento não é seu')
    if request.method == "GET":
        # verifica a quantidade de certificados gerados
        # subtraindo o total de certificados menos os certificados desse evento
        qtd_certificados = evento.participantes.all().count() - Certificado.objects.filter(evento=evento).count()
        return render(request, 'certificados_evento.html', {'qtd_certificados': qtd_certificados,
                                                            'evento': evento,})
    

def gerar_certificado(request, id):
    # buscando na tabela Evento pelo id passado como parâmetro
    # se não encontrar, devolva uma "página não encontrada" 
    evento = get_object_or_404(Evento,id=id)
    # verifica se o evento pertence ao criador do evento
    if not evento.criador == request.user:
        raise Http404('Esse evento não é seu')
    
    path_template = os.path.join(settings.BASE_DIR, 'templates/static/evento/img/template_certificado.png')
    path_fonte = os.path.join(settings.BASE_DIR, 'templates/static/fontes/arimo.ttf')

    for participante in evento.participantes.all():
        # TODO validar se o certificado já foi gerado

        # abre a imagem
        img = Image.open(path_template) 
        # cria uma variável para escrever na imagem
        draw = ImageDraw.Draw(img)
        # para utilizar uma fonte na imagem, é preciso passar o caminho e o tamanho da fonte
        fonte_nome = ImageFont.truetype(path_fonte, 80)
        fonte_info = ImageFont.truetype(path_fonte, 30)

        # é preciso passar as coordenadas em forma de tupla, 
        # depois o texto a ser digitado, 
        # depois a fonte a ser utilizada
        # e por último a cor da fonte em forma de tupla
        draw.text((222, 632), f"{participante.username}", font=fonte_nome, fill=(0, 0, 0))
        draw.text((761, 775), f"{evento.nome}", font=fonte_info, fill=(0, 0, 0))
        draw.text((816, 842), f"{evento.carga_horaria} horas.", font=fonte_info, fill=(0, 0, 0))

        # cria uma variável para salvar essa imagem para manipular de acordo com as necessidades
        output = BytesIO()
        # é preciso passar o caminho onde será salvo, nesse caso, dentro da variável output
        # depois o formato da imagem
        # depois a qualidade da imagem
        img.save(output, format="PNG", quality=100)
        # aponta para o início do arquivo
        output.seek(0)
        # agora é preciso converter essa imagem em um arquivo que o Django compreende
        # existem dois tipos de arquivo  que o Django utiliza: InMemoryUploadedFile e TemporaryUploadedFile
        # para finalizar é preciso criar a imagem final passando:
        # o arquivo, 
        # tipo do campo, 
        # nome (gerado com função que gera um nome aleatório de 8 bites), 
        # tipo de imagem
        # tamanho, que recebe a função getsizeof, que recebe o tamanho de outoput e retorna o tamanho dele mesmo
        # charset, se fosse um texto, poderia ser o UTF-8, mas como é imagem, não precisa, então None
        img_final = InMemoryUploadedFile(
                                output,
                                'Imagefield',
                                f'{token_urlsafe(8)}.png',
                                'image/jpeg',
                                sys.getsizeof(output),
                                None
                                )
        certificado_gerado = Certificado(
                            certificado=img_final,
                            participante=participante,
                            evento=evento
                            )
        certificado_gerado.save()
    messages.add_message(request, constants.SUCCESS, 'Certificados gerados com sucesso!')
    return redirect(reverse('eventos:certificados_evento', kwargs={'id':id}))


def procurar_certificado(request, id):
    evento = get_object_or_404(Evento,id=id)
    if not evento.criador == request.user:
        raise Http404('Esse evento não é seu')

    email = request.POST.get('email')
    # buscar pelo evento e pelo email que foi passado pelo POST, mostrando apenas o primeiro
    certificado = Certificado.objects.filter(evento=evento).filter(participante__email=email).first()
    if not certificado:
        messages.add_message(request, constants.WARNING, 'Este certificado ainda não foi gerado')
        return redirect(reverse('eventos:certificados_evento', kwargs={'id':id}))
    else:
        return redirect(certificado.certificado.url)


