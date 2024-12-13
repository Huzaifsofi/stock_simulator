from niftystocks import ns
#from jugaad_data.nse import NSELive
import json
import requests
from bs4 import BeautifulSoup





stock_list = []

q = ns.get_nifty50()

for item in q:
    try:
        url = f'https://www.google.com/finance/quote/{item}:NSE'
        
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            stock_name = soup.find('div', {'role': 'heading', 'aria-level': '1', 'class': 'zzDege'}).text
            stock_price_div = price_text = soup.find('div', class_='YMlKec fxKbKc').text
            stock_price = price_text.replace('₹', '')

            if stock_name and stock_price_div:
                stock_data = {
                    'stock_code': item,
                    'company_name': stock_name,
                    'current_price': stock_price
                }

                stock_list.append(stock_data)
            else:
                pass
    except:
        pass


stock_data_json = json.dumps(stock_list, indent=4)
print(stock_data_json)

