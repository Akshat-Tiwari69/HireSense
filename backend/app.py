from flask import Flask, jsonify
from flask_cors import CORS
import os

# Initialize Flask app
app = Flask(__name__)

# Enable CORS so frontend can call our APIs
CORS(app)

# Ensure uploads folder exists
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API is running"""
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
