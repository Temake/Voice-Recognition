from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo
from .models import Teacher

class LoginForm(FlaskForm):
    """Login form for teachers"""
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    """Registration form for teachers"""
    first_name = StringField('First Name', validators=[
        DataRequired(),
        Length(min=2, max=50, message='First name must be between 2 and 50 characters')
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(),
        Length(min=2, max=50, message='Last name must be between 2 and 50 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        """Check if email is already registered"""
        teacher = Teacher.query.filter_by(email=email.data.lower()).first()
        if teacher:
            raise ValidationError('Email already registered. Please use a different email or login.')
