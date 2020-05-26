from flask import Flask, render_template, g
import sqlite3 as sql

from helpers import apiprice, error_page

app = Flask(__name__)

DATABASE = 'portfolio.db'

# def get_db():
#     db = getattr(g, '_database',None)
#     if db is None:


#con = sqlite3.connect('portfolio.db')
# cursor = con.cursor()
# print(cursor.execute("SELECT * FROM users"))
# con.commit()
# con.close()

# session.user_id = True

@app.route('/', methods=['GET'])
def index_page_landing():
    userid = 1 #TODO - download from session
    with sql.connect(DATABASE) as con:
        # to have result of .execute as dictionary
        con.row_factory = sql.Row
        cur = con.cursor()

        cur.execute("SELECT * FROM portfolio")
        rows = cur.fetchall()

        # write results of api query in dictionary
        i = 0
        row_api = {}
        total = 0
        for row in rows:
            res = apiprice(row['ticker'])
            if res is not None:
                row_api[i] = {'fullName': res['name'], 'price': res['price'],'fullPrice' : res['price'] * row['number']}

                total += row_api[i]['fullPrice']
                i += 1
            else:
                error_page('Could not load price')

        return render_template('index.html', row=rows, row_api=row_api,length=i)
        con.close()





if __name__ == "__main__":
    app.run()