import os
import json
import time
import pyautogui
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
        pyautogui.FAILSAFE = False
        self.img_folder = os.path.join(os.getcwd(), "img") 

        try:
            with open("answers.json", "r", encoding="utf-8") as f:
                self.brain = json.load(f)
        except:
            self.brain = {}

        profile_path = os.path.join(os.getcwd(), "chrome_profile")
        self.options.add_argument(f"user-data-dir={profile_path}")
        self.options.add_argument("--lang=pt-BR") 
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)

    def start(self):
        os.system("taskkill /f /im chrome.exe >nul 2>&1")
        print("🕵️‍♂️ Iniciando V15 (Scroll + Visão + Volume)...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.options)
        self.driver.get("https://www.linkedin.com/login")
        self.driver.maximize_window()
        time.sleep(3)
        if "login" in self.driver.current_url:
            print("⚠️ FAÇA LOGIN MANUALMENTE!")
            input("Pressione ENTER após logar...")

    def collect_jobs(self, niche):
        print(f"🔎 Buscando: {niche}")
        links = set()
        # MUDANÇA 1: Aumentei range e adicionei f_TPR=r604800 (Última Semana) para ter mais vagas
        for page in range(0, 100, 25): 
            url = f"https://www.linkedin.com/jobs/search/?keywords={niche}&location=Worldwide&f_AL=true&f_TPR=r604800&start={page}"
            try:
                self.driver.get(url)
                time.sleep(2)
                # Scroll na página de busca para carregar mais
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                cards = self.driver.find_elements(By.CSS_SELECTOR, "a.job-card-container__link")
                for c in cards:
                    href = c.get_attribute("href")
                    if href and "/jobs/view/" in href:
                        links.add(href.split("?")[0])
            except: break
        return list(links)

    def _scroll_modal(self, modal):
        """ Rola o modal para baixo para revelar botões escondidos """
        try:
            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", modal)
            time.sleep(0.5)
        except: pass

    def _visual_click(self, image_name, confidence=0.7):
        """ Procura e clica (Confiança ajustada para 0.7 para achar mais fácil) """
        img_path = os.path.join(self.img_folder, image_name)
        if not os.path.exists(img_path): return False
        try:
            location = pyautogui.locateCenterOnScreen(img_path, confidence=confidence)
            if location:
                print(f"   👁️ Visualizado: {image_name}")
                pyautogui.click(location)
                time.sleep(1)
                return True
        except: pass
        return False

    def _is_on_screen(self, image_name, confidence=0.7):
        img_path = os.path.join(self.img_folder, image_name)
        if not os.path.exists(img_path): return False
        try:
            return pyautogui.locateOnScreen(img_path, confidence=confidence) is not None
        except: return False

    def _unfollow_company(self, modal):
        try:
            labels = modal.find_elements(By.TAG_NAME, "label")
            for label in labels:
                txt = label.text.lower()
                if "follow" in txt or "seguir" in txt:
                    try:
                        inp = label.find_element(By.CSS_SELECTOR, "input")
                        if inp.is_selected():
                            print("   🚫 Unfollow via Código")
                            self.driver.execute_script("arguments[0].click();", inp)
                    except:
                        label.click()
        except: pass

    def _solve_questions(self, modal):
        try:
            inputs = modal.find_elements(By.CSS_SELECTOR, "input, textarea")
            for inp in inputs:
                if inp.is_displayed() and not inp.get_attribute("value"):
                    if "text" in inp.get_attribute("type"):
                        inp.send_keys("1")
        except: pass

    def smart_apply(self, url, cv_type):
        try:
            self.driver.get(url)
            time.sleep(3)

            # 1. ABRIR EASY APPLY (Tenta Visual Primeiro)
            clicked = False
            if self._visual_click("easy_apply.png", confidence=0.7): clicked = True
            
            if not clicked:
                try:
                    btns = self.driver.find_elements(By.CSS_SELECTOR, "button.jobs-apply-button")
                    for btn in btns:
                        if "simplificada" in btn.text.lower() or "easy" in btn.text.lower():
                            btn.click()
                            clicked = True
                            break
                except: pass

            if not clicked:
                print("   ⏭️ Vaga externa (Botão não reconhecido).")
                return False

            # 2. LOOP DE NAVEGAÇÃO
            time.sleep(2)
            for step in range(20): # Aumentei passos
                # Sucesso?
                if "enviada" in self.driver.page_source.lower() or "submitted" in self.driver.page_source.lower():
                    return True

                try:
                    modal = self.driver.find_element(By.CLASS_NAME, "jobs-easy-apply-content")
                except:
                    if step > 2: return True 
                    return False

                self._solve_questions(modal)
                
                # MUDANÇA CRUCIAL: Rola o modal para baixo antes de procurar botões!
                self._scroll_modal(modal) 

                # 3. LÓGICA DE ENVIO (SUBMIT)
                # Procura o botão visualmente APÓS rolar a tela
                if self._is_on_screen("submit.png", confidence=0.7):
                    print("   🚀 Botão Submit na tela!")
                    self._unfollow_company(modal) # Garante unfollow
                    time.sleep(0.5)
                    self._visual_click("submit.png", confidence=0.7) # Clica
                    time.sleep(4)
                    return True

                # 4. NAVEGAÇÃO (NEXT/REVIEW)
                avancou = False
                if self._visual_click("review.png", confidence=0.7): avancou = True
                elif self._visual_click("next.png", confidence=0.7): avancou = True
                
                # Fallback Código
                if not avancou:
                    try:
                        btns = modal.find_elements(By.CSS_SELECTOR, "button.artdeco-button--primary")
                        for btn in btns:
                            txt = btn.text.lower()
                            # Só clica se NÃO for submit/enviar (para respeitar a lógica visual acima)
                            if "submit" not in txt and "enviar" not in txt:
                                btn.click()
                                time.sleep(2)
                                break
                    except: pass
                
                time.sleep(2)

            return False

        except Exception as e:
            print(f"Erro: {e}")
            return False

    def close(self):
        if self.driver: self.driver.quit()