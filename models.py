from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

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
    hash = db.Column(db.String(128))
    currency = db.Column(db.String(64))
    minsum = db.Column(db.Integer())

    def __repr__(self):
        return '<user_db {}>'.format(self.name)

class week_db(db.Model):
    userid = db.Column(db.Integer(), primary_key=True)
    monday = db.Column(db.Boolean())
    tuesday = db.Column(db.Boolean())
    wednesday = db.Column(db.Boolean())
    thursday = db.Column(db.Boolean())
    friday = db.Column(db.Boolean())
    saturday = db.Column(db.Boolean())
    sunday = db.Column(db.Boolean())

    def __repr__(self):
        return '<week_db {}>'.format(self.userid)