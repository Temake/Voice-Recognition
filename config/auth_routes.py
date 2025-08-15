from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, Teacher
from .forms import LoginForm, RegistrationForm

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Teacher login"""
    if current_user.is_authenticated:
        return redirect(url_for('config.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        teacher = Teacher.query.filter_by(email=form.email.data.lower()).first()
        
        if teacher and teacher.check_password(form.password.data) and teacher.is_active:
            login_user(teacher, remember=True)
            flash('Welcome back!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('config.index'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
    
    return render_template('auth/login.html', form=form, title='Sign In')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Teacher registration"""
    if current_user.is_authenticated:
        return redirect(url_for('config.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Create new teacher
            teacher = Teacher(
                email=form.email.data.lower().strip(),
                first_name=form.first_name.data.strip(),
                last_name=form.last_name.data.strip()
            )
            teacher.set_password(form.password.data)
            
            # Save to database
            db.session.add(teacher)
            db.session.commit()
            
            flash('Registration successful! Please sign in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('auth/register.html', form=form, title='Register')

@auth.route('/logout')
@login_required
def logout():
    """Teacher logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
