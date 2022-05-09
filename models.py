#################################
#####	 NI FILE BUAT APA? 	#####
#################################

"""Application Models"""
from os import name
from typing import Text
from sqlalchemy.sql.expression import true
from flask_sqlalchemy import SQLAlchemy
from decimal import Decimal
from passlib.apps import custom_app_context as pwd_context

db = SQLAlchemy()

#################################
#####		Siswa			#####
#################################
class Login(db.Model):  
	__tablename__ = 'login'
	id = db.Column(db.Integer,  primary_key = True, autoincrement=True)
	public_id = db.Column(db.String)
	indentifier=db.Column(db.String(50))
	password = db.Column(db.String)
	role=db.Column(db.Integer)
	def __unicode__(self):
		return self.id

class Student(db.Model):  
	__tablename__ = 'student'
	nisn = db.Column(db.String(50),  primary_key = True,)
	fullname = db.Column(db.String(50))
	datebirth = db.Column(db.String(50))
	id_class = db.Column(db.Integer, db.ForeignKey('class.id_class'))
	attendance=db.relationship("StudentAttendance")
	courseAttendance=db.relationship("SCAttendance")
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
	nign = db.Column(db.String(50),  primary_key = True,)
	fullname = db.Column(db.String(50))
	datebirth = db.Column(db.String(50))
	homeRoom=db.relationship("Class")
	course=db.relationship("Course")
	attendance=db.relationship("TeacherAttendance")
	courseAttendance=db.relationship("TCAttendance")
	def __unicode__(self):
		return self.id
db.Index('idx_Teacher_id', Teacher.nign)
db.Index('idx_Teacher_fullname', Teacher.fullname)


#################################
#####		Kelas			#####
#################################
class Class(db.Model):  
	__tablename__ = 'class'
	id_class = db.Column(db.Integer,  primary_key = True,)
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
	id_course = db.Column(db.Integer,  primary_key = True,)
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
	id_sa = db.Column(db.Integer,  primary_key = True,)
	nisn = db.Column(db.String(50), db.ForeignKey('student.nisn'))
	temperature = db.Column(db.Float(3))
	check_in = db.Column(db.DateTime())
	check_out = db.Column(db.DateTime())
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
	id_ta = db.Column(db.Integer,  primary_key = True,)
	nign = db.Column(db.String(50), db.ForeignKey('teacher.nign'))
	temperature = db.Column(db.Float(3))
	check_in = db.Column(db.DateTime())
	check_out = db.Column(db.DateTime())
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
	id_tca = db.Column(db.Integer,  primary_key = True,)
	nign = db.Column(db.String(50), db.ForeignKey('teacher.nign'))
	attend_course = db.Column(db.DateTime())
	id_attend = db.Column(db.Integer,  db.ForeignKey('course_attendance.id_attend'))
	def __unicode__(self):
		return self.id
db.Index('idx_TCAttendance_id', TCAttendance.id_tca)
db.Index('idx_TCAttendance_attend', TCAttendance.attend_course)


#################################
##### Presensi Mapel Siswa	#####
#################################

class SCAttendance(db.Model):  
	__tablename__ = 'sc_attendance'
	id_sca = db.Column(db.Integer,  primary_key = True,)
	nisn = db.Column(db.String(50),  db.ForeignKey('student.nisn'))
	attend_course = db.Column(db.DateTime)
	id_attend = db.Column(db.Integer,  db.ForeignKey('course_attendance.id_attend'))
	def __unicode__(self):
		return self.id
db.Index('idx_SCAttendance_id', SCAttendance.id_sca)
db.Index('idx_SCAttendance_attend', SCAttendance.attend_course)


#################################
#####	Presensi Mapel		#####
#################################

class CourseAttendance(db.Model):  
	__tablename__ = 'course_attendance'
	id_attend = db.Column(db.Integer,  primary_key = True,)
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