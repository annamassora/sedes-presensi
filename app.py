import datetime
import uuid
from xml.dom.minidom import Identified
import jwt, os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from validate import validate_book, validate_email_and_password, validate_user
from models import db
from auth_middleware import token_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import json
from json import JSONEncoder
load_dotenv()
app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a secret'
print(SECRET_KEY)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://sedes:abcdef@localhost:5432/sedes'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
from models import *

@app.route("/")
def hello():
    return "Hello World!"


@app.route('/api/register', methods=['POST'])
def signup_user():  
   print(request.form)
   username =  request.form.get("username", type = str, default = "")
   datebirth =  request.form.get("datebirth", type = str, default = "")
   password =  request.form.get("password", type = str, default = "")
   indentifier =  request.form.get("indentifier", type = str, default = "")
   role =  request.form.get("role", type = int, default = "")
   hashed_password = generate_password_hash(password, method='sha256')

   new_user = Login(public_id=str(uuid.uuid4()), password=hashed_password, indentifier=indentifier, role=role)
   db.session.add(new_user)
   if(role==0):
      teacher = Teacher(nign=indentifier, fullname=username, datebirth=datebirth)
      db.session.add(teacher)
   if(role==1):
      student = Student( nisn=indentifier, fullname=username, datebirth=datebirth)
      db.session.add(student)
   db.session.commit()
   return jsonify({'message': 'registered successfully'})   


@app.route('/api/login', methods=['POST'])  
def login_user():
   print("login")
   auth = request.authorization
   app.logger.debug(auth)
   if not auth or not auth.username or not auth.password:  
      return jsonify({'status':'could not verify', 'code':401})
   user = Login.query.filter_by(indentifier=auth.username).first()
   app.logger.debug(user)
   if user!=None:
      if check_password_hash(user.password, auth.password):
         token = jwt.encode({'public_id': user.public_id, 'role': user.role, 'indentifier': user.indentifier, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])  
         current_user=None
         if user.role==0:
            teacher=Teacher.query.filter_by(nign=user.indentifier).first()
            current_user = {
               'username': teacher.fullname,
               'indentifier': teacher.nign,
               'datebirth': teacher.datebirth,
               'role':user.role
               }
         if user.role==1:
            student=Student.query.filter_by(nisn=user.indentifier).first()
            current_user = {
               'username': student.fullname,
               'indentifier': student.nisn,
               'datebirth': student.datebirth,
               'role':user.role
               }
         app.logger.debug(f"current_user : current_user")
         return jsonify({'token' : token, "user":current_user, 'status':200})
   return jsonify({'status':'unauthorized', 'status':600})    


@app.route('/api/user', methods=['GET'])
@token_required
def get_all_users(current_user):
   if current_user["role"]==1 : 
      return jsonify({'status': 401, 'messege':"not a teacher"})
   print("current_user ", current_user["user"].fullname)
   users = Student.query.all() 
   result = []   
   for user in users:   
       user_data = {}   
       user_data['nisn'] = user.nisn  
       user_data['name'] = user.fullname
       result.append(user_data)   
   return jsonify({'status':200,'users': result})


@app.route('/api/presensi', methods=['GET'])
@token_required
def presensi(current_user):
   if current_user["role"]==1 : 
      return jsonify({'status': 401, 'messege':"not a teacher"})
   print("current_user ", current_user["user"].fullname)
   users = Student.query.all() 
   result = []   
   for user in users:   
       user_data = {}   
       user_data['nisn'] = user.nisn  
       user_data['name'] = user.fullname
       result.append(user_data)   
   return jsonify({'status':200,'users': result})

@app.route('/api/kelas', methods=['GET'])
@token_required
def get_kelas(current_user):
   if current_user["role"]==1 : 
      return jsonify({'status': 401, 'messege':"not a teacher"})
   print("current_user ", current_user["user"].fullname)
   users = Student.query.all() 
   result = []   
   for user in users:   
       user_data = {}   
       user_data['nisn'] = user.nisn  
       user_data['name'] = user.fullname
       result.append(user_data)   
   return jsonify({'status':200,'users': result})

@app.route('/api/mapel', methods=['GET'])
@token_required
def get_mapel(current_user):
   # if current_user["role"]==1 : 
   #    return jsonify({'status': 401, 'messege':"not a teacher"})
   print("current_user ", current_user["user"].fullname)
   mapel = Student.query.all() 
   result = []   
   for user in users:   
       user_data = {}   
       user_data['nisn'] = user.nisn  
       user_data['name'] = user.fullname
       result.append(user_data)   
   return jsonify({'status':200,'users': result})  


if __name__ == "__main__":
    app.run(debug=True)
