import json
import re
from collections import Counter
import os

class ResumeTailor:
    def __init__(self, json_path):
        self.json_path = json_path
        self.profile = self._load_profile()
        
        # Mapeamento de sinônimos (Expansão de Competências)
        self.keyword_map = {
            "python": ["python", "pandas", "numpy", "script", "automação", "selenium", "scraping", "api"],
            "security": ["segurança", "security", "nmap", "vulnerabilidade", "pentest", "hardening", "burp", "owasp", "invasão", "red team", "blue team"],
            "dados": ["dados", "data", "excel", "dashboard", "kpi", "analise", "power bi", "analytics", "sql"],
            "infra": ["infraestrutura", "rede", "suporte", "hardware", "aws", "nuvem", "helpdesk", "sla", "chamados", "acessos"]
        }

    def _load_profile(self):
        """Carrega o JSON externo."""
        if not os.path.exists(self.json_path):
            raise FileNotFoundError(f"Erro: O arquivo '{self.json_path}' não foi encontrado na pasta!")
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _analyze_job_description(self, job_text):
        """
        Analisa o texto da vaga e retorna um score por categoria (tag).
        """
        job_text = job_text.lower()
        scores = {"python": 0, "security": 0, "dados": 0, "infra": 0}
        found_keywords = []

        for category, keywords in self.keyword_map.items():
            for word in keywords:
                # Regex para encontrar a palavra exata (evita falsos positivos como 'data' em 'candidata')
                if re.search(r'\b' + re.escape(word) + r'\b', job_text):
                    scores[category] += 1
                    found_keywords.append(word)
        
        # Define a tag dominante (Se houver empate ou zero, assume 'python' como default)
        dominant_tag = max(scores, key=scores.get) if any(scores.values()) else "python"
        return dominant_tag, scores, found_keywords

    def tailor_resume(self, job_description):
        """
        Constrói o objeto de dados do currículo customizado.
        """
        print(f"🔄 Lendo perfil de: {self.json_path}...")
        dominant_tag, scores, found_keywords = self._analyze_job_description(job_description)
        
        print(f"🤖 ANÁLISE DA VAGA:")
        print(f"   --> Foco Identificado: {dominant_tag.upper()}")
        print(f"   --> Palavras-chave encontradas: {list(set(found_keywords))}")
        print("-" * 30)

        # 1. Selecionar o Resumo Profissional (Summary) mais adequado
        summary_map = {
            "python": "dev_data",
            "dados": "dev_data",
            "security": "security",
            "infra": "support"
        }
        # Pega a chave correta ou usa 'dev_data' como fallback
        selected_summary_key = summary_map.get(dominant_tag, "dev_data")
        
        try:
            tailored_summary = self.profile['profile']['summaries'][selected_summary_key]
        except KeyError:
            # Fallback se a chave não existir no JSON
            tailored_summary = self.profile['profile']['summaries']['dev_data']

        # 2. Reordenar Experiências (Priorizar as mais relevantes)
        experiences = self.profile['profile']['experience_pool']
        
        # A lógica aqui é: Se a tag da experiência bate com a tag da vaga, ela ganha 1 ponto e sobe.
        sorted_experiences = sorted(
            experiences, 
            key=lambda x: 1 if dominant_tag in x.get('tags', []) else 0, 
            reverse=True
        )

        return {
            "name": self.profile['profile']['name'], # <--- ADICIONE ESTA LINHA
            "contact": self.profile['profile']['contact'],
            "selected_summary": tailored_summary,
            "skills": self.profile['profile']['skills'],
            "education": self.profile['profile']['education'],
            "sorted_experiences": sorted_experiences,
            "metadata": {
                "dominant_focus": dominant_tag,
                "keywords": found_keywords
            }
        }

# --- ÁREA DE TESTE (SIMULAÇÃO) ---
if __name__ == "__main__":
    # Simulação de uma vaga que exige SEGURANÇA (copie e cole descrições reais aqui para testar)
    vaga_teste = """
    Vaga: Analista de Cyber Security.
    Requisitos: Conhecimento avançado em NMAP, Burp Suite e Pentest.
    Desejável experiência com Python para scripts de segurança.
    """

    try:
        # Instancia a classe apontando para o arquivo JSON
        brain = ResumeTailor("master_profile.json")
        
        # Executa a mágica
        resultado = brain.tailor_resume(vaga_teste)

        print("\n📄 RESULTADO DO MODELO DE DADOS (PREVIEW):")
        print(f"Candidato: {resultado['name']}") # <--- AGORA ACESSAMOS DIRETO, SEM ['contact']
        print(f"Resumo Aplicado: {resultado['selected_summary'][:100]}...") # Mostra só o começo
        print("\nOrdem das Experiências:")
        for exp in resultado['sorted_experiences']:
            match = "✅ (Match)" if resultado['metadata']['dominant_focus'] in exp['tags'] else "❌"
            print(f"{match} {exp['company']} - {exp['role']}")

    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        print("Verifique se o arquivo 'master_profile.json' está na mesma pasta e se o formato está correto.")