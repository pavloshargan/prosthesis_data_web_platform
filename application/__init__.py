from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms import TextField

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

UPLOAD_FOLDER = 'application/uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from application import bcrypt

class MyModelView(ModelView):
    def index(self):
        return self.render('login.html')
    def on_model_change(self, form, User, is_created=False):
        User.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

from application.models import *
admin = Admin(app)
admin.add_view(MyModelView(User, db.session))

# Database initialization function
def create_database():
    with app.app_context():
        db.create_all()

# Call the function to initialize the database
create_database()

from application import routes
