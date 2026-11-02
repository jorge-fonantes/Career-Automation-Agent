import argparse
import html
import sys
import time

import config
from history import JobHistory
from job_filter import filtrar
from sources import coletar_vagas
from telegram_notifier import TelegramBot

LIMITE_MENSAGEM = 4000
LIMITE_LOCAL = 60

def resumir_local(local):
    # Vagas LATAM da Himalayas listam dezenas de países
    if len(local) <= LIMITE_LOCAL:
        return local
    return "Brasil e outros países" if "brazil" in local.lower() else local[:LIMITE_LOCAL] + "..."

def formatar_vaga(job):
    titulo = html.escape(job.title)
    url = html.escape(job.url, quote=True)
    linhas = [f'⭐ {job.score} | <a href="{url}">{titulo}</a>']
    empresa = html.escape(job.company) or "Empresa não informada"
    local = html.escape(resumir_local(job.location)) or "Local não informado"
    linhas.append(f"🏢 {empresa} | 🌎 {local}")
    linhas.append(f"🔎 Fonte: {html.escape(job.source)}")
    return "\n".join(linhas)

def montar_mensagens(vagas):
    """ Divide o relatório no limite do Telegram, sabendo quais vagas estão em cada mensagem. """
    mensagens = []
    texto = f"🛠️ <b>SUPORTE TÉCNICO REMOTO</b> ({len(vagas)} novas)\n\n"
    bloco = []
    for job in vagas:
        item = formatar_vaga(job) + "\n\n"
        if bloco and len(texto) + len(item) > LIMITE_MENSAGEM:
            mensagens.append((texto, bloco))
            texto, bloco = "", []
        texto += item
        bloco.append(job)
    if bloco:
        mensagens.append((texto, bloco))
    return mensagens

def buscar_no_navegador():
    # Só importa o Selenium aqui: o modo padrão não precisa de Chrome
    from safe_scanner import SafeScanner

    try:
        bot = SafeScanner()
    except Exception as e:
        print(f"Erro ao abrir navegador: {e}")
        return []

    vagas = []
    try:
        bot.wait_for_login()
        for termo in config.TERMOS_BUSCA_NAVEGADOR:
            print(f"\n🔎 Buscando: {termo}")
            vagas.extend(bot.scan_linkedin(termo))
            vagas.extend(bot.scan_indeed(termo))
            time.sleep(2)
    finally:
        bot.close()
    return vagas

def enviar(vagas, tg, historico):
    """ Só marca como enviada a vaga que chegou, para uma falha não fazer ela sumir. """
    for texto, bloco in montar_mensagens(vagas):
        if not tg.base_url:
            print(texto)
            continue
        if not tg.send_report(texto):
            print("⚠️ Envio interrompido. As vagas restantes voltam na próxima execução.")
            return
        time.sleep(1)
        historico.marcar_enviadas(bloco)

def main():
    # Sem isso, o console do Windows pode quebrar ao imprimir emoji
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Busca vagas remotas de suporte técnico.")
    parser.add_argument("--navegador", action="store_true",
                        help="inclui LinkedIn e Indeed (abre o Chrome e pede login manual)")
    parser.add_argument("--simular", action="store_true",
                        help="mostra as vagas no terminal, sem Telegram e sem gravar histórico")
    args = parser.parse_args()

    print("🤖 --- MÁQUINA DE VAGAS (SUPORTE TÉCNICO REMOTO) ---")

    vagas, falhas = coletar_vagas()
    if args.navegador:
        vagas.extend(buscar_no_navegador())

    selecionadas = filtrar(vagas)
    print(f"\n🎯 Suporte técnico compatível: {len(selecionadas)} de {len(vagas)} vagas lidas")

    if args.simular:
        for job in selecionadas[:config.MAX_VAGAS_RELATORIO]:
            print(f"{job.score:>3} | {job.title} | {job.company} | {resumir_local(job.location)} | {job.source}\n      {job.url}")
        return

    historico = JobHistory(config.ARQUIVO_HISTORICO)
    tg = TelegramBot()
    try:
        novas = historico.novas(selecionadas)
        print(f"✅ Vagas novas: {len(novas)}")

        if novas:
            enviar(novas[:config.MAX_VAGAS_RELATORIO], tg, historico)
        elif not vagas:
            # Sem isso, todas as fontes fora do ar pareceria "nenhuma vaga nova"
            tg.send_report(f"⚠️ Nenhuma fonte respondeu: {html.escape(', '.join(falhas))}")
    finally:
        historico.close()

    print("\n🏁 FIM.")

if __name__ == "__main__":
    main()
