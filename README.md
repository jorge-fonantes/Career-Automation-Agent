# 🤖 Career Automation Agent (LinkedIn Auto-Applier)

> **Automação Inteligente de Candidaturas com Geração de Currículos Dinâmicos**

Este projeto é um agente autônomo desenvolvido em Python que varre o LinkedIn em busca de vagas compatíveis com seu perfil, gera currículos PDF personalizados para cada vaga e realiza a candidatura automaticamente (Easy Apply).

## 🚀 Funcionalidades

* **Busca Massiva:** Varre múltiplos nichos (Dados, Dev, Segurança, Suporte) simultaneamente.
* **Scroll Infinito:** Carrega centenas de vagas automaticamente antes de filtrar.
* **Currículos Dinâmicos (PDF):** Gera um CV em PDF novo para cada vaga, destacando as skills que a descrição pede.
* **Modo Bilíngue:** Detecta se a vaga é internacional e gera o currículo em **Inglês** automaticamente.
* **Preenchimento Inteligente:** Responde formulários de "Anos de Experiência", "Pretensão Salarial" e "Visto" baseado em um arquivo de configuração (`answers.json`).
* **Notificações Telegram:** Envia relatórios em tempo real sobre vagas encontradas e aplicadas direto no seu celular.
* **Anti-Detecção:** Usa perfil local do Chrome e técnicas de navegação humana para evitar bloqueios.

## 🛠️ Instalação

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/career-automation-agent.git](https://github.com/seu-usuario/career-automation-agent.git)
    cd career-automation-agent
    ```

2.  **Crie um ambiente virtual (Opcional, mas recomendado):**
    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # Linux/Mac:
    source .venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Configuração

### 1. Variáveis de Ambiente (`.env`)
Crie um arquivo `.env` na raiz do projeto e adicione suas chaves:
```env
OPENAI_API_KEY=sua_chave_aqui
TELEGRAM_BOT_TOKEN=seu_token_telegram
TELEGRAM_CHAT_ID=seu_chat_id