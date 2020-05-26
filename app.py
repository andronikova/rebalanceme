from flask import Flask, render_template, g
import sqlite3 as sql

from helpers import apiprice

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
        cur = con.cursor()

        cur.execute("SELECT * FROM portfolio")
        rows = cur.fetchall()

    return render_template('index.html', row=rows)
    con.close()



if __name__ == "__main__":
    app.run()