from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class portfolio(db.Model):
    userid = db.Column(db.Integer(),primary_key=True)
    ticker = db.Column(db.String())
    number = db.Column(db.Integer())
    fraction = db.Column(db.Integer())

    # def __init__(self, userid, ticker, number, fraction):
    #     self.userid = userid
    #     self.ticker = ticker
    #     self.number = number
    #     self.fraction = fraction

    def __repr__(self):
        return '<portfolio {}>'.format(self.ticker)


class cash(db.Model):
    userid = db.Column(db.Integer())
    rub = db.Column(db.Integer())
    euro = db.Column(db.Integer())
    usd = db.Column(db.Integer())

    # def __init__(self, userid, rub, euro, usd):
    #     self.userid = userid
    #     self.rub = rub
    #     self.euro = euro
    #     self.usd = usd

    def __repr__(self):
        return '<cash {}>'.format(self.userid)

class history(db.Model):
    userid = db.Column(db.Integer())
    date = db.Column(db.DateTime, default=datetime.utcnow())