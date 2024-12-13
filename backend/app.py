from flask import Flask,  jsonify, request
from flask_restful import Resource, Api
from flask_cors import CORS
from niftystocks import ns
import yfinance as yf
import psycopg2

app = Flask(__name__)
api = Api(app)

CORS(app)

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
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                '''CREATE TABLE IF NOT EXISTS stocks (
                id serial PRIMARY KEY,
                name varchar(100),
                price float,
                current_price float
                );'''
            )

            conn.commit()
        except Exception as e:
            return {"message": str(e)}, 500
        finally:
            cur.close()
            conn.close()


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
            """
            cur.execute(
                '''CREATE TABLE IF NOT EXISTS stocks (
                id serial PRIMARY KEY,
                name varchar(100),
                price float,
                current_price float
                );'''
            )
            """

            cur.execute(
                '''INSERT INTO stocks (name, price, current_price) VALUES (%s, %s, %s);''',
                (data['name'], data['price'], data['price'])
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


class GetPotId(Resource):
    def get(self, stock_id):
        print("stock id: ", stock_id)
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            
            cur.execute("SELECT * FROM stocks WHERE id = %s", (stock_id,))

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
                id = datas['id']

                try:
                    stock = yf.Ticker(name)
                    stock_info = stock.history(period='1d')

                    if stock_info.empty:
                        continue
                    
                    price_raw = stock_info['Close'].iloc[0]
                    price = f"{price_raw:.2f}"
                
                    update_query = '''UPDATE stocks SET current_price = %s WHERE id = %s'''
                    cur.execute(update_query, (price, id))
                    conn.commit()
                except Exception as stock_error:
                    # Log any issue with fetching stock data
                    print(f"Error fetching data for {name}: {stock_error}")
                    continue
            return jsonify({"message": "Stock prices updated successfully!"})
        except Exception as e:
            return {"message": str(e)}, 500
        finally:
            if 'cur' in locals():
                cur.close()
            conn.close()

    

class Signup(Resource):
    def post(self):
        data = request.get_json()

        email = data["email"]
        username = data["username"]
        password = data["password"]

        if not email or not username or not password:
            return {"message": "Bad request, 'email', 'username' and 'password' are required"}, 400

        conn = get_db_connection()
        try:
            cur = conn.cursor()
        
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password TEXT NOT NULL
                );
            ''')
            

            cur.execute("SELECT 1 FROM users WHERE username = %s;", (username,))
            if cur.fetchone():
                return {"message": "Username already exists. Please choose a different one."}, 400
            else: 
                # Insert the user into the database
                cur.execute(
                    '''INSERT INTO users (email, username, password) VALUES (%s, %s, %s);''',
                    (email, username, password)
                )
                conn.commit()
            
        except Exception as e:
            return {"message": str(e)}, 500
        finally:
            cur.close()
            conn.close()

        return {"message": "User created successfully"}, 201


class Login(Resource):
    def post(self):
        data = request.get_json()

        username = data["username"]
        password = data["password"]

        if not username or not password:
            return {"message": "Bad request, 'username' and 'password' are required"}, 400

        conn = get_db_connection()
        try:
            cur = conn.cursor()

            cur.execute("SELECT 1 FROM users WHERE username = %s;", (username,))
            if  cur.fetchone():
                cur.execute("SELECT password FROM users WHERE username = %s;", (username,))
                user_password = cur.fetchone()[0]

              
                if user_password == password:
                    return {"message": "sucessfully logged IN"}, 200
                else: 
                    return {"message": "failed logged IN"}, 400
            else: 
                return {"message": "Username already exists. Please choose a different one."}, 400
            
            
        except Exception as e:
            return {"message": str(e)}, 500
        finally:
            cur.close()
            conn.close()


class GetHistory(Resource):
    def get(self):
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            
            # Execute the query
            cur.execute("SELECT * FROM history ORDER BY id DESC")

            # Fetch all rows
            rows = cur.fetchall()

            # Get column names from the cursor description
            column_names = [desc[0] for desc in cur.description]
            print("Rows:", rows)
            # Combine column names and rows into a list of dictionaries
            data = [dict(zip(column_names, row)) for row in rows]

            # Return JSON response
            return jsonify(data)
        except Exception as e:
            return jsonify({"message": "Error fetching data", "error": str(e)}), 500
        finally:
            # Ensure the cursor and connection are closed
            if cur:
                cur.close()
            conn.close()

class History(Resource):

    def post(self):
        data = request.json

        stock_name = data['stock_name']
        stock_price = data['price']
        stock_sell_price = data['sell_price']
        stock_total = data['sell_price'] - data['price']

        if not stock_name or not stock_price or not stock_sell_price:
            return {"message": "Bad request, 'stock_name', 'stock_price', 'stock_sell_price' and 'stock_total' are required"}, 400

        conn = get_db_connection()
        try:
            cur = conn.cursor()
        
            cur.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id SERIAL PRIMARY KEY,
                    stock_name VARCHAR(255) NOT NULL,
                    stock_price float,
                    stock_sell_price float,
                    stock_total float,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            cur.execute(
                '''INSERT INTO history (stock_name, stock_price, stock_sell_price, stock_total) VALUES (%s, %s, %s, %s);''',
                (stock_name, stock_price, stock_sell_price, stock_total)
            )
            conn.commit()
            return {"message": "history created successfully"}, 201

        except Exception as e:
            return {"message": str(e)}, 500
        finally:
            cur.close()
            conn.close()

    def get(self):
        pass

api.add_resource(Heello, '/')
api.add_resource(Potfoliyo, '/pot')
api.add_resource(DeletePot, '/del/<int:item_id>')
api.add_resource(GetPot, '/get/pot')
api.add_resource(GetPotId, '/pot/<int:stock_id>')
api.add_resource(UpdatePot, '/put/pot')

#auth
api.add_resource(Signup, '/auth/signup')
api.add_resource(Login, '/auth/login')

#history
api.add_resource(History, '/history')
api.add_resource(GetHistory, '/get/history')

if __name__ == '__main__':
    app.run(debug=True)