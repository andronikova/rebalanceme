from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class portfolio_db(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    userid = db.Column(db.Integer())
    ticker = db.Column(db.String(64))
    number = db.Column(db.Integer())
    fraction = db.Column(db.Integer())

    def __repr__(self):
        return '<portfolio_db {}>'.format(self.ticker)


class cash_db(db.Model):
    userid = db.Column(db.Integer(),primary_key=True)
    rub = db.Column(db.Integer())
    euro = db.Column(db.Integer())
    usd = db.Column(db.Integer())

    def __repr__(self):
        return '<cash_db {}>'.format(self.userid)

# class history(db.Model):
#     userid = db.Column(db.Integer())
#     date = db.Column(db.DateTime, default=datetime.utcnow())