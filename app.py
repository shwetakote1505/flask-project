import os
import json
from flask import Flask, request, jsonify, render_template, redirect, url_for
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB', 'testdb')
MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', 'submissions')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev')

mongo_client = None

def get_mongo_collection():
    global mongo_client
    if not MONGODB_URI:
        return None
    if mongo_client is None:
        mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client[MONGODB_DB]
    return db[MONGODB_COLLECTION]

@app.route('/api', methods=['GET'])
def api_list():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except:
        return jsonify({'error': 'Something went wrong'}), 500

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({'success': False, 'error': 'Empty payload'}), 400

        name = payload.get('name')
        email = payload.get('email')

        if not name or not email:
            return jsonify({'success': False, 'error': 'Name and Email required'}), 400

        collection = get_mongo_collection()
        if collection is None:
            return jsonify({'success': False, 'error': 'MongoDB is not configured'}), 500


        result = collection.insert_one(payload)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/success')
def success():
    return render_template('success.html')

if __name__ == '__main__':
    app.run(debug=True)
