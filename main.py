import time
from safe_scanner import SafeScanner

# Tenta usar seu notificador do Telegram
try:
    from telegram_notifier import TelegramBot
    has_telegram = True
except:
    has_telegram = False
    print("⚠️ 'telegram_notifier.py' não encontrado. Links aparecerão no terminal.")

def main():
    # SEUS NICHOS (Focados em Tech)
    nichos = [
        "Python Developer", 
        "Cyber Security", 
        "Data Analyst", 
        "DevOps Engineer",
        "Technical Support"
    ]

    print("🤖 --- MÁQUINA DE VAGAS (WORLDWIDE + REMOTE) ---")
    
    # 1. Abre o Navegador
    try:
        bot = SafeScanner()
    except Exception as e:
        print(f"Erro ao abrir navegador: {e}")
        return

    # 2. Login Manual
    bot.wait_for_login()

    if has_telegram:
        tg = TelegramBot()
        tg.send_report("🚀 Scanner Iniciado! Foco: Worldwide & Remote.")

    total_links = []

    # 3. Varredura (Só LinkedIn e Indeed)
    for nicho in nichos:
        print(f"\n🔎 Buscando: {nicho}")
        
        v1 = bot.scan_linkedin(nicho)
        v2 = bot.scan_indeed(nicho)
        
        total_links.extend(v1)
        total_links.extend(v2)
        
        time.sleep(2) 

    # 4. Envio
    print(f"\n✅ Total de vagas novas: {len(total_links)}")
    
    if total_links:
        print("📤 Enviando relatório para Telegram...")
        buffer = f"📊 *VAGAS REMOTAS RECENTES* ({len(total_links)})\n\n"
        
        for item in total_links:
            item_limpo = item + "\n\n"
            
            if len(buffer) + len(item_limpo) > 4000:
                if has_telegram: tg.send_report(buffer)
                else: print(buffer)
                buffer = "" 
                time.sleep(1)
            
            buffer += item_limpo
            
        if has_telegram: tg.send_report(buffer)
        else: print(buffer)
    else:
        msg = "❌ Nenhuma vaga encontrada nas últimas 24h com esses filtros."
        print(msg)
        if has_telegram: tg.send_report(msg)

    print("\n🏁 FIM. O navegador fechará em breve.")
    # Forçamos o fechamento seguro
    bot.close()

if __name__ == "__main__":
    main()