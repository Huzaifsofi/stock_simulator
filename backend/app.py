from flask import Flask,  jsonify, request
from flask_restful import Resource, Api
from niftystocks import ns
import yfinance as yf
import psycopg2

app = Flask(__name__)
api = Api(app)

def get_db_connection():
    conn = psycopg2.connect(
        host="postgres",
        database="flaskdb",
        user="postgres",
        password="postgrespassword"
    )
    return conn


class Heello(Resource):

    def get(self):
        # Fetch the Nifty 50 tickers
        q = ns.get_nifty50()

        # Pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # Calculate the start and end index for slicing
        start = (page - 1) * per_page
        end = start + per_page

        # Slice the tickers list for pagination
        paginated_tickers = q[start:end]

        stock_data = []
        stock_list = []

        # Collect stock data
        for tickers in paginated_tickers:
            try:
                ticker = f'{tickers}.NS'
                stock = yf.Ticker(ticker)
                stock_info = stock.history(period='1d')
                price = stock_info['Close'].iloc[0]
                stock_data.append((tickers, price))
            except Exception as e:
                print(f"Error fetching data for {tickers}: {e}")

        # Prepare the paginated stock list
        for stock in stock_data:
            stock_dict = {
                'stock_name': stock[0],
                'stock_price': f"{stock[1]:.2f}"
            }
            stock_list.append(stock_dict)

        return jsonify(stock_list)



class Potfoliyo(Resource):

    def post(self):
        # Parse the request data
        data = request.get_json()

        # Validate data
        if 'name' not in data or 'price' not in data:
            return {"message": "Bad request, 'name' and 'price' are required"}, 400

        if isinstance(data['price'], str):
            data['price'] = float(data['price'])

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                '''CREATE TABLE IF NOT EXISTS stocks (
                id serial PRIMARY KEY,
                name varchar(100),
                price float);'''
            )

            cur.execute(
                '''INSERT INTO stocks (name, price) VALUES (%s, %s);''',
                (data['name'], data['price'])
            )
            conn.commit()
        except Exception as e:
            return {"message": str(e)}, 500
        finally:
            cur.close()
            conn.close()


        return {"message": "sucessfully added"}, 201
    

class DeletePot(Resource):
    def delete(self, item_id):
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM stocks WHERE id = %s', (item_id,))
            conn.commit()
            
            if cur.rowcount == 0:
                return {"message": "Item not found"}, 404
            
            return {"message": "Item successfully deleted"}, 200
        except Exception as e:
            return {"message": str(e)}, 500
        finally:
            cur.close()
            conn.close()


class GetPot(Resource):

    def get(self):
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            
            cur.execute('select * from stocks')

            rows = cur.fetchall()

            column_names = [desc[0] for desc in cur.description]
            data = [dict(zip(column_names, row)) for row in rows]

            return jsonify(data)
        except Exception as e:
            return {"message": str(e)}, 500
        finally:
            if 'cur' in locals():
                cur.close()
            conn.close()

        

class UpdatePot(Resource):

    def put(self):
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            
            cur.execute('select * from stocks')

            rows = cur.fetchall()

            column_names = [desc[0] for desc in cur.description]
            data = [dict(zip(column_names, row)) for row in rows]
            for datas in data:
                name = datas['name']
                stock = yf.Ticker(name)
                stock_info = stock.history(period='1d')
                price_raw = stock_info['Close'].iloc[0]
                price = f"{price_raw:.2f}"
                #print(f"Stock: {tickers} - Price: {price:.2f} ")



            return jsonify(data)
        except Exception as e:
            return {"message": str(e)}, 500
        finally:
            if 'cur' in locals():
                cur.close()
            conn.close()

    

    



api.add_resource(Heello, '/')
api.add_resource(Potfoliyo, '/pot')
api.add_resource(DeletePot, '/del/<int:item_id>')
api.add_resource(GetPot, '/get/pot')
api.add_resource(UpdatePot, '/put/pot')

if __name__ == '__main__':
    app.run(debug=True)