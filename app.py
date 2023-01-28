#Load env variables
from dotenv import load_dotenv
load_dotenv()

import os, datetime
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
    subject = db.Column(db.String)
    sender = db.Column(db.String)
    recipient = db.Column(db.String)
    date = db.Column(db.Integer)
    label = db.Column(db.String)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    db.session.query(MyEmail).delete()
    for message in messages:
        myemail = MyEmail(id=message.id,subject=message.subject,sender=message.from_[0]['name'],recipient=message.to[0]['name'],\
            date=datetime.datetime.fromtimestamp(int(message.date)).strftime('%Y-%m-%d %H:%M:%S'),label=message.labels[0]['name'])
        db.session.add(myemail)
        db.session.commit()
    #myemails = MyEmail.query.all()

    result = db.session.query(MyEmail).with_entities(MyEmail.label, db.func.count(MyEmail.label).label('Count')).group_by(MyEmail.label).all()

    labels = [row[0] for row in result]
    values = [row[1] for row in result]

    return render_template('index.html', title='Total count of email labels', max=50, labels=labels, values=values)

