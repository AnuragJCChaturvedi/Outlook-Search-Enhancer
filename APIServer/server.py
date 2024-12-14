from flask import Flask, request, jsonify
from flask_cors import CORS
import requests  # Correct import

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.route('/outlook-query', methods=['POST'])
def receive_outlook_query():
    try:
        data = request.json
        if not data or 'query' not in data:
            return jsonify({'error': 'No query received'}), 400

        query = data['query']
        
        response = requests.get(f"http://localhost:5001/api/post?q={query}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Response from external API: {response_data}")
            return jsonify({
                'status': 'success',
                'query': query,
                'external_response': response_data
            })
        else:
            return jsonify({'error': f"API Error {response.status_code}"}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
