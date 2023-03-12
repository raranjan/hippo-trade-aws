import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import warnings
warnings.filterwarnings('ignore')

options = webdriver.ChromeOptions() #newly added 
options.headless = True
chrome_driver_verison = "110.0.5481.77"

driver = webdriver.Chrome(ChromeDriverManager(version=chrome_driver_verison).install(), options=options)
driver.get("https://in.investing.com/indices/bank-nifty-technical?timeFrame=3600")
html=driver.page_source
soup = BeautifulSoup(html,'html.parser')

section = soup.find("section", {"class": "instrument"})
print(section)