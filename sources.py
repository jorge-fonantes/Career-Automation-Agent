import html
import re
import time
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
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
    for termo in config.TERMOS_BUSCA + config.TERMOS_BUSCA_EXTRA:
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

def fetch_workingnomads():
    return parse_workingnomads(_get("https://www.workingnomads.com/api/exposed_jobs/").json())

def parse_workingnomads(dados):
    return [Job(
        title=j["title"],
        company=j.get("company_name", ""),
        url=j["url"],
        source="Working Nomads",
        location=j.get("location", ""),
        description=j.get("description", ""),
        published=_data_iso(j.get("pub_date")),
    ) for j in dados]

def fetch_remotar():
    vagas = []
    for termo in config.TERMOS_BUSCA + config.TERMOS_BUSCA_EXTRA + config.TERMOS_BUSCA_PT:
        vagas.extend(parse_remotar(_get("https://api.remotar.com.br/jobs", search=termo).json()))
        time.sleep(1)
    return vagas

def parse_remotar(dados):
    vagas = []
    for j in dados.get("data", []):
        if j.get("type") != "remote" or j.get("expired"):
            continue
        empresa = j.get("companyDisplayName") or (j.get("company") or {}).get("name", "")
        url = j.get("externalLink") if j.get("isExternalLink") else None
        vagas.append(Job(
            title=j["title"],
            company=empresa,
            url=url or f"https://remotar.com.br/job/{j['id']}",
            source="Remotar",
            # O Remotar é brasileiro: sem país informado, a vaga é para o Brasil
            location="Brasil" if not j.get("countryId") else str(j.get("country") or ""),
            description=j.get("description") or "",
            published=_data_iso(j.get("createdAt")),
        ))
    return vagas

RE_CARD_INFOJOBS = re.compile(r'id="vacancy\d+"[^>]*data-href="([^"]+)"(.*?)(?=id="vacancy\d+"|\Z)', re.S)
RE_TITULO_INFOJOBS = re.compile(r'js_vacancyTitle[^>]*>\s*(.*?)\s*</h2>', re.S)
RE_DATA_INFOJOBS = re.compile(r'js_date" data-value="([^"]+)"')
RE_EMPRESA_INFOJOBS = re.compile(r'/empresa-([a-z0-9-]+)__\d+')
RE_RESUMO_INFOJOBS = re.compile(r'class="text-medium">\s*([^<]+?)\s*</div>')
FUSO_BRASIL = timezone(timedelta(hours=-3))

def fetch_infojobs():
    vagas = []
    for termo in config.TERMOS_BUSCA_PT:
        # Usa o filtro "Home office" do próprio InfoJobs
        slug = "+".join(_sem_acento(termo).split())
        pagina = _get(f"https://www.infojobs.com.br/vagas-de-emprego-{slug}-trabalho-home-office.aspx").text
        vagas.extend(parse_infojobs(pagina))
        time.sleep(1)
    return vagas

def _sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)).lower()

def parse_infojobs(pagina):
    vagas = []
    for href, cartao in RE_CARD_INFOJOBS.findall(pagina):
        titulo = RE_TITULO_INFOJOBS.search(cartao)
        if not titulo or "Home office" not in cartao:
            continue
        data = RE_DATA_INFOJOBS.search(cartao)
        empresa = RE_EMPRESA_INFOJOBS.search(cartao)
        resumos = RE_RESUMO_INFOJOBS.findall(cartao)
        vagas.append(Job(
            title=titulo.group(1),
            # O nome da empresa vem misturado com selos no HTML; o endereço da página dela é mais limpo
            company=empresa.group(1).replace("-", " ").title() if empresa else "",
            url="https://www.infojobs.com.br" + html.unescape(href),
            source="InfoJobs",
            location="Brasil",
            description=max(resumos, key=len) if resumos else "",
            published=datetime.strptime(data.group(1), "%Y/%m/%d %H:%M:%S").replace(tzinfo=FUSO_BRASIL) if data else None,
        ))
    return vagas

FONTES = {
    "Remotive": fetch_remotive,
    "Remote OK": fetch_remoteok,
    "We Work Remotely": fetch_weworkremotely,
    "Himalayas": fetch_himalayas,
    "Jobicy": fetch_jobicy,
    "Working Nomads": fetch_workingnomads,
    "Remotar": fetch_remotar,
    "InfoJobs": fetch_infojobs,
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
