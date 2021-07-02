from flask_pymongo import PyMongo

def initialize_db(app):
    mongo = PyMongo(app)
    db = mongo.db
    accounts_col = db.accounts
    transfers_col = db.transfers
    return (accounts_col, transfers_col)