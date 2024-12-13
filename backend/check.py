import yfinance as yf
from niftystocks import ns

# List of Nifty 50 stock tickers (partial list, add more as needed)
nifty_50_tickers = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS'
]

q = ns.get_nifty50()

stock_data = []

stock_list = []

for tickers in q:
    try:
        ticker_symbol = f'{tickers}.NS'  # Add .NS to indicate NSE tickers
        stock = yf.Ticker(ticker_symbol)
        stock_info = stock.history(period='1d')

        # Check if stock_info is empty before accessing data
        if stock_info.empty:
            print(f"Stock data not available for {tickers}")
            continue

        # Extract the closing price and format it
        price_raw = stock_info['Close'].iloc[0]
        price = f"{price_raw:.2f}"

        # Append the ticker and price to stock_data list
        stock_data.append((tickers, price))

        print(f"Stock: {tickers} - Price: {price}")
    except Exception as e:
        print(f"Error fetching data for {tickers}: {str(e)}")

"""
for stock in stock_data:
    stock_dict = {
        'stock_name': stock[0],
        'stock_price': {stock[1]:.2f}
    }

    stock_list.append(stock_dict)

    #print(f"Stock: {stock[0]} - Price: {stock[1]:.2f}")
"""