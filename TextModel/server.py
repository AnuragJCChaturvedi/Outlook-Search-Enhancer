from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import json

from main import query_emails

jsonldata = None

jsonl_file_path = "deleted_items.jsonl"

with open(jsonl_file_path, 'r') as file:
    jsonldata = [json.loads(line.strip()) for line in file]

# Create a Flask app instance
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Define a route for the root URL
@app.route('/')
def home():
    return "Hello, World!"

# Define a route that accepts POST requests
@app.route('/api/post', methods=['GET'])
def receive_data():
    query = request.args.get('q')
    most_active_sender, most_active_recipient, docIds = query_emails(query)
    matching_records = [record for record in jsonldata if 'docNo' in record and record['docNo'] in docIds]
    return jsonify({
        'message': 'Data received successfully!',
        "result": matching_records,
        "active_sender": most_active_sender, 
        "active_receiver": most_active_recipient
})

# Start the server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
