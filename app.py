#Load env variables
from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from nylas import APIClient

from sqlalchemy.sql import func

#Initialize Nylas API client
nylas = APIClient(os.environ.get("CLIENT_ID"),
    os.environ.get("CLIENT_SECRET"),
    os.environ.get("ACCESS_TOKEN"),
)
#Fetch messages
messages = nylas.messages

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class MyEmail(db.Model):
    id = db.Column(db.String, primary_key = True)
    sender = db.Column(db.String)
    recipient = db.Column(db.String)
    date = db.Column(db.Integer)
    label = db.Column(db.String)

@app.route('/')
def index():
    db.session.query(MyEmail).delete()
    for message in messages:
        myemail = MyEmail(id=message.id,sender=message.from_[0]['name'],recipient=message.to[0]['name'],date=message.date,label=message.labels[0]['name'])
        db.session.add(myemail)
        db.session.commit()
    myemails = MyEmail.query.all()
    return render_template('index.html', myemails=myemails)