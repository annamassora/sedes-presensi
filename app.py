import datetime
from tabnanny import check
from unicodedata import decimal
import uuid
import logging
from xml.dom.minidom import Identified
import jwt, os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from sqlalchemy import Float, String, null
from models import db
from auth_middleware import token_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import json
from sqlalchemy import and_
from json import JSONEncoder
load_dotenv()
app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}}) #API TU BUAT APA?
SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a secret'
print(SECRET_KEY)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://sedes:abcdef@localhost:5432/sedes'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
from models import *

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
         return jsonify({'access':{ 'token' : token, "user":current_user,}, 'status':200})
   return jsonify({'status':'unauthorized', 'status':600})    

@app.route('/getQrCode', methods=['GET'])
def get_qr_code():
   location=request.args.get("location")
   token = jwt.encode({'location':location}, app.config['SECRET_KEY'])
   return jsonify({'status':200,'qrToken': token})

def checkget_qr_code(qrString):
   try:
      tokenData = jwt.decode(qrString, app.config['SECRET_KEY'], algorithms=['HS256'])
      print(f"tokenData {tokenData}")
      return {'status':200,'tokenData': tokenData}
   except:
      return {'status':402,'tokenData': "ERROR!!"}

@app.route('/api/checkin', methods=['POST']) 
@token_required
def attendance(current_user):
   temperature =  request.form.get("temperature",type = float)
   qrString =  request.form.get("qrString",type = str)
   qrStringData=checkget_qr_code(qrString)
   app.logger.debug(f"qrStringData {qrStringData}")
   app.logger.debug(f"current_user {current_user['user'].nisn}")
   if qrStringData["status"]!=200:  
      return jsonify({'message': 'qr_code is invalid'})
   else:
      app.logger.debug(f"attendance :  {temperature} {qrString} {current_user}")
      if current_user["role"]==1 : 
         checkin = StudentAttendance(nisn=current_user["user"].nisn, temperature=temperature,location=qrStringData["tokenData"]["location"], check_in=datetime.datetime.now())
         db.session.add(checkin)  
      if current_user["role"]==0 : 
         checkin = TeacherAttendance(nign=current_user["user"].nign, temperature=temperature,location=qrStringData["tokenData"]["location"], check_in=datetime.datetime.now())
         db.session.add(checkin)
      db.session.commit()
      return jsonify({'checkout':temperature, 'statusMessage':"success", 'status':200})

@app.route('/api/last_checkin', methods=['GET'])
@token_required
def get_last_chekin(current_user):
   print("current_user ", current_user["user"])
   if current_user["role"]==0 : 
      userAttendances = TeacherAttendance.query.filter(and_(TeacherAttendance.nign==current_user["user"].nign, TeacherAttendance.check_out==None)).all()
      attendance = []
      for userAttendance in userAttendances:
         attendance.append({
            'id':userAttendance.id_ta,
            'temperature':str(userAttendance.temperature),
            'location':userAttendance.location,
            'check_in':userAttendance.check_in.strftime("%d-%b-%Y %H:%M"),
         })
      return jsonify({'status':200,'attendance': attendance})
   if current_user["role"]==1 : 
      print("current_user ", current_user["user"].nisn)
      userAttendances = StudentAttendance.query.filter(and_(StudentAttendance.nisn==current_user["user"].nisn, StudentAttendance.check_out==None)).all()
      attendance = []
      print("userAttendances ", userAttendances)
      for userAttendance in userAttendances:
         attendance.append(
            {
               'id':userAttendance.id_sa,
               'temperature':str(userAttendance.temperature),
               'location':userAttendance.location,
               'check_in':userAttendance.check_in.strftime("%d-%b-%Y %H:%M"),
            }
         )
         print("user_data ", attendance)
      return jsonify({'status':200,'attendance': attendance})


@app.route('/api/check_out', methods=['POST'])
@token_required
def check_out(current_user):
   id =  request.form.get("id",type = str)
   print(f"id {request.form}")
   try:
      if current_user["role"]==0 : 
         db.session.query(TeacherAttendance).\
            filter(and_(TeacherAttendance.id_ta==id, TeacherAttendance.nign==current_user["user"].nign ,TeacherAttendance.check_out==None)).\
            update({TeacherAttendance.check_out: datetime.datetime.now()})
         db.session.commit()
      elif current_user["role"]==1 : 
         db.session.query(StudentAttendance).\
            filter(and_(StudentAttendance.id_sa==id, StudentAttendance.nisn==current_user["user"].nisn ,StudentAttendance.check_out==None)).\
            update({StudentAttendance.check_out: datetime.datetime.now()})

         db.session.commit()
      return jsonify({'status':200,"message":"success"})
   except:
      return jsonify({'status':404,"message":"error"})


@app.route('/api/report', methods=['GET'])
@token_required
def get_report(current_user):
   print("current_user ", current_user["user"])
   if current_user["role"]==0 : 
      userAttendances = TeacherAttendance.query.filter_by(nign=current_user["user"].nign).all()
      attendance = []
      for userAttendance in userAttendances:
         attendance.append(
            {
               'temperature':str(userAttendance.temperature),
               'location':userAttendance.location,
               'check_in':userAttendance.check_in.strftime("%d-%b-%Y %H:%M"),
               'check_out':userAttendance.check_out.strftime("%d-%b-%Y %H:%M") if userAttendance.check_out!=None else "0",
            }
         )
      return jsonify({'status':200,'attendance': attendance})
   if current_user["role"]==1 : 
      print("current_user ", current_user["user"].nisn)
      userAttendances = StudentAttendance.query.filter_by(nisn=current_user["user"].nisn).all()
      attendance = []
      print("userAttendances ", userAttendances)
      for userAttendance in userAttendances:
         attendance.append(
            {
               'temperature':str(userAttendance.temperature),
               'location':userAttendance.location,
               'check_in':userAttendance.check_in.strftime("%d-%b-%Y %H:%M"),
               'check_out':userAttendance.check_out.strftime("%d-%b-%Y %H:%M") if userAttendance.check_out!=None else "0",
            }
         )
         print("user_data ", attendance)
      return jsonify({'status':200,'attendance': attendance})
   

# @app.route('/api/user', methods=['GET'])
# @token_required
# def get_all_users(current_user):
#    if current_user["role"]==1 : 
#       return jsonify({'status': 401, 'messege':"not a teacher"})
#    print("current_user ", current_user["user"].fullname)
#    users = Student.query.all() 
#    result = []   
#    for user in users:   
#        user_data = {}   
#        user_data['nisn'] = user.nisn  
#        user_data['name'] = user.fullname
#        result.append(user_data)   
#    return jsonify({'status':200,'users': result})


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
