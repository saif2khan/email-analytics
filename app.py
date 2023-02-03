# Requirements from server.py 

from __future__ import print_function
import os
import sys
import textwrap

import requests, jmespath
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_dance.contrib.nylas import make_nylas_blueprint, nylas
from flask_login import logout_user

import datetime
from flask import Flask, render_template, request, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
from nylas import APIClient
from sqlalchemy.sql import func

app = Flask(__name__)
app.config.from_pyfile("config.py")

basedir = os.path.abspath(os.path.dirname(__file__))
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

colors = [
    "#F7464A", "#46BFBD", "#FDB45C", "#FEDCBA",
    "#ABCDEF", "#DDDDDD", "#ABCABC", "#4169E1",
    "#C71585", "#FF4500", "#FEDCBA", "#46BFBD"]

# Use Flask-Dance to automatically set up the OAuth endpoints for Nylas.
# For more information, check out the documentation: http://flask-dance.rtfd.org
nylas_bp = make_nylas_blueprint()
app.register_blueprint(nylas_bp, url_prefix="/login")

# Teach Flask how to find out that it's behind an ngrok proxy
app.wsgi_app = ProxyFix(app.wsgi_app)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/', methods=['GET','POST'])
def index():
    
    # If the user has already connected to Nylas via OAuth,
    # `nylas.authorized` will be True. Otherwise, it will be False.
    if not nylas.authorized:
        # OAuth requires HTTPS. The template will display a handy warning,
        # unless we've overridden the check.
        return render_template(
            "before_authorized.html",
            insecure_override=os.environ.get("OAUTHLIB_INSECURE_TRANSPORT"),
        )

    # If we've gotten to this point, then the user has already connected
    # to Nylas via OAuth. Let's set up the SDK client with the OAuth token:
    client = APIClient(
        client_id=app.config["NYLAS_OAUTH_CLIENT_ID"],
        client_secret=app.config["NYLAS_OAUTH_CLIENT_SECRET"],
        access_token=nylas.access_token,
    )
    
    if request.method == 'POST':
        if request.form.get('action1') == 'Logout':
            db.session.query(MyEmail).delete()
            client.revoke_all_tokens()
            return render_template('before_authorized.html')
    
    db.session.query(MyEmail).delete()
    #Fetch messages
    messages = client.messages
    account = client.account
    name = jmespath.search('name',account)

    for message in messages:
        myemail = MyEmail(id=message.id,subject=message.subject,sender=message.from_[0]['name'],recipient=message.to[0]['name'],\
            date=datetime.datetime.fromtimestamp(int(message.date)).strftime('%Y-%m-%d %H:%M:%S'),label=message.labels[0]['name'])
        db.session.add(myemail)
        db.session.commit()

    result = db.session.query(MyEmail).with_entities(MyEmail.label, db.func.count(MyEmail.label).label('Count')).group_by(MyEmail.label).all()

    labels = [row[0] for row in result]
    values = [row[1] for row in result]

    result_pie = db.session.query(MyEmail).with_entities(MyEmail.sender, db.func.count(MyEmail.sender).label('Count')).group_by(MyEmail.sender).all()

    labels_pie = [row[0] for row in result_pie]
    values_pie = [row[1] for row in result_pie]

    return render_template('index.html', labels=labels, values=values, set=zip(values_pie,labels_pie,colors), name=name)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
