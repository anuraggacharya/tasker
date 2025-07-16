# auth_middleware.py
import jwt
from functools import wraps
from flask import request, jsonify, current_app,g
from werkzeug.exceptions import Unauthorized
from config import Config

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        #print(request.headers)
        # Check for token in multiple locations
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        elif 'token' in request.cookies:
            token = request.cookies.get('token')
        elif request.args.get('token'):
            token = request.args.get('token')

        if not token:
            if request.accept_mimetypes.accept_json:
                return jsonify({'message': 'Token is missing!'}), 401
            return Unauthorized(description="Token is missing!")

        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            g.current_user = {
                'id': data['user_id'],
                'username': data['username'],
                'email': data.get('email')
            }
        except jwt.ExpiredSignatureError:
            if request.accept_mimetypes.accept_json:
                return jsonify({'message': 'Token has expired!'}), 401
            return Unauthorized(description="Token has expired!")
        except jwt.InvalidTokenError:
            if request.accept_mimetypes.accept_json:
                return jsonify({'message': 'Invalid token!'}), 401
            return Unauthorized(description="Invalid token!")

        return f(*args, **kwargs)

    return decorated


def roles_required(*required_roles):
    def decorator(f):
        @wraps(f)
        @token_required  # This ensures token is checked first
        def decorated(*args, **kwargs):
            # Get user roles from database or token
            user_roles = get_user_roles(request.current_user['id'])

            if not any(role in user_roles for role in required_roles):
                if request.accept_mimetypes.accept_json:
                    return jsonify({'message': 'Insufficient permissions!'}), 403
                return Unauthorized(description="Insufficient permissions!")

            return f(*args, **kwargs)
        return decorated
    return decorator


def get_user_roles(user_id):
    """Helper function to get user roles from database"""
    # Implement your actual role lookup logic here
    return ['user']  # Default role for all users
