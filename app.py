from datetime import date, datetime, timedelta
from io import StringIO
from dateutil.relativedelta import relativedelta
from tabnanny import check
from unicodedata import decimal
import uuid
import logging
from xml.dom.minidom import Identified
import jwt, os
from dotenv import load_dotenv
from flask import Flask, make_response, request, jsonify
from sqlalchemy import Float, String, null
from models import db
from auth_middleware import token_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import json
from sqlalchemy import and_
from sqlalchemy import func
from json import JSONEncoder
from flask import render_template, request, redirect
import csv
import codecs
import pandas as pd
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
   title = request.form.get("title", type = str, default = "")
   password =  request.form.get("password", type = str, default = "")
   indentifier =  request.form.get("indentifier", type = str, default = "")
   role =  request.form.get("role", type = int, default = 1)
   id_class =  request.form.get("class_id", type = int, default = 1)
   if(password==""):
      password=datebirth
   hashed_password = generate_password_hash(password, method='sha256')
   public_id=str(uuid.uuid4())
   new_user = Login(public_id=public_id, password=hashed_password, indentifier=indentifier, role=role)
   db.session.add(new_user)
   if(role==0):
      teacher = Teacher(nourut=indentifier, public_id= public_id, fullname=username, datebirth=datebirth, title=title)
      db.session.add(teacher)
   if(role==1):
      student = Student( nisn=indentifier, public_id= public_id, fullname=username, datebirth=datebirth, id_class=id_class)
      db.session.add(student)
   if(role==2):
      admin = Admin(id_admin=indentifier, public_id= public_id, fullname=username)
      db.session.add(admin)
   if(role==3):
      employee = Employee(nourut=indentifier, public_id= public_id, fullname=username,  datebirth=datebirth, title=title)
      db.session.add(employee)
   db.session.commit()
   return jsonify({'message': 'registered successfully'})   


@app.route('/api/login', methods=['POST'])  
def login_user():
   print("login")
   auth = request.authorization
   app.logger.debug(f"auth {auth}")
   if not auth or not auth.username or not auth.password:  
      return jsonify({'status':'could not verify', 'code':401})
   user = Login.query.filter_by(indentifier=auth.username).first()
   app.logger.debug(f"user {user}")
   if user!=None:
      if check_password_hash(user.password, auth.password):
         token = jwt.encode({'public_id': user.public_id, 'role': user.role, 'indentifier': user.indentifier, 'exp' : datetime.utcnow() + timedelta(days=1)}, app.config['SECRET_KEY'])  
         current_user=None
         if user.role==0:
            teacher=Teacher.query.filter_by(nourut=user.indentifier).first()
            current_user = {
               'username': teacher.fullname,
               'indentifier': teacher.nourut,
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
         if user.role==2:
            admin=Admin.query.filter_by(id_admin=user.indentifier).first()
            current_user = {
               'username': admin.fullname,
               'indentifier': admin.id_admin,
               'role':user.role
               }
         if user.role==3:
            employee=Employee.query.filter_by(nourut=user.indentifier).first()
            current_user = {
               'username': employee.fullname,
               'indentifier': employee.nourut,
               'datebirth': employee.datebirth,
               'role':user.role
               }
         app.logger.debug(f"current_user : current_user")
         return jsonify({'access':{ 'token' : token, "user":current_user,}, 'status':200})
   return jsonify({'status':'unauthorized', 'status':600})   


#Create QRCode
@app.route('/api/qrcode', methods=['POST'])
@token_required
def qr_code(current_user):
   print(request.form)
   location =  request.form.get("location", type = str, default = "")
   if location == '':
      return jsonify({'status':600,'message':"empty location"})
   if current_user["role"]==2:
      qrString = jwt.encode({'location':location}, app.config['SECRET_KEY'])
      qrcode = QRCode(location=location, qrString=qrString)
      db.session.add(qrcode)
      db.session.commit()
      return jsonify({'status':200,'qrString': qrString})
   return jsonify({'status':600,'message':"unauthorized"})
   

#Get QRCode
@app.route('/api/getQrCode', methods=['GET'])
@token_required
def get_qr_code(current_user):
   if current_user["role"]==2:
      qrcodeList = QRCode.query.all() 
      qrList=[]
      for qrcode in qrcodeList:
         qrList.append({
            'id':qrcode.id_qr,
            'location':qrcode.location,
            'qrString':qrcode.qrString,
         })
      print(qrList)
      return jsonify({'status':200,'qrList': qrList})
   return jsonify({'status':600,'message':"unauthorized"})


#Get Time
@app.route('/api/getTime', methods=['GET'])
@token_required
def get_time(current_user):
   if current_user["role"]==2:
      timesetList = TimeSetting.query.all() 
      timeList=[]
      if timesetList == []:
         timeSiswa = TimeSetting(id_time="student", ket="Siswa", jam_masuk="00.00",jam_keluar="00.00")
         timeGuru = TimeSetting(id_time="teacher", ket="Guru", jam_masuk="00.00",jam_keluar="00.00")
         timeEmployee = TimeSetting(id_time="employee", ket="Karyawan", jam_masuk="00.00",jam_keluar="00.00")
         db.session.add(timeSiswa)
         db.session.add(timeGuru)
         db.session.add(timeEmployee)
         db.session.commit()
         timesetList = TimeSetting.query.all() 
      for time in timesetList:
            timeList.append({
               'id':time.id_time,
               'Keterangan':time.ket,
               'JamMasuk':time.jam_masuk,
               'JamKeluar':time.jam_keluar
            })
      timeList = sorted(timeList, key=lambda d: d['id'],reverse=True) 
      print(timeList)
      return jsonify({'status':200,'timeList': timeList})
   return jsonify({'status':600,'message':"unauthorized"})


##### Update Time  
@app.route('/api/updateTime', methods=['POST'])
@token_required
def updateTime(current_user):
   if current_user["role"]==2:
      id =  request.form.get("id", type = str, default = "")
      tipe_jam = request.form.get("tipe_jam", type = int, default = 0 )
      timeData = request.form.get("timeData", type = str, default = "")
      app.logger.debug(f"id {id}")
      app.logger.debug(f"tipe_jam {tipe_jam}")
      app.logger.debug(f"timeData {timeData}")
      
      if tipe_jam == 0:
         existingTime=db.session.query(TimeSetting).\
                      filter(TimeSetting.id_time==id)
         existingTime.update({TimeSetting.jam_masuk: timeData})
         db.session.commit()
      else :
         existingTime=db.session.query(TimeSetting).\
                      filter(TimeSetting.id_time==id)
         existingTime.update({TimeSetting.jam_keluar: timeData})
         db.session.commit()
      return jsonify({'status':200,'message': "update data success"})
   return jsonify({'status':600,'message':"unauthorized"})



#Delete QRCode
@app.route("/api/deleteQrCode", methods=["POST"])
@token_required
def qr_delete(current_user):
   if current_user["role"]==2:
      id = request.form.get("id",type = int)
      qrCode = QRCode.query.get(id)
      db.session.delete(qrCode)
      db.session.commit()
      return jsonify({'status':200, 'message':'success'})
   return jsonify({'status':600,'message':"unauthorized"})


#Check QRCode
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
   # temperature =  request.form.get("temperature",type = float)
   qrString =  request.form.get("qrString",type = str)
   qrStringData=checkget_qr_code(qrString)
   app.logger.debug(f"qrStringData {qrStringData}")
   if qrStringData["status"]!=200:  
      return jsonify({'message': 'qr_code is invalid'})
   else:
      app.logger.debug(f"attendance :  {qrString} {current_user}")
      if current_user["role"]==0 : 
         checkin = TeacherAttendance(nourut=current_user["user"].nourut, location=qrStringData["tokenData"]["location"], check_in=datetime.now())
         db.session.add(checkin)
      if current_user["role"]==1 : 
         checkin = StudentAttendance(nisn=current_user["user"].nisn, location=qrStringData["tokenData"]["location"], check_in=datetime.now())
         db.session.add(checkin)  
      if current_user["role"]==3 : 
         checkin = EmployeeAttendance(nourut=current_user["user"].nourut, location=qrStringData["tokenData"]["location"], check_in=datetime.now())
         db.session.add(checkin)
      db.session.commit()
      return jsonify({'checkout':"success", 'status':200})

@app.route('/api/last_checkin', methods=['GET'])
@token_required
def get_last_chekin(current_user):
   print("current_user ", current_user["user"])
   if current_user["role"]==0 : 
      userAttendances = TeacherAttendance.query.filter(and_(TeacherAttendance.nourut==current_user["user"].nourut, TeacherAttendance.check_out==None)).all()
      attendance = []
      for userAttendance in userAttendances:
         attendance.append({
            'id':userAttendance.id_ta,
            # 'temperature':str(userAttendance.temperature),
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
               # 'temperature':str(userAttendance.temperature),
               'location':userAttendance.location,
               'check_in':userAttendance.check_in.strftime("%d-%b-%Y %H:%M"),
            })
   if current_user["role"]==3 : 
      userAttendances = EmployeeAttendance.query.filter(and_(EmployeeAttendance.nourut==current_user["user"].nourut, EmployeeAttendance.check_out==None)).all()
      attendance = []
      for userAttendance in userAttendances:
         attendance.append({
            'id':userAttendance.id_ea,
            # 'temperature':str(userAttendance.temperature),
            'location':userAttendance.location,
            'check_in':userAttendance.check_in.strftime("%d-%b-%Y %H:%M"),
         })
         print("user_data ", attendance)
      return jsonify({'status':200,'attendance': attendance})
   return jsonify({'status':600,'message':"unauthorized"})


@app.route('/api/check_out', methods=['POST'])
@token_required
def check_out(current_user):
   id =  request.form.get("id",type = str)
   print(f"id {request.form}")
   try:
      if current_user["role"]==0 : 
         db.session.query(TeacherAttendance).\
            filter(and_(TeacherAttendance.id_ta==id, TeacherAttendance.nourut==current_user["user"].nourut ,TeacherAttendance.check_out==None)).\
            update({TeacherAttendance.check_out: datetime.now()})
         db.session.commit()
      elif current_user["role"]==1 : 
         db.session.query(StudentAttendance).\
            filter(and_(StudentAttendance.id_sa==id, StudentAttendance.nisn==current_user["user"].nisn ,StudentAttendance.check_out==None)).\
            update({StudentAttendance.check_out: datetime.now()})
         db.session.commit()
      elif current_user["role"]==3 : 
         db.session.query(EmployeeAttendance).\
            filter(and_(EmployeeAttendance.id_ea==id, EmployeeAttendance.nourut==current_user["user"].nourut ,EmployeeAttendance.check_out==None)).\
            update({EmployeeAttendance.check_out: datetime.now()})
         db.session.commit()
      return jsonify({'status':200,"message":" "})
   except:
      return jsonify({'status':404,"message":"error"})


@app.route('/api/report', methods=['GET'])
@token_required
def get_report(current_user):
   print("current_user ", current_user["user"])
   #get month year selected
   year=request.args.get("year")
   month=request.args.get("month")
   print(f"year,month {request.args}")
   filter_before= date(int(year), int(month)+1, 1)
   print("filter_before ", filter_before)
   filter_after = filter_before+relativedelta(months=+1)
   print("filter_after ", filter_after)
   if current_user["role"]==0 : 
      print("current_user ", current_user["user"].nourut)
      userAttendances = TeacherAttendance.query.filter(and_(TeacherAttendance.nourut==current_user["user"].nourut, TeacherAttendance.check_in.between(filter_before,filter_after))).all()
      attendance = []
      for userAttendance in userAttendances:
         attendance.append(
            {
               # 'temperature':str(userAttendance.temperature),
               'location':userAttendance.location,
               'check_in':userAttendance.check_in.strftime("%d-%b-%Y %H:%M"),
               'check_out':userAttendance.check_out.strftime("%d-%b-%Y %H:%M") if userAttendance.check_out!=None else "0",
            }
         )
      return jsonify({'status':200,'attendance': attendance})
   if current_user["role"]==1 : 
      print("current_user ", current_user["user"].nisn)
      userAttendances = StudentAttendance.query.filter(and_(StudentAttendance.nisn==current_user["user"].nisn, StudentAttendance.check_in.between(filter_before,filter_after))).all()
      attendance = []
      # print("userAttendances ", userAttendances)
      for userAttendance in userAttendances:
         attendance.append(
            {
               # 'temperature':str(userAttendance.temperature),
               'location':userAttendance.location,
               'check_in':userAttendance.check_in.strftime("%d-%b-%Y %H:%M"),
               'check_out':userAttendance.check_out.strftime("%d-%b-%Y %H:%M") if userAttendance.check_out!=None else "0",
            }
         )
   if current_user["role"]==3 : 
      print("current_user ", current_user["user"].nourut)
      userAttendances = EmployeeAttendance.query.filter(and_(EmployeeAttendance.nourut==current_user["user"].nourut, EmployeeAttendance.check_in.between(filter_before,filter_after))).all()
      attendance = []
      for userAttendance in userAttendances:
         attendance.append(
            {
               # 'temperature':str(userAttendance.temperature),
               'location':userAttendance.location,
               'check_in':userAttendance.check_in.strftime("%d-%b-%Y %H:%M"),
               'check_out':userAttendance.check_out.strftime("%d-%b-%Y %H:%M") if userAttendance.check_out!=None else "0",
            }
         )
         # print("user_data ", attendance)
      return jsonify({'status':200,'attendance': attendance})
   return jsonify({'status':600,'message':"unauthorized"})


#-----------------------------------------------------------------#
#                          ADMIN AREA                             #
#-----------------------------------------------------------------#


#################################
#####		     Guru			 #####
#################################

##### Daftar Guru  
@app.route('/api/teacher', methods=['GET'])
@token_required
def get_teacherlist(current_user):
   print("current_user ", current_user["user"])
   if current_user["role"]==2 : 
      userReport = Teacher.query.all()
      list = []
      for userReport in userReport:
         list.append(
            {
               'fullname':userReport.fullname,
               'nourut':userReport.nourut,
               'datebirth':userReport.datebirth,
               'title':userReport.title
            }
         )
      list = sorted(list, key=lambda d: d['nourut'],reverse=False) 
      return jsonify({'status':200,'list': list})
   return jsonify({'status':600,'message':"unauthorized"})

##### Add Guru  
@app.route('/api/addTeacher', methods=['POST'])
@token_required
def addTeacher(current_user):  
   print(request.form)
   username =  request.form.get("username", type = str, default = "")
   datebirth =  request.form.get("datebirth", type = str, default = "")
   indentifier =  request.form.get("identifier", type = str, default = "") 
   if current_user["role"]==2:
      try:
         hashed_password = generate_password_hash(datebirth, method='sha256')
         new_user = Login(public_id=str(uuid.uuid4()), password=hashed_password, indentifier=indentifier, role=0)
         db.session.add(new_user)
         teacher = Teacher(nourut=indentifier, fullname=username, datebirth=datebirth)
         db.session.add(teacher)
         db.session.commit()
         return jsonify({'status':200, 'message': 'registered successfully' })
      except:
         return jsonify({'status':400, 'message': 'registered Failed' })
      
   return jsonify({'status':600,'message':"unauthorized"})


##### Delete Guru  
@app.route("/api/deleteTeacher", methods=["POST"])
@token_required
def deleteTeacher(current_user):
   if current_user["role"]==2:
      id = request.get_json()
      print(id)
      # {id:[id]}
      id=id["id"]
      if id[0] == 'all':
         db.session.query(Teacher).delete()
         db.session.query(Login).filter(Login.role==0).delete()
         db.session.commit()
      else:
         db.session.query(Teacher).filter(Teacher.nourut.in_((id))).delete()
         db.session.query(Login).filter(Login.indentifier.in_((id))).delete()
         db.session.commit()
      return jsonify({'status':200, 'message':'success'})
   return jsonify({'status':600,'message':"unauthorized"})


##### Import CSV Guru  
@app.route('/api/importTeacher', methods=['POST'])
@token_required
def import_Teacher(current_user):
   if current_user["role"]==2:
      daftar_guru=  request.files.get('daftar_guru')
      reader = pd.read_csv(daftar_guru)
      for guru in reader.iterrows():
         no = db.session.query(func.count(Teacher.nourut)).scalar()
         noUrut = f"G-{no}"
         public_id=str(uuid.uuid4())
         print(guru[1])
         password=guru[1].TTL
         hashed_password = generate_password_hash(password, method='sha256')
         new_user = Login(public_id=public_id, password=hashed_password, indentifier=noUrut, role=0)
         db.session.add(new_user)
         teacher = Teacher( nourut=noUrut, public_id= public_id, fullname=guru[1].Nama, datebirth=guru[1].TTL, title=guru[1].Jabatan)
         db.session.add(teacher)
      db.session.commit()
      return jsonify({'status':200, 'message': 'registered successfully' })
   return jsonify({'status':600,'message':"unauthorized"})


##### Update Data Guru  
@app.route('/api/updateTeacher', methods=['POST'])
@token_required
def updateTeacher(current_user):
   if current_user["role"]==2:
      teacherData = request.get_json()

      # {
      #    id:idguru1,
      #    title:title guru1
      # },
      print(teacherData)
      existingTeacher=db.session.query(Teacher).filter(Teacher.nourut==str(teacherData["id"]))
      existingTeacher.update({Teacher.title: teacherData["title"]})
      db.session.commit()
      return jsonify({'status':200,'message': "update data success"})
   return jsonify({'status':600,'message':"unauthorized"})


##### Download CSV Guru 
@app.route("/api/downloadTeacherReport", methods=["GET"])
@token_required
def downloadTeacherReport(current_user):
   if current_user["role"]==2:
      si = StringIO()
      cw = csv.writer(si)
      c = TeacherAttendance.query.all()
      # print(c[0].nourut)
      cw.writerow([ column.name for column in TeacherAttendance.__mapper__.columns])
      [cw.writerow([getattr(curr, column.name) for column in TeacherAttendance.__mapper__.columns]) for curr in c]
      response = make_response(si.getvalue())
      response.headers['Content-Disposition'] = 'attachment; filename=report.csv'
      response.headers["Content-type"] = "text/csv"
      return response
   return jsonify({'status':600,'message':"unauthorized"})


##### Report Guru
@app.route('/api/teacherDetail', methods=['GET'])
@token_required
def get_teacherDetail(current_user):
   print("current_user ", current_user["user"])
   #get month year selected
   id = request.args.get("nourut")
   year=request.args.get("year")
   month=request.args.get("month")
   print(f"year,month {request.args}")
   filter_before= date(int(year), int(month)+1, 1)
   print("filter_before ", filter_before)
   filter_after = filter_before+relativedelta(months=+1)
   print("filter_after ", filter_after)
   if current_user["role"]==2 : 
      userReports = TeacherAttendance.query.filter(and_(TeacherAttendance.nourut==id, TeacherAttendance.check_in.between(filter_before,filter_after))).all()
      attendance = []
      for userReport in userReports:
         attendance.append(
            {
               # 'temperature':str(userReport.temperature),
               'location':userReport.location,
               'check_in':userReport.check_in.strftime("%d-%b-%Y %H:%M"),
               'check_out':userReport.check_out.strftime("%d-%b-%Y %H:%M") if userReport.check_out!=None else "0",
            }
         )
      return jsonify({'status':200,'attendance': attendance})
   return jsonify({'status':600,'message':"unauthorized"})



#################################
#####		     Siswa			 #####
#################################

##### Daftar Siswa  
@app.route('/api/student', methods=['GET'])
@token_required
def get_studentlist(current_user):
   print("current_user ", current_user["user"])
   if current_user["role"]==2 : 
      userReport = Student.query.all()
      list = []
      for userReport in userReport:
         list.append(
            {
               'fullname':userReport.fullname,
               'nisn':userReport.nisn,
               'datebirth':userReport.datebirth,
               'id_class': userReport.id_class
            }
         )
      list = sorted(list, key=lambda k: (k['id_class'], k['fullname']),reverse=False) 
      return jsonify({'status':200,'list': list})
   return jsonify({'status':600,'message':"unauthorized"})


##### Add Siswa 
@app.route('/api/addStudent', methods=['POST'])
@token_required
def addStudent(current_user):  
   print(request.form)
   username =  request.form.get("username", type = str, default = "")
   datebirth =  request.form.get("datebirth", type = str, default = "")
   indentifier =  request.form.get("identifier", type = str, default = "")
   id_class = request.form.get("id_class", type = str, default = "")  
   if current_user["role"]==2:
      try:
         hashed_password = generate_password_hash(datebirth, method='sha256')
         new_user = Login(public_id=str(uuid.uuid4()), password=hashed_password, indentifier=indentifier, role=1)
         db.session.add(new_user)
         student = Student(nisn=indentifier, fullname=username, datebirth=datebirth, id_class=id_class)
         db.session.add(student)
         db.session.commit()
         return jsonify({'status':200, 'message': 'registered successfully' })
      except:
         return jsonify({'status':400, 'message': 'registered Failed' })
   return jsonify({'status':600,'message':"unauthorized"})


##### Delete Siswa 
@app.route("/api/deleteStudent", methods=["POST"])
@token_required
def deleteStudent(current_user):
   if current_user["role"]==2:
      id = request.get_json()
      id=id["id"]
      print(id[0])
      if id[0] == 'all':
         db.session.query(Student).delete()
         db.session.query(Login).filter(Login.role==1).delete()
         db.session.commit()
      else:
         db.session.query(Student).filter(Student.nisn.in_((id))).delete()
         db.session.query(Login).filter(Login.indentifier.in_((id))).delete()
         db.session.commit()
      return jsonify({'status':200, 'message':'success'})
   return jsonify({'status':600,'message':"unauthorized"})


##### Import CSV Siswa 
@app.route('/api/importStudent', methods=['POST'])
@token_required
def import_Student(current_user):
   if current_user["role"]==2:
      daftar_siswa =  request.files.get('daftar_siswa')
      reader = pd.read_csv(daftar_siswa)
      for siswa in reader.iterrows():
         existingSiswa=db.session.query(Student).filter(Student.nisn==str(siswa[1].nisn))
         print(existingSiswa)
         if existingSiswa.all():
            existingSiswa.update({Student.id_class: siswa[1].Kelas})
            db.session.commit()
         else: 
            public_id=str(uuid.uuid4())
            password=siswa[1].TTL
            hashed_password = generate_password_hash(password, method='sha256')
            # print(siswa[1].nisn)
            new_user = Login(public_id=public_id, password=hashed_password, indentifier=siswa[1].nisn, role=1)
            db.session.add(new_user)
            student = Student( public_id= public_id, fullname=siswa[1].Nama, nisn=siswa[1].nisn, datebirth=siswa[1].TTL, id_class=siswa[1].Kelas)
            db.session.add(student)
            db.session.commit()
      return jsonify({'status':200, 'message': 'registered successfully' })
   return jsonify({'status':600,'message':"unauthorized"})


##### Update Data Siswa  
@app.route('/api/updateStudent', methods=['POST'])
@token_required
def updateStudent(current_user):
   if current_user["role"]==2:
      studentData = request.get_json()
      # {
      #    id:idsiswa1,
      #    id_class=id_class1
      # },
      print(studentData)
      existingStudent=db.session.query(Student).filter(Student.nisn==str(studentData["id"]))
      existingStudent.update({Student.id_class: studentData["kelas"]})
      db.session.commit()
      return jsonify({'status':200,'message': "update data success"})
   return jsonify({'status':600,'message':"unauthorized"})


##### Download CSV Siswa
@app.route("/api/downloadStudentReport", methods=["GET"])
@token_required
def downloadStudentReport(current_user):
   if current_user["role"]==2:
      si = StringIO()
      cw = csv.writer(si)
      c = StudentAttendance.query.all()
      cw.writerow([ column.name for column in StudentAttendance.__mapper__.columns])
      [cw.writerow([getattr(curr, column.name) for column in StudentAttendance.__mapper__.columns]) for curr in c]
      response = make_response(si.getvalue())
      response.headers['Content-Disposition'] = 'attachment; filename=report.csv'
      response.headers["Content-type"] = "text/csv"
      return response
   return jsonify({'status':600,'message':"unauthorized"})


##### Report Siswa  
@app.route('/api/studentDetail', methods=['GET'])
@token_required
def get_studentDetail(current_user):
   print("current_user ", current_user["user"])
   #get month year selected
   id = request.args.get("nisn")
   year=request.args.get("year")
   month=request.args.get("month")
   print(f"year,month {request.args}")
   filter_before= date(int(year), int(month)+1, 1)
   print("filter_before ", filter_before)
   filter_after = filter_before+relativedelta(months=+1)
   print("filter_after ", filter_after)
   if current_user["role"]==2 : 
      userReports = StudentAttendance.query.filter(and_(StudentAttendance.nisn==id, StudentAttendance.check_in.between(filter_before,filter_after))).all()
      attendance = []
      for userReport in userReports:
         attendance.append(
            {
               # 'temperature':str(userReport.temperature),
               'location':userReport.location,
               'check_in':userReport.check_in.strftime("%d-%b-%Y %H:%M"),
               'check_out':userReport.check_out.strftime("%d-%b-%Y %H:%M") if userReport.check_out!=None else "0",
            }
         )
      return jsonify({'status':200,'attendance': attendance})
   return jsonify({'status':600,'message':"unauthorized"})


#################################
#####		    Karyawan		 #####
#################################

##### Daftar Karyawan  
@app.route('/api/employee', methods=['GET'])
@token_required
def get_employeelist(current_user):
   print("current_user ", current_user["user"])
   if current_user["role"]==2 : 
      userReport = Employee.query.all()
      list = []
      for userReport in userReport:
         list.append(
            {
               'fullname':userReport.fullname,
               'nourut':userReport.nourut,
               'datebirth':userReport.datebirth,
               'title':userReport.title
            }
         )
      list = sorted(list, key=lambda d: d['nourut'],reverse=False)
      return jsonify({'status':200,'list': list})
   return jsonify({'status':600,'message':"unauthorized"})


##### Add Karyawan  
@app.route('/api/addEmployee', methods=['POST'])
@token_required
def addEmployee(current_user):  
   print(request.form)
   username =  request.form.get("username", type = str, default = "")
   datebirth =  request.form.get("datebirth", type = str, default = "")
   indentifier =  request.form.get("identifier", type = str, default = "") 
   if current_user["role"]==2:
      try:
         hashed_password = generate_password_hash(datebirth, method='sha256')
         new_user = Login(public_id=str(uuid.uuid4()), password=hashed_password, indentifier=indentifier, role=3)
         db.session.add(new_user)
         employee = Employee(nourut=indentifier, fullname=username, datebirth=datebirth)
         db.session.add(employee)
         db.session.commit()
         return jsonify({'status':200, 'message': 'registered successfully' })
      except:
         return jsonify({'status':400, 'message': 'registered Failed' })
      
   return jsonify({'status':600,'message':"unauthorized"})


##### Delete Karyawan  
@app.route("/api/deleteEmployee", methods=["POST"])
@token_required
def deleteEmployee(current_user):
   if current_user["role"]==2:
      id = request.get_json()
      id=id["id"]
      print(id[0])
      if id[0] == 'all':
         db.session.query(Employee).delete()
         db.session.query(Login).filter(Login.role==3).delete()
         db.session.commit()
      else:
         db.session.query(Employee).filter(Employee.nourut.in_((id))).delete()
         db.session.query(Login).filter(Login.indentifier.in_((id))).delete()
         db.session.commit()
      return jsonify({'status':200, 'message':'success'})
   return jsonify({'status':600,'message':"unauthorized"})


##### Update Data Karyawan 
@app.route('/api/updateEmployee', methods=['POST'])
@token_required
def updateEmployee(current_user):
   if current_user["role"]==2:
      employeeData = request.get_json()
      # {
      #    id:idkaryawan1,
      #    title:title karyawan1
      # },
      print(employeeData)
      existingEmployee=db.session.query(Employee).filter(Employee.nourut==str(employeeData["id"]))
      existingEmployee.update({Employee.title: employeeData["title"]})
      db.session.commit()
      return jsonify({'status':200,'message': "update data success"})
   return jsonify({'status':600,'message':"unauthorized"})


##### Import CSV Karyawan  
@app.route('/api/importEmployee', methods=['POST'])
@token_required
def import_Employee(current_user):
   if current_user["role"]==2:
      daftar_karyawan=  request.files.get('daftar_karyawan')
      reader = pd.read_csv(daftar_karyawan)
      for karyawan in reader.iterrows():
         no = db.session.query(func.count(Employee.nourut)).scalar()
         noUrut = f"K-{no}"
         public_id=str(uuid.uuid4())
         print(karyawan[1])
         password=karyawan[1].TTL
         hashed_password = generate_password_hash(password, method='sha256')
         new_user = Login(public_id=public_id, password=hashed_password, indentifier=noUrut, role=3)
         db.session.add(new_user)
         employee = Employee( nourut=noUrut, public_id= public_id, fullname=karyawan[1].Nama, datebirth=karyawan[1].TTL, title=karyawan[1].Jabatan)
         db.session.add(employee)
      db.session.commit()
      return jsonify({'status':200, 'message': 'registered successfully' })
   return jsonify({'status':600,'message':"unauthorized"})


##### Download CSV Karyawan 
@app.route("/api/downloadEmployeeReport", methods=["GET"])
@token_required
def downloadEmployeeReport(current_user):
   if current_user["role"]==2:
      si = StringIO()
      cw = csv.writer(si)
      c = EmployeeAttendance.query.all()
      # print(c[0].nourut)
      cw.writerow([ column.name for column in EmployeeAttendance.__mapper__.columns])
      [cw.writerow([getattr(curr, column.name) for column in EmployeeAttendance.__mapper__.columns]) for curr in c]
      response = make_response(si.getvalue())
      response.headers['Content-Disposition'] = 'attachment; filename=report.csv'
      response.headers["Content-type"] = "text/csv"
      return response
   return jsonify({'status':600,'message':"unauthorized"})


##### Report Karyawan
@app.route('/api/employeeDetail', methods=['GET'])
@token_required
def get_employeeDetail(current_user):
   print("current_user ", current_user["user"])
   #get month year selected
   id = request.args.get("nourut")
   year=request.args.get("year")
   month=request.args.get("month")
   print(f"year,month {request.args}")
   filter_before= date(int(year), int(month)+1, 1)
   print("filter_before ", filter_before)
   filter_after = filter_before+relativedelta(months=+1)
   print("filter_after ", filter_after)
   if current_user["role"]==2 : 
      userReports = EmployeeAttendance.query.filter(and_(EmployeeAttendance.nourut==id, EmployeeAttendance.check_in.between(filter_before,filter_after))).all()
      attendance = []
      for userReport in userReports:
         attendance.append(
            {
               # 'temperature':str(userReport.temperature),
               'location':userReport.location,
               'check_in':userReport.check_in.strftime("%d-%b-%Y %H:%M"),
               'check_out':userReport.check_out.strftime("%d-%b-%Y %H:%M") if userReport.check_out!=None else "0",
            }
         )
      return jsonify({'status':200,'attendance': attendance})
   return jsonify({'status':600,'message':"unauthorized"})



















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


# @app.route('/api/kelas', methods=['GET'])
# @token_required
# def get_kelas(current_user):
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

# @app.route('/api/mapel', methods=['GET'])
# @token_required
# def get_mapel(current_user):
#    # if current_user["role"]==1 : 
#    #    return jsonify({'status': 401, 'messege':"not a teacher"})
#    print("current_user ", current_user["user"].fullname)
#    mapel = Student.query.all() 
#    result = []   
#    for user in users:   
#        user_data = {}   
#        user_data['nisn'] = user.nisn  
#        user_data['name'] = user.fullname
#        result.append(user_data)   
#    return jsonify({'status':200,'users': result})  




if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0")
