from flask import Flask, render_template, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_current_user, get_raw_jwt
from flask_sqlalchemy import SQLAlchemy
from pymongo import MongoClient
import requests, json, statistics
from bson.json_util import dumps, loads

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///plaid'

client = MongoClient('localhost', 27017)
nosql_db = client["plaid_project"]
db = SQLAlchemy(app)

# When looking for all-time transactions, arbitrarily long date range
STARTDATE = "1950-01-01"
ENDDATE = "2050-01-01"

# In memory token blacklist
token_blacklist = set()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    item_id = db.Column(db.String(80), unique=True, nullable=True)
    access_token = db.Column(db.String(80), unique=True, nullable=True)

app.config['JWT_BLACKLIST_ENABLED'] = True
app.config["JWT_HEADER_TYPE"] = 'JWT'
jwt = JWTManager(app)

@jwt.user_loader_callback_loader
def user_loader_callback(identity):
    return User.query.filter_by(username=identity).first()

@jwt.token_in_blacklist_loader
def token_in_blacklist(decrypted_token):
    return decrypted_token['jti'] in token_blacklist

@app.route("/")
def index():
    return render_template("app.html");   

@app.route('/api/auth/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    if not username:
        return jsonify({"msg": "No username provided"}), 400

    if (User.query.filter_by(username=username).first()==None):
        return jsonify({"msg": "User by that name does not exist"}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200

@app.route('/api/auth/logout', methods=['DELETE'])
@jwt_required
def logout():
    token_blacklist.add(get_raw_jwt()['jti'])
    print(token_blacklist)
    return jsonify({"msg": "Logged out"}), 200

@app.route("/api/auth/register", methods=['POST'])
def register():
    username = request.json.get('username', None)
    if not username:
        return jsonify({"msg": "No username provided"}), 400

    if (User.query.filter_by(username=username).first()==None):
        new_user = User(username=username,item_id=None, access_token=None)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'msg': "Register OK"}), 200
    return jsonify({'msg': "User by that name already exists"}), 401

@app.route('/api/auth/validateToken', methods=["GET"])
@jwt_required
def validate_token():
    return jsonify({"msg": get_current_user().username}), 200    

@app.route('/api/users/list', methods=["GET"])
def list_users():
    return jsonify({"user_list": [u.username for u in User.query.all()]}), 200

@app.route("/api/users/delete", methods=['DELETE'])
def delete_user():
    username= request.get_json()["username"]
    if (User.query.filter_by(username=username).first()!=None):
        User.query.filter_by(username=username).delete()
        db.session.commit()
        return jsonify({'msg': "User deleted"}), 200
    return jsonify({'msg': 'User does not exist'}), 401

@app.route("/api/banking/takeToken", methods=['POST'])
@jwt_required
def take_token():
    try: 
        user = User.query.filter_by(username=get_current_user().username).first()
        public_token= request.get_json('public_token')["public_token"]
        token_exchange = json.loads(requests.post("https://sandbox.plaid.com/item/public_token/exchange", json={"client_id": "5e19f294e37dd70013289ed0", "secret": "020f82349f79e51db0c2e8292a4394", "public_token": public_token}).text)
        user.access_token = token_exchange["access_token"]
        user.item_id = token_exchange["item_id"]
        db.session.commit()
        return jsonify({'msg': 'Tokens exchanged'}), 200
    except:
        return jsonify({'msg': 'An internal server error occurred'}), 500

@app.route("/api/banking/balance", methods=['GET'])
@jwt_required
def get_balance():
        if get_current_user().access_token==None:
            return jsonify({'msg': 'User must have access token stored first'}), 401
        balance = json.loads(requests.post("https://sandbox.plaid.com/accounts/balance/get", json={"client_id": "5e19f294e37dd70013289ed0", "secret": "020f82349f79e51db0c2e8292a4394", "access_token": get_current_user().access_token}).text)
        retList = []
        for account in balance["accounts"]:
            retDict = {"account_id": account["account_id"], "current_balance": account["balances"]["current"]}
            retList.append(retDict)

        return jsonify({"balances": retList}), 200

@app.route("/api/banking/transactions/save", methods=['POST'])
@jwt_required
def save_transaction():
        if get_current_user().access_token==None:
            return jsonify({'msg': 'User must have access token stored first'}), 401
        remaining = int(json.loads(requests.post("https://sandbox.plaid.com/transactions/get", json={"client_id": "5e19f294e37dd70013289ed0", "secret": "020f82349f79e51db0c2e8292a4394", "access_token": get_current_user().access_token, "start_date": STARTDATE, "end_date": ENDDATE}).text)["total_transactions"])
        offset = 0
        while (offset < remaining):
            get_transactions = json.loads(requests.post("https://sandbox.plaid.com/transactions/get", json={"client_id": "5e19f294e37dd70013289ed0", "secret": "020f82349f79e51db0c2e8292a4394", "access_token": get_current_user().access_token, "start_date": STARTDATE, "end_date": ENDDATE, "options": {"offset": offset}}).text)
            for transaction in get_transactions["transactions"]:
                transaction["username"] = get_current_user().username
                transaction["date"] = int(transaction["date"].replace("-","")) # Compare dates as if they were integers
                nosql_db.transactions.insert(transaction)
            offset = offset + len(get_transactions["transactions"])

        return jsonify({"msg": "Transactions saved."}), 200

@app.route("/api/banking/transactions/stats", methods=['GET'])
@jwt_required
def get_stats():
        if get_current_user().access_token==None:
            return jsonify({'msg': 'User must have access token stored first'}), 401
        if nosql_db.transactions.find({"username": get_current_user().username})==[]:
            return jsonify({'msg': 'User has no transactions stored'}), 401
        categories = nosql_db.transactions.distinct("category")
        responseDict={}
        for category in categories:
            amount_list=[]
            for trans in nosql_db.transactions.find({"category": category, "username": get_current_user().username }):
                amount_list.append(trans["amount"])
            responseDict[category]=amount_list
        Res = {}
        for key, value in responseDict.items():
            Res[key] = {  "freq": max(set(responseDict[key]), key=responseDict[key].count), "avg": statistics.mean(responseDict[key]), "median": statistics.median(responseDict[key]), "max": max(responseDict[key]), "min": min(responseDict[key])}
        return jsonify(Res), 200

@app.route("/api/banking/transactions/filtered", methods=['POST'])
@jwt_required
def filtered_search():
        if get_current_user().access_token==None:
            return jsonify({'msg': 'User must have access token stored first'}), 401
        if nosql_db.transactions.find({"username": get_current_user().username})==[]:
            return jsonify({'msg': 'User has no transactions stored'}), 401
        input_filter = request.get_json()                
        mongo_filter={"username": get_current_user().username}

        if ("lowerBound" in request.get_json().keys() or "upperBound" in request.get_json().keys() or "exactAmount" in request.get_json().keys()):
            mongo_filter["amount"] = {}
    
        if ("startDate" in request.get_json().keys() or "endDate" in request.get_json().keys() or "exactDate" in request.get_json().keys() ):
            mongo_filter["date"] = {}

        if (input_filter.get("categories", None)!=None):
            mongo_filter["category"]={ "$all": input_filter["categories"] }

        if (input_filter.get("lowerBound", None)!=None):
            mongo_filter["amount"]["$gte"]=input_filter["lowerBound"]

        if (input_filter.get("upperBound", None)!=None):
            mongo_filter["amount"]["$lte"]=input_filter["upperBound"]

        if (input_filter.get("exactAmount", None)!=None):
            mongo_filter["amount"]["$lte"]=input_filter["exactAmount"]
            mongo_filter["amount"]["$gte"]=input_filter["exactAmount"]
            
        if (input_filter.get("startDate", None)!=None):
            mongo_filter["date"]["$gte"]=int(input_filter["startDate"].replace("-",""))

        if (input_filter.get("endDate", None)!=None):
            mongo_filter["date"]["$lte"]=int(input_filter["endDate"].replace("-",""))

        if (input_filter.get("exactDate", None)!=None):
            mongo_filter["date"]["$lte"]=int(input_filter["exactDate"].replace("-",""))
            mongo_filter["date"]["$gte"]=int(input_filter["exactDate"].replace("-",""))

        transactions = []
        for trans in nosql_db.transactions.find(mongo_filter):
            trans["_id"]=str(trans["_id"])
            trans["date"]=str(trans["date"])[:4] + "-" + str(trans["date"])[4:6] + "-" + str(trans["date"])[6:8]
            transactions.append(trans)
        return jsonify({"transactions": transactions}), 200
            

if __name__ == "__main__":
    app.secret_key = 'change this'
    app.run(host='127.0.0.1', port=5000, debug=True)
