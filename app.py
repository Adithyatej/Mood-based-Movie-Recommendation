from flask import Flask, request,render_template, redirect,session, Response, jsonify,url_for
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import pandas as pd
import numpy
import h5py
import requests
from patsy import dmatrices
from model import recommend



movies=pd.read_csv('output.csv')



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    type_of_movies = db.Column(db.String(100),nullable=False)
    Angry = db.Column(db.String(100),nullable=False)
    Bored = db.Column(db.String(100),nullable=False)
    Peace = db.Column(db.String(100),nullable=False)
    Happy = db.Column(db.String(100),nullable=False)
    Sad = db.Column(db.String(100),nullable=False)
    Terror = db.Column(db.String(100),nullable=False)
    Romantic = db.Column(db.String(100),nullable=False)
    Thrilled = db.Column(db.String(100),nullable=False)
    Disgust = db.Column(db.String(100),nullable=False)

    def __init__(self,email,password,name,type_of_movies,Angry,Bored,Peace,Happy,Sad,Terror,Romantic,Thrilled,Disgust):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.type_of_movies=type_of_movies
        self.Angry=Angry
        self.Bored=Bored
        self.Peace=Peace
        self.Happy=Happy
        self.Sad=Sad
        self.Terror=Terror
        self.Romantic=Romantic
        self.Thrilled=Thrilled
        self.Disgust=Disgust
    
    def check_password(self,password):
        return bcrypt.checkpw(password.encode('utf-8'),self.password.encode('utf-8'))

with app.app_context():
    db.create_all()

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        # handle request
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        type_of_movies=request.form['type_of_movies']
        Angry = request.form['Angry']
        Bored = request.form['Bored']
        Peace = request.form['Peace']
        Happy = request.form['Happy']
        Sad = request.form['Sad']
        Terror = request.form['Terror']
        Romantic = request.form['Romantic']
        Thrilled = request.form['Thrilled']
        Disgust = request.form['Disgust']

        new_user = User(name=name,email=email,password=password,type_of_movies=type_of_movies,Angry=Angry,Bored=Bored,Peace=Peace,Happy=Happy,Sad=Sad,Terror=Terror,Romantic=Romantic,Thrilled=Thrilled,Disgust=Disgust)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')


@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Query the database to find the user with the specified email
        user = User.query.filter_by(email=email).first()

        # Check if the user exists
        if user:
            # Check if the new password matches the confirm password
            if new_password == confirm_password:
                # Update the user's password in the database
                user.password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                db.session.commit()
                return redirect('/login')
            else:
                return redirect('/forgotpasswordpage')
        else:
            return redirect('/notemail')

    return render_template('forgotpassword.html')




@app.route('/notemail')
def notemail():

    return render_template('notemail.html')



@app.route('/forgotpasswordpage')
def forgot_password1():

    return render_template('forgotpassword1.html')


@app.route('/about')
def about():
    return render_template('sampleabout.html')
    


@app.route('/')
def index():
    return render_template('home.html')




# Route to handle the form submission and update the password in the data

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        print(request.form)
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['email'] = user.email
            return redirect('/index')
        else:
            return render_template('login.html',error='Invalid user')

    return render_template('login.html')




@app.route('/index')
def dashboard():
    if session['email']:
        user = User.query.filter_by(email=session['email']).first()
        return render_template('index.html',user=user)
    
    return redirect('/login')


@app.route('/recommendation', methods=['POST'])
def recommendation():
    recommended_movies=[]
    recommended_movies_poster=[]
    recommended_pop=[]
    movies_list=movies['title'].values
    status =False
    print(request.form['email'])
    print(request.form['user'])
    print(request.form['Happy'])
    print(request.form['type_of_movies'])
    print(request.form['email'])
    if request.method == "POST":
        try:
            if request.form:
                movies_name = request.form['Happy']
                type_of_movies=request.form['type_of_movies']
                user=request.form['user']
                email=request.form['email']
                

                recommended_id,recommended_movies,recommended_movies_poster,recommended_pop=recommend(movies_name,type_of_movies,email)
                print(recommended_movies)
                print(recommended_movies_poster)
                print(recommended_pop)
                print(recommended_id)
                status=True
                session['user']=user
                session['recommended_id']=recommended_id
                session['recommended_movies'] = recommended_movies
                session['recommended_movies_poster'] = recommended_movies_poster
                session['recommended_pop']=recommended_pop
                session['status'] = True


                return redirect('/prediction')



        except Exception as e:
            error = {'error': e}
            return render_template('index.html', error=error)
    
    
    return render_template('index.html')
        

@app.route('/prediction',methods=['GET'])
def prediction():
    User=session.get('user')
    recommended_id= session.get('recommended_id',[])
    recommended_movies = session.get('recommended_movies',[])
    recommended_movies_poster = session.get('recommended_movies_poster',[])
    recommended_pop=session.get('recommended_pop',[])
    zipped_movies = zip(recommended_id,recommended_movies_poster,recommended_movies,recommended_pop)
    status = session.get('status')
    print(status)
    if status:
        return render_template('prediction.html',zipped_movies=zipped_movies,status=status,User=User)
    else:
        return redirect('/')

@app.route('/logout')
def logout():
    session.pop('email',None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
