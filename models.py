from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class portfolio_db(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    userid = db.Column(db.Integer())
    ticker = db.Column(db.String(64))
    number = db.Column(db.Integer())
    fraction = db.Column(db.Integer())

    def __repr__(self):
        return '<portfolio_db {}>'.format(self.ticker)


class ticker_db(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    userid = db.Column(db.Integer())
    ticker = db.Column(db.String(64))
    number = db.Column(db.Integer())
    currency = db.Column(db.String(64))
    classname = db.Column(db.String(64))

    def __repr__(self):
        return '<ticker_db {}>'.format(self.ticker)

class class_db(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    userid = db.Column(db.Integer())
    classname = db.Column(db.String(64))
    fraction = db.Column(db.Integer())
    diapason = db.Column(db.Integer())
    activeticker = db.Column(db.String(64))

    def __repr__(self):
        return '<class_db {}>'.format(self.classname)


class cash_db(db.Model):
    userid = db.Column(db.Integer(),primary_key=True)
    RUB = db.Column(db.Integer())
    EUR = db.Column(db.Integer())
    USD = db.Column(db.Integer())

    def __repr__(self):
        return '<cash_db {}>'.format(self.userid)

class user_db(db.Model):
    userid = db.Column(db.Integer(),primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64))
    password = db.Column(db.String(64))
    currency = db.Column(db.String(64))
    minsum = db.Column(db.Integer())
    reportfrequency = db.Column(db.Integer())
    reportday = db.Column(db.String(64))

    def __repr__(self):
        return '<user_db {}>'.format(self.name)

# class history(db.Model):
#     userid = db.Column(db.Integer())
#     date = db.Column(db.DateTime, default=datetime.utcnow())