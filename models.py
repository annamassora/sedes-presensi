"""Application Models"""
from os import name
from typing import Text
from sqlalchemy.sql.expression import true
from flask_sqlalchemy import SQLAlchemy
from decimal import Decimal
from passlib.apps import custom_app_context as pwd_context

db = SQLAlchemy()

class Login(db.Model):  
	__tablename__ = 'login'
	public_id = db.Column(db.String(255),  primary_key = True,passive_deletes=True)
	indentifier=db.Column(db.String(50))
	password = db.Column(db.String)
	role=db.Column(db.Integer)
	def __unicode__(self):
		return self.id

#################################
#####		Admin			#####
#################################

class Admin(db.Model):  
	__tablename__ = 'admin'
	id_admin = db.Column(db.String(50),  primary_key = True)
	public_id = db.Column(db.String(255), db.ForeignKey('login.public_id',ondelete='CASCADE'))
	fullname = db.Column(db.String(50))
	login = db.relationship(Login, backref=db.backref("admin", cascade="all,delete"))
	def __unicode__(self):
		return self.id
db.Index('idx_id_admin', Admin.id_admin)
db.Index('idx_Admin_fullname', Admin.fullname)

#################################
#####		Siswa			#####
#################################

class Student(db.Model):  
	__tablename__ = 'student'
	nisn = db.Column(db.String(50),  primary_key = True)
	fullname = db.Column(db.String(50))
	datebirth = db.Column(db.String(50))
	public_id = db.Column(db.String(255), db.ForeignKey('login.public_id',ondelete='CASCADE'))
	id_class = db.Column(db.Integer, db.ForeignKey('class.id_class'))
	login = db.relationship(Login, backref=db.backref("student", cascade="all,delete"))
	attendance=db.relationship("StudentAttendance", passive_deletes=True)
	courseAttendance=db.relationship("SCAttendance", passive_deletes=True)
	def __unicode__(self):
		return self.id
db.Index('idx_Student_id', Student.nisn)
db.Index('idx_Student_fullname', Student.fullname)
db.Index('idx_Student_class', Student.id_class)


#################################
#####		Guru			#####
#################################

class Teacher(db.Model):  
	__tablename__ = 'teacher'
	nign = db.Column(db.String(50),  primary_key = True)
	fullname = db.Column(db.String(50))
	datebirth = db.Column(db.String(50))
	homeRoom=db.relationship("Class")
	course=db.relationship("Course")
	public_id = db.Column(db.String(255), db.ForeignKey('login.public_id',ondelete='CASCADE'))
	login = db.relationship(Login, backref=db.backref("teacher", cascade="all,delete"))
	attendance=db.relationship("TeacherAttendance", passive_deletes=True)
	courseAttendance=db.relationship("TCAttendance", passive_deletes=True)
	def __unicode__(self):
		return self.id
db.Index('idx_Teacher_id', Teacher.nign)
db.Index('idx_Teacher_fullname', Teacher.fullname)


#################################
#####		Kelas			#####
#################################
class Class(db.Model):  
	__tablename__ = 'class'
	id_class = db.Column(db.Integer,  primary_key = True,autoincrement=True)
	fullname = db.Column(db.String(50))
	period = db.Column(db.String(50))
	nign = db.Column(db.String(50), db.ForeignKey('teacher.nign'))
	student=db.relationship("Student")
	course=db.relationship("Course")
	def __unicode__(self):
		return self.id
db.Index('idx_Class_id', Class.id_class)
db.Index('idx_Class_fullname', Class.fullname)
db.Index('idx_Class_period', Class.period)


#################################
#####		Mapel			#####
#################################

class Course(db.Model):  
	__tablename__ = 'course'
	id_course = db.Column(db.Integer,  primary_key = True,autoincrement=True)
	fullname = db.Column(db.String(50))
	id_class = db.Column(db.Integer, db.ForeignKey('class.id_class'))
	nign = db.Column(db.String(50), db.ForeignKey('teacher.nign'))
	courseAttendance=db.relationship("CourseAttendance")
	def __unicode__(self):
		return self.id
db.Index('idx_Course_id', Course.id_course)
db.Index('idx_Course_fullname', Course.fullname)


#################################
#####	Presensi Siswa		#####
#################################

class StudentAttendance(db.Model):  
	__tablename__ = 'student_attendance'
	id_sa = db.Column(db.Integer,  primary_key = True, autoincrement=True)
	nisn = db.Column(db.String(50), db.ForeignKey('student.nisn',ondelete='CASCADE'))
	location = db.Column(db.String(50))
	temperature = db.Column(db.Numeric(14,2))
	check_in = db.Column(db.DateTime())
	check_out = db.Column(db.DateTime(),nullable = True )
	def __unicode__(self):
		return self.id
db.Index('idx_StudentAttendance_id', StudentAttendance.id_sa)
db.Index('idx_StudentAttendance_temperature', StudentAttendance.temperature)
db.Index('idx_StudentAttendance_checkin', StudentAttendance.check_in)
db.Index('idx_StudentAttendance_checkout', StudentAttendance.check_out)


#################################
#####	Presensi Guru		#####
#################################

class TeacherAttendance(db.Model):  
	__tablename__ = 'teacher_attendance'
	id_ta = db.Column(db.Integer,  primary_key = True,autoincrement=True)
	nign = db.Column(db.String(50), db.ForeignKey('teacher.nign',ondelete='CASCADE'))
	location = db.Column(db.String(50))
	temperature = db.Column(db.Numeric(14,2))
	check_in = db.Column(db.DateTime())
	check_out = db.Column(db.DateTime(),nullable = True )
	def __unicode__(self):
		return self.id
db.Index('idx_TeacherAttendance_id', TeacherAttendance.id_ta)
db.Index('idx_TeacherAttendance_temperature', TeacherAttendance.temperature)
db.Index('idx_TeacherAttendance_checkin', TeacherAttendance.check_in)
db.Index('idx_TeacherAttendance_checkout', TeacherAttendance.check_out)


#################################
##### Presensi Mapel Guru	#####
#################################

class TCAttendance(db.Model):  
	__tablename__ = 'tc_attendance'
	id_tca = db.Column(db.Integer,  primary_key = True,autoincrement=True)
	nign = db.Column(db.String(50), db.ForeignKey('teacher.nign'))
	attend_course = db.Column(db.DateTime())
	id_attend = db.Column(db.Integer,  db.ForeignKey('course_attendance.id_attend',ondelete='CASCADE'))
	def __unicode__(self):
		return self.id
db.Index('idx_TCAttendance_id', TCAttendance.id_tca)
db.Index('idx_TCAttendance_attend', TCAttendance.attend_course)


#################################
##### Presensi Mapel Siswa	#####
#################################

class SCAttendance(db.Model):  
	__tablename__ = 'sc_attendance'
	id_sca = db.Column(db.Integer,  primary_key = True,autoincrement=True)
	nisn = db.Column(db.String(50),  db.ForeignKey('student.nisn'))
	attend_course = db.Column(db.DateTime)
	id_attend = db.Column(db.Integer,  db.ForeignKey('course_attendance.id_attend',ondelete='CASCADE'))
	def __unicode__(self):
		return self.id
db.Index('idx_SCAttendance_id', SCAttendance.id_sca)
db.Index('idx_SCAttendance_attend', SCAttendance.attend_course)


#################################
#####	Presensi Mapel		#####
#################################

class CourseAttendance(db.Model):  
	__tablename__ = 'course_attendance'
	id_attend = db.Column(db.Integer,  primary_key = True,autoincrement=True)
	id_course = db.Column(db.Integer, db.ForeignKey('course.id_course'))
	id_class = db.Column(db.Integer, db.ForeignKey('class.id_class'))
	date = db.Column(db.Date)
	scAttendance=db.relationship("SCAttendance")
	tcAttendance=db.relationship("TCAttendance")
	def __unicode__(self):
		return self.id
db.Index('idx_CourseAttendance_id', CourseAttendance.id_attend)
db.Index('idx_CourseAttendance_date', CourseAttendance.date)


#################################
#####		QR Code			#####
#################################

class QRCode(db.Model):  
	__tablename__ = 'qrcode'
	id_qr = db.Column(db.Integer,  primary_key = True,autoincrement=True)
	location= db.Column(db.String(50))
	qrString= db.Column(db.String(255))
	def __unicode__(self):
		return self.id
db.Index('idx_QRCode_id', QRCode.id_qr)
db.Index('idx_QRCode_location', QRCode.location)

#################################
#####	Buku Kemajuan		#####
#################################

# class BookClass(db.Model):  
# 	__tablename__ = 'book_class'
# 	id_attend = db.Column(db.Integer,  db.ForeignKey('id_attend'))
# 	student_attend = db.Column(db.String(200))
# 	course = db.Column(db.String(200))
# 	id_course = db.Column(db.Integer,  db.ForeignKey('id_course'))
# 	def __unicode__(self):
# 		return self.id