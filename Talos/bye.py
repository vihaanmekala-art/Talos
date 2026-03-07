import requests
API_KEY = "B3B3TBNQS82TUU0G"
symbol = "NVDA"
url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}'

response = requests.get(url)
data = response.json()

# This will show you EVERY key available for NVDA
print(data.keys()) 

# This prints the specific ones you asked for
print(f"P/E Ratio: {data.get('PERatio')}")
print(f"P/S Ratio: {data.get('PriceToSalesRatioTTM')}")