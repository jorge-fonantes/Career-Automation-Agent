# Tudo que define "qual vaga me interessa" fica aqui, para ajustar sem mexer na lógica.
# Os termos são comparados em minúsculas e sem acento, sempre como palavra inteira.

# Buscas enviadas às fontes (a filtragem de verdade acontece depois, em job_filter.py)
TERMOS_BUSCA = [
    "technical support",
    "it support",
    "help desk",
    "service desk",
    "support engineer",
]

# Buscas extras do modo navegador (LinkedIn/Indeed), onde há vagas em português
TERMOS_BUSCA_NAVEGADOR = TERMOS_BUSCA + [
    "suporte técnico",
    "analista de suporte",
]

# Título que, sozinho, já identifica uma vaga de suporte técnico
TITULOS_TECNICOS = [
    "technical support", "tech support", "technical customer support",
    "technical product support", "it support", "it helpdesk", "it help desk",
    "it service desk", "it technician", "it specialist", "it analyst",
    "help desk", "helpdesk", "service desk", "desktop support", "desktop engineer",
    "application support", "applications support", "systems support",
    "network support", "cloud support", "saas support", "support engineer",
    "support technician", "tier 1 support", "tier 2 support", "tier 3 support",
    "l1 support", "l2 support", "l3 support",
    "suporte tecnico", "analista de suporte", "tecnico de suporte",
    "tecnico em informatica", "tecnico de informatica", "suporte de ti", "suporte ti",
    "suporte n1", "suporte n2", "suporte n3", "suporte a sistemas",
    "suporte de sistemas", "suporte de infraestrutura", "soporte tecnico",
]

# Título ambíguo: só vale se a descrição mostrar conteúdo técnico
TITULOS_AMBIGUOS = [
    "customer support", "support specialist", "support analyst", "support agent",
    "support representative", "support associate", "product support",
    "customer care", "suporte ao cliente", "suporte",
]

# Quantos termos de DESCRICAO_TECNICA um título ambíguo precisa ter
MIN_TERMOS_TITULO_AMBIGUO = 3

DESCRICAO_TECNICA = [
    "troubleshoot", "troubleshooting", "debug", "debugging", "root cause", "logs",
    "api", "apis", "sql", "linux", "windows", "macos", "active directory", "azure",
    "aws", "vpn", "dns", "tcp/ip", "networking", "saas", "microsoft 365", "office 365",
    "itil", "remote desktop", "escalate to engineering", "jira", "technical issues",
    "redes", "infraestrutura", "chamados", "resolucao de problemas",
]

# Descarta a vaga se o título tiver qualquer um destes
TITULOS_EXCLUIDOS = [
    "manager", "director", "head of", "vice president", "vp", "supervisor",
    "gerente", "coordenador", "coordenadora", "diretor", "diretora",
    "sales", "account executive", "business development", "customer success",
    "recruiter", "recruitment", "marketing", "designer", "copywriter",
    "software engineer", "software developer", "developer", "accountant",
    "bookkeeper", "nurse", "medical", "dental", "legal", "paralegal", "insurance",
    "administrative support", "executive assistant", "virtual assistant",
    "billing", "payroll", "tax", "vendas", "comercial", "administrativo",
    "administrativa", "cobranca", "juridico", "contabil", "enfermagem",
]

# Região no título: há fontes que marcam "Anywhere" em vagas como "Support Analyst - Philippines"
TITULOS_REGIAO_RESTRITA = [
    "emea", "apac", "amer", "europe", "uk", "germany", "france", "spain", "portugal", "italy",
    "philippines", "india", "pakistan", "australia", "canada", "canadian", "north america",
    "colombia", "mexico", "argentina", "chile", "peru",
    "usa", "us only", "us based", "us-based", "us remote", "united states",
]

# Bônus de nível: você compete melhor nestas vagas, então elas sobem no relatório
TITULOS_ENTRADA = ["junior", "jr", "entry level", "entry-level", "associate", "tier 1", "l1", "n1", "trainee", "estagio"]
TITULOS_SENIOR = ["senior", "sr", "staff", "principal", "lead", "tier 3", "l3", "n3"]

# Localidade que aceita quem mora no Brasil. Qualquer outra (ex.: "USA Only") é descartada.
LOCAIS_BRASIL = ["brazil", "brasil", "latam", "latin america", "south america", "america latina"]
LOCAIS_ABERTOS = [
    "worldwide", "world wide", "global", "globally", "anywhere in the world", "americas",
]

# Descrição que restringe a vaga mesmo quando a localidade parece aberta
RESTRICOES_DESCRICAO = [
    r"must (be|reside|live|be located|be based) (in|within) the (us|usa|u\.s\.|united states|uk|united kingdom)",
    r"(authorized|eligible|authorization) to work in the (us|usa|u\.s\.|united states|uk|united kingdom)",
    r"(us|u\.s\.) (citizen|citizens|citizenship)",
    r"security clearance",
    r"us[- ]based (candidates|applicants) only",
]

# Vagas mais antigas que isso são ignoradas (o histórico evita repetir as mais novas)
MAX_DIAS_VAGA = 30

# Limite por relatório. O que sobrar não é perdido: vem na próxima execução.
MAX_VAGAS_RELATORIO = 30

ARQUIVO_HISTORICO = "vagas_vistas.sqlite3"
