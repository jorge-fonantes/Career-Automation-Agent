import time
import json
import os
import re
from playwright.sync_api import sync_playwright

class SmartLinkedinBot:
    def __init__(self):
        try:
            with open("answers.json", "r", encoding="utf-8") as f:
                self.brain = json.load(f)
        except:
            self.brain = {"keywords_map": {}}

    def start_connected(self):
        """Conecta ao Chrome aberto na porta 9222"""
        self.p = sync_playwright().start()
        
        print("🔌 Conectando ao Chrome na porta 9222...")
        try:
            # Conecta na sessão existente
            self.browser = self.p.chromium.connect_over_cdp("http://localhost:9222")
            
            # Pega a aba que já está aberta
            context = self.browser.contexts[0]
            if context.pages:
                self.page = context.pages[0]
            else:
                self.page = context.new_page()
                
            print("✅ Conectado! Usando sua sessão logada.")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            print("Certifique-se de que rodou o comando no PowerShell:")
            print('& "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\\chrome_debug_profile"')
            return False

    def collect_jobs(self, niche):
        print(f"🔎 Buscando: {niche}")
        links = set()
        
        for start in range(0, 50, 25): 
            url = f"https://www.linkedin.com/jobs/search/?keywords={niche}&location=Worldwide&f_AL=true&start={start}"
            try:
                self.page.goto(url)
                time.sleep(2)
                
                # Scroll
                for _ in range(3):
                    self.page.mouse.wheel(0, 1000)
                    time.sleep(1)
                
                job_links = self.page.locator("a.job-card-container__link").all()
                for link in job_links:
                    href = link.get_attribute("href")
                    if href and "/jobs/view/" in href:
                        # --- CORREÇÃO DO URL INVÁLIDO AQUI ---
                        clean_link = href.split("?")[0]
                        if not clean_link.startswith("http"):
                            clean_link = "https://www.linkedin.com" + clean_link
                        
                        links.add(clean_link)
                        
            except Exception as e:
                print(f"⚠️ Erro na coleta: {e}")
                
        print(f"   + {len(links)} vagas encontradas.")
        return list(links)

    def _smart_fill(self):
        try:
            # Inputs de texto
            inputs = self.page.locator("input[type='text'], input.artdeco-text-input--input").all()
            for inp in inputs:
                if not inp.is_visible(): continue
                
                try:
                    label_id = inp.get_attribute("id")
                    label_text = self.page.locator(f"label[for='{label_id}']").inner_text().lower()
                except:
                    label_text = ""
                
                if not label_text: continue

                for key, val in self.brain['keywords_map'].items():
                    if key in label_text and not inp.input_value():
                        answer = val
                        if any(x in label_text for x in ["anos", "years", "quanto", "experience"]):
                            answer = "".join(filter(str.isdigit, val)) or "2"
                        
                        inp.fill(answer)
                        print(f"   ✍️ Preenchi: {answer}")
                        break

            # Radio Buttons
            fieldsets = self.page.locator("fieldset").all()
            for fs in fieldsets:
                text = fs.inner_text().lower()
                for key, val in self.brain['keywords_map'].items():
                    if key in text:
                        target = fs.locator(f"label:has-text('{val}')").first
                        if target.is_visible():
                            target.click()

            # Selects
            selects = self.page.locator("select").all()
            for s in selects:
                if s.is_visible() and not s.input_value():
                    try: s.select_option(index=1)
                    except: pass
        except: pass

    def apply_to_job(self, url, cv_pt, cv_en):
        try:
            self.page.goto(url)
            time.sleep(2)
            
            try:
                title = self.page.locator("h1").first.inner_text().lower()
            except: 
                title = "vaga desconhecida"
                
            is_pt = any(x in title for x in ["analista", "dados", "brasil", "remoto", "desenvolvedor"])
            cv = cv_pt if is_pt else cv_en
            lang = "PT" if is_pt else "EN"
            print(f"   📖 {title[:40]}... ({lang})")

            # CLIQUE INICIAL
            apply_btn = self.page.locator('a[data-view-name="job-apply-button"]').first
            
            if not apply_btn.is_visible():
                apply_btn = self.page.locator('.jobs-apply-button--top-card button').first
            
            if not apply_btn.is_visible():
                 apply_btn = self.page.locator("button, a").filter(has_text=re.compile(r"^(Candidatura simplificada|Easy Apply)$")).first

            if apply_btn.is_visible():
                apply_btn.click()
            else:
                print("   ❌ Botão de candidatura não encontrado.")
                return False

            # --- LOOP DO FORMULÁRIO ---
            modal = self.page.locator(".jobs-easy-apply-content")
            
            for step in range(15):
                time.sleep(1.5)
                
                if not modal.is_visible():
                    if self.page.locator("text=Candidatura enviada").is_visible() or self.page.locator("text=Application submitted").is_visible():
                        return True
                    return False

                # Upload CV
                file_input = modal.locator("input[type='file']").first
                if file_input.is_visible():
                    try:
                        file_input.set_input_files(cv)
                        print("   📎 CV Anexado")
                        time.sleep(2)
                    except: pass

                # Preenche campos
                self._smart_fill()

                # --- BOTÕES DE AÇÃO ---
                btn_submit = modal.locator("button[data-live-test-easy-apply-submit-button]").first
                if btn_submit.is_visible():
                    btn_submit.click()
                    print("   ✅ Botão Enviar clicado!")
                    time.sleep(4)
                    try: self.page.locator("button[aria-label='Dismiss']").click(timeout=2000)
                    except: pass
                    return True

                btn_next = modal.locator("button[data-easy-apply-next-button]").first
                if not btn_next.is_visible():
                    btn_next = modal.locator("button").filter(has_text="Avançar").first

                if btn_next.is_visible():
                    btn_next.click()
                    continue 

                btn_review = modal.locator("button[data-live-test-easy-apply-review-button]").first
                if btn_review.is_visible():
                    btn_review.click()
                    continue

                if modal.locator(".artdeco-inline-feedback--error").is_visible():
                    print("   ⚠️ Travado em erro de validação.")
                    self.page.locator("button[aria-label='Dismiss']").click()
                    self.page.locator("[data-test-dialog-primary-btn]").click()
                    return False

            return False

        except Exception as e:
            print(f"   ⚠️ Erro: {e}")
            return False

# --- EXECUÇÃO ---
if __name__ == "__main__":
    # ⚠️ CAMINHOS DOS SEUS CURRÍCULOS
    CV_PT = r"C:\Users\Jorge\Documents\Career-Automation-Agent\curriculo_pt.pdf"
    CV_EN = r"C:\Users\Jorge\Documents\Career-Automation-Agent\curriculo_en.pdf"

    bot = SmartLinkedinBot()
    
    if bot.start_connected():
        vagas = bot.collect_jobs("Python Developer")
        
        print(f"\n🔥 Processando {len(vagas)} vagas...")
        for i, vaga in enumerate(vagas):
            print(f"\n--- {i+1}/{len(vagas)} ---")
            result = bot.apply_to_job(vaga, CV_PT, CV_EN)
            if result:
                print("🎉 SUCESSO!")
            else:
                print("⏭️ Próxima...")