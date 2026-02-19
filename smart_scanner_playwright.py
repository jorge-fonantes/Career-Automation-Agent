import time
import json
import os
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

class SmartLinkedinBot:
    def __init__(self):
        try:
            with open("answers.json", "r", encoding="utf-8") as f:
                self.brain = json.load(f)
        except:
            self.brain = {"keywords_map": {}}

    def start(self, headless=False):
        """
        headless=True -> Roda invisível (minimizado/background).
        headless=False -> Abre a janela para você ver.
        """
        self.playwright = sync_playwright().start()
        
        # Lança o navegador (Chromium é a base do Chrome)
        # args=['--start-maximized'] ajuda a renderizar botões que somem em telas pequenas
        self.browser = self.playwright.chromium.launch(
            headless=headless, 
            args=['--start-maximized'] if not headless else []
        )
        
        # AQUI ESTÁ A CORREÇÃO DO BENGALI E GEOLOCALIZAÇÃO
        self.context = self.browser.new_context(
            locale='pt-BR',
            timezone_id='America/Sao_Paulo',
            geolocation={'latitude': -22.9068, 'longitude': -43.1729}, # Rio de Janeiro
            permissions=['geolocation'],
            viewport={'width': 1920, 'height': 1080} # Força tela grande mesmo invisível
        )
        
        # Aplica camuflagem anti-bot
        self.page = self.context.new_page()
        stealth_sync(self.page)
        
        print("🕵️‍♂️ Robô Playwright Iniciado...")
        
        # Login
        self.page.goto("https://www.linkedin.com/login")
        time.sleep(2)
        
        if "login" in self.page.url:
            print("⚠️ FAÇA LOGIN MANUALMENTE!")
            if headless:
                print("❌ Erro: Não é possível logar manualmente em modo Headless na primeira vez.")
                print("   Rode com headless=False, logue, e salve os cookies (recurso avançado).")
                self.close()
                return
            else:
                input("Pressione ENTER aqui no terminal após fazer login...")

    def collect_jobs(self, niche):
        print(f"🔎 Buscando: {niche}")
        links = set()
        
        for page_num in range(0, 50, 25): # Exemplo: 2 páginas
            url = f"https://www.linkedin.com/jobs/search/?keywords={niche}&location=Worldwide&f_AL=true&start={page_num}"
            try:
                self.page.goto(url)
                
                # Scroll inteligente para carregar vagas
                for _ in range(3):
                    self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                
                # Seleciona os links das vagas (muito mais robusto que o Selenium)
                # O seletor pode variar, mas geralmente é a classe abaixo
                locator = self.page.locator(".job-card-container__link")
                count = locator.count()
                
                for i in range(count):
                    link = locator.nth(i).get_attribute("href")
                    if link and "/jobs/view/" in link:
                        clean_link = link.split("?")[0]
                        links.add(clean_link)
                        
            except Exception as e:
                print(f"⚠️ Erro ao coletar: {e}")
                
        print(f"   + {len(links)} vagas encontradas.")
        return list(links)

    def smart_apply(self, url, cv_pt, cv_en):
        try:
            self.page.goto(url)
            
            # --- TÍTULO DA VAGA ---
            # Tenta pegar o h1. Se falhar, pega o título da página
            try:
                title_locator = self.page.locator("h1")
                job_title = title_locator.first.inner_text().lower()
            except:
                job_title = self.page.title().lower()
                
            print(f"   📖 Vaga: {job_title[:40]}...")
            
            # Decisão de CV
            termos_pt = ["analista", "engenheiro", "dados", "brasil", "remoto"]
            is_pt = any(t in job_title for t in termos_pt)
            cv_path = cv_pt if is_pt else cv_en
            lang = "PT" if is_pt else "EN"
            print(f"   📄 CV: {lang}")

            # --- BOTÃO "CANDIDATURA SIMPLIFICADA" ---
            # O Playwright tem um jeito melhor: get_by_role ou get_by_label
            # Isso clica exatamente no que o usuário vê, ignorando HTML confuso
            
            # Tenta clicar no botão inicial
            # Procura por texto ou aria-label, ignorando maiúsculas/minúsculas
            apply_button = self.page.locator("button, a").filter(has_text=re.compile(r"^(Candidatura simplificada|Easy Apply)$", re.IGNORECASE)).first
            
            if apply_button.count() > 0 and apply_button.is_visible():
                apply_button.click()
            else:
                print("   ❌ Botão inicial não encontrado.")
                return False, lang

            # --- PREENCHIMENTO DO FORMULÁRIO ---
            # O Playwright espera o modal abrir automaticamente
            modal = self.page.locator(".jobs-easy-apply-content")
            
            for step in range(15):
                time.sleep(1) # Pequena pausa humana
                
                # 1. UPLOAD DE CV
                # Procura input file dentro do modal
                file_input = modal.locator("input[type='file']")
                if file_input.count() > 0:
                    try:
                        file_input.set_input_files(cv_path)
                        print("   📎 CV Anexado!")
                        time.sleep(2) # Tempo para upload
                    except: pass

                # 2. BOTÕES DE AÇÃO (Avançar / Enviar)
                # Procura botões primários visíveis dentro do modal
                # Usa Regex para pegar "Avançar", "Next", "Submit", "Enviar"
                primary_btn = modal.locator("button.artdeco-button--primary").first
                
                if primary_btn.is_visible():
                    btn_text = primary_btn.inner_text().lower()
                    
                    # Se for Enviar/Submit
                    if "enviar" in btn_text or "submit" in btn_text:
                        primary_btn.click()
                        print("   ✅ Enviado (provavelmente)!")
                        
                        # Fecha modal de sucesso se aparecer
                        close_btn = self.page.locator("button[aria-label='Dismiss']").first
                        if close_btn.is_visible():
                            close_btn.click()
                        return True, lang
                    
                    # Se for Avançar/Next/Review
                    else:
                        primary_btn.click()
                        continue # Vai para o próximo passo do loop
                
                # Se não achou botão, verifica se tem erro ou se acabou
                error_msg = modal.locator(".artdeco-inline-feedback--error").first
                if error_msg.is_visible():
                    print("   ⚠️ Travado em erro de validação.")
                    self._close_modal()
                    return False, lang
            
            self._close_modal()
            return False, lang

        except Exception as e:
            print(f"   ⚠️ Erro crítico na vaga: {e}")
            return False, lang

    def _close_modal(self):
        try:
            # Clica no X ou no botão de descartar
            dismiss_btn = self.page.locator("button[aria-label='Dismiss']").first
            if dismiss_btn.is_visible():
                dismiss_btn.click()
                
            confirm_discard = self.page.locator("button[data-test-dialog-primary-btn]").first
            if confirm_discard.is_visible():
                confirm_discard.click()
        except: pass

    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

# --- PARA RODAR ---
if __name__ == "__main__":
    bot = SmartLinkedinBot()
    # Mude headless=True para rodar em background (minimizado)
    bot.start(headless=False) 
    
    # Exemplo de uso
    vagas = bot.collect_jobs("Python Developer")
    # ... resto da sua lógica de loop ...