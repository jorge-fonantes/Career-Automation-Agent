import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import random
from urllib.parse import quote_plus

from sources import Job

class SafeScanner:
    def __init__(self):
        print("🔧 Iniciando Chrome Invisível (Undetected)...")
        options = uc.ChromeOptions()
        options.add_argument('--no-first-run')
        options.add_argument('--no-service-autorun')
        options.add_argument('--password-store=basic')
        
        # Tenta evitar o erro de WinError 6 mantendo o processo mais limpo
        self.driver = uc.Chrome(options=options, version_main=None) 
        self.driver.maximize_window()

    def wait_for_login(self):
        print("\n" + "█"*60)
        print("🛑 PAUSA PARA LOGIN (SOMENTE LINKEDIN E INDEED)")
        print("█"*60)
        print("1. Logue no LinkedIn (Mude o idioma para English se puder).")
        print("2. Logue no Indeed.")
        print("3. Resolva CAPTCHAS.")
        print("4. NÃO FECHE O NAVEGADOR.")
        print("█"*60)
        input("👉 APÓS LOGAR, VOLTE AQUI E APERTE [ENTER]...")

    def random_scroll(self):
        # Scroll lento para carregar os elementos
        for _ in range(random.randint(3, 5)):
            self.driver.execute_script(f"window.scrollBy(0, {random.randint(400, 800)});")
            time.sleep(random.uniform(1.5, 3.0))

    def scan_linkedin(self, keyword):
        vagas = []
        seen_links = set()
        # geoId=92000000 -> Worldwide | geoId=106057199 -> Brasil
        for regiao, geo_id in (("Worldwide", 92000000), ("Brasil", 106057199)):
            print(f"   🔵 LinkedIn: Buscando '{keyword}' (Remote/{regiao})...")
            vagas.extend(self._scan_linkedin_regiao(keyword, regiao, geo_id, seen_links))
        return vagas

    def _scan_linkedin_regiao(self, keyword, regiao, geo_id, seen_links):
        vagas = []

        # URL MÁGICA PARA REMOTO + ÚLTIMAS 24H
        # f_WT=2 -> Remote
        # f_TPR=r86400 -> Últimas 24h
        url = f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(keyword)}&f_TPR=r86400&f_WT=2&geoId={geo_id}"

        try:
            self.driver.get(url)
            time.sleep(5)
            self.random_scroll()

            # Seletores atualizados
            cards = self.driver.find_elements(By.CSS_SELECTOR, "a.job-card-container__link, a.job-card-list__title")

            for card in cards[:15]:
                try:
                    link = card.get_attribute("href").split("?")[0]
                    text = card.text.strip().split("\n")[0]

                    if link and "/jobs/view/" in link and link not in seen_links:
                        if text: # Só adiciona se tiver título
                            vagas.append(Job(title=text, company="", url=link, source="LinkedIn", location=regiao))
                            seen_links.add(link)
                except: continue
        except Exception as e:
            print(f"   ⚠️ Erro ao ler LinkedIn: {e}")
        return vagas

    def scan_indeed(self, keyword):
        print(f"   🟣 Indeed: Buscando '{keyword}' (Remote)...")
        vagas = []
        # URL indeed com filtro Remote (&sc=0kf%3Aattr(DSQF7)%3B) e Last 24h (fromage=1)
        url = f"https://br.indeed.com/jobs?q={quote_plus(keyword)}&sc=0kf%3Aattr(DSQF7)%3B&fromage=1"

        try:
            self.driver.get(url)
            time.sleep(6) 
            self.random_scroll()

            cards = self.driver.find_elements(By.CSS_SELECTOR, "h2.jobTitle a, a[data-jk]")
            
            seen_links = set()
            for card in cards[:15]:
                try:
                    link = card.get_attribute("href")
                    try: title = card.find_element(By.TAG_NAME, "span").text
                    except: title = keyword
                    
                    if link and link not in seen_links:
                        vagas.append(Job(title=title, company="", url=link, source="Indeed", location="Brasil"))
                        seen_links.add(link)
                except: continue
        except Exception as e:
            print(f"   ⚠️ Erro ao ler Indeed: {e}")
        return vagas

    def close(self):
        try:
            self.driver.quit()
        except: 
            pass # Ignora erro se já estiver fechado