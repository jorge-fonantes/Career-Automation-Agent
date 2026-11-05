from datetime import datetime, timedelta, timezone

import pytest

import config
from job_filter import avaliar, chave_vaga, filtrar
from sources import Job

TECNICA = "Troubleshooting with logs, SQL queries and API debugging for our SaaS."

def vaga(title="Technical Support Specialist", location="Worldwide", description="", company="Acme", **extra):
    return Job(title=title, company=company, url=f"https://x.test/{title}{location}", source="Teste",
               location=location, description=description, **extra)

@pytest.mark.parametrize("titulo", [
    "Technical Support Engineer", "IT Support Specialist", "Help Desk Analyst",
    "Service Desk Technician", "Analista de Suporte Técnico", "Suporte N1",
    "Técnico de Suporte", "Tier 2 Support", "L2 Support Engineer", "Soporte Técnico",
])
def test_aceita_titulos_de_suporte_tecnico(titulo):
    assert avaliar(vaga(titulo)) is not None

@pytest.mark.parametrize("titulo", [
    "Customer Success Manager", "Sales Support Representative", "Software Engineer",
    "IT Support Manager", "Virtual Assistant", "Medical Billing Specialist",
    "Suporte Administrativo", "Analista de Suporte Comercial", "Audit Support Lead",
    "Product Designer",
])
def test_rejeita_outras_areas(titulo):
    assert avaliar(vaga(titulo, description=TECNICA)) is None

def test_titulo_ambiguo_depende_da_descricao():
    assert avaliar(vaga("Customer Support Specialist", description="Answer emails kindly.")) is None
    assert avaliar(vaga("Customer Support Specialist", description=TECNICA)) is not None

def test_termo_nao_casa_dentro_de_outra_palavra():
    # "tax" não pode barrar "syntax", nem "it support" casar em "audit support"
    assert avaliar(vaga("Syntax Technical Support")) is not None
    assert avaliar(vaga("Audit Support")) is None

@pytest.mark.parametrize("local", [
    "Worldwide", "Anywhere in the World", "Brazil", "Brasil", "LATAM", "Latin America",
    "South America", "Americas", "Remote", "USA, Brazil", "",
])
def test_aceita_local_compativel_com_brasil(local):
    assert avaliar(vaga(location=local)) is not None

@pytest.mark.parametrize("local", [
    "USA Only", "United States", "North America Only", "Philippines", "EMEA", "Remote - US",
    "Anywhere in the US", "Colorado", "Canada Only",
])
def test_rejeita_local_restrito(local):
    assert avaliar(vaga(location=local)) is None

@pytest.mark.parametrize("descricao", [
    "You must be located in the United States.",
    "Candidates must be authorized to work in the US.",
    "U.S. citizens only.",
    "Requires an active security clearance.",
])
def test_rejeita_restricao_escondida_na_descricao(descricao):
    assert avaliar(vaga(description=descricao)) is None

@pytest.mark.parametrize("titulo", [
    "Billing Support Analyst - Philippines", "Support Engineer (EMEA)",
    "Technical Support Specialist, UK", "IT Support (US Only)",
])
def test_rejeita_regiao_restrita_no_titulo_mesmo_com_local_aberto(titulo):
    assert avaliar(vaga(titulo, location="Anywhere in the World", description=TECNICA)) is None

def test_ranking_favorece_brasil_e_nivel_de_entrada():
    assert avaliar(vaga(location="Brazil")) > avaliar(vaga(location="Worldwide")) > avaliar(vaga(location=""))
    assert avaliar(vaga("Junior Technical Support")) > avaliar(vaga("Technical Support"))
    assert avaliar(vaga("Technical Support")) > avaliar(vaga("Senior Technical Support"))

def test_filtrar_remove_vaga_antiga_mantem_sem_data():
    agora = datetime.now(timezone.utc)
    antiga = vaga("Help Desk", published=agora - timedelta(days=config.MAX_DIAS_VAGA + 1))
    nova = vaga("Service Desk", published=agora - timedelta(days=1))
    sem_data = vaga("IT Support")
    assert {j.title for j in filtrar([antiga, nova, sem_data])} == {"Service Desk", "IT Support"}

def test_filtrar_junta_mesma_vaga_de_fontes_diferentes_e_ordena():
    a = vaga(location="Worldwide")
    b = vaga(location="Brazil")
    outra = vaga("IT Support", company="Outra")
    resultado = filtrar([outra, a, b])
    assert len(resultado) == 2
    assert resultado[0].location == "Brazil"

def test_chave_ignora_pontuacao_e_acento():
    assert chave_vaga(vaga("Técnico de Suporte!", company="ACME Inc.")) == chave_vaga(vaga("tecnico de suporte", company="Acme  inc"))

def test_rejeita_sucesso_do_cliente_em_portugues():
    assert avaliar(vaga("Analista de Suporte e Sucesso do Aluno", location="Brasil")) is None
    assert avaliar(vaga("Analista de Suporte Técnico Pleno", location="Brasil")) is not None

@pytest.mark.parametrize("titulo", ["Analista Suporte Jr N1", "Técnico de NOC", "Analista de Atendimento Técnico"])
def test_aceita_titulos_brasileiros_sem_descricao_longa(titulo):
    assert avaliar(vaga(titulo, location="Brasil")) is not None
