import os
import json
import time
import re
import pyautogui # A BIBLIOTECA DO MOUSE
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SmartLinkedinBot:
    def __init__(self):
        self.driver = None
        self.options = Options()
        
        # Configuração de segurança do PyAutoGUI
        pyautogui.FAILSAFE = False 
        
        try:
            with open("answers.json", "r", encoding="utf-8") as f:
                self.brain = json.load(f)
        except:
            self.brain = {"keywords_map": {}}

        profile_path = os.path.join(os.getcwd(), "chrome_profile")
        self.options.add_argument(f"user-data-dir={profile_path}")
        
        self.options.add_argument("--lang=pt-BR") 
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-extensions") 
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)

    def start(self):
        os.system("taskkill /f /im chrome.exe >nul 2>&1")
        time.sleep(1)
        print("🕵️‍♂️ Iniciando Robô Híbrido...")
        print("⚠️  ATENÇÃO: NÃO MEXA NO MOUSE ENQUANTO O ROBÔ ESTIVER RODANDO!")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.options)
        
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(3)
        if "login" in self.driver.current_url:
            print("⚠️ FAÇA LOGIN MANUALMENTE!")
            input("Pressione ENTER após logar...")
        
        print("✅ Maximizando janela (OBRIGATÓRIO para o mouse funcionar)...")
        self.driver.maximize_window()

    def human_click(self, element):
        """
        Calcula a posição do elemento na tela e move o mouse físico para clicar nele.
        """
        try:
            # 1. Rola até o elemento ficar no meio da tela
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)

            # 2. Pega informações da geometria da tela e do elemento
            # Precisamos compensar a barra de endereço do Chrome (aprox 110-120px)
            # A matemática abaixo tenta adivinhar onde o elemento está na sua tela física
            
            # Pega posição da janela do navegador
            win_x = self.driver.execute_script("return window.screenX;")
            win_y = self.driver.execute_script("return window.screenY;")
            
            # Pega altura da interface do Chrome (Abas + URL)
            # Geralmente outerHeight - innerHeight dá o tamanho das bordas + barra
            ui_height = self.driver.execute_script("return window.outerHeight - window.innerHeight;")
            
            # Pega posição do elemento relativa à página visível
            rect = element.rect # x, y, width, height
            
            # CALCULO FINAL DO ALVO
            target_x = win_x + rect['x'] + (rect['width'] / 2)
            target_y = win_y + rect['y'] + (rect['height'] / 2) + ui_height

            # Move o mouse e clica
            pyautogui.moveTo(target_x, target_y, duration=0.3)
            pyautogui.click()
            
            # Tira o mouse de cima para não atrapalhar tooltips
            pyautogui.moveRel(-200, 0) 
            
            return True
        except Exception as e:
            print(f"   ⚠️ Erro no clique físico: {e}")
            # Fallback para clique normal se o mouse falhar
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except: return False

    def collect_jobs(self, niche):
        print(f"🔎 Buscando MUNDO TODO: {niche}")
        links = set()
        
        for page in range(0, 250, 25):
            url = f"https://www.linkedin.com/jobs/search/?keywords={niche}&location=Worldwide&geoId=92000000&f_AL=true&f_WT=2&f_TPR=r604800&start={page}"
            try:
                self.driver.get(url)
                time.sleep(3)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                cards = self.driver.find_elements(By.CSS_SELECTOR, "a.job-card-container__link")
                current_links = [c.get_attribute("href").split("?")[0] for c in cards if c.get_attribute("href")]
                
                if not current_links: break
                for href in current_links:
                    if "/jobs/view/" in href: links.add(href)
            except: break
                
        print(f"   + {len(links)} vagas para este nicho.")
        return list(links)

    def _extract_number(self, text):
        nums = re.findall(r'\d+', str(text))
        return nums[0] if nums else "2" 

    def _fill_smart_fields(self, modal_element):
        try:
            inputs = modal_element.find_elements(By.CSS_SELECTOR, "input.artdeco-text-input--input, input[type='text']")
            for inp in inputs:
                parent_txt = ""
                try:
                    inp_id = inp.get_attribute("id")
                    if inp_id:
                        label = modal_element.find_element(By.CSS_SELECTOR, f"label[for='{inp_id}']")
                        parent_txt = label.text.lower()
                except: pass
                
                if not parent_txt: continue
                is_numeric = any(x in parent_txt for x in ["anos", "years", "quanto", "how many", "experiência", "experience"])
                
                for key, val in self.brain['keywords_map'].items():
                    if key in parent_txt and not inp.get_attribute('value'):
                        answer = self._extract_number(val) if is_numeric else val
                        inp.clear()
                        inp.send_keys(answer)
                        break
        except: pass

        try:
            fieldsets = modal_element.find_elements(By.TAG_NAME, "fieldset")
            for fs in fieldsets:
                txt = fs.text.lower()
                for key, val in self.brain['keywords_map'].items():
                    if key in txt:
                        try:
                            labels = fs.find_elements(By.TAG_NAME, "label")
                            for lab in labels:
                                if val.lower() in lab.text.lower():
                                    self.human_click(lab) # Clica com o mouse na opção
                                    break
                        except: pass
        except: pass

        try:
            selects = modal_element.find_elements(By.TAG_NAME, "select")
            for sel in selects:
                try: Select(sel).select_by_index(1) 
                except: pass
        except: pass

    def _close_modal(self):
        try:
            close_btn = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Descartar'], button[aria-label='Dismiss']")
            self.human_click(close_btn)
            time.sleep(1)
            confirm_btn = self.driver.find_elements(By.CSS_SELECTOR, "button[data-test-dialog-primary-btn]")
            if confirm_btn: self.human_click(confirm_btn[0])
            time.sleep(1)
        except: pass

    def smart_apply(self, url, cv_pt, cv_en):
        lang = "EN"
        try:
            self.driver.get(url)
            time.sleep(4)
            
            try: titulo = self.driver.find_element(By.CSS_SELECTOR, "h1").text.lower()
            except: titulo = self.driver.title.lower()
            print(f"   📖 Vaga: {titulo[:45]}...")

            termos_pt = ["analista", "desenvolvedor", "engenheiro", "dados", "brasil", "remoto"]
            is_pt = any(termo in titulo for termo in termos_pt)
            cv_path = cv_pt if is_pt else cv_en
            lang = "PT" if is_pt else "EN"
            print(f"   📄 CV: {lang}")

            # --- BOTÃO INICIAL (USANDO MOUSE FÍSICO) ---
            apply_btn = None
            try: apply_btn = self.driver.find_element(By.CSS_SELECTOR, "a[data-view-name='job-apply-button']")
            except: pass
            
            if not apply_btn:
                try: apply_btn = self.driver.find_element(By.CSS_SELECTOR, ".jobs-apply-button--top-card button")
                except: pass

            if not apply_btn:
                print("   ❌ Botão inicial não encontrado.")
                return False, lang
            
            # AQUI ESTÁ A MÁGICA: O MOUSE VAI ANDAR SOZINHO E CLICAR
            self.human_click(apply_btn)
            
            # Espera o modal abrir
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "jobs-easy-apply-content"))
                )
            except:
                print("   ⚠️ Modal não abriu (Clique falhou ou vaga externa).")
                return False, lang

        except Exception as e:
            print(f"   ⚠️ Erro crítico: {e}")
            return False, lang

        # --- LOOP DENTRO DO MODAL ---
        for step in range(15):
            time.sleep(2)
            
            try:
                modal = self.driver.find_element(By.CLASS_NAME, "jobs-easy-apply-content")
            except:
                if "enviada" in self.driver.page_source.lower() or "submitted" in self.driver.page_source.lower():
                    return True, lang
                return False, lang

            # Upload
            try:
                file_inputs = modal.find_elements(By.CSS_SELECTOR, "input[type='file']")
                for fi in file_inputs:
                    fi.send_keys(cv_path)
                    print(f"   📎 CV Anexado!")
                    time.sleep(2)
            except: pass

            # Preenche
            self._fill_smart_fields(modal)

            # --- CLIQUE FÍSICO NOS BOTÕES DE AÇÃO ---
            clicked = False
            selectors = [
                "button[data-live-test-easy-apply-submit-button]", 
                "button[data-easy-apply-next-button]",             
                "button[data-live-test-easy-apply-review-button]", 
                "button[aria-label='Avançar para próxima etapa']",
                "button.artdeco-button--primary"
            ]
            
            for sel in selectors:
                btns = modal.find_elements(By.CSS_SELECTOR, sel)
                for btn in btns:
                    if btn.is_displayed():
                        # CLIQUE HÍBRIDO!
                        self.human_click(btn)
                        clicked = True
                        
                        txt_check = (btn.text + " " + (btn.get_attribute("aria-label") or "")).lower()
                        if "submit" in txt_check or "enviar" in txt_check:
                            time.sleep(5)
                            if "enviada" in self.driver.page_source.lower() or "submitted" in self.driver.page_source.lower():
                                try: 
                                    dismiss = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Dismiss']")
                                    self.human_click(dismiss)
                                except: pass
                                return True, lang
                        break
                if clicked: break

            if not clicked:
                if "enviada" in self.driver.page_source.lower() or "submitted" in self.driver.page_source.lower():
                    return True, lang
                
                if modal.find_elements(By.CLASS_NAME, "artdeco-inline-feedback--error"):
                    print("   ⚠️ Travado em erro. Pulando.")
                    self._close_modal()
                    return False, lang
            
        self._close_modal()
        return False, lang

    def close(self):
        if self.driver: self.driver.quit()