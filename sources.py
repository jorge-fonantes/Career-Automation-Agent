import html
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

import config

TIMEOUT = 30
PAGINAS_HIMALAYAS = 3  # A busca traz 20 vagas por página
HEADERS = {"User-Agent": "Career-Automation-Agent/2.0 (uso pessoal)"}

@dataclass
class Job:
    title: str
    company: str
    url: str
    source: str
    location: str = ""
    description: str = ""
    published: datetime | None = None
    score: int = field(default=0, compare=False)

    def __post_init__(self):
        # Algumas fontes entregam "Support &amp; Ops" já escapado
        self.title = html.unescape(self.title).strip()
        self.company = html.unescape(self.company).strip()
        self.location = html.unescape(self.location).strip()

def _data_iso(valor):
    if not valor: return None
    try:
        data = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError:
        return None
    return data if data.tzinfo else data.replace(tzinfo=timezone.utc)

def _data_epoch(valor):
    try:
        return datetime.fromtimestamp(int(valor), timezone.utc)
    except (TypeError, ValueError):
        return None

def _data_rss(valor):
    try:
        return parsedate_to_datetime(valor)
    except (TypeError, ValueError):
        return None

def _get(url, **params):
    resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp

def fetch_remotive():
    vagas = []
    for termo in config.TERMOS_BUSCA:
        dados = _get("https://remotive.com/api/remote-jobs", search=termo).json()
        vagas.extend(parse_remotive(dados))
        time.sleep(1)
    return vagas

def parse_remotive(dados):
    return [Job(
        title=j["title"],
        company=j.get("company_name", ""),
        url=j["url"],
        source="Remotive",
        location=j.get("candidate_required_location", ""),
        description=j.get("description", ""),
        published=_data_iso(j.get("publication_date")),
    ) for j in dados.get("jobs", [])]

def fetch_remoteok():
    return parse_remoteok(_get("https://remoteok.com/api", tag="support").json())

def parse_remoteok(dados):
    # O primeiro item do JSON é o aviso legal, não uma vaga
    return [Job(
        title=j["position"],
        company=j.get("company", ""),
        url=j["url"],
        source="Remote OK",
        location=j.get("location", ""),
        description=j.get("description", ""),
        published=_data_iso(j.get("date")),
    ) for j in dados if "position" in j]

def fetch_weworkremotely():
    vagas = []
    for categoria in ("remote-customer-support-jobs", "remote-devops-sysadmin-jobs"):
        vagas.extend(parse_weworkremotely(_get(f"https://weworkremotely.com/categories/{categoria}.rss").text))
    return vagas

def parse_weworkremotely(xml_texto):
    vagas = []
    for item in ET.fromstring(xml_texto).iter("item"):
        # O título vem como "Empresa: Cargo"
        empresa, _, cargo = (item.findtext("title") or "").partition(": ")
        vagas.append(Job(
            title=cargo or empresa,
            company=empresa if cargo else "",
            url=item.findtext("link") or item.findtext("guid") or "",
            source="We Work Remotely",
            location=item.findtext("region") or "",
            description=item.findtext("description") or "",
            published=_data_rss(item.findtext("pubDate")),
        ))
    return vagas

def fetch_himalayas():
    vagas = []
    for termo in config.TERMOS_BUSCA:
        for pagina in range(1, PAGINAS_HIMALAYAS + 1):
            vagas.extend(parse_himalayas(_get("https://himalayas.app/jobs/api/search", q=termo, page=pagina).json()))
            time.sleep(1)
    return vagas

def parse_himalayas(dados):
    return [Job(
        title=j["title"],
        company=j.get("companyName", ""),
        url=j.get("applicationLink") or j.get("guid", ""),
        source="Himalayas",
        # Lista vazia significa que a vaga não tem restrição de país
        location=", ".join(j.get("locationRestrictions") or []) or "Worldwide",
        description=j.get("description", ""),
        published=_data_epoch(j.get("pubDate")),
    ) for j in dados.get("jobs", [])]

def fetch_jobicy():
    return parse_jobicy(_get("https://jobicy.com/api/v2/remote-jobs", count=100, tag="support").json())

def parse_jobicy(dados):
    return [Job(
        title=j["jobTitle"],
        company=j.get("companyName", ""),
        url=j["url"],
        source="Jobicy",
        location=j.get("jobGeo", ""),
        description=j.get("jobDescription", ""),
        published=_data_iso(j.get("pubDate")),
    ) for j in dados.get("jobs", [])]

FONTES = {
    "Remotive": fetch_remotive,
    "Remote OK": fetch_remoteok,
    "We Work Remotely": fetch_weworkremotely,
    "Himalayas": fetch_himalayas,
    "Jobicy": fetch_jobicy,
}

def coletar_vagas():
    """ Uma fonte fora do ar não derruba as outras. Devolve (vagas, nomes das fontes que falharam). """
    vagas, falhas = [], []
    for nome, buscar in FONTES.items():
        try:
            encontradas = buscar()
            print(f"   ✅ {nome}: {len(encontradas)} vagas lidas")
            vagas.extend(encontradas)
        except Exception as e:
            print(f"   ⚠️ Erro em {nome}: {e}")
            falhas.append(nome)
    return vagas, falhas
