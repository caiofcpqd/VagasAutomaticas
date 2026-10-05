import subprocess
import time
import urllib.request
import os
import unicodedata
import json
import ssl
from datetime import datetime
from playwright.sync_api import sync_playwright
import winsound

# mude para sua região
VAR_LOCAL = 'rio-janeiro,-rj'
VAR_LOCAL2 = 'rio-de-janeiro,-rj'
VAR_LOCAL3 = 'rio-de-janeiro'
VAR_LOCAL4 = 'Rio%20de%20Janeiro'
VAR_LOCAL5 = 'Rio%20de%20Janeiro'

QUANTIDADE_VAGAS_INDEED = 20
QUANTIDADE_VAGAS_INFOJOBS = 20
QUANTIDADE_VAGAS_GLASSDOOR = 20
QUANTIDADE_VAGAS_LINKEDIN = 20
QUANTIDADE_VAGAS_RIOVAGAS = 20

AGUARDAR_ENTRE_COLETAS = 10
AGUARDAR_CONTEUDO = 5000

# mude para seu path
EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
EDGE_PROFILE = 'C:\\Users\\Caio\\Desktop\\project\\capVagas_Api\\capVagas_Script\\edge_indeed'
DEBUG_PORT = 9222

# mude para sua api
API_URL = 'https://localhost:7200/api/Web'

INDEED_URL = f'https://br.indeed.com/l-{VAR_LOCAL2}-vagas.html?sort=date'
INFOJOBS_URL = f'https://www.infojobs.com.br/empregos-em-{VAR_LOCAL}.aspx?campo=griddate&orden=desc'
GLASSDOOR_URL = f'https://www.glassdoor.com.br/Vaga/{VAR_LOCAL3}-vagas-SRCH_IL.0,14_IC2402386.htm?sortBy=date_desc&fromAge=1'
# mude para o link do seu filtro linkedin, este abaixo pega mais para estágios
LINKEDIN_URL = f'https://br.linkedin.com/jobs/search?keywords=Estagio%20Ti&location={VAR_LOCAL4}%2C%20{VAR_LOCAL4}%2C%20Brasil&geoId=106701406&distance=50&f_TPR=r86400&activeFilter=f_TPR&position=1&pageNum=0'
RIOVAGAS_URLS = ['https://riovagas.com.br/category/riovagas/', 'https://riovagas.com.br/category/riovagas/page/2/']

ARQUIVO_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vagas_novas.txt')

def remover_acentos(texto):
    texto = unicodedata.normalize('NFD', texto)
    return ''.join(caractere for caractere in texto if unicodedata.category(caractere) != 'Mn')

def esperar_porta():
    for _ in range(30):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{DEBUG_PORT}/json/version', timeout=1)
            return True
        except:
            time.sleep(1)
    return False

def salvar_log(origem, vaga):
    agora = datetime.now()
    data = agora.strftime('%d/%m/%Y')
    horario = agora.strftime('%H:%M:%S')

    with open(ARQUIVO_LOG, 'a', encoding='utf-8') as arquivo:
        arquivo.write('========================================\n')
        arquivo.write(f'VAGA NOVA ADICIONADA AS {horario}\n')
        arquivo.write(f'Origem: {origem}\n')
        arquivo.write(f'Data: {data}\n')
        arquivo.write(f"Vaga: {vaga['vaga']}\n")
        arquivo.write(f"Empresa: {vaga['empresa']}\n")
        arquivo.write(f"Local: {vaga['local']}\n")

        if vaga.get('data_publicacao'):
            arquivo.write(f"Publicada no site: {vaga['data_publicacao']}\n")

        if vaga.get('salario'):
            arquivo.write(f"Salario: {vaga['salario']}\n")

        arquivo.write(f"Link: {vaga['link']}\n")
        arquivo.write('========================================\n\n')

def notificar_nova_vaga(origem, vaga):
    horario = datetime.now().strftime('%H:%M:%S')

    print()
    print('========================================')
    print(f'VAGA NOVA ADICIONADA AS {horario}')
    print(f'Origem: {origem}')
    print('========================================')
    print()
    print(f"Vaga: {vaga['vaga']}")
    print(f"Empresa: {vaga['empresa']}")
    print(f"Local: {vaga['local']}")

    if vaga.get('data_publicacao'):
        print(f"Publicada no site: {vaga['data_publicacao']}")

    if vaga.get('salario'):
        print(f"Salario: {vaga['salario']}")

    print(f"Link: {vaga['link']}")
    print()
    salvar_log(origem, vaga)
    print(f'Salvo em: {ARQUIVO_LOG}')
    print()

def garantir_dados_vaga(vaga):
    if not vaga.get('vaga'):
        vaga['vaga'] = 'Não encontrado'

    if not vaga.get('empresa'):
        vaga['empresa'] = 'Não encontrado'

    if not vaga.get('local'):
        vaga['local'] = 'Rio de Janeiro'

    if not vaga.get('link'):
        vaga['link'] = 'Não encontrado'

    if not vaga.get('data_publicacao'):
        vaga['data_publicacao'] = 'Não encontrado'

    if not vaga.get('salario'):
        vaga['salario'] = 'Salário não encontrado'

    return vaga

def chave_vaga(vaga):
    link = (vaga.get('link') or '').strip().lower().rstrip('/')

    if link and link != 'não encontrado':
        return f'link:{link}'

    titulo = remover_acentos((vaga.get('vaga') or '').lower().strip())
    empresa = remover_acentos((vaga.get('empresa') or '').lower().strip())
    local = remover_acentos((vaga.get('local') or '').lower().strip())

    return f'dados:{titulo}|{empresa}|{local}'

def remover_vagas_duplicadas(vagas):
    resultado = []
    chaves = set()

    for vaga in vagas:
        vaga = garantir_dados_vaga(vaga)
        chave = chave_vaga(vaga)

        if chave in chaves:
            continue

        chaves.add(chave)
        resultado.append(vaga)

    return resultado

def pegar_vagas_novas(vagas, vagas_conhecidas):
    novas = []

    for identificador, vaga in vagas.items():
        if identificador not in vagas_conhecidas:
            vaga = garantir_dados_vaga(vaga)
            novas.append(vaga)

    return remover_vagas_duplicadas(novas)

def enviar_vagas_api(vagas):
    if not vagas:
        return

    vagas = remover_vagas_duplicadas(vagas)
    dados = []

    for vaga in vagas:
        vaga = garantir_dados_vaga(vaga)

        dados.append({
            'titulo': vaga.get('vaga', ''),
            'empresa': vaga.get('empresa', ''),
            'local': vaga.get('local', ''),
            'link': vaga.get('link', ''),
            'dataPublicacao': vaga.get('data_publicacao', ''),
            'salario': vaga.get('salario', ''),
            'origem': vaga.get('origem', '')
        })

    try:
        requisicao = urllib.request.Request(API_URL, data=json.dumps(dados, ensure_ascii=False).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        contexto = ssl._create_unverified_context()

        with urllib.request.urlopen(requisicao, context=contexto, timeout=10) as resposta:
            if resposta.status == 200:
                print()
                print(f'{len(dados)} vaga(s) enviada(s) para a API.')
            else:
                print()
                print(f'API retornou status {resposta.status}.')

    except Exception as e:
        print()
        print(f'Erro ao enviar vagas para API: {e}')
        print()

def pegar_vagas_indeed(page):
    cards = page.locator('div.job_seen_beacon')
    quantidade = cards.count()

    if QUANTIDADE_VAGAS_INDEED > 0:
        quantidade = min(quantidade, QUANTIDADE_VAGAS_INDEED)

    vagas = {}

    for i in range(quantidade):
        card = cards.nth(i)

        try:
            link_element = card.locator('h3.jobTitle a').first
            job_id = link_element.get_attribute('data-jk')
            link = link_element.get_attribute('href')
        except:
            job_id = None
            link = None

        if not job_id:
            continue

        if link and link.startswith('/'):
            link = 'https://br.indeed.com' + link

        try:
            vaga = card.locator('h3.jobTitle').inner_text().strip()
        except:
            vaga = 'Não encontrado'

        try:
            empresa = card.locator("[data-testid='company-name']").inner_text().strip()
        except:
            empresa = 'Não encontrado'

        try:
            local = card.locator("[data-testid='text-location']").inner_text().strip()
        except:
            local = 'Rio de Janeiro'

        vagas[job_id] = {
            'vaga': vaga,
            'empresa': empresa,
            'local': local,
            'link': link,
            'data_publicacao': '',
            'salario': ''
        }

    return vagas

def pegar_vagas_riovagas(page):
    dados = page.locator('article.vce-post').evaluate_all('''cards => cards.map(card => {
        const link = card.querySelector("h2.entry-title a");
        const time = card.querySelector("time.updated");

        return {
            vaga: link ? link.innerText.trim() : "",
            link: link ? link.href : "",
            data_publicacao: time ? (time.getAttribute("datetime") || time.innerText.trim()) : ""
        };
    })''')

    vagas = {}

    for item in dados:
        link = item.get('link')

        if not link:
            continue

        vagas[link] = {
            'vaga': item.get('vaga', 'Não encontrado'),
            'empresa': 'riovagas',
            'local': 'Rio de Janeiro',
            'link': link,
            'data_publicacao': item.get('data_publicacao', ''),
            'salario': ''
        }

    return vagas

def pegar_vagas_infojobs(page):
    dados = page.locator('div.js_vacanciesGridFragment div.js_rowCard').evaluate_all(f'''cards => cards.slice(0, {QUANTIDADE_VAGAS_INFOJOBS}).map(card => {{
        const cardLink = card.querySelector("div.js_cardLink");
        const titulo = card.querySelector(".js_vacancyTitle");
        const empresa = card.querySelector("div.text-body a[href*='infojobs.com.br']");
        const empresaFallback = card.querySelector("div.d-flex.align-items-baseline div.text-body");
        const local = card.querySelector("div.mb-8");
        const data = card.querySelector(".js_date");

        return {{
            id: cardLink ? cardLink.getAttribute("data-id") : card.getAttribute("data-id"),
            vaga: titulo ? titulo.innerText.trim() : "Não encontrado",
            empresa: empresa ? empresa.innerText.trim() : (empresaFallback ? empresaFallback.innerText.trim() : "Não encontrado"),
            local: local ? local.innerText.trim() : "Rio de Janeiro",
            link: cardLink ? cardLink.getAttribute("data-href") : "",
            data_publicacao: data ? data.getAttribute("data-value") : ""
        }};
    }})''')

    vagas = {}

    for item in dados:
        id_vaga = item.get('id')

        if not id_vaga:
            continue

        link = item.get('link')

        if link and link.startswith('/'):
            link = 'https://www.infojobs.com.br' + link

        vagas[id_vaga] = {
            'vaga': item.get('vaga', 'Não encontrado'),
            'empresa': item.get('empresa', 'Não encontrado'),
            'local': item.get('local', 'Rio de Janeiro'),
            'link': link,
            'data_publicacao': item.get('data_publicacao', ''),
            'salario': ''
        }

    return vagas

def pegar_vagas_glassdoor(page):
    dados = page.locator("li[data-test='jobListing']").evaluate_all(f"""cards => cards.slice(0, {QUANTIDADE_VAGAS_GLASSDOOR}).map(card => {{
        const titulo = card.querySelector("[data-test='job-title']");
        const empresa = card.querySelector(".EmployerProfile_compactEmployerName__9MGcV");
        const local = card.querySelector("[data-test='emp-location']");
        const salario = card.querySelector("[data-test='detailSalary']");
        const idade = card.querySelector("[data-test='job-age']");

        return {{
            id: card.getAttribute("data-jobid") || "",
            vaga: titulo ? titulo.innerText.trim() : "Não encontrado",
            empresa: empresa ? empresa.innerText.trim() : "Não encontrado",
            local: local ? local.innerText.trim() : "Rio de Janeiro",
            salario: salario ? salario.innerText.trim() : "",
            idade: idade ? idade.innerText.trim() : "",
            link: titulo ? titulo.href : ""
        }};
    }})""")

    vagas = {}

    for item in dados:
        id_vaga = item.get('id')

        if not id_vaga:
            continue

        vagas[id_vaga] = {
            'vaga': item.get('vaga', 'Não encontrado'),
            'empresa': item.get('empresa', 'Não encontrado'),
            'local': item.get('local', 'Rio de Janeiro'),
            'link': item.get('link', ''),
            'salario': item.get('salario', ''),
            'data_publicacao': item.get('idade', '')
        }

    return vagas

def pegar_vagas_linkedin(page):
    dados = page.locator('ul.jobs-search__results-list li div.base-search-card.job-search-card').evaluate_all(f'''cards => cards.slice(0, {QUANTIDADE_VAGAS_LINKEDIN}).map(card => {{
        const titulo = card.querySelector(".base-search-card__title");
        const empresa = card.querySelector(".base-search-card__subtitle a");
        const local = card.querySelector(".job-search-card__location");
        const data = card.querySelector("time.job-search-card__listdate--new");
        const link = card.querySelector("a.base-card__full-link");
        const urn = card.getAttribute("data-entity-urn") || "";

        return {{
            id: urn.replace("urn:li:jobPosting:", ""),
            vaga: titulo ? titulo.innerText.trim() : "Não encontrado",
            empresa: empresa ? empresa.innerText.trim() : "Não encontrado",
            local: local ? local.innerText.trim() : "Rio de Janeiro",
            data_publicacao: data ? (data.getAttribute("datetime") || data.innerText.trim()) : "",
            idade: data ? data.innerText.trim() : "",
            link: link ? link.href : ""
        }};
    }})''')

    vagas = {}

    for item in dados:
        id_vaga = item.get('id')

        if not id_vaga:
            continue

        vagas[id_vaga] = {
            'vaga': item.get('vaga', 'Não encontrado'),
            'empresa': item.get('empresa', 'Não encontrado'),
            'local': item.get('local', 'Rio de Janeiro'),
            'link': item.get('link', ''),
            'data_publicacao': item.get('idade', ''),
            'salario': ''
        }

    return vagas

def carregar_riovagas(page, url, numero):
    print()
    print(f'Carregando RioVagas pagina {numero}...')

    try:
        page.goto(url, wait_until='domcontentloaded', timeout=30000)
        print(f'Pagina {numero} carregada.')
        print(f'URL atual: {page.url}')

        try:
            print(f'Titulo: {page.title()}')
        except:
            pass

        print(f'Aguardando {AGUARDAR_CONTEUDO / 1000:.0f} segundos para o conteudo...')
        page.wait_for_timeout(AGUARDAR_CONTEUDO)

        vagas = pegar_vagas_riovagas(page)
        print(f'RioVagas pagina {numero}: {len(vagas)} vagas encontradas.')

        return vagas

    except Exception as e:
        print()
        print(f'Erro ao carregar RioVagas pagina {numero}:')
        print(type(e).__name__)
        print(str(e))
        print()
        return {}

def carregar_infojobs(page):
    print()
    print('Carregando InfoJobs...')

    try:
        page.goto(INFOJOBS_URL, wait_until='domcontentloaded', timeout=30000)
        print('InfoJobs carregado.')
        print(f'URL atual: {page.url}')

        try:
            print(f'Titulo: {page.title()}')
        except:
            pass

        print(f'Aguardando {AGUARDAR_CONTEUDO / 1000:.0f} segundos para o conteudo...')
        page.wait_for_timeout(AGUARDAR_CONTEUDO)
        print(f'Coletando os {QUANTIDADE_VAGAS_INFOJOBS} primeiros cards...')

        vagas = pegar_vagas_infojobs(page)
        print(f'InfoJobs: {len(vagas)} vagas coletadas.')

        return vagas

    except Exception as e:
        print()
        print('Erro ao carregar InfoJobs:')
        print(type(e).__name__)
        print(str(e))
        print()
        return {}

def carregar_glassdoor(page):
    print()
    print('Carregando Glassdoor...')

    try:
        page.goto(GLASSDOOR_URL, wait_until='domcontentloaded', timeout=30000)
        print('Glassdoor carregado.')
        print(f'URL atual: {page.url}')

        try:
            print(f'Titulo: {page.title()}')
        except:
            pass

        print(f'Aguardando {AGUARDAR_CONTEUDO / 1000:.0f} segundos para o conteudo...')
        page.wait_for_timeout(AGUARDAR_CONTEUDO)
        print(f'Coletando os {QUANTIDADE_VAGAS_GLASSDOOR} primeiros cards...')

        vagas = pegar_vagas_glassdoor(page)
        print(f'Glassdoor: {len(vagas)} vagas coletadas.')

        return vagas

    except Exception as e:
        print()
        print('Erro ao carregar Glassdoor:')
        print(type(e).__name__)
        print(str(e))
        print()
        return {}

def carregar_linkedin(page):
    print()
    print('Carregando LinkedIn...')

    try:
        page.goto(LINKEDIN_URL, wait_until='domcontentloaded', timeout=30000)
        print('LinkedIn carregado.')
        print(f'URL atual: {page.url}')

        try:
            print(f'Titulo: {page.title()}')
        except:
            pass

        print(f'Aguardando {AGUARDAR_CONTEUDO / 1000:.0f} segundos para o conteudo...')
        page.wait_for_timeout(AGUARDAR_CONTEUDO)
        print(f'Coletando os {QUANTIDADE_VAGAS_LINKEDIN} primeiros cards...')

        vagas = pegar_vagas_linkedin(page)
        print(f'LinkedIn: {len(vagas)} vagas coletadas.')

        return vagas

    except Exception as e:
        print()
        print('Erro ao carregar LinkedIn:')
        print(type(e).__name__)
        print(str(e))
        print()
        return {}

def verificar_indeed(page, vagas_conhecidas):
    print()
    print('========================================')
    print('VERIFICANDO INDEED')
    print('========================================')

    try:
        page.reload(wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(AGUARDAR_CONTEUDO)

        vagas_atual = pegar_vagas_indeed(page)
        print(f'Indeed: {len(vagas_atual)} vagas encontradas.')

        vagas_novas = pegar_vagas_novas(vagas_atual, vagas_conhecidas)

        for vaga in vagas_novas:
            vaga['origem'] = 'Indeed'
            notificar_nova_vaga('Indeed', vaga)

        if not vagas_novas:
            print('Indeed: nenhuma vaga nova.')

        return vagas_atual, vagas_novas

    except Exception as e:
        print()
        print('Erro ao verificar Indeed:')
        print(type(e).__name__)
        print(str(e))
        print()
        return vagas_conhecidas, []

def verificar_riovagas(page, vagas_conhecidas):
    print()
    print('========================================')
    print('VERIFICANDO RIOVAGAS')
    print('========================================')

    vagas_pagina1 = carregar_riovagas(page, RIOVAGAS_URLS[0], 1)
    vagas_pagina2 = carregar_riovagas(page, RIOVAGAS_URLS[1], 2)

    todas_vagas = {}
    todas_vagas.update(vagas_pagina1)
    todas_vagas.update(vagas_pagina2)
    todas_vagas = dict(list(todas_vagas.items())[:QUANTIDADE_VAGAS_RIOVAGAS])

    print()
    print(f'RioVagas total: {len(todas_vagas)} vagas.')

    if not vagas_pagina1 and not vagas_pagina2:
        return vagas_conhecidas, []

    vagas_novas = pegar_vagas_novas(todas_vagas, vagas_conhecidas)

    for vaga in vagas_novas:
        vaga['origem'] = 'RioVagas'
        notificar_nova_vaga('RioVagas', vaga)

    if not vagas_novas:
        print('RioVagas: nenhuma vaga nova.')

    return todas_vagas, vagas_novas

def verificar_infojobs(page, vagas_conhecidas):
    print()
    print('========================================')
    print('VERIFICANDO INFOJOBS')
    print('========================================')

    vagas_atual = carregar_infojobs(page)

    print()
    print(f'InfoJobs total: {len(vagas_atual)} vagas.')

    if not vagas_atual:
        return vagas_conhecidas, []

    vagas_novas = pegar_vagas_novas(vagas_atual, vagas_conhecidas)

    for vaga in vagas_novas:
        vaga['origem'] = 'InfoJobs'
        notificar_nova_vaga('InfoJobs', vaga)

    if not vagas_novas:
        print('InfoJobs: nenhuma vaga nova.')

    return vagas_atual, vagas_novas

def verificar_glassdoor(page, vagas_conhecidas):
    print()
    print('========================================')
    print('VERIFICANDO GLASSDOOR')
    print('========================================')

    vagas_atual = carregar_glassdoor(page)

    print()
    print(f'Glassdoor total: {len(vagas_atual)} vagas.')

    if not vagas_atual:
        return vagas_conhecidas, []

    vagas_novas = pegar_vagas_novas(vagas_atual, vagas_conhecidas)

    for vaga in vagas_novas:
        vaga['origem'] = 'Glassdoor'
        notificar_nova_vaga('Glassdoor', vaga)

    if not vagas_novas:
        print('Glassdoor: nenhuma vaga nova.')

    return vagas_atual, vagas_novas

def verificar_linkedin(page, vagas_conhecidas):
    print()
    print('========================================')
    print('VERIFICANDO LINKEDIN')
    print('========================================')

    vagas_atual = carregar_linkedin(page)

    print()
    print(f'LinkedIn total: {len(vagas_atual)} vagas.')

    if not vagas_atual:
        return vagas_conhecidas, []

    vagas_novas = pegar_vagas_novas(vagas_atual, vagas_conhecidas)

    for vaga in vagas_novas:
        vaga['origem'] = 'LinkedIn'
        notificar_nova_vaga('LinkedIn', vaga)

    if not vagas_novas:
        print('LinkedIn: nenhuma vaga nova.')

    return vagas_atual, vagas_novas

def main():
    with sync_playwright() as p:
        print('Iniciando Edge separado...')

        processo = subprocess.Popen([
            EDGE_PATH,
            f'--remote-debugging-port={DEBUG_PORT}',
            f'--user-data-dir={EDGE_PROFILE}',
            '--no-first-run',
            '--no-default-browser-check',
            '--window-position=-3000,-3000',
            '--window-size=1920,1080'
        ])

        if not esperar_porta():
            processo.kill()
            raise Exception('Nao foi possivel iniciar o Edge na porta 9222.')

        print('Conectando ao Edge...')

        browser = p.chromium.connect_over_cdp(f'http://127.0.0.1:{DEBUG_PORT}')
        context = browser.contexts[0]

        page_indeed = context.new_page()
        page_riovagas = context.new_page()
        page_infojobs = context.new_page()
        page_glassdoor = context.new_page()
        page_linkedin = context.new_page()

        print()
        print('========================================')
        print('CRIANDO LISTAS INICIAIS')
        print('========================================')
        print()
        print('Carregando Indeed...')

        try:
            page_indeed.goto(INDEED_URL, wait_until='domcontentloaded', timeout=30000)
            page_indeed.wait_for_timeout(AGUARDAR_CONTEUDO)
            vagas_indeed = pegar_vagas_indeed(page_indeed)
            print(f'Indeed inicial: {len(vagas_indeed)} vagas.')
        except Exception as e:
            print(f'Erro no Indeed inicial: {e}')
            vagas_indeed = {}

        vagas_rio_1 = carregar_riovagas(page_riovagas, RIOVAGAS_URLS[0], 1)
        vagas_rio_2 = carregar_riovagas(page_riovagas, RIOVAGAS_URLS[1], 2)

        vagas_riovagas = {}
        vagas_riovagas.update(vagas_rio_1)
        vagas_riovagas.update(vagas_rio_2)
        vagas_riovagas = dict(list(vagas_riovagas.items())[:QUANTIDADE_VAGAS_RIOVAGAS])

        print()
        print(f'RioVagas inicial: {len(vagas_riovagas)} vagas.')

        vagas_infojobs = carregar_infojobs(page_infojobs)
        print()
        print(f'InfoJobs inicial: {len(vagas_infojobs)} vagas.')

        vagas_glassdoor = carregar_glassdoor(page_glassdoor)
        print()
        print(f'Glassdoor inicial: {len(vagas_glassdoor)} vagas.')

        vagas_linkedin = carregar_linkedin(page_linkedin)
        print()
        print(f'LinkedIn inicial: {len(vagas_linkedin)} vagas.')

        print()
        print('========================================')
        print('MONITORAMENTO INICIADO')
        print('========================================')
        print()
        print('Coletando os 20 cards mais recentes de cada site.')
        print('Os filtros de palavras e locais ficam na API.')
        print(f'Nova coleta a cada {AGUARDAR_ENTRE_COLETAS} segundos.')
        print()

        while True:
            vagas_para_api = []

            vagas_riovagas, vagas_novas = verificar_riovagas(page_riovagas, vagas_riovagas)
            vagas_para_api.extend(vagas_novas)

            vagas_infojobs, vagas_novas = verificar_infojobs(page_infojobs, vagas_infojobs)
            vagas_para_api.extend(vagas_novas)

            vagas_glassdoor, vagas_novas = verificar_glassdoor(page_glassdoor, vagas_glassdoor)
            vagas_para_api.extend(vagas_novas)

            vagas_linkedin, vagas_novas = verificar_linkedin(page_linkedin, vagas_linkedin)
            vagas_para_api.extend(vagas_novas)

            vagas_indeed, vagas_novas = verificar_indeed(page_indeed, vagas_indeed)
            vagas_para_api.extend(vagas_novas)

            vagas_para_api = remover_vagas_duplicadas(vagas_para_api)

            if vagas_para_api:
                print()
                print('========================================')
                print(f'ENVIANDO {len(vagas_para_api)} VAGA(S) NOVA(S) PARA A API')
                print('========================================')
                enviar_vagas_api(vagas_para_api)
            else:
                print()
                print('Nenhuma vaga nova encontrada nesta coleta.')

            print()
            print(f'Aguardando {AGUARDAR_ENTRE_COLETAS} segundos para a proxima coleta...')
            time.sleep(AGUARDAR_ENTRE_COLETAS)


try:
    main()

except Exception as e:
    print()
    print()
    print('========================================')
    print('ERRO:')
    print('========================================')
    print()
    print(type(e).__name__)
    print(str(e))
    print()

finally:
    input('Pressione ENTER para fechar...')
