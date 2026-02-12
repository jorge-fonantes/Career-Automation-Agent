from smart_scanner import SmartLinkedinBot
from resume_tailor import ResumeTailor
from clean_builder import PDFResumeBuilder
from telegram_notifier import TelegramBot # Novo
import time
import os
import shutil

def main():
    print("🤖 --- MÁQUINA V5.1: TELEGRAM + CLEANUP ---")
    
    # TELEGRAM
    tg = TelegramBot()
    tg.send_report("🚀 Robô Iniciado! Buscando vagas...")

    nichos = [
        "Analista de Dados", "Python Developer", "Engenheiro de Dados",
        "Analista de Sistemas", "Analista de Segurança da Informação",
        "Cyber Security", "Analista de Suporte", "DevOps"
    ]
    
    bot = SmartLinkedinBot()
    brain = ResumeTailor("master_profile.json")
    builder = PDFResumeBuilder()

    try:
        bot.start()
    except:
        tg.send_report("❌ Erro fatal ao iniciar Chrome.")
        return

    # 1. COLETA
    print("\n📦  COLETANDO...")
    all_links = set()
    for n in nichos:
        links = bot.collect_jobs(n)
        all_links.update(links)
    
    lista = list(all_links)
    msg_vagas = f"✅ {len(lista)} vagas encontradas para processamento."
    print(msg_vagas)
    tg.send_report(msg_vagas)

    sucessos = 0
    falhas = 0

    # 2. DISPARO
    print("\n🔥  APLICANDO...")
    for i, url in enumerate(lista):
        print(f"\n--- {i+1}/{len(lista)} ---")
        
        desc = bot.get_description(url)
        if not desc: continue
        
        is_english = any(x in desc.lower() for x in ["english", "fluent", "advanced"])
        lang = "EN" if is_english else "PT"

        try:
            data = brain.tailor_resume(desc)
            foco = data['metadata']['dominant_focus'].upper()
            nome_arq = f"CV_{foco}_{lang}_{int(time.time())}.pdf"
            path = os.path.abspath(f"output/{nome_arq}")
            
            builder.build(data, path, is_english=is_english)
            
        except Exception as e:
            print(f"❌ Erro CV: {e}")
            continue

        if bot.smart_apply(url, path):
            print("🎉 ENVIADO!")
            tg.send_report(f"✅ Vaga Aplicada: {foco} ({lang})\n{url}")
            sucessos += 1
        else:
            print("⏭️ Falha.")
            falhas += 1

    # 3. RELATÓRIO FINAL E LIMPEZA
    final_report = f"🏁 **FIM DA EXECUÇÃO**\n\n✅ Enviados: {sucessos}\n❌ Pulados: {falhas}"
    tg.send_report(final_report)
    print("\n🧹 Limpando arquivos temporários...")
    
    try:
        # Deleta todos os arquivos da pasta output
        folder = 'output'
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Erro ao deletar {file_path}: {e}")
        print("✨ Pasta output limpa!")
    except Exception as e:
        print(f"Erro na limpeza: {e}")

    bot.close()

if __name__ == "__main__":
    main()