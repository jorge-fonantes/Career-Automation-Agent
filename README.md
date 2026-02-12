📦 1. requirements.txt

Este arquivo lista todas as bibliotecas externas que o Python precisa baixar para o seu robô funcionar.

Crie um arquivo chamado requirements.txt na raiz do projeto e cole isso:

(Nota: Incluí openai pois seu resume_tailor.py provavelmente usa a API da OpenAI para adaptar o currículo. Se você estiver usando outra IA ou lógica local, pode remover).

Como instalar:
Quem baixar seu projeto (ou você mesmo em outra máquina) só precisará rodar:
pip install -r requirements.txt
📘 2. README.md

Este é o cartão de visitas do seu projeto. Ele explica o que o robô faz, como configurar e como rodar.

Crie um arquivo chamado README.md e cole este conteúdo (ele usa a formatação Markdown, que fica bonita no GitHub):
2. Cérebro do Robô (answers.json)

Configure as respostas padrão para os formulários do LinkedIn no arquivo answers.json:
3. Seu Perfil Base (master_profile.json)

Certifique-se de que seus dados (Experiência, Educação, Skills) estão atualizados neste arquivo JSON para que a IA possa montar os currículos.
▶️ Como Usar

Certifique-se de que o Chrome está fechado e execute:

O robô irá:

    Abrir o navegador (pode pedir login na 1ª vez).

    Coletar vagas.

    Gerar PDFs e aplicar.

    Te avisar no Telegram.

    Limpar os arquivos temporários ao final.

📂 Estrutura do Projeto

    main.py: O maestro que coordena tudo.

    smart_scanner.py: O motor de navegação (Selenium) com lógica anti-crash.

    clean_builder.py: Gerador de PDFs limpos e profissionais (ReportLab).

    resume_tailor.py: Inteligência Artificial que adapta o conteúdo do CV.

    telegram_notifier.py: Módulo de comunicação.

⚠️ Disclaimer

Este projeto é para fins educativos e de automação pessoal. O uso excessivo de automação pode infringir os Termos de Serviço do LinkedIn. Use com moderação e responsabilidade.

Desenvolvido por Jorge Fonantes