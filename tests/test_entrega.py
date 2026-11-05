from datetime import timezone

import main
from history import JobHistory
from sources import (Job, coletar_vagas, parse_himalayas, parse_infojobs, parse_remoteok, parse_remotar,
                     parse_weworkremotely)
import sources
import telegram_notifier

def job(n, title="Support_Engineer *urgente* <R&D>"):
    return Job(title=f"{title} {n}", company="A&B", url=f"https://x.test/?a={n}&b=1", source="Teste", location="Worldwide")

class TelegramFalso:
    base_url = "https://teste"

    def __init__(self, falhar_na=None):
        self.enviadas = []
        self.falhar_na = falhar_na

    def send_report(self, texto):
        if len(self.enviadas) + 1 == self.falhar_na:
            return False
        self.enviadas.append(texto)
        return True

def test_html_escapa_caracteres_do_titulo():
    texto = main.formatar_vaga(job(1))
    assert "&lt;R&amp;D&gt;" in texto and "A&amp;B" in texto
    assert 'href="https://x.test/?a=1&amp;b=1"' in texto

def test_titulo_ja_escapado_nao_escapa_duas_vezes():
    assert "Support &amp; Ops" in main.formatar_vaga(Job("Support &amp; Ops", "", "https://x.test", "Teste"))

def test_resumir_local_longo():
    assert main.resumir_local("Worldwide") == "Worldwide"
    assert main.resumir_local("Argentina, " * 10 + "Brazil") == "Brasil e outros países"

def test_mensagens_respeitam_limite_e_nao_perdem_vagas():
    vagas = [job(n) for n in range(100)]
    mensagens = main.montar_mensagens(vagas)
    assert len(mensagens) > 1
    assert all(len(texto) <= main.LIMITE_MENSAGEM for texto, _ in mensagens)
    assert sum(len(bloco) for _, bloco in mensagens) == 100

def test_historico_so_marca_o_que_foi_entregue(tmp_path, monkeypatch):
    monkeypatch.setattr(main.time, "sleep", lambda _: None)
    historico = JobHistory(tmp_path / "h.sqlite3")
    vagas = [job(n) for n in range(100)]
    total_blocos = len(main.montar_mensagens(vagas))

    main.enviar(vagas, TelegramFalso(falhar_na=2), historico)
    restantes = historico.novas(vagas)
    assert 0 < len(restantes) < 100

    main.enviar(restantes, TelegramFalso(), historico)
    assert historico.novas(vagas) == []
    assert total_blocos > 1
    historico.close()

def test_sem_telegram_nao_grava_historico(tmp_path, capsys):
    historico = JobHistory(tmp_path / "h.sqlite3")
    tg = TelegramFalso()
    tg.base_url = None
    main.enviar([job(1)], tg, historico)
    assert historico.novas([job(1)]) == [job(1)]
    assert "https://x.test" in capsys.readouterr().out
    historico.close()

def test_historico_persiste_entre_execucoes(tmp_path):
    caminho = tmp_path / "h.sqlite3"
    h = JobHistory(caminho)
    h.marcar_enviadas([job(1)])
    h.close()
    h = JobHistory(caminho)
    assert h.novas([job(1), job(2)]) == [job(2)]
    h.close()

class RespostaFalsa:
    def __init__(self, status, corpo=None):
        self.status_code = status
        self.ok = status < 400
        self.text = "erro"
        self.corpo = corpo or {}

    def json(self):
        return self.corpo

def bot_com_respostas(monkeypatch, respostas):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "c")
    monkeypatch.setattr(telegram_notifier.time, "sleep", lambda _: None)
    fila = iter(respostas)
    enviados = []
    def post(url, json, timeout):
        enviados.append(json)
        return next(fila)
    monkeypatch.setattr(telegram_notifier.requests, "post", post)
    return telegram_notifier.TelegramBot(), enviados

def test_telegram_erro_400_devolve_false(monkeypatch):
    bot, enviados = bot_com_respostas(monkeypatch, [RespostaFalsa(400)])
    assert bot.send_report("x") is False
    assert enviados[0]["parse_mode"] == "HTML"

def test_telegram_429_tenta_de_novo(monkeypatch):
    espera = RespostaFalsa(429, {"parameters": {"retry_after": 1}})
    bot, enviados = bot_com_respostas(monkeypatch, [espera, RespostaFalsa(200)])
    assert bot.send_report("x") is True
    assert len(enviados) == 2

def test_telegram_verificar_detecta_chat_errado(monkeypatch):
    bot, enviados = bot_com_respostas(monkeypatch, [RespostaFalsa(400), RespostaFalsa(200)])
    assert bot.verificar() is False
    assert bot.verificar() is True
    assert enviados[0]["action"] == "typing"

def test_enviar_informa_falha(tmp_path, monkeypatch):
    monkeypatch.setattr(main.time, "sleep", lambda _: None)
    historico = JobHistory(tmp_path / "h.sqlite3")
    assert main.enviar([job(1)], TelegramFalso(falhar_na=1), historico) is False
    assert main.enviar([job(1)], TelegramFalso(), historico) is True
    historico.close()

def test_fonte_com_erro_nao_derruba_as_outras(monkeypatch):
    def quebra(): raise TimeoutError("fora do ar")
    monkeypatch.setattr(sources, "FONTES", {"Ruim": quebra, "Boa": lambda: [job(1)]})
    vagas, falhas = coletar_vagas()
    assert len(vagas) == 1 and falhas == ["Ruim"]

def test_parse_remoteok_ignora_aviso_legal():
    dados = [{"legal": "aviso"}, {"position": "IT Support", "url": "https://x.test", "date": "2026-11-01T08:00:12+00:00"}]
    vagas = parse_remoteok(dados)
    assert [j.title for j in vagas] == ["IT Support"]
    assert vagas[0].published.tzinfo == timezone.utc

def test_parse_himalayas_sem_restricao_vira_worldwide():
    dados = {"jobs": [{"title": "Help Desk", "applicationLink": "https://x.test", "locationRestrictions": [], "pubDate": 1793317142}]}
    assert parse_himalayas(dados)[0].location == "Worldwide"

CARTAO_INFOJOBS = """
<div id="vacancy1" data-id="1" class="js_cardLink" data-href="/vaga-de-suporte-tecnico-em-sao-paulo__1.aspx">
<div hidden class="js_date" data-value="2026/10/29 04:30:00"></div>
<h2 class="h3 js_vacancyTitle">
Suporte T&#xE9;cnico N1
</h2>
<a href="https://www.infojobs.com.br/empresa-indigo-app__123.aspx">Indigo<span data-bs-title="<div>selo</div>">App</span></a>
Home office
<div class="text-medium">Atendimento de chamados, troubleshooting e redes.</div>
</div>
<div id="vacancy2" data-id="2" class="js_cardLink" data-href="/vaga-de-presencial__2.aspx">
<h2 class="h3 js_vacancyTitle">Suporte Presencial</h2>
Presencial
</div>
"""

def test_parse_infojobs_le_cartao_e_ignora_presencial():
    vagas = parse_infojobs(CARTAO_INFOJOBS)
    assert len(vagas) == 1
    v = vagas[0]
    assert (v.title, v.company, v.location) == ("Suporte Técnico N1", "Indigo App", "Brasil")
    assert v.url == "https://www.infojobs.com.br/vaga-de-suporte-tecnico-em-sao-paulo__1.aspx"
    assert v.published.utcoffset().total_seconds() == -3 * 3600
    assert "troubleshooting" in v.description

def test_parse_remotar_so_remotas_e_link_externo():
    dados = {"data": [
        {"id": 1, "title": "Suporte N2", "type": "remote", "isExternalLink": True,
         "externalLink": "https://ats.test/1", "company": {"name": "Acme"}, "createdAt": "2026-11-04T22:35:17.113-03:00"},
        {"id": 2, "title": "Help Desk", "type": "remote", "isExternalLink": False, "company": {"name": "Beta"}},
        {"id": 3, "title": "Suporte", "type": "hybrid", "company": {"name": "Gama"}},
    ]}
    vagas = parse_remotar(dados)
    assert [v.url for v in vagas] == ["https://ats.test/1", "https://remotar.com.br/job/2"]
    assert all(v.location == "Brasil" for v in vagas)

def test_parse_wwr_separa_empresa_e_cargo():
    xml = """<rss><channel><item><title>Acme: IT Support: Tier 2</title>
    <link>https://x.test</link><region>Anywhere in the World</region>
    <pubDate>Mon, 02 Nov 2026 17:00:15 +0000</pubDate></item></channel></rss>"""
    vaga = parse_weworkremotely(xml)[0]
    assert (vaga.company, vaga.title, vaga.location) == ("Acme", "IT Support: Tier 2", "Anywhere in the World")
