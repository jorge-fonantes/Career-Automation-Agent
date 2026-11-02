# 🛠️ Career Automation Agent (Suporte Técnico Remoto)

> **Foco:** Suporte técnico, help desk e service desk 100% remotos, abertos para quem mora no Brasil

Agregador que procura vagas em fontes públicas, descarta o que não é suporte técnico ou não aceita candidatos no Brasil, ordena o restante e envia só as novidades para o seu **Telegram**. Ele não se candidata por você: entrega a vaga, você aplica.

## 🚀 Funcionalidades

- **Sem login e sem CAPTCHA:** o modo padrão usa APIs e feeds públicos, então pode rodar agendado, sem ninguém por perto.
- **Filtro de área:** aceita suporte técnico, help desk e service desk. Títulos ambíguos como "Customer Support" só passam se a descrição for técnica.
- **Filtro de localidade:** aceita Brasil, LATAM, Americas e Worldwide. Descarta restrições como "USA Only", inclusive quando aparecem no título ou na descrição.
- **Pontuação:** vagas para Brasil/LATAM e de nível inicial aparecem primeiro.
- **Só novidades:** o histórico evita repetir vagas, e a mesma vaga publicada em duas fontes aparece uma vez.
- **Nada se perde:** a vaga só entra no histórico depois que o Telegram confirma o envio.

## 🌐 Fontes

| Fonte | Tipo | Precisa de login? |
| --- | --- | --- |
| Remotive | API pública | Não |
| Remote OK | API pública | Não |
| We Work Remotely | RSS | Não |
| Himalayas | API pública | Não |
| Jobicy | API pública | Não |
| LinkedIn e Indeed | Chrome (`--navegador`) | Sim, manual |

As fontes públicas têm poucas vagas escritas em português. Para ampliar a busca no Brasil, use `--navegador`.

## 📦 Instalação

Requer Python 3.10 ou superior.

```bash
git clone https://github.com/jorge-fonantes/Career-Automation-Agent.git
cd Career-Automation-Agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz do projeto. Sem ele, as vagas aparecem só no terminal.

```
TELEGRAM_BOT_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_chat_id
```

## ▶️ Como usar

```bash
python main.py              # busca e envia as vagas novas
python main.py --simular    # só mostra no terminal, sem enviar nem gravar histórico
python main.py --navegador  # inclui LinkedIn e Indeed (abre o Chrome e pede login manual)
python -m pytest            # roda os testes
```

## ⏰ Automação na nuvem

O GitHub Actions roda a busca a cada 6 horas, mesmo com o computador desligado (`.github/workflows/buscar-vagas.yml`). Para ativar, cadastre em **Settings > Secrets and variables > Actions** os segredos `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`.

O histórico `vagas_vistas.sqlite3` fica no repositório, para a nuvem lembrar o que já enviou. Ele guarda só títulos e links públicos de vagas. Antes de rodar a busca no computador, use `git pull` para não reenviar vagas.

## ⚙️ Personalização

Tudo que define o tipo de vaga fica em `config.py`: termos de busca, títulos aceitos e excluídos, localidades, idade máxima da vaga e limite por relatório.

## 🔮 Roadmap

- [ ] Adicionar **Gupy** e outras fontes de vagas em português.
- [ ] Adicionar **Greenhouse** e **Lever** de empresas remote-first.
- [ ] Filtro de salário.

Remotive, Remote OK e Jobicy pedem crédito e link para a vaga original. O relatório já mostra a fonte e usa o link original.
