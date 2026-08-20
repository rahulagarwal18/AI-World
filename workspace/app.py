from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, World!"

@app.route('/api/echo', methods=['POST'])
def echo():
    data = request.get_json(silent=True) or {}
    return jsonify({"you_sent": data})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
