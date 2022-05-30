from functools import wraps
import jwt
from flask import Flask, request, jsonify, make_response, abort,current_app
import models

def token_required(f):  
   @wraps(f)  
   def decorator(*args, **kwargs):
      token = None 
      current_app.logger.debug(request.headers)

      if 'token' in request.headers:  
         token = request.headers['token'] 
      if not token:  
         return jsonify({'message': 'a valid token is missing'})
      try:  
         data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
         print(token)
         current_user=None
         if data['role']==0:
            current_user = {
               'user':models.Teacher.query.filter_by(nign=data['indentifier']).first(),
               'role':data['role']
               }
         if data['role']==1:
            current_user = {
               'user':models.Student.query.filter_by(nisn=data['indentifier']).first(),
               'role':data['role']
               }
            print(current_user)

         if data['role']==2:
            current_user = {
               'user':models.Admin.query.filter_by(id_admin=data['indentifier']).first(),
               'role':data['role']
               }
            print(current_user)
      except:  
         return jsonify({'message': 'token is invalid'})
      return f(current_user, *args,  **kwargs)
   return decorator 