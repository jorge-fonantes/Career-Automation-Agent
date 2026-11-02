import html
import re
import unicodedata
from datetime import datetime, timedelta, timezone

import config

def normalizar(texto):
    """ Minúsculas, sem HTML e sem acento: 'Técnico' e 'tecnico' viram a mesma coisa. """
    texto = re.sub(r"<[^>]+>", " ", html.unescape(texto or ""))
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c)).lower()

def _regex(termos):
    return re.compile(r"(?<![\w])(?:" + "|".join(re.escape(normalizar(t)) for t in termos) + r")(?![\w])")

RE_TECNICO = _regex(config.TITULOS_TECNICOS)
RE_AMBIGUO = _regex(config.TITULOS_AMBIGUOS)
RE_EXCLUIDO = _regex(config.TITULOS_EXCLUIDOS)
RE_REGIAO_TITULO = _regex(config.TITULOS_REGIAO_RESTRITA)
RE_ENTRADA = _regex(config.TITULOS_ENTRADA)
RE_SENIOR = _regex(config.TITULOS_SENIOR)
RE_BRASIL = _regex(config.LOCAIS_BRASIL)
RE_ABERTO = _regex(config.LOCAIS_ABERTOS)
RE_RESTRICAO = re.compile("|".join(config.RESTRICOES_DESCRICAO))
RE_TERMOS_DESCRICAO = _regex(config.DESCRICAO_TECNICA)
RE_SO_REMOTO = re.compile(r"^(100% )?(remote|remoto|anywhere)$")

def termos_tecnicos(descricao):
    return set(RE_TERMOS_DESCRICAO.findall(descricao))

def pontos_titulo(titulo, descricao):
    """ Pontos da vaga por área de atuação, ou None se não for suporte técnico. """
    if RE_EXCLUIDO.search(titulo) or RE_REGIAO_TITULO.search(titulo):
        return None
    if RE_TECNICO.search(titulo):
        return 50
    if RE_AMBIGUO.search(titulo) and len(termos_tecnicos(descricao)) >= config.MIN_TERMOS_TITULO_AMBIGUO:
        return 25
    return None

def pontos_local(local):
    """ Pontos por localidade, ou None se a vaga não aceitar quem mora no Brasil. """
    local = local.strip()
    if not local:
        return 0  # Fonte não informou: mantém, mas sem bônus
    if RE_BRASIL.search(local):
        return 20
    if RE_ABERTO.search(local) or RE_SO_REMOTO.match(local):
        return 10
    return None

def recente(job, agora=None):
    if job.published is None:
        return True
    agora = agora or datetime.now(timezone.utc)
    return job.published >= agora - timedelta(days=config.MAX_DIAS_VAGA)

def avaliar(job):
    """ Devolve a pontuação da vaga, ou None se ela deve ser descartada. """
    titulo = normalizar(job.title)
    descricao = normalizar(job.description)

    area = pontos_titulo(titulo, descricao)
    local = pontos_local(normalizar(job.location))
    if area is None or local is None or RE_RESTRICAO.search(descricao):
        return None

    pontos = area + local + min(len(termos_tecnicos(descricao)) * 2, 10)
    if RE_ENTRADA.search(titulo):
        pontos += 10
    elif RE_SENIOR.search(titulo):
        pontos -= 10
    return pontos

def chave_vaga(job):
    """ A mesma vaga costuma aparecer em várias fontes, com URLs diferentes. """
    empresa = re.sub(r"\W+", "", normalizar(job.company))
    titulo = re.sub(r"\W+", "", normalizar(job.title))
    return f"{empresa}|{titulo}" if empresa else job.url

def filtrar(vagas):
    """ Mantém só as vagas que interessam, sem duplicatas, melhores primeiro. """
    selecionadas = {}
    for job in vagas:
        if not job.url or not recente(job):
            continue
        pontos = avaliar(job)
        if pontos is None:
            continue
        job.score = pontos
        chave = chave_vaga(job)
        if chave not in selecionadas or pontos > selecionadas[chave].score:
            selecionadas[chave] = job
    return sorted(selecionadas.values(), key=lambda j: j.score, reverse=True)
