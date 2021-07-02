
from flask import Flask, jsonify, request
from bson import ObjectId
from pymongo.errors import BulkWriteError, DuplicateKeyError
from datetime import datetime

#Initialize the mongodb db and the collections that we will use in the app
from database.db import initialize_db

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'db'
app.config['MONGO_URI'] = 'mongodb://mongo:27017/db'
app.config['JSON_SORT_KEYS'] = False

accounts_collection, transfers_collection = initialize_db(app)    

@app.route('/accounts', methods=['GET'])
def get_all_customers():
  """
  Input: None
  Output: A json containing all of the accounts present in the DB

  This method will go over all the accounts present in the database and returns a JSON
  """
  output = [cust for cust in accounts_collection.find({}, {'_id': 0})]
  return jsonify({'result' : output})


@app.route("/account/<account_id>", methods=['GET'])
def get_one_customer(account_id):
  """
  Input: account_id
  Output: JSON representing the information related to the account id passed as a parameter

  This method returns the data (id, name, balance) associated to a given account id
  """
  output = accounts_collection.find_one_or_404({"_id": ObjectId(account_id)}, {"_id": 0})
  return jsonify({'result' : output})


@app.route('/balance/<account_id>', methods=['GET'])
def get_account_balance(account_id):
  """
  Input: account_id
  Output: JSON only containing the balance associated to the account id

  This method with search in the db for a field matching the requested account
  id and only display its balance.
  """
  output = accounts_collection.find_one_or_404({"_id": ObjectId(account_id)}, {"balance": 1, "_id": 0})
  return jsonify({'result' : output})


@app.route('/account', methods=['POST'])
def add_one_account():
  """
  Input: JSON from the POST request: name of the customer & initial balance
  Output: JSON corresponding to the added account (name + balance)

  This method allows anyone to add one user to the mongoDB by providing a name and a balance.
  The POST request takes a JSON with key-values such as the following example:

  {
    "name" : "Simon Cariou",
    "balance" : 12345
  }

  """
  name = request.json['name']
  balance = request.json['balance']
  account_id = accounts_collection.insert({'name': name, 'balance': balance})
  new_account = accounts_collection.find_one_or_404({'_id': account_id})
  output = {'name' : new_account['name'], 'balance' : new_account['balance']}
  return jsonify({'result' : output})


@app.route('/transfer', methods=['PUT'])
def transfer():
  """
  This method allows to transfer funds between 2 accounts: the emitter and the receiver
  An entry is added to the transfer collection in order to keep track of all the transfers
  made by anyone.
  The PUT request takes a JSON with key-values such as the following example:
  
  {
    "emitter" : "60cc868f89089e7208d48544",
    "receiver" : "60cc868f89089e7208d48545",
    "amount" : 50
  }
  """
  id_emitter = request.json['emitter']
  id_receiver = request.json['receiver']
  transfered_amount = request.json['amount']

  #Get the balance of the emitter's account in order to check that he/she has sufficient fund to make the transfer
  initial_balance_emitter = accounts_collection.find_one_or_404({"_id": ObjectId(id_emitter)})["balance"]

  #Check that the balance of the emitter is sufficient to send the amount of money set in the request:
  if(initial_balance_emitter - transfered_amount > 0 ):
    #Updating the balance of the emitter (substract the amount that is transfered to the balance)
    accounts_collection.update_one({"_id": ObjectId(id_emitter)}, {'$inc': {'balance': -transfered_amount}})

    #Updating the balance of the receiver (add the amount that is transfered to the balance)
    accounts_collection.update_one({"_id": ObjectId(id_receiver)}, {'$inc': {'balance': transfered_amount}})
    return_msg = "Success"

    #Add the transfer to the transfer history
    transfers_collection.insert_one({"date": f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                                "emitter":id_emitter,
                                "receiver": id_receiver,
                                "amount": transfered_amount})

  else:
    return_msg = "Error, insufficient funds"

  

  return jsonify({'result' : return_msg})


@app.route('/transfers/<emitter_account_id>', methods=['GET'])
def get_account_transfer_history(emitter_account_id):
  """
  Input: emitter_account_id
  Output: JSON only containing all of the transfers that the given account_id has made.

  This method with search in the transfers collection and will spit out all of the transfers matching
  the account_id
  """
  output = [transfer for transfer in transfers_collection.find({"emitter": emitter_account_id}, {"_id": 0})]
  return jsonify({'result' : output})

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)