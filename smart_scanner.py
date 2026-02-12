import os
import json
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

class SmartLinkedinBot:
    def __init__(self):
        self.driver = None
        self.options = Options()
        
        try:
            with open("answers.json", "r", encoding="utf-8") as f:
                self.brain = json.load(f)
        except:
            self.brain = {"keywords_map": {}}

        profile_path = os.path.join(os.getcwd(), "chrome_profile")
        self.options.add_argument(f"user-data-dir={profile_path}")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)

    def start(self):
        os.system("taskkill /f /im chrome.exe >nul 2>&1")
        time.sleep(1)
        print("🕵️‍♂️ Iniciando Robô Seguro...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.options)
        
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(3)
        if "login" in self.driver.current_url:
            print("⚠️ FAÇA LOGIN MANUALMENTE!")
            input("Pressione ENTER após logar...")

    def collect_jobs(self, niche):
        print(f"🔎 Buscando: {niche}")
        links = set()
        urls = [
            f"https://www.linkedin.com/jobs/search/?keywords={niche}&location=Brasil&f_AL=true&f_WT=2",
            f"https://www.linkedin.com/jobs/search/?keywords={niche}&location=Rio%20de%20Janeiro%2C%20Brasil&geoId=104105663&f_AL=true&f_WT=3"
        ]
        
        for url in urls:
            try:
                self.driver.get(url)
                time.sleep(3)
                for _ in range(8): # Scroll
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    try: self.driver.find_element(By.CLASS_NAME, 'infinite-scroller__show-more-button').click()
                    except: pass
                
                cards = self.driver.find_elements(By.CLASS_NAME, "job-card-container__link")
                for c in cards:
                    links.add(c.get_attribute("href").split("?")[0])
            except: pass
        
        return list(links)

    def get_description(self, url):
        try:
            self.driver.get(url)
            time.sleep(2)
            try: self.driver.find_element(By.CLASS_NAME, "jobs-description__footer-button").click()
            except: pass
            return self.driver.find_element(By.ID, "job-details").text
        except: return ""

    def _extract_number(self, text):
        nums = re.findall(r'\d+', str(text))
        return nums[0] if nums else "1"

    def _fill_smart_fields(self):
        # 1. INPUTS
        inputs = self.driver.find_elements(By.TAG_NAME, "input")
        for inp in inputs:
            try:
                try: parent_txt = inp.find_element(By.XPATH, "./..").text.lower()
                except: parent_txt = ""
                
                is_numeric = inp.get_attribute("type") == "number" or any(x in parent_txt for x in ["anos", "years", "quanto"])
                
                for key, val in self.brain['keywords_map'].items():
                    if key in parent_txt and not inp.get_attribute('value'):
                        answer = self._extract_number(val) if is_numeric else val
                        inp.send_keys(answer)
                        print(f"   ✍️  Preenchi: '{answer}' ({key})")
                        break
            except: pass

        # 2. SELECTS (Com Segurança Anti-Bengali)
        # Só pega selects que estão dentro do modal de aplicação
        try:
            modal = self.driver.find_element(By.CLASS_NAME, "jobs-easy-apply-content")
            selects = modal.find_elements(By.TAG_NAME, "select")
            
            for sel in selects:
                try:
                    parent_txt = sel.find_element(By.XPATH, "./..").text.lower()
                    dropdown = Select(sel)
                    
                    # A. Tenta achar no JSON
                    found = False
                    for key, val in self.brain['keywords_map'].items():
                        if key in parent_txt:
                            try:
                                dropdown.select_by_visible_text(val)
                                found = True
                                break
                            except: pass

                    # B. Regra Especial para País/Telefone
                    if not found and ("phone" in parent_txt or "país" in parent_txt or "country" in parent_txt):
                        try:
                            dropdown.select_by_visible_text("Brazil (+55)")
                            print("   🇧🇷 Selecionei Brasil (+55)")
                            found = True
                        except: pass

                    # C. NÃO CLICAMOS MAIS ALEATORIAMENTE
                    # Se não achou resposta, deixa em branco pro humano ver ou pula
                    
                except: pass
        except: pass # Se não achou modal, não faz nada

        # 3. RADIOS
        try:
            fieldsets = self.driver.find_elements(By.TAG_NAME, "fieldset")
            for fs in fieldsets:
                q = fs.text.lower()
                for key, val in self.brain['keywords_map'].items():
                    if key in q:
                        opts = fs.find_elements(By.TAG_NAME, "label")
                        for opt in opts:
                            if val.lower() in opt.text.lower():
                                opt.click()
                                break
        except: pass

    def smart_apply(self, url, cv_path):
        print(f"⚡ Aplicando: {url}")
        try:
            self.driver.get(url)
            time.sleep(3)
            btns = self.driver.find_elements(By.TAG_NAME, "button")
            apply = next((b for b in btns if "Candidatura simplificada" in b.text or "Easy Apply" in b.text), None)
            if not apply: return False
            apply.click()
        except: return False

        for _ in range(12):
            time.sleep(2)
            try:
                self.driver.find_element(By.CSS_SELECTOR, "input[type='file']").send_keys(cv_path)
            except: pass

            self._fill_smart_fields()

            btns = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'artdeco-button--primary')]")
            clicked = False
            for btn in btns:
                txt = btn.text.lower()
                if "enviar" in txt or "submit" in txt:
                    btn.click()
                    time.sleep(3)
                    if "enviada" in self.driver.page_source or "submitted" in self.driver.page_source: return True
                    try: self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Fechar']").click()
                    except: pass
                    return True
                
                if "avançar" in txt or "next" in txt or "revisar" in txt or "review" in txt:
                    btn.click()
                    clicked = True
                    break
            
            if not clicked:
                if "enviada" in self.driver.page_source: return True
                # Se tiver erro, o robô para nessa vaga e vai pra próxima (evita loop infinito)
                if self.driver.find_elements(By.CLASS_NAME, "artdeco-inline-feedback--error"):
                    print("   ⚠️  Travado em erro. Pulando.")
                    return False

        return False

    def close(self):
        if self.driver: self.driver.quit()