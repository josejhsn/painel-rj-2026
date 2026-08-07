# -*- coding: utf-8 -*-
"""
Coletor de leiloes de imoveis - corredor Tijuca -> Lapa -> Catete -> Copacabana (RJ)

O que faz:
  1. Busca os imoveis em leilao listados hoje no Portal Zuk para a cidade do Rio de Janeiro
     (fonte testada e acessivel via HTTP simples, sem bloqueio anti-robo).
  2. Calcula, por imovel: R$/m2, comparacao com a media do bairro, custo total estimado
     (lance + comissao + ITBI + laudemio quando aplicavel), e um semaforo de risco.
  3. Gera um arquivo HTML unico e autossuficiente (LEILOES-RJ.html) com filtros,
     que pode ser aberto offline em qualquer navegador e enviado por WhatsApp/e-mail.

Como rodar de novo (os dados mudam quase todo dia):
  python coletor.py

Fontes automatizadas: Portal Zuk, Mega Leiloes, RJ Leiloes, Juliana Vettorazzo,
Rymer Leiloes, Gustavo Lourenco Leiloeiro.

Fontes que AINDA NAO sao raspadas automaticamente (bloqueio anti-robo ou exigem
varrer leilao por leilao com estrutura propria) ficam como links de checagem manual
dentro do HTML gerado: Caixa, Santander, Itau, Bradesco, Biasi Leiloes.
"""

import json
import os
import re
import unicodedata
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")

import requests

# --------------------------------------------------------------------------------------
# Configuracao
# --------------------------------------------------------------------------------------

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

ZUK_CITY_URL = "https://www.portalzuk.com.br/leilao-de-imoveis/c/todos-imoveis/rj/regiao/rio-de-janeiro"
ZUK_LOAD_MORE_URL = "https://www.portalzuk.com.br/leilao-de-imoveis/mais"
MAX_PAGINAS = 15  # trava de seguranca para nao entrar em loop infinito

MEGA_RJ_URL = "https://www.megaleiloes.com.br/imoveis/rj/rio-de-janeiro"
MEGA_MAX_PAGINAS = 15

FONTES_CONTATO = {
    "Portal Zuk": {"site": "https://www.portalzuk.com.br", "obs": "Habilitacao e lances pelo proprio site; sem telefone/e-mail por lote."},
    "Mega Leiloes": {"site": "https://www.megaleiloes.com.br", "obs": "Habilitacao e lances pelo proprio site; sem telefone/e-mail por lote."},
    "RJ Leiloes": {"site": "https://www.rjleiloes.com.br", "obs": "Habilitacao e lances pelo proprio site; sem telefone/e-mail por lote."},
    "Juliana Vettorazzo": {"site": "https://www.jvleiloes.lel.br", "obs": "Habilitacao e lances pelo proprio site; sem telefone/e-mail por lote."},
    "Rymer Leiloes": {"site": "https://rymerleiloes.com.br", "obs": "Habilitacao e lances pelo proprio site; sem telefone/e-mail por lote."},
    "Gustavo Lourenco": {"site": "https://gustavoleiloeiro.com.br", "obs": "Habilitacao e lances pelo proprio site; sem telefone/e-mail por lote."},
}

# Corredor de interesse, na ordem geografica pedida (usado para ordenar e destacar).
# Chaves normalizadas (sem acento, minusculo) -> nome de exibicao.
CORREDOR_BAIRROS = {
    "tijuca": "Tijuca",
    "alto da boa vista": "Alto da Boa Vista",
    "vila isabel": "Vila Isabel",
    "andarai": "Andarai",
    "maracana": "Maracana",
    "praca da bandeira": "Praca da Bandeira",
    "rio comprido": "Rio Comprido",
    "estacio": "Estacio",
    "cidade nova": "Cidade Nova",
    "centro": "Centro",
    "saude": "Saude",
    "gamboa": "Gamboa",
    "santo cristo": "Santo Cristo",
    "fatima": "Fatima",
    "lapa": "Lapa",
    "santa teresa": "Santa Teresa",
    "gloria": "Gloria",
    "catete": "Catete",
    "flamengo": "Flamengo",
    "laranjeiras": "Laranjeiras",
    "cosme velho": "Cosme Velho",
    "botafogo": "Botafogo",
    "humaita": "Humaita",
    "urca": "Urca",
    "copacabana": "Copacabana",
    "leme": "Leme",
}
ORDEM_CORREDOR = list(CORREDOR_BAIRROS.keys())

# R$/m2 de referencia por bairro (pesquisa de mercado ago/2026 - ver ESTUDO-LEILOES-RJ.md).
# None = sem numero especifico encontrado; a ferramenta cai para a media da cidade e avisa.
BENCHMARKS_M2 = {
    "tijuca": 6838,
    "lapa": None,
    "centro": None,
    "gloria": 8781,
    "catete": 6883,
    "flamengo": 11072,
    "laranjeiras": 12179,
    "botafogo": 11100,
    "copacabana": 12687,
    "leme": 12000,  # colado em Copacabana, sem numero proprio -> aproximacao
}
MEDIA_CIDADE_M2 = 11049  # FipeZap jul/2026, cidade do Rio como um todo

# Bairros onde parte relevante do terreno costuma ser "terreno de marinha" (laudemio a
# uniao, ~5%). E por PARCELA, nao por bairro inteiro - aqui so sinalizamos "possivel,
# confirmar na matricula", nunca como certeza.
BAIRROS_LAUDEMIO_POSSIVEL = {
    "copacabana", "leme", "flamengo", "catete", "gloria", "botafogo", "urca",
}

# Municipios do estado do RJ diferentes da capital - usado para reconhecer quando um
# endereco tipo "Bairro/RJ" na verdade se refere a OUTRA cidade (a convencao comum nesses
# sites e' omitir "Rio de Janeiro" quando e' a capital, mas nomear a cidade quando nao e').
OUTROS_MUNICIPIOS_RJ = {
    "niteroi", "cabo frio", "teresopolis", "teresopo", "petropolis", "nova friburgo",
    "angra dos reis", "volta redonda", "duque de caxias", "nilopolis", "nil", "sao goncalo",
    "itaborai", "marica", "queimados", "nova iguacu", "belford roxo", "mesquita",
    "nova iguaçu", "nova iguac", "itaguai", "seropedica", "nl", "araruama", "saquarema",
    "rio das ostras", "macae", "campos dos goytacazes", "resende", "barra do pirai",
    "paraty", "mangaratiba", "guapimirim", "cachoeiras de macacu", "itaperuna",
}

COMISSAO_LEILOEIRO_PCT = 5.0
ITBI_RJ_PCT = 3.0
CARTORIO_PCT = 1.5
LAUDEMIO_PCT = 5.0

OUTRAS_FONTES = [
    {"nome": "Imoveis Caixa (venda direta, leilao SFI, licitacao)", "url": "https://venda-imoveis.caixa.gov.br/sistema/busca-imovel.asp?sltTipoBusca=imoveis"},
    {"nome": "Imoveis Banco Santander (via Zuk)", "url": "https://www.portalzuk.com.br/leilao-de-imoveis/v/banco-santander"},
    {"nome": "Imoveis Itau", "url": "https://www.itau.com.br/imoveis-itau"},
    {"nome": "Imoveis Bradesco (leiloes)", "url": "https://banco.bradesco/html/classic/produtos-servicos/leiloes/index.shtm"},
    {"nome": "Biasi Leiloes", "url": "https://www.biasileiloes.com.br"},
    {"nome": "TJRJ - Leilao de Imoveis (editais oficiais)", "url": "https://portaltj.tjrj.jus.br/leilao-imoveis"},
]

OUTPUT_HTML = "LEILOES-RJ.html"
DOCS_DIR = "docs"


# --------------------------------------------------------------------------------------
# Coleta - Portal Zuk
# --------------------------------------------------------------------------------------

def normaliza(txt):
    """minusculo, sem acento, espacos simples - para comparar bairros com seguranca."""
    if not txt:
        return ""
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", txt).strip().lower()


def buscar_html_zuk():
    """Baixa a listagem completa (com paginacao) da cidade do Rio de Janeiro na Zuk."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    r = session.get(ZUK_CITY_URL, timeout=30)
    r.raise_for_status()
    html = r.text

    token_match = re.search(r'name="_token" value="([^"]+)"', html)
    token = token_match.group(1) if token_match else None

    total_html = html
    total_cards = len(re.findall(r"card-property card_lotes_div", html))

    if token:
        for _ in range(MAX_PAGINAS):
            payload = {
                "limit": total_cards,
                "count_imovel_zuk": total_cards,
                "path": ZUK_CITY_URL,
                "order": "data_leilao",
                "div_parceiro_count": 0,
                "_token": token,
            }
            resp = session.post(
                ZUK_LOAD_MORE_URL,
                data=payload,
                timeout=30,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": ZUK_CITY_URL,
                    "X-CSRF-TOKEN": token,
                },
            )
            if resp.status_code != 200:
                break
            novos = len(re.findall(r"card-property card_lotes_div", resp.text))
            if novos == 0:
                break
            total_html += resp.text
            total_cards += novos

    return total_html


CARD_START_RE = re.compile(r'<div class="card-property card_lotes_div"')

TITLE_RE = re.compile(r'title="([^"]*)"')
HREF_RE = re.compile(r'<a\s+[^>]*href="(https://www\.portalzuk\.com\.br/imovel/[^"]+)"')
IMG_RE = re.compile(r'<img src="([^"]+)"')
TIPO_RE = re.compile(r'<span class="card-property-price-lote">([^<]+)</span>')
CIDADE_BAIRRO_RE = re.compile(r'>([A-Za-zÀ-ú ]+?)\s*/\s*[A-Z]{2}</a>\s*-\s*([A-Za-zÀ-ú\'\- ]+)</span>')
ENDERECO_RE = re.compile(r'margin-left:2\.5rem;">([^<]+)</span>')
PRECO_LABEL_RE = re.compile(r'class="card-property-price-label"[^>]*>\s*([^<]+?)\s*</span>')
PRECO_VALOR_RE = re.compile(r'class="card-property-price-value">R\$\s*([\d.,]+)')
DESCONTO_RE = re.compile(r'arrow-down"></i>(\d+)<i data-feather="percent">')
DATA_LEILAO_RE = re.compile(r'class="card-property-price-data">([^<]+)</span>')
AREA_RE = re.compile(r'card-property-info-label">([\d,]+)m2? ?(constru[ií]da|[uú]til)?', re.I)
DESOCUPADO_RE = re.compile(r'card-property-news">\s*Desocupado')
PRACAS_RE = re.compile(r'data-pracas="(\d+)"')
VENDA_DIRETA_RE = re.compile(r'card-property-proposta-open">\s*([^<]+?)\s*</span>')
PROPOSTA_ABERTA_RE = re.compile(r'class="card-property-price-value">\s*([^<R][^<]*)</span>')


def parse_valor_br(s):
    if not s:
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def extrair_comitente(title):
    """O atributo title do card traz algo como:
    "Apartamento em leilao - Rua X, 1 - Rio De Janeiro/RJ - Banco Santander Brasil S/A | Z12345"
    """
    if not title:
        return None
    partes = title.split(" - ")
    if len(partes) >= 4:
        comitente = partes[-1].split("|")[0].strip()
        return comitente or None
    return None


def classificar_modalidade(comitente):
    if not comitente:
        return "Verificar edital"
    c = normaliza(comitente)
    bancos = ["banco", "itau", "santander", "bradesco", "caixa", "safra", "votorantim", "bmg", "sicredi", "sicoob"]
    if any(b in c for b in bancos):
        return "Extrajudicial (banco)"
    return "Verificar edital"


def parse_cards(html):
    starts = [m.start() for m in CARD_START_RE.finditer(html)]
    blocos = [
        html[starts[i]: starts[i + 1] if i + 1 < len(starts) else starts[i] + 4000]
        for i in range(len(starts))
    ]

    imoveis = []
    for bloco in blocos:
        href_m = HREF_RE.search(bloco)
        if not href_m:
            continue
        url = href_m.group(1)
        lote_id_m = re.search(r"-(\d+)$", url)
        lote_id = lote_id_m.group(1) if lote_id_m else url

        title_m = TITLE_RE.search(bloco)
        title = title_m.group(1) if title_m else ""

        img_m = IMG_RE.search(bloco)
        imagem = img_m.group(1) if img_m else None

        tipo_m = TIPO_RE.search(bloco)
        tipo = tipo_m.group(1).strip() if tipo_m else "Nao informado"

        cb_m = CIDADE_BAIRRO_RE.search(bloco)
        cidade = cb_m.group(1).strip() if cb_m else "Rio de Janeiro"
        bairro = cb_m.group(2).strip() if cb_m else "Nao informado"

        end_m = ENDERECO_RE.search(bloco)
        endereco = end_m.group(1).strip() if end_m else ""

        preco_label_m = PRECO_LABEL_RE.search(bloco)
        preco_label = preco_label_m.group(1).strip() if preco_label_m else ""

        preco_valor_m = PRECO_VALOR_RE.search(bloco)
        preco = parse_valor_br(preco_valor_m.group(1)) if preco_valor_m else None

        venda_direta_m = VENDA_DIRETA_RE.search(bloco)
        if venda_direta_m and preco is None:
            # ex: "Venda Direta" com preco "Aberto para proposta" (sem valor fixo)
            texto_m = PROPOSTA_ABERTA_RE.search(bloco)
            preco_label = texto_m.group(1).strip() if texto_m else venda_direta_m.group(1).strip()

        desconto_m = DESCONTO_RE.search(bloco)
        desconto_pct = int(desconto_m.group(1)) if desconto_m else None

        data_m = DATA_LEILAO_RE.search(bloco)
        data_leilao = data_m.group(1).strip() if data_m else ""

        area_m = AREA_RE.search(bloco)
        area_m2 = parse_valor_br(area_m.group(1)) if area_m else None

        desocupado = bool(DESOCUPADO_RE.search(bloco))

        pracas_m = PRACAS_RE.search(bloco)
        pracas = pracas_m.group(1) if pracas_m else None

        comitente = extrair_comitente(title)

        bairro_norm = normaliza(bairro)

        modalidade = "Venda direta" if venda_direta_m else classificar_modalidade(comitente)

        imoveis.append({
            "id": "zuk-" + lote_id,
            "fonte": "Portal Zuk",
            "tipo": tipo,
            "cidade": cidade,
            "bairro": bairro,
            "bairro_norm": bairro_norm,
            "endereco": endereco,
            "preco": preco,
            "preco_label": preco_label or "Valor",
            "desconto_pct": desconto_pct,
            "data_leilao": data_leilao,
            "area_m2": area_m2,
            "quartos": None,
            "vagas": None,
            "ocupacao": "Desocupado" if desocupado else "Verificar edital",
            "comitente": comitente,
            "modalidade": modalidade,
            "pracas": pracas,
            "etapas": [],
            "status_leilao": "",
            "imagem_url": imagem,
            "pagina_url": url,
            "no_corredor": bairro_norm in CORREDOR_BAIRROS,
        })

    # dedupe por id (a paginacao pode repetir cards de borda)
    vistos = set()
    unicos = []
    for im in imoveis:
        if im["id"] in vistos:
            continue
        vistos.add(im["id"])
        unicos.append(im)
    return unicos


# --------------------------------------------------------------------------------------
# Coleta - Mega Leiloes
# --------------------------------------------------------------------------------------

MEGA_CARD_START_RE = re.compile(r'<div class="card open">')
MEGA_HREF_TITLE_RE = re.compile(r'<a class="card-title" href="([^"]+)"[^>]*>([^<]+)</a>')
MEGA_LOCALITY_RE = re.compile(r'class="card-locality"[^>]*title="([^"]+)"')
MEGA_PRICE_RE = re.compile(r'class="card-price">R\$\s*([\d.,]+)')
MEGA_DESCONTO_RE = re.compile(r'class="value">(\d+)%</span><br>abaixo')
MEGA_MODALIDADE_RE = re.compile(r'class="card-instance-title"><a[^>]*>([^<]+)</a>')
MEGA_LOTE_RE = re.compile(r'class="card-batch-number">([^<]+)</div>')
MEGA_IMG_RE = re.compile(r'class="card-image[^"]*"[^>]*data-bg="([^"]+)"')
MEGA_PRACA_DATA_RE = re.compile(r'<b>(\d+.\s*Pra.a):</b>\s*([^<]+)</span>')
MEGA_PRACA_VALOR_RE = re.compile(r'class="card-instance-value">R\$\s*([\d.,]+)')
MEGA_STATUS_RE = re.compile(r'class="card-status">([^<]+)</div>')


def buscar_html_mega():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    html_total = ""
    for pagina in range(1, MEGA_MAX_PAGINAS + 1):
        url = MEGA_RJ_URL if pagina == 1 else f"{MEGA_RJ_URL}?pagina={pagina}"
        r = session.get(url, timeout=30)
        if r.status_code != 200:
            break
        n_cards = len(MEGA_CARD_START_RE.findall(r.text))
        if n_cards == 0:
            break
        html_total += r.text
        if n_cards < 12:  # pagina "curta" = provavelmente a ultima
            break
    return html_total


def parse_titulo_mega(titulo, cidade_fallback="Rio de Janeiro"):
    """Duas formas observadas no titulo do card:
    A) 'Apartamento 220 m2 (...) com 01 vaga - Penha - Rio de Janeiro - RJ'
    B) 'Sala Comercial 27 m2 - Rio de Janeiro-RJ - Rua X, 5644 - Sala 1108 - Engenho de Dentro'
       (cidade+UF colados num unico trecho, endereco no meio, bairro no final)
    """
    partes = [p.strip() for p in titulo.split(" - ") if p.strip()]
    tipo, area_m2, vagas = None, None, None
    if partes:
        m = re.match(r"^([A-Za-zÀ-ú/ ]+?)\s+([\d.,]+)\s*m\s*[2²]?", partes[0], re.I)
        if m:
            tipo = m.group(1).strip()
            area_m2 = parse_valor_br(m.group(2))
        vagas_m = re.search(r"(\d+)\s*vagas?", partes[0], re.I)
        vagas = int(vagas_m.group(1)) if vagas_m else None

    cidade_uf_idx = next(
        (i for i, p in enumerate(partes) if re.match(r"^[A-Za-zÀ-ú ]+-[A-Z]{2}$", p)), None
    )
    if partes and re.match(r"^[A-Z]{2}$", partes[-1] or ""):
        # Formato A: ultimo item e a UF isolada
        cidade = partes[-2] if len(partes) >= 2 else cidade_fallback
        bairro = partes[1] if len(partes) >= 3 else "Nao informado"
    elif cidade_uf_idx is not None:
        # Formato B: cidade+UF colados num trecho; bairro e o ultimo pedaco do titulo
        cidade = partes[cidade_uf_idx].rsplit("-", 1)[0]
        bairro = partes[-1] if len(partes) > cidade_uf_idx + 1 else "Nao informado"
    else:
        cidade = cidade_fallback
        bairro = partes[1] if len(partes) >= 2 else "Nao informado"

    return tipo or "Nao informado", area_m2, vagas, bairro, cidade


def parse_cards_mega(html):
    starts = [m.start() for m in MEGA_CARD_START_RE.finditer(html)]
    blocos = [
        html[starts[i]: starts[i + 1] if i + 1 < len(starts) else starts[i] + 5000]
        for i in range(len(starts))
    ]

    imoveis = []
    for bloco in blocos:
        ht_m = MEGA_HREF_TITLE_RE.search(bloco)
        if not ht_m:
            continue
        url, titulo = ht_m.group(1).split("?")[0], ht_m.group(2).strip()

        lote_id_m = re.search(r"-[a-z](\d+)$", url, re.I)
        lote_id = "mega-" + (lote_id_m.group(1) if lote_id_m else str(abs(hash(url))))

        tipo, area_m2, vagas, bairro, cidade = parse_titulo_mega(titulo)
        bairro_norm = normaliza(bairro)

        preco_m = MEGA_PRICE_RE.search(bloco)
        preco = parse_valor_br(preco_m.group(1)) if preco_m else None

        desconto_m = MEGA_DESCONTO_RE.search(bloco)
        desconto_pct = int(desconto_m.group(1)) if desconto_m else None

        modalidade_m = MEGA_MODALIDADE_RE.search(bloco)
        modalidade_txt = modalidade_m.group(1).strip() if modalidade_m else "Verificar edital"
        modalidade = "Extrajudicial (banco)" if "extrajudicial" in normaliza(modalidade_txt) else (
            "Verificar edital" if "judicial" not in normaliza(modalidade_txt) else "Judicial"
        )

        img_m = MEGA_IMG_RE.search(bloco)
        imagem = img_m.group(1) if img_m else None

        status_m = MEGA_STATUS_RE.search(bloco)
        status = status_m.group(1).strip() if status_m else ""

        datas = MEGA_PRACA_DATA_RE.findall(bloco)
        valores = MEGA_PRACA_VALOR_RE.findall(bloco)
        etapas = []
        for i, (label, data) in enumerate(datas):
            valor = parse_valor_br(valores[i]) if i < len(valores) else None
            etapas.append({"etapa": label.strip(), "data": data.strip(), "valor": valor})
        data_leilao = etapas[0]["data"] if etapas else ""
        preco_label = etapas[0]["etapa"] if etapas else "Valor"
        if preco is None and etapas:
            preco = etapas[0]["valor"]

        ocupacao_texto = normaliza(titulo + " " + bloco[:400])
        ocupacao = "Desocupado" if "desocupad" in ocupacao_texto else "Verificar edital"

        imoveis.append({
            "id": lote_id,
            "fonte": "Mega Leiloes",
            "tipo": tipo,
            "cidade": cidade,
            "bairro": bairro,
            "bairro_norm": bairro_norm,
            "endereco": bairro,  # Mega nao mostra endereco de rua no card, so bairro
            "preco": preco,
            "preco_label": preco_label,
            "desconto_pct": desconto_pct,
            "data_leilao": data_leilao,
            "area_m2": area_m2,
            "quartos": None,
            "vagas": vagas,
            "ocupacao": ocupacao,
            "comitente": None,
            "modalidade": modalidade,
            "pracas": str(len(etapas)) if etapas else None,
            "etapas": etapas,
            "status_leilao": status,
            "imagem_url": imagem,
            "pagina_url": url,
            "no_corredor": bairro_norm in CORREDOR_BAIRROS,
        })

    vistos = set()
    unicos = []
    for im in imoveis:
        if im["id"] in vistos:
            continue
        vistos.add(im["id"])
        unicos.append(im)
    return unicos


# --------------------------------------------------------------------------------------
# Coleta - plataforma Soleon (RJ Leiloes, Juliana Vettorazzo Leiloeira)
# Sites diferentes, mesmo motor de leiloes -> mesma estrutura de card, um parser serve os dois.
# --------------------------------------------------------------------------------------

SOLEON_SITES = {
    "RJ Leiloes": "https://www.rjleiloes.com.br",
    "Juliana Vettorazzo": "https://www.jvleiloes.lel.br",
}
SOLEON_MAX_EVENTOS = 10

SOLEON_LOTE_START_RE = re.compile(r'<div class="col-12 mb-4">')
SOLEON_TITULO_RE = re.compile(r"<h5>([^<]+)</h5>")
SOLEON_CIDADE_RE = re.compile(r"<b>Cidade:</b>\s*([^<]+?)\s*(?:<br|</div)")
SOLEON_ENDERECO_RE = re.compile(r"<b>Endere.o:</b>\s*([^<]+?)\s*(?:<br|</div)")
SOLEON_MODALIDADE_RE = re.compile(r'label_lote ([a-z_]+)"')
SOLEON_PRECO_LABEL_RE = re.compile(r"<h5>([^<]*)</h5>\s*<h4[^>]*>R\$\s*([\d.,]+)")
SOLEON_URL_RE = re.compile(r'href="(https?://[^"]+/item/\d+/detalhes[^"]*)"')
SOLEON_IMG_RE = re.compile(r"background:\s*url\('([^']+)'\)")
SOLEON_AREA_RE = re.compile(r"(\d+[\d.,]*)\s*m.\s*(?:de\s*.rea\s*)?(?:constru.da|privativa|.til)", re.I)


def buscar_eventos_soleon(session, base_url):
    r = session.get(base_url, timeout=30)
    ids = sorted(set(re.findall(r"/leilao/(\d+)/lotes", r.text)), key=int, reverse=True)
    return ids[:SOLEON_MAX_EVENTOS]


def parse_cards_soleon(html, fonte):
    starts = [m.start() for m in SOLEON_LOTE_START_RE.finditer(html)]
    blocos = [
        html[starts[i]: starts[i + 1] if i + 1 < len(starts) else starts[i] + 3500]
        for i in range(len(starts))
    ]
    imoveis = []
    for bloco in blocos:
        url_m = SOLEON_URL_RE.search(bloco)
        if not url_m:
            continue
        url = url_m.group(1)
        lote_id_m = re.search(r"/item/(\d+)/", url)
        lote_id = lote_id_m.group(1) if lote_id_m else str(abs(hash(url)))

        titulo_m = SOLEON_TITULO_RE.search(bloco)
        titulo = titulo_m.group(1).strip() if titulo_m else ""

        cidade_m = SOLEON_CIDADE_RE.search(bloco)
        cidade = cidade_m.group(1).strip() if cidade_m else "Rio de Janeiro"
        if "rio de janeiro" not in normaliza(cidade):
            continue

        endereco_m = SOLEON_ENDERECO_RE.search(bloco)
        endereco = endereco_m.group(1).strip() if endereco_m else titulo

        bairro = "Nao informado"
        m_bairro = re.search(r"(?:,\s*|\bem\s+)([A-Za-zÀ-ú' ]+?)\s*/\s*RJ", titulo, re.I)
        if m_bairro:
            bairro = re.sub(r"^(em|na|no)\s+", "", m_bairro.group(1).strip(), flags=re.I)
        if normaliza(bairro) in OUTROS_MUNICIPIOS_RJ:
            continue  # outra cidade do estado, nao a capital
        bairro_norm = normaliza(bairro)

        modalidade_m = SOLEON_MODALIDADE_RE.search(bloco)
        modalidade = "Verificar edital"
        if modalidade_m:
            classe = modalidade_m.group(1)
            if "venda_direta" in classe:
                modalidade = "Venda direta"
            elif "extrajudicial" in classe:
                modalidade = "Extrajudicial (banco)"
            elif "judicial" in classe:
                modalidade = "Judicial"

        preco, preco_label = None, "Valor"
        pm = SOLEON_PRECO_LABEL_RE.search(bloco)
        if pm:
            preco_label = pm.group(1).strip() or "Valor"
            preco = parse_valor_br(pm.group(2))

        tipo_m = re.match(r"^([A-Za-zÀ-ú]+)", titulo)
        tipo = tipo_m.group(1) if tipo_m else "Nao informado"

        area_m = SOLEON_AREA_RE.search(bloco)
        area_m2 = parse_valor_br(area_m.group(1)) if area_m else None

        img_m = SOLEON_IMG_RE.search(bloco)
        imagem = img_m.group(1) if img_m else None

        imoveis.append({
            "id": f"soleon-{lote_id}",
            "fonte": fonte,
            "tipo": tipo,
            "cidade": cidade,
            "bairro": bairro,
            "bairro_norm": bairro_norm,
            "endereco": endereco,
            "preco": preco,
            "preco_label": preco_label,
            "desconto_pct": None,
            "data_leilao": "",
            "area_m2": area_m2,
            "quartos": None,
            "vagas": None,
            "ocupacao": "Verificar edital",
            "comitente": None,
            "modalidade": modalidade,
            "pracas": None,
            "etapas": [],
            "status_leilao": "",
            "imagem_url": imagem,
            "pagina_url": url,
            "no_corredor": bairro_norm in CORREDOR_BAIRROS,
        })
    return imoveis


def coletar_soleon(nome_fonte, base_url):
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    ids = buscar_eventos_soleon(session, base_url)
    todos = []
    for eid in ids:
        try:
            r = session.get(f"{base_url}/leilao/{eid}/lotes", timeout=30)
            if r.status_code == 200:
                todos += parse_cards_soleon(r.text, nome_fonte)
        except Exception:
            continue
    vistos, unicos = set(), []
    for im in todos:
        if im["id"] in vistos:
            continue
        vistos.add(im["id"])
        unicos.append(im)
    return unicos


# --------------------------------------------------------------------------------------
# Coleta - Rymer Leiloes (plataforma "Suporte Leiloes")
# --------------------------------------------------------------------------------------

RYMER_BUSCA_URL = "https://www.rymerleiloes.com.br/busca?categoria=imoveis"
RYMER_ARTICLE_START_RE = re.compile(r"<article>")
RYMER_HREF_RE = re.compile(r'<a href="(/oferta/leilao/imoveis/[^"]+)"')
RYMER_TITULO_RE = re.compile(r"<h3>([^<]+)</h3>")
RYMER_ENDERECO_RE = re.compile(r"<h3>[^<]+</h3>\s*<p>([^<]+)</p>")
RYMER_MODALIDADE_RE = re.compile(r'class="status-leilao[^"]*">\s*([^<]+?)\s*</span>')
RYMER_ETAPA_RE = re.compile(r"<p>(\d.\s*Leil.o):\s*([^<]+)</p>\s*<p>Lance inicial:\s*R\$\s*([\d.,]+)</p>")
RYMER_IMG_RE = re.compile(r'<img class="foto" src="([^"]+)"')
RYMER_AREA_RE = re.compile(r"(\d+[\d.,]*)\s*m.\s*(?:de\s*.rea\s*)?(?:constru.da|privativa|.til)", re.I)


def buscar_html_rymer():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    r = session.get(RYMER_BUSCA_URL, timeout=30)
    return r.text if r.status_code == 200 else ""


def parse_cards_rymer(html):
    starts = [m.start() for m in RYMER_ARTICLE_START_RE.finditer(html)]
    blocos = [
        html[starts[i]: starts[i + 1] if i + 1 < len(starts) else starts[i] + 2500]
        for i in range(len(starts))
    ]
    imoveis = []
    for bloco in blocos:
        href_m = RYMER_HREF_RE.search(bloco)
        if not href_m:
            continue
        url = "https://www.rymerleiloes.com.br" + href_m.group(1)
        lote_id_m = re.search(r"/id-(\d+)/", url)
        lote_id = lote_id_m.group(1) if lote_id_m else str(abs(hash(url)))

        titulo_m = RYMER_TITULO_RE.search(bloco)
        titulo = titulo_m.group(1).strip() if titulo_m else ""
        if not titulo:
            continue

        endereco_m = RYMER_ENDERECO_RE.search(bloco)
        endereco = endereco_m.group(1).strip().rstrip(".").rstrip(",") if endereco_m else titulo
        partes_end = [p.strip() for p in endereco.split(",") if p.strip()]
        ultimo = re.sub(r"\s*/\s*RJ$", "", partes_end[-1], flags=re.I).strip() if partes_end else ""
        # convencao comum: "Bairro/RJ" quando e' a capital, "Cidade/RJ" quando nao e'.
        if normaliza(ultimo) in OUTROS_MUNICIPIOS_RJ or normaliza(ultimo).startswith(tuple(OUTROS_MUNICIPIOS_RJ)):
            continue  # fora da cidade do Rio de Janeiro
        cidade = "Rio de Janeiro"
        bairro = ultimo if ultimo else "Nao informado"
        bairro_norm = normaliza(bairro)

        modalidade_m = RYMER_MODALIDADE_RE.search(bloco)
        modalidade_txt = modalidade_m.group(1).strip() if modalidade_m else ""
        modalidade = {
            "judicial": "Judicial", "extrajudicial": "Extrajudicial (banco)", "venda direta": "Venda direta",
        }.get(normaliza(modalidade_txt), "Verificar edital")

        etapas = []
        for label, data, valor in RYMER_ETAPA_RE.findall(bloco):
            etapas.append({"etapa": label.strip(), "data": data.strip(), "valor": parse_valor_br(valor)})
        preco = etapas[0]["valor"] if etapas else None
        preco_label = etapas[0]["etapa"] if etapas else "Lance inicial"
        data_leilao = etapas[0]["data"] if etapas else ""

        tipo_m = re.match(r"^([A-Za-zÀ-ú]+)", titulo)
        tipo = tipo_m.group(1) if tipo_m else "Nao informado"

        area_m = RYMER_AREA_RE.search(titulo) or RYMER_AREA_RE.search(bloco)
        area_m2 = parse_valor_br(area_m.group(1)) if area_m else None

        img_m = RYMER_IMG_RE.search(bloco)
        imagem = img_m.group(1) if img_m else None

        imoveis.append({
            "id": f"rymer-{lote_id}",
            "fonte": "Rymer Leiloes",
            "tipo": tipo,
            "cidade": cidade,
            "bairro": bairro,
            "bairro_norm": bairro_norm,
            "endereco": endereco,
            "preco": preco,
            "preco_label": preco_label,
            "desconto_pct": None,
            "data_leilao": data_leilao,
            "area_m2": area_m2,
            "quartos": None,
            "vagas": None,
            "ocupacao": "Verificar edital",
            "comitente": None,
            "modalidade": modalidade,
            "pracas": str(len(etapas)) if etapas else None,
            "etapas": etapas,
            "status_leilao": "",
            "imagem_url": imagem,
            "pagina_url": url,
            "no_corredor": bairro_norm in CORREDOR_BAIRROS,
        })

    vistos, unicos = set(), []
    for im in imoveis:
        if im["id"] in vistos:
            continue
        vistos.add(im["id"])
        unicos.append(im)
    return unicos


# --------------------------------------------------------------------------------------
# Coleta - Gustavo Lourenco Leiloeiro (plataforma "Suporte Leiloes")
# --------------------------------------------------------------------------------------

GUSTAVO_URL = "https://gustavoleiloeiro.com.br/?tipo=todos"
GUSTAVO_ARTICLE_START_RE = re.compile(r"<article>")
GUSTAVO_HREF_RE = re.compile(r'<a href="(/eventos/leilao/[^"]+)"')
GUSTAVO_NOME_RE = re.compile(r"<h3>([^<]+)</h3>")
GUSTAVO_CIDADE_RE = re.compile(r'class="p1">\s*([^<]+?)\s*</p>')
GUSTAVO_AREA_RE = re.compile(r'class="p2">\s*([\d.,]+)\s*m')
GUSTAVO_BAIRRO_RE = re.compile(r'class="p3">\s*([^<]+?)\s*</p>')
GUSTAVO_BAIRRO_TITULO_RE = re.compile(r"\b(?:EM|NA|NO)\s+([A-ZÀ-Ú][A-ZÀ-Ú' -]*?)\s*/\s*RJ", re.I)
GUSTAVO_AREA_TITULO_RE = re.compile(r"(\d+[\d.,]*)\s*M", re.I)
GUSTAVO_PRECO_RE = re.compile(r"Lance inicial:\s*R\$\s*([\d.,]+)")
GUSTAVO_IMG_RE = re.compile(r'<img src="([^"]+)"')


def buscar_html_gustavo():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    r = session.get(GUSTAVO_URL, timeout=30)
    return r.text if r.status_code == 200 else ""


def parse_cards_gustavo(html):
    starts = [m.start() for m in GUSTAVO_ARTICLE_START_RE.finditer(html)]
    blocos = [
        html[starts[i]: starts[i + 1] if i + 1 < len(starts) else starts[i] + 2200]
        for i in range(len(starts))
    ]
    imoveis = []
    for bloco in blocos:
        href_m = GUSTAVO_HREF_RE.search(bloco)
        if not href_m:
            continue
        url = "https://gustavoleiloeiro.com.br" + href_m.group(1)
        lote_id_m = re.search(r"leilao/(\d+)|lote/(\d+)", href_m.group(1))
        lote_id = next((g for g in (lote_id_m.groups() if lote_id_m else []) if g), None) or str(abs(hash(url)))

        nome_m = GUSTAVO_NOME_RE.search(bloco)
        nome = nome_m.group(1).strip() if nome_m else ""
        if not nome:
            continue

        cidade_m = GUSTAVO_CIDADE_RE.search(bloco)
        bairro_m = GUSTAVO_BAIRRO_RE.search(bloco)
        if cidade_m:
            cidade = cidade_m.group(1).strip()
            if "rio de janeiro" not in normaliza(cidade):
                continue
            bairro = bairro_m.group(1).strip() if bairro_m else "Nao informado"
        else:
            # sem campos explicitos: bairro/cidade vem do titulo ("... EM BAIRRO/RJ")
            bt_m = GUSTAVO_BAIRRO_TITULO_RE.search(nome)
            bairro = bt_m.group(1).strip().title() if bt_m else "Nao informado"
            if normaliza(bairro) in OUTROS_MUNICIPIOS_RJ or not bt_m:
                continue  # ou e' outra cidade do RJ, ou nao deu pra confirmar que e' Rio de Janeiro
            cidade = "Rio de Janeiro"
        bairro_norm = normaliza(bairro)

        area_m = GUSTAVO_AREA_RE.search(bloco) or GUSTAVO_AREA_TITULO_RE.search(nome)
        area_m2 = parse_valor_br(area_m.group(1)) if area_m else None

        preco_m = GUSTAVO_PRECO_RE.search(bloco)
        preco = parse_valor_br(preco_m.group(1)) if preco_m else None

        img_m = GUSTAVO_IMG_RE.search(bloco)
        imagem = img_m.group(1) if img_m else None

        imoveis.append({
            "id": f"gustavo-{lote_id}",
            "fonte": "Gustavo Lourenco",
            "tipo": "Nao informado",
            "cidade": cidade,
            "bairro": bairro,
            "bairro_norm": bairro_norm,
            "endereco": nome,
            "preco": preco,
            "preco_label": "Lance inicial",
            "desconto_pct": None,
            "data_leilao": "",
            "area_m2": area_m2,
            "quartos": None,
            "vagas": None,
            "ocupacao": "Verificar edital",
            "comitente": None,
            "modalidade": "Verificar edital",
            "pracas": None,
            "etapas": [],
            "status_leilao": "",
            "imagem_url": imagem,
            "pagina_url": url,
            "no_corredor": bairro_norm in CORREDOR_BAIRROS,
        })

    vistos, unicos = set(), []
    for im in imoveis:
        if im["id"] in vistos:
            continue
        vistos.add(im["id"])
        unicos.append(im)
    return unicos


# --------------------------------------------------------------------------------------
# Enriquecimento - custos, comparacao de mercado, semaforo de risco
# --------------------------------------------------------------------------------------

def enriquecer(imovel):
    preco = imovel["preco"] or 0
    area = imovel["area_m2"]
    bairro_norm = imovel["bairro_norm"]

    preco_m2 = round(preco / area, 2) if area and preco else None

    benchmark = BENCHMARKS_M2.get(bairro_norm)
    benchmark_fonte = "bairro"
    if benchmark is None:
        benchmark = MEDIA_CIDADE_M2
        benchmark_fonte = "media da cidade (sem numero especifico do bairro)"

    desconto_vs_mercado_pct = None
    if preco_m2:
        desconto_vs_mercado_pct = round((1 - preco_m2 / benchmark) * 100, 1)

    laudemio_possivel = bairro_norm in BAIRROS_LAUDEMIO_POSSIVEL

    pct_custos = COMISSAO_LEILOEIRO_PCT + ITBI_RJ_PCT + CARTORIO_PCT
    if laudemio_possivel:
        pct_custos += LAUDEMIO_PCT

    custo_total_estimado = round(preco * (1 + pct_custos / 100), 2) if preco else None

    # semaforo de risco (heuristica simples e transparente)
    if imovel["modalidade"] == "Venda direta":
        risco = "verde"
        risco_label = "Menor risco: venda direta (negociacao direta, sem disputa de leilao)"
    elif imovel["modalidade"] == "Extrajudicial (banco)" and imovel["ocupacao"] == "Desocupado":
        risco = "verde"
        risco_label = "Menor risco: extrajudicial e desocupado"
    elif imovel["modalidade"] == "Extrajudicial (banco)":
        risco = "amarelo"
        risco_label = "Risco medio: extrajudicial, ocupacao a confirmar"
    elif imovel["ocupacao"] == "Desocupado":
        risco = "amarelo"
        risco_label = "Risco medio: desocupado, mas modalidade a confirmar"
    else:
        risco = "vermelho"
        risco_label = "Risco alto: confirmar modalidade e ocupacao no edital antes de tudo"

    endereco_busca = f"{imovel['endereco']}, {imovel['bairro']}, Rio de Janeiro, RJ".strip(", ")

    imovel.update({
        "preco_m2": preco_m2,
        "benchmark_m2": benchmark,
        "benchmark_fonte": benchmark_fonte,
        "desconto_vs_mercado_pct": desconto_vs_mercado_pct,
        "laudemio_possivel": laudemio_possivel,
        "custo_total_estimado": custo_total_estimado,
        "pct_custos_extra": round(pct_custos, 1),
        "risco": risco,
        "risco_label": risco_label,
        "link_maps": "https://www.google.com/maps/search/" + requests.utils.quote(endereco_busca),
        "link_streetview": "https://www.google.com/maps/search/?api=1&query=" + requests.utils.quote(endereco_busca) + "&layer=c",
        "link_zap_predio": "https://www.zapimoveis.com.br/aluguel/imoveis/rj+rio-de-janeiro/?transacao=aluguel&q=" + requests.utils.quote(imovel["endereco"] or imovel["bairro"]),
        "link_olx_predio": "https://www.olx.com.br/imoveis/aluguel/estado-rj?q=" + requests.utils.quote(imovel["endereco"] or imovel["bairro"]),
        "link_google_fotos": "https://www.google.com/search?tbm=isch&q=" + requests.utils.quote(endereco_busca),
    })
    return imovel


# --------------------------------------------------------------------------------------
# Geracao do HTML
# --------------------------------------------------------------------------------------

HTML_TEMPLATE = r"""<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow, noarchive">
<title>Leiloes de Imoveis - Tijuca a Copacabana</title>
<style>
  :root {
    color-scheme: light dark;
    --bg: #f6f5f2;
    --card-bg: #ffffff;
    --text: #1c1b19;
    --text-dim: #6b6862;
    --border: #e4e1da;
    --accent: #8a3b2f;
    --accent-2: #2f6b4f;
    --verde: #2f8f5b;
    --amarelo: #b8860b;
    --vermelho: #b23b3b;
    --chip-bg: #f0eee8;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #16151a;
      --card-bg: #201f26;
      --text: #ecebe8;
      --text-dim: #9d9a93;
      --border: #34323b;
      --accent: #e0a08a;
      --accent-2: #7fd6ab;
      --verde: #5fd48b;
      --amarelo: #e0b84a;
      --vermelho: #f08a8a;
      --chip-bg: #2a2932;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 0;
    background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.5;
  }
  header {
    padding: 28px 20px 18px;
    max-width: 1100px; margin: 0 auto;
  }
  header h1 { font-size: 1.5rem; margin: 0 0 6px; }
  header p { color: var(--text-dim); margin: 4px 0; font-size: 0.92rem; }
  .meta-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
  .meta-chip {
    background: var(--chip-bg); border: 1px solid var(--border);
    border-radius: 999px; padding: 4px 12px; font-size: 0.8rem; color: var(--text-dim);
  }
  .btn-atualizar {
    cursor: pointer; font-family: inherit; color: var(--accent-2); border-color: var(--accent-2);
    font-weight: 600;
  }
  .btn-atualizar:disabled { opacity: 0.6; cursor: default; }
  .btn-atualizar:hover:not(:disabled) { background: var(--accent-2); color: #fff; }
  .status-atualizar { font-size: 0.78rem; color: var(--text-dim); min-height: 1.2em; margin: 6px 0 0; }
  .container { max-width: 1100px; margin: 0 auto; padding: 0 20px 60px; }

  .filtros {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 20px 24px;
    background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 12px; padding: 18px 20px; margin-bottom: 20px;
  }
  .filtro-grupo { display: flex; flex-direction: column; gap: 10px; min-width: 0; }
  .filtro-grupo.wide { grid-column: 1 / -1; }
  .filtro-grupo.wide .subgrupos { display: flex; gap: 28px; flex-wrap: wrap; }
  .filtro-grupo.wide .subgrupos > label { flex: 1 1 220px; max-width: 380px; }
  .filtro-grupo-titulo {
    font-size: 0.68rem; text-transform: uppercase; letter-spacing: .05em;
    color: var(--text-dim); font-weight: 700;
  }
  .filtros label { display: flex; flex-direction: column; gap: 4px; font-size: 0.78rem; color: var(--text-dim); }
  .filtros select, .filtros input {
    padding: 8px 10px; border-radius: 8px; border: 1px solid var(--border);
    background: var(--bg); color: var(--text); font-size: 0.9rem;
  }
  #contagem { font-size: 0.85rem; color: var(--text-dim); margin: 4px 0 16px; }

  .aviso-vazio {
    background: var(--chip-bg); border: 1px dashed var(--border); border-radius: 12px;
    padding: 22px; text-align: center; color: var(--text-dim); font-size: 0.92rem;
  }

  .grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
  }
  .card {
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px;
    overflow: hidden; display: flex; flex-direction: column;
  }
  .card img { width: 100%; height: 170px; object-fit: cover; display: block; background: var(--chip-bg); }
  .card .no-img {
    width: 100%; height: 170px; display: flex; align-items: center; justify-content: center;
    background: var(--chip-bg); color: var(--text-dim); font-size: 0.82rem; text-align: center; padding: 10px;
  }
  .card-body { padding: 14px 16px 16px; display: flex; flex-direction: column; gap: 8px; flex: 1; }
  .badges { display: flex; flex-wrap: wrap; gap: 6px; }
  .badge { font-size: 0.72rem; padding: 3px 9px; border-radius: 999px; border: 1px solid var(--border); color: var(--text-dim); }
  .badge.corredor { background: var(--accent); color: #fff; border-color: var(--accent); }
  .badge.risco-verde { background: color-mix(in srgb, var(--verde) 20%, transparent); color: var(--verde); border-color: var(--verde); }
  .badge.risco-amarelo { background: color-mix(in srgb, var(--amarelo) 20%, transparent); color: var(--amarelo); border-color: var(--amarelo); }
  .badge.risco-vermelho { background: color-mix(in srgb, var(--vermelho) 20%, transparent); color: var(--vermelho); border-color: var(--vermelho); }

  .card h3 { margin: 2px 0 0; font-size: 1.02rem; }
  .card .endereco { font-size: 0.85rem; color: var(--text-dim); }
  .preco-linha { display: flex; align-items: baseline; gap: 8px; margin-top: 2px; }
  .preco-linha .valor { font-size: 1.3rem; font-weight: 700; color: var(--accent); }
  .preco-linha .label { font-size: 0.75rem; color: var(--text-dim); }

  .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 12px; font-size: 0.82rem; margin-top: 4px; }
  .info-grid .k { color: var(--text-dim); }
  .info-grid .v { font-weight: 600; }
  .v.positivo { color: var(--verde); }
  .v.negativo { color: var(--vermelho); }

  .custo-total {
    margin-top: 4px; padding: 8px 10px; background: var(--chip-bg); border-radius: 8px;
    font-size: 0.8rem; color: var(--text-dim);
  }
  .custo-total b { color: var(--text); }

  .links-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
  .links-row a {
    font-size: 0.76rem; text-decoration: none; color: var(--accent-2);
    border: 1px solid var(--border); padding: 5px 9px; border-radius: 8px;
  }
  .links-row a:hover { border-color: var(--accent-2); }
  .ver-anuncio {
    margin-top: auto; display: block; text-align: center; padding: 9px;
    background: var(--accent); color: #fff !important; border-radius: 8px; font-weight: 600;
    font-size: 0.85rem; text-decoration: none;
  }

  section.manual {
    margin-top: 40px; background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 14px; padding: 20px;
  }
  section.manual h2 { font-size: 1.1rem; margin-top: 0; }
  section.manual p { color: var(--text-dim); font-size: 0.88rem; }
  .fontes-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; margin-top: 12px; }
  .fontes-grid a {
    display: block; padding: 10px 14px; border: 1px solid var(--border); border-radius: 10px;
    text-decoration: none; color: var(--text); font-size: 0.85rem; background: var(--bg);
  }
  .fontes-grid a:hover { border-color: var(--accent); }

  .tabs { display: flex; gap: 8px; max-width: 1100px; margin: 0 auto 20px; padding: 0 20px; }
  .tab-btn {
    padding: 9px 18px; border-radius: 999px; border: 1px solid var(--border);
    background: var(--card-bg); color: var(--text-dim); cursor: pointer;
    font-size: 0.85rem; font-weight: 600; font-family: inherit;
  }
  .tab-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
  .tab-content[hidden] { display: none; }

  .manual-article { max-width: 780px; }
  .manual-article h2 { font-size: 1.3rem; margin: 0 0 4px; }
  .manual-article > p.lead { color: var(--text-dim); margin-top: 0; }
  .manual-article h3 { font-size: 1.05rem; margin: 28px 0 8px; padding-top: 14px; border-top: 1px solid var(--border); }
  .manual-article h4 { font-size: 0.92rem; margin: 16px 0 6px; }
  .manual-article p, .manual-article li { color: var(--text-dim); font-size: 0.9rem; }
  .manual-article strong { color: var(--text); }
  .manual-article table { width: 100%; border-collapse: collapse; margin: 10px 0 16px; font-size: 0.84rem; }
  .manual-article th, .manual-article td { text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--border); }
  .manual-article th { color: var(--text); }
  .semaforo-legenda { display: flex; flex-direction: column; gap: 8px; margin: 10px 0 16px; }
  .semaforo-legenda .item { display: flex; gap: 10px; align-items: baseline; font-size: 0.88rem; }
  .semaforo-legenda .dot { width: 12px; height: 12px; border-radius: 50%; flex: none; margin-top: 4px; }
  .dot.verde { background: var(--verde); } .dot.amarelo { background: var(--amarelo); } .dot.vermelho { background: var(--vermelho); }
  .step-list { counter-reset: step; list-style: none; padding: 0; margin: 10px 0 16px; }
  .step-list li { counter-increment: step; margin-bottom: 12px; padding-left: 36px; position: relative; }
  .step-list li::before {
    content: counter(step); position: absolute; left: 0; top: 0; width: 24px; height: 24px;
    border-radius: 50%; background: var(--accent); color: #fff; font-size: 0.72rem;
    display: flex; align-items: center; justify-content: center; font-weight: 700;
  }
  .bairros-tags { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0 16px; }
  .bairros-tags span { background: var(--chip-bg); border: 1px solid var(--border); border-radius: 999px; padding: 3px 11px; font-size: 0.78rem; color: var(--text-dim); }

  /* --- combo multi-select (bairro / tipo) --- */
  .combo { position: relative; }
  .combo-btn {
    width: 100%; text-align: left; padding: 8px 10px; border-radius: 8px; border: 1px solid var(--border);
    background: var(--bg); color: var(--text); font-size: 0.9rem; cursor: pointer; font-family: inherit;
  }
  .combo-panel {
    display: none; position: absolute; z-index: 20; top: calc(100% + 4px); left: 0; min-width: 240px;
    max-height: 320px; overflow-y: auto; background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 10px; padding: 8px; box-shadow: 0 8px 24px rgba(0,0,0,.18);
  }
  .combo.open .combo-panel { display: block; }
  .combo-search {
    width: 100%; padding: 7px 9px; margin-bottom: 6px; border-radius: 6px; border: 1px solid var(--border);
    background: var(--bg); color: var(--text); font-size: 0.85rem;
  }
  .combo-option { display: flex; align-items: center; gap: 8px; padding: 5px 6px; border-radius: 6px; font-size: 0.85rem; cursor: pointer; }
  .combo-option:hover { background: var(--chip-bg); }
  .combo-option input { margin: 0; }
  .combo-actions { display: flex; justify-content: space-between; margin-top: 6px; padding-top: 6px; border-top: 1px solid var(--border); }
  .combo-actions button {
    font-size: 0.75rem; color: var(--accent-2); background: none; border: none; cursor: pointer; padding: 2px 4px; font-family: inherit;
  }

  /* --- faixa de preco (slider duplo) --- */
  .range-wrap { position: relative; height: 34px; margin-top: 6px; }
  .range-wrap input[type="range"] {
    position: absolute; width: 100%; top: 10px; margin: 0; -webkit-appearance: none; appearance: none;
    background: transparent; pointer-events: none;
  }
  .range-wrap input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none; pointer-events: auto; width: 15px; height: 15px; border-radius: 50%;
    background: var(--accent); cursor: pointer; border: 2px solid var(--card-bg);
  }
  .range-wrap input[type="range"]::-moz-range-thumb {
    pointer-events: auto; width: 15px; height: 15px; border-radius: 50%;
    background: var(--accent); cursor: pointer; border: 2px solid var(--card-bg);
  }
  .range-wrap input[type="range"]::-webkit-slider-runnable-track { background: transparent; }
  .range-track { position: absolute; top: 15px; left: 0; right: 0; height: 4px; background: var(--border); border-radius: 2px; }
  .range-track-fill { position: absolute; top: 15px; height: 4px; background: var(--accent); border-radius: 2px; }
  .range-inputs { display: flex; gap: 6px; margin-top: 4px; }
  .range-inputs input[type="number"] {
    width: 100%; padding: 6px 7px; border-radius: 6px; border: 1px solid var(--border);
    background: var(--bg); color: var(--text); font-size: 0.8rem;
  }

  /* --- tabela completa --- */
  .tabela-toolbar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; }
  .btn-exportar {
    background: var(--accent-2); color: #fff; border: none; padding: 9px 16px; border-radius: 8px;
    font-size: 0.85rem; font-weight: 600; cursor: pointer; font-family: inherit;
  }
  .btn-exportar:hover { opacity: 0.9; }
  .tabela-scroll { overflow-x: auto; border: 1px solid var(--border); border-radius: 12px; }
  table.tabela-imoveis { width: 100%; border-collapse: collapse; font-size: 0.82rem; white-space: nowrap; }
  table.tabela-imoveis th, table.tabela-imoveis td { padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--border); }
  table.tabela-imoveis thead th {
    background: var(--chip-bg); position: sticky; top: 0; cursor: pointer; user-select: none; color: var(--text);
  }
  table.tabela-imoveis thead th:hover { color: var(--accent); }
  table.tabela-imoveis tbody tr:hover { background: var(--chip-bg); }
  table.tabela-imoveis td.num { text-align: right; }
  table.tabela-imoveis .col-fixa {
    position: sticky; left: 0; background: var(--card-bg); z-index: 5;
    box-shadow: 2px 0 4px rgba(0,0,0,.06);
  }
  table.tabela-imoveis thead .col-fixa { background: var(--chip-bg); z-index: 6; cursor: default; }
  table.tabela-imoveis tbody tr:hover .col-fixa { background: var(--chip-bg); }
  .btn-abrir {
    display: inline-block; background: var(--accent); color: #fff !important; text-decoration: none;
    padding: 5px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 600;
  }
  table.tabela-imoveis a { color: var(--accent-2); text-decoration: none; }

  footer { text-align: center; color: var(--text-dim); font-size: 0.78rem; padding: 30px 20px; }
</style>
</head>
<body>
<header>
  <h1>Leiloes de imoveis - corredor Tijuca &rarr; Lapa &rarr; Catete &rarr; Copacabana</h1>
  <p>Painel gerado automaticamente a partir de __TOTAL_FONTES__ fontes (__NOMES_FONTES__). Para morar &mdash; nao e ferramenta de investimento.</p>
  <div class="meta-row">
    <span class="meta-chip" id="chip-gerado">Gerado em __DATA_GERACAO__</span>
    <span class="meta-chip" id="chip-total">__TOTAL_IMOVEIS__ imoveis no Rio de Janeiro hoje</span>
    <span class="meta-chip">__TOTAL_CORREDOR__ no corredor de interesse</span>
    <button class="meta-chip btn-atualizar" id="btn-atualizar" onclick="atualizarDados()">&#8635; Atualizar</button>
  </div>
  <p id="status-atualizar" class="status-atualizar"></p>
</header>

<div class="tabs">
  <button class="tab-btn active" data-tab="imoveis" onclick="mudarAba('imoveis')">Imoveis em leilao</button>
  <button class="tab-btn" data-tab="tabela" onclick="mudarAba('tabela')">Tabela completa</button>
  <button class="tab-btn" data-tab="manual" onclick="mudarAba('manual')">Como funciona (manual)</button>
</div>

<div class="container">

  <div class="filtros">
    <div class="filtro-grupo">
      <span class="filtro-grupo-titulo">Onde</span>
      <label>Bairro
        <div class="combo" id="combo-bairro">
          <button type="button" class="combo-btn" id="combo-bairro-btn">Todos</button>
          <div class="combo-panel">
            <input type="text" class="combo-search" id="combo-bairro-search" placeholder="Digite o bairro...">
            <div id="combo-bairro-options"></div>
            <div class="combo-actions">
              <button type="button" onclick="comboLimpar('bairro')">Limpar</button>
              <button type="button" onclick="comboFechar('bairro')">Aplicar</button>
            </div>
          </div>
        </div>
      </label>
      <label>So o corredor de interesse
        <select id="f-corredor">
          <option value="1">Sim (Tijuca-Copacabana)</option>
          <option value="0">Nao, mostrar Rio todo</option>
        </select>
      </label>
    </div>

    <div class="filtro-grupo">
      <span class="filtro-grupo-titulo">O que</span>
      <label>Tipo de imovel
        <div class="combo" id="combo-tipo">
          <button type="button" class="combo-btn" id="combo-tipo-btn">Todos</button>
          <div class="combo-panel">
            <input type="text" class="combo-search" id="combo-tipo-search" placeholder="Digite o tipo...">
            <div id="combo-tipo-options"></div>
            <div class="combo-actions">
              <button type="button" onclick="comboLimpar('tipo')">Limpar</button>
              <button type="button" onclick="comboFechar('tipo')">Aplicar</button>
            </div>
          </div>
        </div>
      </label>
      <label>Vagas de garagem
        <select id="f-vagas">
          <option value="">Qualquer</option>
          <option value="1">1+</option>
          <option value="2">2+</option>
          <option value="3">3+</option>
        </select>
      </label>
    </div>

    <div class="filtro-grupo wide">
      <span class="filtro-grupo-titulo">Quanto</span>
      <div class="subgrupos">
        <label>Faixa de preco (arraste ou digite)
          <div class="range-wrap" id="range-preco">
            <div class="range-track"></div>
            <div class="range-track-fill" id="range-preco-fill"></div>
            <input type="range" id="range-preco-min" min="0" max="1" step="1">
            <input type="range" id="range-preco-max" min="0" max="1" step="1">
          </div>
          <div class="range-inputs">
            <input type="text" inputmode="numeric" id="f-preco-min" placeholder="Min R$">
            <input type="text" inputmode="numeric" id="f-preco-max" placeholder="Max R$">
          </div>
        </label>
        <label>Metragem (m2)
          <div class="range-inputs">
            <input type="text" inputmode="numeric" id="f-area-min" placeholder="Min">
            <input type="text" inputmode="numeric" id="f-area-max" placeholder="Max">
          </div>
        </label>
      </div>
    </div>

    <div class="filtro-grupo">
      <span class="filtro-grupo-titulo">Situacao</span>
      <label>Ocupacao
        <select id="f-ocupacao">
          <option value="">Todas</option>
          <option value="Desocupado">Desocupado</option>
          <option value="Verificar edital">Verificar edital</option>
        </select>
      </label>
      <label>Risco
        <select id="f-risco">
          <option value="">Todos</option>
          <option value="verde">Verde</option>
          <option value="amarelo">Amarelo</option>
          <option value="vermelho">Vermelho</option>
        </select>
      </label>
      <label>Fonte
        <select id="f-fonte"><option value="">Todas</option></select>
      </label>
    </div>

    <div class="filtro-grupo">
      <span class="filtro-grupo-titulo">Exibicao</span>
      <label>Ordenar por
        <select id="f-ordem">
          <option value="corredor">Corredor primeiro</option>
          <option value="desconto">Maior desconto vs. mercado</option>
          <option value="preco">Menor preco</option>
          <option value="data">Data do leilao</option>
        </select>
      </label>
    </div>
  </div>

  <div id="tab-imoveis" class="tab-content">
    <div id="contagem"></div>
    <div id="lista"></div>
  </div>

  <div id="tab-tabela" class="tab-content" hidden>
    <div class="tabela-toolbar">
      <div id="contagem-tabela"></div>
      <button class="btn-exportar" onclick="exportarExcel()">Exportar para Excel (.xls)</button>
    </div>
    <div class="tabela-scroll">
      <table class="tabela-imoveis" id="tabela-imoveis">
        <thead id="tabela-head"></thead>
        <tbody id="tabela-body"></tbody>
      </table>
    </div>
  </div>

  <div id="tab-manual" class="tab-content manual-article" hidden>
    __MANUAL_HTML__
  </div>

  <footer>
    Dados de leilao mudam quase todo dia &mdash; rode <code>python coletor.py</code> de novo para atualizar.
    Numeros de referencia de R$/m2 sao estimativas de mercado (ago/2026), nao substituem avaliacao propria.
    Sempre leia o edital completo e confira a matricula no cartorio antes de dar lance.
  </footer>
</div>

<script>
function mudarAba(nome) {
  document.querySelectorAll('.tab-content').forEach(el => el.hidden = el.id !== 'tab-' + nome);
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.toggle('active', el.dataset.tab === nome));
}

let DADOS = __DADOS_JSON__;
const GERADO_EM_EMBUTIDO = "__DATA_GERACAO__";

const fmtBRL = v => v == null ? "-" : v.toLocaleString('pt-BR', {style:'currency', currency:'BRL', maximumFractionDigits:0});
const fmtNum = v => v == null ? "-" : v.toLocaleString('pt-BR', {maximumFractionDigits:0});

// pontos de milhar nos campos digitaveis (Min/Max de preco e metragem)
function desformatarMilhar(s) {
  return (s || "").replace(/\./g, "").replace(/[^\d]/g, "");
}
function formatarCampoMilhar(input) {
  const raw = desformatarMilhar(input.value);
  input.value = raw === "" ? "" : Number(raw).toLocaleString('pt-BR');
}
function valorCampoMilhar(id) {
  const raw = desformatarMilhar(document.getElementById(id).value);
  return raw === "" ? null : Number(raw);
}
function ligarFormatoMilhar(id) {
  const el = document.getElementById(id);
  el.addEventListener('input', () => {
    const raw = desformatarMilhar(el.value);
    el.value = raw === "" ? "" : Number(raw).toLocaleString('pt-BR');
  });
}

function normalizaJs(s) {
  return (s || "").toString().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}
// distancia de edicao simples (tolera 1-2 erros de digitacao)
function levenshtein(a, b) {
  if (a === b) return 0;
  const m = a.length, n = b.length;
  if (!m) return n; if (!n) return m;
  let prev = Array.from({length: n + 1}, (_, i) => i);
  for (let i = 1; i <= m; i++) {
    let cur = [i];
    for (let j = 1; j <= n; j++) {
      cur[j] = a[i - 1] === b[j - 1] ? prev[j - 1] : 1 + Math.min(prev[j - 1], prev[j], cur[j - 1]);
    }
    prev = cur;
  }
  return prev[n];
}
function combinaTexto(query, alvo) {
  const q = normalizaJs(query), t = normalizaJs(alvo);
  if (!q) return true;
  if (t.includes(q)) return true;
  // tolera erro de digitacao: compara com janelas do tamanho da query dentro do alvo
  const tol = q.length <= 4 ? 1 : 2;
  if (levenshtein(q, t.slice(0, q.length)) <= tol) return true;
  return t.split(/[ -]/).some(palavra => levenshtein(q, palavra.slice(0, q.length)) <= tol);
}

function riscoLabel(r) { return {verde:'Verde', amarelo:'Amarelo', vermelho:'Vermelho'}[r] || r; }

// --------------------- combos multi-select (bairro / tipo) ---------------------
const CORREDOR_ORDEM = __CORREDOR_JSON__;
const combos = {
  bairro: { valores: new Set(), selecionados: new Set() },
  tipo: { valores: new Set(), selecionados: new Set() },
};

function montarValoresCombo() {
  CORREDOR_ORDEM.forEach(b => combos.bairro.valores.add(b));
  DADOS.forEach(d => { if (d.bairro) combos.bairro.valores.add(d.bairro); if (d.tipo) combos.tipo.valores.add(d.tipo); });
}

function renderCombo(nome) {
  const termo = document.getElementById(`combo-${nome}-search`).value;
  const cont = document.getElementById(`combo-${nome}-options`);
  const valores = [...combos[nome].valores].sort((a, b) => a.localeCompare(b, 'pt-BR'));
  const filtrados = valores.filter(v => combinaTexto(termo, v));
  cont.innerHTML = filtrados.map(v => {
    const id = `chk-${nome}-${v.replace(/[^a-zA-Z0-9]/g, '')}`;
    const marcado = combos[nome].selecionados.has(v);
    return `<label class="combo-option" for="${id}">
      <input type="checkbox" id="${id}" value="${v}" ${marcado ? 'checked' : ''} onchange="comboToggle('${nome}', this.value, this.checked)">
      ${v}
    </label>`;
  }).join('') || `<div style="padding:6px;font-size:0.82rem;color:var(--text-dim)">Nada encontrado &mdash; confira a digitacao.</div>`;
}

function comboAtualizarBotao(nome) {
  const btn = document.getElementById(`combo-${nome}-btn`);
  const sel = combos[nome].selecionados;
  btn.textContent = sel.size === 0 ? 'Todos' : (sel.size === 1 ? [...sel][0] : `${sel.size} selecionados`);
}

function comboToggle(nome, valor, marcado) {
  if (marcado) combos[nome].selecionados.add(valor); else combos[nome].selecionados.delete(valor);
  comboAtualizarBotao(nome);
  aplicarFiltros();
}
function comboLimpar(nome) {
  combos[nome].selecionados.clear();
  renderCombo(nome);
  comboAtualizarBotao(nome);
  aplicarFiltros();
}
function comboFechar(nome) {
  document.getElementById(`combo-${nome}`).classList.remove('open');
}

['bairro', 'tipo'].forEach(nome => {
  document.getElementById(`combo-${nome}-btn`).addEventListener('click', () => {
    const el = document.getElementById(`combo-${nome}`);
    const abrir = !el.classList.contains('open');
    document.querySelectorAll('.combo.open').forEach(c => c.classList.remove('open'));
    if (abrir) { el.classList.add('open'); renderCombo(nome); document.getElementById(`combo-${nome}-search`).focus(); }
  });
  document.getElementById(`combo-${nome}-search`).addEventListener('input', () => renderCombo(nome));
});
document.addEventListener('click', (ev) => {
  document.querySelectorAll('.combo.open').forEach(c => { if (!c.contains(ev.target)) c.classList.remove('open'); });
});

// --------------------- faixa de preco (slider duplo + inputs) ---------------------
let precoMin = 0, precoMax = 1;
function initRangePreco() {
  const precos = DADOS.map(d => d.preco).filter(v => v != null);
  precoMin = precos.length ? Math.min(...precos) : 0;
  precoMax = precos.length ? Math.max(...precos) : 1;
  const rMin = document.getElementById('range-preco-min');
  const rMax = document.getElementById('range-preco-max');
  [rMin, rMax].forEach(r => { r.min = precoMin; r.max = precoMax; });
  rMin.value = precoMin; rMax.value = precoMax;
  document.getElementById('f-preco-min').placeholder = `Min (${fmtBRL(precoMin)})`;
  document.getElementById('f-preco-max').placeholder = `Max (${fmtBRL(precoMax)})`;
  atualizarRangeVisual();
}
function atualizarRangeVisual() {
  const rMin = document.getElementById('range-preco-min'), rMax = document.getElementById('range-preco-max');
  let vMin = Number(rMin.value), vMax = Number(rMax.value);
  if (vMin > vMax) { [vMin, vMax] = [vMax, vMin]; }
  const span = (precoMax - precoMin) || 1;
  const pctMin = ((vMin - precoMin) / span) * 100, pctMax = ((vMax - precoMin) / span) * 100;
  const fill = document.getElementById('range-preco-fill');
  fill.style.left = pctMin + '%'; fill.style.width = Math.max(0, pctMax - pctMin) + '%';
}
['range-preco-min', 'range-preco-max'].forEach(id => {
  document.getElementById(id).addEventListener('input', () => {
    atualizarRangeVisual();
    document.getElementById('f-preco-min').value = Number(document.getElementById('range-preco-min').value).toLocaleString('pt-BR');
    document.getElementById('f-preco-max').value = Number(document.getElementById('range-preco-max').value).toLocaleString('pt-BR');
    aplicarFiltros();
  });
});
['f-preco-min', 'f-preco-max'].forEach((id, i) => {
  ligarFormatoMilhar(id);
  document.getElementById(id).addEventListener('change', () => {
    const alvo = document.getElementById(i === 0 ? 'range-preco-min' : 'range-preco-max');
    const v = valorCampoMilhar(id);
    if (v != null) alvo.value = v;
    atualizarRangeVisual();
    aplicarFiltros();
  });
});
['f-area-min', 'f-area-max'].forEach(id => {
  ligarFormatoMilhar(id);
  document.getElementById(id).addEventListener('change', aplicarFiltros);
});

// --------------------- card (aba Imoveis) ---------------------
function card(d) {
  const img = d.imagem_url
    ? `<img src="${d.imagem_url}" alt="${d.endereco}" loading="lazy">`
    : `<div class="no-img">Sem foto do leiloeiro &mdash; use os links de fotos alternativas abaixo</div>`;

  const descMercado = d.desconto_vs_mercado_pct != null
    ? `<span class="v ${d.desconto_vs_mercado_pct > 0 ? 'positivo' : 'negativo'}">${d.desconto_vs_mercado_pct > 0 ? '-' : '+'}${Math.abs(d.desconto_vs_mercado_pct)}% vs bairro</span>`
    : `<span class="v">sem area p/ calcular</span>`;

  return `
  <div class="card">
    ${img}
    <div class="card-body">
      <div class="badges">
        ${d.no_corredor ? '<span class="badge corredor">Corredor</span>' : ''}
        <span class="badge risco-${d.risco}">${riscoLabel(d.risco)}</span>
        <span class="badge">${d.fonte}</span>
        <span class="badge">${d.modalidade}</span>
        <span class="badge">${d.ocupacao}</span>
      </div>
      <h3>${d.tipo} &mdash; ${d.bairro}</h3>
      <div class="endereco">${d.endereco || 'Endereco no anuncio'} &middot; ${d.cidade}</div>
      <div class="preco-linha">
        <span class="valor">${fmtBRL(d.preco)}</span>
        <span class="label">${d.preco_label}${d.desconto_pct ? ' &middot; ' + d.desconto_pct + '% abaixo da avaliacao' : ''}</span>
      </div>
      <div class="info-grid">
        <span class="k">Area</span><span class="v">${d.area_m2 ? d.area_m2 + ' m2' : '-'}</span>
        <span class="k">Vagas</span><span class="v">${d.vagas ?? '-'}</span>
        <span class="k">R$/m2</span><span class="v">${d.preco_m2 ? fmtBRL(d.preco_m2) : '-'}</span>
        <span class="k">Referencia do bairro</span><span class="v">${fmtBRL(d.benchmark_m2)}</span>
        <span class="k">vs. mercado</span>${descMercado}
        <span class="k">Leilao</span><span class="v">${d.data_leilao || '-'}</span>
        <span class="k">Comitente</span><span class="v">${d.comitente || 'Verificar edital'}</span>
      </div>
      <div class="custo-total">
        Custo total estimado (lance + ${d.pct_custos_extra}%: comissao, ITBI, cartorio${d.laudemio_possivel ? ', possivel laudemio' : ''}):
        <b>${fmtBRL(d.custo_total_estimado)}</b>
      </div>
      <div class="links-row">
        <a href="${d.link_maps}" target="_blank">Ver no mapa</a>
        <a href="${d.link_zap_predio}" target="_blank">Fotos: aluguel no bairro (ZAP)</a>
        <a href="${d.link_olx_predio}" target="_blank">Fotos: OLX</a>
        <a href="${d.link_google_fotos}" target="_blank">Google Imagens do endereco</a>
      </div>
      <a class="ver-anuncio" href="${d.pagina_url}" target="_blank">Ver anuncio original (${d.fonte}) &rarr;</a>
    </div>
  </div>`;
}

// --------------------- tabela completa ---------------------
const COLUNAS_TABELA = [
  {chave: 'fonte', label: 'Fonte'},
  {chave: 'tipo', label: 'Tipo'},
  {chave: 'bairro', label: 'Bairro'},
  {chave: 'endereco', label: 'Endereco'},
  {chave: 'area_m2', label: 'Area (m2)', num: true},
  {chave: 'vagas', label: 'Vagas', num: true},
  {chave: 'preco', label: 'Preco atual', num: true, money: true},
  {chave: 'preco_label', label: 'Etapa'},
  {chave: 'data_leilao', label: 'Data'},
  {chave: 'preco_m2', label: 'R$/m2', num: true, money: true},
  {chave: 'benchmark_m2', label: 'Ref. bairro R$/m2', num: true, money: true},
  {chave: 'desconto_vs_mercado_pct', label: '% vs mercado', num: true},
  {chave: 'custo_total_estimado', label: 'Custo total estimado', num: true, money: true},
  {chave: 'ocupacao', label: 'Ocupacao'},
  {chave: 'modalidade', label: 'Modalidade'},
  {chave: 'risco', label: 'Risco'},
  {chave: 'comitente', label: 'Comitente/Vendedor'},
];
let ordemTabela = {chave: 'desconto_vs_mercado_pct', dir: -1};

function renderTabelaHead() {
  const head = document.getElementById('tabela-head');
  head.innerHTML = '<tr><th class="col-fixa">Abrir</th>' + COLUNAS_TABELA.map(c =>
    `<th onclick="ordenarTabela('${c.chave}')">${c.label}${ordemTabela.chave === c.chave ? (ordemTabela.dir === 1 ? ' \u25b2' : ' \u25bc') : ''}</th>`
  ).join('') + '</tr>';
}
function ordenarTabela(chave) {
  ordemTabela.dir = (ordemTabela.chave === chave) ? -ordemTabela.dir : 1;
  ordemTabela.chave = chave;
  aplicarFiltros();
}
function renderTabela(lista) {
  renderTabelaHead();
  const body = document.getElementById('tabela-body');
  const contagem = document.getElementById('contagem-tabela');
  contagem.textContent = `${lista.length} imo${lista.length === 1 ? 'vel' : 'veis'}.`;
  body.innerHTML = lista.map(d => {
    const tds = COLUNAS_TABELA.map(c => {
      let v = d[c.chave];
      let texto = v == null || v === '' ? '-' : (c.money ? fmtBRL(v) : (c.num ? fmtNum(v) : v));
      if (c.chave === 'endereco' || c.chave === 'bairro') {
        texto = `<a href="${d.pagina_url}" target="_blank" title="Abrir anuncio original">${texto}</a>`;
      }
      return `<td class="${c.num ? 'num' : ''}">${texto}</td>`;
    }).join('');
    return `<tr><td class="col-fixa"><a class="btn-abrir" href="${d.pagina_url}" target="_blank">Abrir &rarr;</a></td>${tds}</tr>`;
  }).join('');
}

// --------------------- exportar Excel (.xls compativel, sem lib externa) ---------------------
function exportarExcel() {
  const lista = filtrarDados();
  const cabecalho = COLUNAS_TABELA.map(c => `<th>${c.label}</th>`).join('') + '<th>Link</th>';
  const linhas = lista.map(d => {
    const tds = COLUNAS_TABELA.map(c => {
      let v = d[c.chave];
      if (v == null || v === '') return '<td>-</td>';
      if (c.money) return `<td style="mso-number-format:'R\\$\\ \\#\\,\\#\\#0';text-align:right;">${v}</td>`;
      if (c.num) return `<td style="mso-number-format:'\\#\\,\\#\\#0';text-align:right;">${v}</td>`;
      return `<td style="mso-number-format:'\\@';">${String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;')}</td>`;
    }).join('');
    return `<tr>${tds}<td>${d.pagina_url}</td></tr>`;
  }).join('');

  const xml = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
  <head><meta charset="UTF-8">
  <!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet>
  <x:Name>Leiloes RJ</x:Name><x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions>
  </x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]-->
  <style>
    table { border-collapse: collapse; font-family: Calibri, Arial, sans-serif; }
    th { background: #8a3b2f; color: #ffffff; font-weight: bold; text-align: center; padding: 6px 10px; }
    td { padding: 5px 10px; text-align: center; border-bottom: 1px solid #e4e1da; }
  </style></head>
  <body><table><thead><tr>${cabecalho}</tr></thead><tbody>${linhas}</tbody></table></body></html>`;

  const blob = new Blob(['\ufeff' + xml], {type: 'application/vnd.ms-excel'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `leiloes-rj-${new Date().toISOString().slice(0,10)}.xls`;
  document.body.appendChild(a); a.click(); a.remove();
}

// --------------------- filtro unico (alimenta cards + tabela) ---------------------
function filtrarDados() {
  const ocupacao = document.getElementById('f-ocupacao').value;
  const risco = document.getElementById('f-risco').value;
  const fonte = document.getElementById('f-fonte').value;
  const soCorredor = document.getElementById('f-corredor').value === '1';
  const vagasMin = document.getElementById('f-vagas').value ? Number(document.getElementById('f-vagas').value) : null;
  const areaMin = valorCampoMilhar('f-area-min');
  const areaMax = valorCampoMilhar('f-area-max');
  const precoMinF = valorCampoMilhar('f-preco-min');
  const precoMaxF = valorCampoMilhar('f-preco-max');
  const bairrosSel = combos.bairro.selecionados;
  const tiposSel = combos.tipo.selecionados;
  const ordem = document.getElementById('f-ordem').value;

  let filtrado = DADOS.filter(d =>
    (bairrosSel.size === 0 || bairrosSel.has(d.bairro)) &&
    (tiposSel.size === 0 || tiposSel.has(d.tipo)) &&
    (!ocupacao || d.ocupacao === ocupacao) &&
    (!risco || d.risco === risco) &&
    (!fonte || d.fonte === fonte) &&
    (!soCorredor || d.no_corredor) &&
    (vagasMin == null || (d.vagas ?? 0) >= vagasMin) &&
    (areaMin == null || (d.area_m2 != null && d.area_m2 >= areaMin)) &&
    (areaMax == null || (d.area_m2 != null && d.area_m2 <= areaMax)) &&
    (precoMinF == null || (d.preco ?? 0) >= precoMinF) &&
    (precoMaxF == null || (d.preco ?? 0) <= precoMaxF)
  );

  if (ordem === 'corredor') {
    filtrado.sort((a, b) => (b.no_corredor - a.no_corredor) || ((b.desconto_vs_mercado_pct ?? -999) - (a.desconto_vs_mercado_pct ?? -999)));
  } else if (ordem === 'desconto') {
    filtrado.sort((a, b) => (b.desconto_vs_mercado_pct ?? -999) - (a.desconto_vs_mercado_pct ?? -999));
  } else if (ordem === 'preco') {
    filtrado.sort((a, b) => (a.preco ?? 0) - (b.preco ?? 0));
  } else if (ordem === 'data') {
    filtrado.sort((a, b) => (a.data_leilao || '').localeCompare(b.data_leilao || ''));
  }

  // a tabela pode reordenar por qualquer coluna clicada, sobrescrevendo a ordenacao acima
  if (document.getElementById('tab-tabela') && !document.getElementById('tab-tabela').hidden) {
    const {chave, dir} = ordemTabela;
    filtrado.sort((a, b) => {
      let va = a[chave], vb = b[chave];
      if (va == null) va = typeof vb === 'number' ? -Infinity : '';
      if (vb == null) vb = typeof va === 'number' ? -Infinity : '';
      if (typeof va === 'number' || typeof vb === 'number') return dir * ((va || 0) - (vb || 0));
      return dir * String(va).localeCompare(String(vb), 'pt-BR');
    });
  }

  return filtrado;
}

function aplicarFiltros() {
  const filtrado = filtrarDados();
  const lista = document.getElementById('lista');
  const contagem = document.getElementById('contagem');

  if (filtrado.length === 0) {
    contagem.textContent = '0 imoveis com esses filtros.';
    lista.innerHTML = `<div class="aviso-vazio">
      Nenhum imovel encontrado com esse filtro agora. Isso e normal: leiloes de apartamento
      em Zona Sul/Centro sao esporadicos e o estoque muda quase todo dia. Tente "mostrar Rio todo"
      ou confira a aba <a href="#" onclick="mudarAba('manual'); return false;">Como funciona (manual)</a>
      &mdash; tem os links de Biasi e Caixa (fontes ainda manuais), que costumam
      ter mais opcoes na regiao do que os grandes agregadores.</div>`;
  } else {
    contagem.textContent = `${filtrado.length} imo${filtrado.length === 1 ? 'vel' : 'veis'} encontrado${filtrado.length === 1 ? '' : 's'}.`;
    lista.innerHTML = `<div class="grid">${filtrado.map(card).join('')}</div>`;
  }

  renderTabela(filtrado);
}

['f-ocupacao','f-risco','f-fonte','f-corredor','f-ordem','f-vagas'].forEach(id =>
  document.getElementById(id).addEventListener('change', aplicarFiltros)
);

function popularSelect(id, valores) {
  const sel = document.getElementById(id);
  const atual = sel.value;
  sel.innerHTML = '<option value="">' + (id === 'f-fonte' ? 'Todas' : 'Todos') + '</option>';
  [...new Set(valores)].filter(Boolean).sort().forEach(v => {
    const opt = document.createElement('option');
    opt.value = v; opt.textContent = v;
    sel.appendChild(opt);
  });
  if ([...sel.options].some(o => o.value === atual)) sel.value = atual;
}

function reinicializarUI() {
  combos.bairro.valores.clear();
  combos.tipo.valores.clear();
  montarValoresCombo();
  popularSelect('f-fonte', DADOS.map(d => d.fonte));
  initRangePreco();
  aplicarFiltros();
}

// --------------------- atualizar (busca dados.json publicado, se disponivel) ---------------------
async function atualizarDados(opts) {
  const silencioso = opts && opts.silent;
  const btn = document.getElementById('btn-atualizar');
  const status = document.getElementById('status-atualizar');
  if (!silencioso) { btn.disabled = true; btn.textContent = '⟳ Atualizando...'; status.textContent = 'Buscando dados mais recentes...'; }
  try {
    const resp = await fetch('./dados.json?t=' + Date.now(), { cache: 'no-store' });
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const novo = await resp.json();
    if (!Array.isArray(novo.imoveis)) throw new Error('formato inesperado');
    DADOS = novo.imoveis;
    document.getElementById('chip-gerado').textContent = 'Gerado em ' + (novo.gerado_em || '?');
    document.getElementById('chip-total').textContent = DADOS.length + ' imoveis no Rio de Janeiro hoje';
    reinicializarUI();
    if (!silencioso) status.textContent = `Atualizado agora - ${DADOS.length} imoveis carregados.`;
  } catch (e) {
    if (!silencioso) {
      status.textContent = 'Nao foi possivel buscar dados novos agora (voce pode estar vendo a copia local deste arquivo). ' +
        'Para dados sempre atualizados, abra pelo link hospedado em vez do arquivo salvo no computador.';
    }
  } finally {
    if (!silencioso) { btn.disabled = false; btn.textContent = '⟳ Atualizar'; }
  }
}

reinicializarUI();
// tenta buscar uma versao mais fresca automaticamente ao abrir, sem incomodar se nao der (ex: arquivo local)
atualizarDados({silent: true});
</script>
</body>
</html>
"""


def montar_manual_html():
    fontes_html = "\n".join(
        f'<a href="{f["url"]}" target="_blank">{f["nome"]}</a>' for f in OUTRAS_FONTES
    )
    bairros_html = "\n".join(f"<span>{nome}</span>" for nome in CORREDOR_BAIRROS.values())

    return f"""
    <h2>Como funciona esta ferramenta</h2>
    <p class="lead">Um guia rapido do raciocinio usado para montar isto e de onde vem cada numero
    que voce ve na aba "Imoveis em leilao" &mdash; para decidir com base no que os dados realmente
    mostram, nao no que parecem mostrar.</p>

    <h3>O mapa mental da pesquisa (antes de programar qualquer coisa)</h3>
    <p>Antes de construir a ferramenta, o primeiro passo foi entender como o mercado de leilao de
    imoveis funciona de verdade no Rio &mdash; sem isso, qualquer numero bonito na tela seria enganoso.
    A ordem foi:</p>
    <ol class="step-list">
      <li><strong>Entender as regras do jogo.</strong> Como funcionam leilao judicial, extrajudicial
      (banco) e venda direta; por que existem duas "pracas" com valores diferentes; quais custos
      existem alem do lance (comissao, ITBI, cartorio, laudemio); quais os riscos reais (imovel
      ocupado, dividas de condominio, risco de anulacao).</li>
      <li><strong>Mapear as fontes de dados e testar cada uma.</strong> Foram checados Portal Zuk,
      site da Caixa, leilaoimovel.com.br e os leiloeiros proprios do Rio (RJ Leiloes, Rymer, Gustavo
      Lourenco). Cada site foi testado tecnicamente antes de decidir usa-lo: a Caixa bloqueou
      (protecao anti-robo), o agregador leilaoimovel.com.br tambem bloqueou, e a Zuk respondeu bem
      &mdash; entao foi ela a fonte automatizada da Fase 1.</li>
      <li><strong>Definir o que realmente importa para morar</strong> (nao para investir): nao e so
      "qual o desconto", e sim ocupacao, modalidade juridica, custo total real e comparacao com o
      preco de mercado do bairro &mdash; por isso o semaforo de risco e o calculo de custo total
      existem.</li>
      <li><strong>Construir o coletor</strong> que busca, calcula e gera esta pagina sozinha a partir
      dos dados brutos.</li>
      <li><strong>Ajustar com o uso real</strong> &mdash; por exemplo, a lista de bairros do corredor
      foi revisada para incluir Saude, Fatima, Santa Teresa, Gamboa, Santo Cristo e outros que
      tinham ficado de fora da primeira versao.</li>
    </ol>

    <h3>As 3 categorias de leilao</h3>
    <table>
      <tr><th>Categoria</th><th>O que e</th><th>Para morar</th></tr>
      <tr><td><strong>Judicial</strong></td><td>Imovel penhorado num processo, leiloado sob supervisao
      de um juiz.</td><td>Maior desconto, mas maior risco: quase sempre ocupado, exige advogado,
      pagamento a vista ou parcelado com hipoteca.</td></tr>
      <tr><td><strong>Extrajudicial (banco)</strong></td><td>Banco retoma o imovel de quem parou de
      pagar o financiamento e leiloa direto, sem passar pelo Judiciario.</td><td>Risco intermediario;
      editais costumam informar ocupacao com mais clareza.</td></tr>
      <tr><td><strong>Venda direta / retomados</strong></td><td>Imovel que nao vendeu em leilao e
      volta ao estoque do banco (Caixa, Santander, Itau, Bradesco), vendido quase como compra normal.</td>
      <td><strong>Mais indicada para morar</strong>: financia ate 95% + FGTS, dividas geralmente
      quitadas. Fica nas fontes manuais por enquanto.</td></tr>
    </table>

    <h3>Por que existem dois valores no mesmo leilao</h3>
    <p>No leilao judicial, a <strong>1&ordf; praca</strong> comeca no valor de avaliacao de um perito
    (com frequencia acima do mercado &mdash; por isso quase ninguem arremata nela). Cerca de uma a
    tres semanas depois, a <strong>2&ordf; praca</strong> permite desconto de ate 50% dessa avaliacao.
    No extrajudicial (banco) o padrao e parecido: 1&ordm; leilao pelo valor de avaliacao do contrato,
    2&ordm; leilao pelo valor da divida, normalmente mais baixo.</p>

    <h3>Custos alem do lance (o que o "custo total estimado" de cada card inclui)</h3>
    <table>
      <tr><th>Custo</th><th>%</th><th>Observacao</th></tr>
      <tr><td>Comissao do leiloeiro</td><td>5%</td><td>Paga junto com o lance</td></tr>
      <tr><td>ITBI (Prefeitura do Rio)</td><td>3%</td><td>Lei municipal 1.364/88</td></tr>
      <tr><td>Cartorio/registro</td><td>~1,5%</td><td>Estimativa</td></tr>
      <tr><td>Laudemio (Uniao)</td><td>5%, se aplicavel</td><td>So quando o imovel pode estar em
      terreno de marinha &mdash; a ferramenta sinaliza "possivel" para Copacabana, Leme, Flamengo,
      Catete, Gloria, Botafogo e Urca, mas isso so se confirma na matricula.</td></tr>
    </table>
    <p>Dividas de condominio, IPTU atrasado e desocupacao <strong>nao entram</strong> nesse calculo
    porque variam caso a caso &mdash; sempre confira no edital.</p>

    <h3>O que significa cada cor do semaforo de risco</h3>
    <div class="semaforo-legenda">
      <div class="item"><span class="dot verde"></span><span><strong>Verde</strong> &mdash;
      extrajudicial (banco) e marcado como desocupado no anuncio. Menor risco relativo.</span></div>
      <div class="item"><span class="dot amarelo"></span><span><strong>Amarelo</strong> &mdash;
      falta confirmar um dos dois fatores (modalidade ou ocupacao).</span></div>
      <div class="item"><span class="dot vermelho"></span><span><strong>Vermelho</strong> &mdash;
      nem modalidade nem ocupacao estao claras no anuncio &mdash; leia o edital com atencao redobrada
      antes de considerar.</span></div>
    </div>
    <p>Essa e uma leitura automatica do texto do anuncio, nao uma analise juridica. Nunca substitui
    ler o edital inteiro.</p>

    <h3>Bairros considerados "no corredor" (Tijuca &rarr; Copacabana)</h3>
    <div class="bairros-tags">
      {bairros_html}
    </div>
    <p>Se um bairro que interessa nao aparecer aqui, e so pedir para incluir.</p>

    <h3>De onde vem cada numero</h3>
    <ul>
      <li><strong>Preco, desconto %, data do leilao, ocupacao, comitente:</strong> extraidos direto
      do anuncio publicado no Portal Zuk no momento em que o coletor rodou.</li>
      <li><strong>R$/m2 de referencia do bairro:</strong> pesquisa de mercado feita em agosto de 2026
      (FipeZap e outras fontes do setor) &mdash; e uma media de mercado, nao uma avaliacao formal do
      imovel especifico.</li>
      <li><strong>"vs. mercado":</strong> compara o R$/m2 do lote com essa referencia do bairro.</li>
      <li><strong>Custo total estimado:</strong> lance multiplicado pelos percentuais da tabela de
      custos acima.</li>
      <li><strong>Links de fotos alternativas:</strong> buscas prontas (Google Maps, ZAP, OLX, Google
      Imagens) para o endereco do imovel &mdash; uteis quando o leiloeiro nao publicou fotos internas,
      por exemplo olhando anuncios de aluguel recentes no mesmo predio.</li>
    </ul>

    <h3>Fontes de dados</h3>
    <h4>Automatica (atualizada a cada vez que o coletor roda)</h4>
    <p><strong>Portal Zuk, Mega Leiloes, RJ Leiloes, Juliana Vettorazzo, Rymer Leiloes</strong> e
    <strong>Gustavo Lourenco Leiloeiro</strong> &mdash; foco na cidade do Rio de Janeiro, todos os
    tipos de imovel. Juntas cobrem leilao judicial, extrajudicial (banco) e tambem lotes em
    <strong>venda direta</strong> (proposta aberta, sem preco fixo definido &mdash; aparece como
    "Aberto para proposta" nos cards, o que e normal e nao um erro da ferramenta). RJ Leiloes e
    Juliana Vettorazzo rodam na mesma plataforma (Soleon); Rymer e Gustavo Lourenco tambem
    compartilham motor (Suporte Leiloes) &mdash; por isso deu pra automatizar as quatro com o
    mesmo tipo de leitor, mesmo sendo leiloeiros independentes.</p>
    <h4>Manual (ainda sem automacao &mdash; vale abrir de tempos em tempos)</h4>
    <p>A Caixa tem protecao anti-robo (confirmada duas vezes, inclusive contra o download publico
    do CSV deles) e o agregador leilaoimovel.com.br tem um desafio JavaScript da Cloudflare, os
    dois exigiriam um navegador automatizado de verdade para superar. A Biasi Leiloes nao esta
    bloqueada, mas publica por evento de leilao com uma estrutura propria, ainda nao automatizada.
    Vale visitar direto:</p>
    <div class="fontes-grid">
      {fontes_html}
    </div>

    <h3>Limitacoes honestas</h3>
    <ul>
      <li>O corredor pode aparecer vazio (ou quase) em determinados dias &mdash; leilao de apartamento
      em Zona Sul/Centro e esporadico, isso nao e falha da ferramenta.</li>
      <li>Nenhum numero aqui substitui ler o edital completo, consultar a matricula no cartorio e,
      no caso de leilao judicial, falar com um advogado.</li>
      <li>Os dados sao uma fotografia do momento em que o coletor rodou &mdash; reabra o arquivo
      gerado mais recente para ver algo atualizado.</li>
    </ul>

    <h3>Passo a passo, do interesse ao apartamento</h3>
    <ol class="step-list">
      <li>Achar o imovel aqui e ler o edital inteiro (ocupacao, dividas, forma de pagamento).</li>
      <li>Pedir a matricula atualizada no cartorio (RGI) para confirmar metragem e ver se ha penhoras,
      hipotecas ou indicio de laudemio.</li>
      <li>Investigar o predio e o entorno: visita externa, conversa com porteiro/vizinhos, Street View,
      anuncios recentes no mesmo predio.</li>
      <li>Definir um lance maximo = valor de mercado &times; desconto desejado &minus; custos estimados
      &minus; reforma prevista.</li>
      <li>Cadastrar-se na plataforma do leiloeiro com antecedencia.</li>
      <li>Dar o lance na 2&ordf; praca (ou 2&ordm; leilao) com o teto ja definido.</li>
      <li>Pagar o lance + comissao no prazo do edital.</li>
      <li>Registrar a arrematacao e, se ocupado, iniciar a desocupacao antes da reforma e mudanca.</li>
    </ol>
    """


def montar_html(imoveis):
    total_corredor = sum(1 for i in imoveis if i["no_corredor"])
    fontes_presentes = sorted({i["fonte"] for i in imoveis})
    gerado_em = datetime.now(FUSO_BRASILIA).strftime("%d/%m/%Y %H:%M")

    html = HTML_TEMPLATE
    html = html.replace("__DATA_GERACAO__", gerado_em)
    html = html.replace("__TOTAL_IMOVEIS__", str(len(imoveis)))
    html = html.replace("__TOTAL_CORREDOR__", str(total_corredor))
    html = html.replace("__TOTAL_FONTES__", str(len(fontes_presentes)))
    html = html.replace("__NOMES_FONTES__", ", ".join(fontes_presentes))
    html = html.replace("__MANUAL_HTML__", montar_manual_html())
    html = html.replace("__DADOS_JSON__", json.dumps(imoveis, ensure_ascii=False))
    html = html.replace("__CORREDOR_JSON__", json.dumps(list(CORREDOR_BAIRROS.values()), ensure_ascii=False))
    return html, gerado_em


def gerar_html(imoveis):
    """Gera o arquivo local (LEILOES-RJ.html) - snapshot embutido, uso offline/manual."""
    html, _ = montar_html(imoveis)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)


def gerar_site_publicavel(imoveis, pasta=DOCS_DIR):
    """Gera docs/index.html + docs/dados.json + docs/robots.txt para publicar no
    GitHub Pages. index.html funciona igual ao LEILOES-RJ.html (mesmo snapshot embutido),
    mas o botao Atualizar consegue buscar dados.json ao vivo (mesma origem = sem CORS)."""
    os.makedirs(pasta, exist_ok=True)
    html, gerado_em = montar_html(imoveis)

    with open(os.path.join(pasta, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    with open(os.path.join(pasta, "dados.json"), "w", encoding="utf-8") as f:
        json.dump({"gerado_em": gerado_em, "imoveis": imoveis}, f, ensure_ascii=False)

    with open(os.path.join(pasta, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nDisallow: /\n")


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------

def main():
    imoveis = []

    print("Buscando imoveis no Portal Zuk (Rio de Janeiro)...")
    try:
        html_zuk = buscar_html_zuk()
        imoveis_zuk = parse_cards(html_zuk)
        print(f"  {len(imoveis_zuk)} imoveis na Zuk.")
        imoveis += imoveis_zuk
    except Exception as e:
        print(f"  Falhou ({e}) - seguindo sem a Zuk desta vez.")

    print("Buscando imoveis na Mega Leiloes (Rio de Janeiro)...")
    try:
        html_mega = buscar_html_mega()
        imoveis_mega = parse_cards_mega(html_mega)
        print(f"  {len(imoveis_mega)} imoveis na Mega Leiloes.")
        imoveis += imoveis_mega
    except Exception as e:
        print(f"  Falhou ({e}) - seguindo sem a Mega desta vez.")

    for nome_fonte, base_url in SOLEON_SITES.items():
        print(f"Buscando imoveis na {nome_fonte}...")
        try:
            imoveis_soleon = coletar_soleon(nome_fonte, base_url)
            print(f"  {len(imoveis_soleon)} imoveis na {nome_fonte}.")
            imoveis += imoveis_soleon
        except Exception as e:
            print(f"  Falhou ({e}) - seguindo sem a {nome_fonte} desta vez.")

    print("Buscando imoveis na Rymer Leiloes...")
    try:
        html_rymer = buscar_html_rymer()
        imoveis_rymer = parse_cards_rymer(html_rymer)
        print(f"  {len(imoveis_rymer)} imoveis na Rymer.")
        imoveis += imoveis_rymer
    except Exception as e:
        print(f"  Falhou ({e}) - seguindo sem a Rymer desta vez.")

    print("Buscando imoveis na Gustavo Lourenco Leiloeiro...")
    try:
        html_gustavo = buscar_html_gustavo()
        imoveis_gustavo = parse_cards_gustavo(html_gustavo)
        print(f"  {len(imoveis_gustavo)} imoveis na Gustavo Lourenco.")
        imoveis += imoveis_gustavo
    except Exception as e:
        print(f"  Falhou ({e}) - seguindo sem a Gustavo Lourenco desta vez.")

    imoveis = [enriquecer(i) for i in imoveis]

    contagem_fonte = Counter(i["fonte"] for i in imoveis)
    contagem_bairro = Counter(i["bairro"] for i in imoveis)
    no_corredor = [i for i in imoveis if i["no_corredor"]]
    print(f"\nTotal: {len(imoveis)} imoveis ({dict(contagem_fonte)})")
    print(f"  {len(no_corredor)} no corredor Tijuca-Lapa-Catete-Copacabana.")
    print("  Bairros encontrados hoje:", dict(contagem_bairro.most_common()))

    gerar_html(imoveis)
    gerar_site_publicavel(imoveis)
    print(f"\nArquivo local gerado: {OUTPUT_HTML}")
    print(f"Site publicavel gerado em: {DOCS_DIR}/ (index.html + dados.json + robots.txt)")
    print("Abra o LEILOES-RJ.html no navegador ou envie por WhatsApp/e-mail.")


if __name__ == "__main__":
    main()
