from flask import render_template, url_for, flash, redirect, request
from application import app, db, bcrypt
from application.forms import RegistrationForm, LoginForm
from application.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
import plotly
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import json
import os
import shutil
from os.path import join, dirname, realpath
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'csv'}

def create_plot(filename):
    path_to_file = os.path.join(app.config['UPLOAD_FOLDER'], current_user.username, filename)
    loaded_df = pd.read_csv(path_to_file)

    # Convert Time to a readable format if necessary
    loaded_df['Time'] = pd.to_datetime(loaded_df['Time'], unit='ms')

    # Creating a plot for each acceleration component
    data = [
        go.Scatter(
            x=loaded_df['Time'], 
            y=loaded_df['Acc_x'],
            mode='lines',
            name='Acc_x'
        ),
        go.Scatter(
            x=loaded_df['Time'], 
            y=loaded_df['Acc_y'],
            mode='lines',
            name='Acc_y'
        ),
        go.Scatter(
            x=loaded_df['Time'], 
            y=loaded_df['Acc_z'],
            mode='lines',
            name='Acc_z'
        )
    ]

    layout = go.Layout(
        title='Acceleration Data',
        xaxis=dict(title='Time'),
        yaxis=dict(title='Acceleration')
    )

    graphJSON = json.dumps({'data': data, 'layout': layout}, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', title='home') 

@app.route("/my_patients")
def my_patients():
    if current_user.is_doctor:
        return render_template('my_patients.html', title='My Patients')
    next_page = request.args.get('next')
    return redirect(next_page) if next_page else redirect(url_for('home'))

@app.route("/new_patient")
def new_patient():
    if current_user.is_doctor:
        return render_template('new_patient.html', title='New Patient')
    next_page = request.args.get('next')
    return redirect(next_page) if next_page else redirect(url_for('home'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import shutil
@app.route("/graphs", methods=['GET', 'POST'])
@login_required
def graphs():
    if current_user.is_doctor:
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('home'))

    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.username)

    # Create user directory if it doesn't exist and copy the sample file
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
        sample_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'sample_data.csv')
        shutil.copy(sample_file_path, user_folder)

    files = os.listdir(user_folder)

    # Initialize selected_file variable
    selected_file = request.form.get('selected_file', files[0] if files else None)

    bar = None
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(user_folder, filename))
                return redirect(url_for('graphs'))
            selected_file = files[0] if files else None  # Reset selected file after upload
        elif 'selected_file' in request.form:
            selected_file = request.form['selected_file']
            if selected_file in files:
                bar = create_plot(selected_file)

    if not bar and selected_file:
        bar = create_plot(selected_file)

    return render_template('graphs.html', files=files, selected_file=selected_file, plot=bar)



@app.route("/help")
def help():
    return render_template('help.html', title='help') 

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('account'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('account'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('account'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('graphs'))


@app.route("/account")
@login_required
def account():
    return render_template('account.html', title='Account')
