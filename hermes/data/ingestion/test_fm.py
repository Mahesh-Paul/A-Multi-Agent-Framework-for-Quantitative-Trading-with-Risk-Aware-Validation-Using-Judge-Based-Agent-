import requests
import os
from dotenv import load_dotenv

load_dotenv()

FMP_API_KEY = os.getenv("FMP_API_KEY")

r = requests.get(f"https://financialmodelingprep.com/api/v3/profile/AAPL?apikey={FMP_API_KEY}")
print(r.json())