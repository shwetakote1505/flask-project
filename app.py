import os
import json
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from pymongo import MongoClient
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Configuration from env (with sensible defaults)
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGODB_DB = os.getenv('MONGODB_DB', 'testdb')
MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', 'submissions')
APP_SECRET = os.getenv('SECRET_KEY', 'dev_secret_key')

app = Flask(__name__)
app.secret_key = APP_SECRET

# Lazy Mongo client
mongo_client = None

def get_mongo_collection():
    """Return the configured MongoDB collection or None if not configured."""
    global mongo_client
    if not MONGODB_URI:
        return None
    if mongo_client is None:
        mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client[MONGODB_DB]
    return db[MONGODB_COLLECTION]

# ===== Existing API route that serves data.json =====
@app.route('/api', methods=['GET'])
def api_list():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({'error': 'data.json not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== Home / index =====
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# ===== To-Do frontend page (form) =====
@app.route('/todo', methods=['GET'])
def todo():
    return render_template('todo.html')

# ===== New backend route to accept form POST (from HTML form) =====
@app.route('/submittodoitem', methods=['POST'])
def submittodoitem():
    try:
        # If called from HTML form (content-type application/x-www-form-urlencoded)
        itemName = request.form.get('itemName')
        itemDescription = request.form.get('itemDescription')

        # If JSON body is sent (e.g., via fetch/Ajax)
        if not itemName and request.is_json:
            payload = request.get_json()
            itemName = payload.get('itemName')
            itemDescription = payload.get('itemDescription')

        # Validate
        if not itemName or not itemDescription:
            # If request came from browser form, flash + redirect to form
            if 'text/html' in request.headers.get('Accept', ''):
                flash('Item Name and Item Description are required.', 'error')
                return redirect(url_for('todo'))
            return jsonify({'success': False, 'error': 'itemName and itemDescription are required'}), 400

        # Prepare document
        doc = {
            "itemName": itemName,
            "itemDescription": itemDescription
        }

        # Insert into MongoDB
        collection = get_mongo_collection()
        if collection is None:
            # If no DB configured, return error
            if 'text/html' in request.headers.get('Accept', ''):
                flash('MongoDB is not configured.', 'error')
                return redirect(url_for('todo'))
            return jsonify({'success': False, 'error': 'MongoDB is not configured'}), 500

        result = collection.insert_one(doc)

        # If request is HTML form, redirect to success page
        if 'text/html' in request.headers.get('Accept', ''):
            return redirect(url_for('success'))

        return jsonify({'success': True, 'inserted_id': str(result.inserted_id)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== Simple POST endpoint that accepts JSON payload (kept from your prior code) =====
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
        return jsonify({'success': True, 'inserted_id': str(result.inserted_id)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/success')
def success():
    return render_template('success.html')

if __name__ == '__main__':
    # For local development only
    app.run(debug=True)
