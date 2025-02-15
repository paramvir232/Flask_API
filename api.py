from flask import Flask, jsonify, request, abort
from flask_restful import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from flask_migrate import Migrate
from sqlalchemy import inspect
from flask_cors import CORS
import jwt
import datetime
from functools import wraps
#Hello From Local test
app = Flask(__name__)
api = Api(app)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://api_1yct_user:YTnRCqigFRXkkjsZLLyQ2UqQfgjJQjG8@dpg-cumuhiggph6c738a6vpg-a/api_1yct'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

def generate_token(username):
    # Create a token with a payload that includes the username and an expiration time
    payload = {
        'user': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token expires in 1 hour
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Expect the token in the Authorization header in the format "Bearer <token>"
        auth_header = request.headers.get('Authorization')
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            # Decode the token to retrieve the payload
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = payload['user']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated




# Define the API model using SQLAlchemy
class API(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)

    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email

    def __repr__(self):
        return f"<API(id={self.id}, name={self.name}, email={self.email})>"

# Customized CRUD class to handle operations
class CRUD:
    @staticmethod
    def add_item(id, name, email):
        try:
            person = API(id=id, name=name, email=email)
            db.session.add(person)
            db.session.commit()
            return {"message": "Inserted", "id": id, "name": name, "email": email}
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": f"Error: {str(e)}"}, 500

    @staticmethod
    def get_item(id):
        try:
            person = API.query.filter_by(id=id).first()
            if person is None:
                return {"message": f"Person ID {id} does not exist!"}, 404
            return {"id": person.id, "name": person.name, "email": person.email}
        except SQLAlchemyError as e:
            return {"message": f"Error: {str(e)}"}, 500
            
    @staticmethod
    def update_item(id, name, email):
        try:
            person = API.query.filter_by(id=id).first()
            if person is None:
                return {"message": f"Person ID {id} does not exist!"}, 404
            # Update the fields
            person.name = name
            person.email = email
            db.session.commit()
            return {"message": "Updated", "id": id, "name": name, "email": email}
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": f"Error: {str(e)}"}, 500
            
    @staticmethod
    def delete_item(id):
        try:
            person = API.query.filter_by(id=id).first()
            if person is None:
                return {"message": f"Person ID {id} does not exist!"}, 404
            db.session.delete(person)
            db.session.commit()
            return {"message": f"Deleted person with ID {id}"}
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": f"Error: {str(e)}"}, 500

    @staticmethod
    def get_all_items():
        try:
            people = API.query.all()
            result = [{'id': person.id, 'name': person.name, 'email': person.email} for person in people]
            return result
        except SQLAlchemyError as e:
            return {"message": f"Error: {str(e)}"}, 500

# Argument parser for incoming requests
args = reqparse.RequestParser()
args.add_argument('name', type=str, help="name required", required=True)
args.add_argument('email', type=str, help="email required", required=True)

class Main(Resource):
    def get(self, id):
        result = CRUD.get_item(id)
        return jsonify(result)

    def put(self, id):
        put_args = args.parse_args()
        result = CRUD.update_item(id, put_args['name'], put_args['email'])
        return jsonify(result)
        
    def post(self,id):
        # Extract data from the JSON body of the request
        data = request.get_json()
        # id = data.get(f'{id}')
        name = data.get('name')
        email = data.get('email')
        
        # Check if all required fields are provided
        if not id or not name or not email:
            return jsonify({"message": "ID, name, and email are required!"}), 400

        result = CRUD.add_item(id, name, email)
        return jsonify(result)

    def delete(self, id):
        result = CRUD.delete_item(id)
        return jsonify(result)
        
with app.app_context():
    inspector = inspect(db.engine)  # Use inspect to check the database engine
    if not inspector.has_table('api'):  # Check if 'api' table exists
        db.create_all()  # Create tables if they don't exist
    else:
        print("Tables already exist, skipping creation.")
# Add resource to API
api.add_resource(Main, '/get/<int:id>')

@app.route('/')
def home():
    result = CRUD.get_all_items()
    return jsonify(result)

@app.route('/post',methods=['POST'])
@token_required
def post(current_user):
    # Extract data from the JSON body of the request
        data = request.get_json()
        id = data.get('id')
        name = data.get('name')
        email = data.get('email')
        
        # Check if all required fields are provided
        if not id or not name or not email:
            return jsonify({"message": "ID, name, and email are required!"}), 400

        result = CRUD.add_item(id, name, email)
        return jsonify(result)

@app.route('/put',methods=['PUT'])
@token_required
def put(current_user):
    data = request.get_json()
    id = data.get('id')
    put_args = args.parse_args()
    result = CRUD.update_item(id, put_args['name'], put_args['email'])
    return jsonify(result)

@app.route('/delete/<int:id>',methods=['DELETE'])
@token_required
def delete(current_user,id):
    result = CRUD.delete_item(id)
    return jsonify(result)

# @app.route('/get/<int:id>',methods=['GET'])
# @token_required
# def get(current_user,id):
#     result = CRUD.get_item(id)
#     return jsonify(result)


@app.route('/login', methods=['POST'])
def login():
    # For demonstration, we assume a JSON payload with username and password.
    # In a real app, verify credentials against a user database.
    auth_data = request.get_json()
    username = auth_data.get('username')
    password = auth_data.get('password')

    # Replace this with proper authentication logic
    if username == 'admin' and password == 'password':
        token = generate_token(username)
        return jsonify({'token': token})
    
    return jsonify({'message': 'Invalid credentials'}), 401


@app.route('/protected', methods=['GET'])
@token_required
def protected(current_user):
    return jsonify({'message': f'Hello, {current_user}! This is a protected endpoint.'})



if __name__ == '__main__':
    # with app.app_context():
    #     db.create_all()
    app.run(debug=True)
