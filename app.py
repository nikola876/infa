from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    profile_pic = db.Column(db.String(150), nullable=True, default='default.png')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=150)])
    profile_pic = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

class DeleteAccountForm(FlaskForm):
    submit = SubmitField('Delete Account')

@app.route('/')
def home():
    users = User.query.all()
    return render_template('home.html', users=users)

@app.route('/accounts')
@login_required
def accounts():
    users = User.query.all()
    return render_template('accounts.html', users=users)

@app.route('/login_as/<int:user_id>', methods=['POST'])
@login_required
def login_as(user_id):
    user = User.query.get(user_id)
    if user:
        return redirect(url_for('login', user_id=user.id)) 
    flash('User not found.', 'danger')
    return redirect(url_for('accounts'))




@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        if user.profile_pic and user.profile_pic != 'default.png':
            pic_path = os.path.join(app.config['UPLOAD_FOLDER'], user.profile_pic)
            if os.path.exists(pic_path):
                os.remove(pic_path)
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} has been deleted.', 'warning')
    else:
        flash('User not found.', 'danger')
    return redirect(url_for('accounts'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    user_id = request.args.get('user_id', type=int) 

    if user_id:
        user = User.query.get(user_id)
        if user:
            form.username.data = user.username 

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Login failed. Check username and password.', 'danger')

    return render_template('login.html', form=form)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    delete_form = DeleteAccountForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        if form.profile_pic.data:
            pic_filename = f"{current_user.id}.png"
            pic_path = os.path.join(app.config['UPLOAD_FOLDER'], pic_filename)
            form.profile_pic.data.save(pic_path)
            current_user.profile_pic = pic_filename
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    form.username.data = current_user.username
    return render_template('profile.html', form=form, delete_form=delete_form, user=current_user)

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get(current_user.id)
    if user and user.profile_pic and user.profile_pic != 'default.png':
        pic_path = os.path.join(app.config['UPLOAD_FOLDER'], user.profile_pic)
        if os.path.exists(pic_path):
            os.remove(pic_path)
    logout_user()
    db.session.delete(user)
    db.session.commit()
    flash('Your account has been deleted.', 'warning')
    return redirect(url_for('home'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
