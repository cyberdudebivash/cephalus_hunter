from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import jwt
from functools import wraps
from core import scan_iocs, monitor_rdp, SECRET_KEY

app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=["100 per minute"])

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        try:
            jwt.decode(token.split(" ")[1], SECRET_KEY, algorithms=['HS256'])
        except:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/scan', methods=['GET'])
@token_required
@limiter.limit("10 per minute")
def api_scan():
    return jsonify(scan_iocs())

@app.route('/monitor', methods=['GET'])
@token_required
@limiter.limit("10 per minute")
def api_monitor():
    return jsonify(monitor_rdp())

@app.route('/auth', methods=['POST'])
def auth():
    data = request.json
    if data.get('key') == os.getenv('API_KEY', 'cyberdude_test'):  # Pro key check
        token = jwt.encode({'user': 'pro'}, SECRET_KEY, algorithm='HS256')
        return jsonify({'token': token})
    return jsonify({'error': 'Invalid key'}), 403

if __name__ == '__main__':
    app.run(ssl_context='adhoc', debug=False)  # Prod: proper certs