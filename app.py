from flask import Flask, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, asc, and_
from dateutil import parser
from datetime import datetime
from werkzeug.exceptions import Unauthorized, NotFound, BadRequest, BadRequestKeyError
from werkzeug.security import generate_password_hash, check_password_hash

from helpers import login_required, populate_lessons_2324, populate_lessons_2425, populate_tuitions_2425, populate_salaries_2425, adjust_lessons, delete_lessons, all_schedules_info, teacher_schedules_info, student_schedules_info, attendance_update, payment_update, add_tuitions

import calendar

# Configure application
app = Flask(__name__)

# Configure session (default using cookies instead of filesystem)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure databases
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///garage_database.db'
db = SQLAlchemy(app)

# Global scope variables
current_school_year = 2425
year_begin = 2024
year_finish = 2025
begin_date = datetime.strptime("2024-9-2", "%Y-%m-%d").date()
finish_date = datetime.strptime("2025-7-31", "%Y-%m-%d").date()

# Create Models (ORM "Object-relational mapper" model) and tables

# Association tables (many-to-many relationships)

students_schedules = db.Table('students_schedules',
    db.Column('students_id', db.Integer, db.ForeignKey('students.student_id'), primary_key = True),
    db.Column('schedule_id', db.Integer, db.ForeignKey('schedules.class_id'), primary_key = True)
)

lesson_students = db.Table('lesson_students',
    db.Column('students_id', db.Integer, db.ForeignKey('students.student_id'), primary_key = True),
    db.Column('lesson_id', db.Integer, db.ForeignKey('lessons.lesson_id'), primary_key = True),
)

student_tuitions = db.Table('student_tuitions',
    db.Column('tuition_id', db.Integer, db.ForeignKey('tuitions.tuition_id'), primary_key=True),
    db.Column('student_id', db.Integer, db.ForeignKey('students.student_id'), primary_key=True)
)

teacher_salaries = db.Table('teacher_salaries',
    db.Column('salary_id', db.Integer, db.ForeignKey('salaries.salary_id'), primary_key=True),
    db.Column('teacher_id', db.Integer, db.ForeignKey('teachers.teacher_id'), primary_key=True)
)

# Models

class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, autoincrement=True, primary_key = True, unique = True, nullable = False)
    name = db.Column(db.String(30), nullable = False, unique = True)
    age = db.Column(db.Integer)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(50), nullable = False)
    enrollment = db.Column(db.Date)
    role = db.Column(db.String(20), nullable = False)
    is_registered = db.Column(db.Boolean, nullable = False)
    hash_password = db.Column(db.String)

class Students(db.Model):
    __tablename__ = "students"

    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key = True, nullable = False)
    course = db.Column(db.String(50))
    instrument = db.Column(db.String(50))
    teacher_id = db.Column(db.Integer)
    monthly_fee = db.Column(db.Integer)
    active = db.Column(db.Boolean, nullable = False)

    user = db.relationship('Users', uselist=False)
    tuitions = db.relationship('Tuitions', secondary=student_tuitions, backref=db.backref('student', lazy=True))

class Teachers(db.Model):
    __tablename__ = "teachers"

    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key = True, nullable = False)
    instrument = db.Column(db.String(50))
    current_salary = db.Column(db.Integer)
    active = db.Column(db.Boolean, nullable = False)

    user = db.relationship('Users', uselist=False)
    salaries = db.relationship('Salaries', secondary=teacher_salaries, backref=db.backref('teacher', lazy=True))

class Tuitions(db.Model):
    __tablename__ = "tuitions"

    tuition_id = db.Column(db.Integer, autoincrement = True, primary_key = True, unique = True, nullable = False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.student_id"), nullable = False)
    tuition_date = db.Column(db.Date, nullable = False)
    tuition_value = db.Column(db.Integer, nullable = False)
    is_payed = db.Column(db.Boolean)
    payment_date = db.Column(db.Date)

class Salaries(db.Model):
    __tablename__ = "salaries"

    salary_id = db.Column(db.Integer, autoincrement = True, primary_key = True, unique = True, nullable = False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.teacher_id"), nullable = False)
    salary_date = db.Column(db.Date, nullable = False)
    salary_value = db.Column(db.Integer, nullable = False)
    is_payed = db.Column(db.Boolean)
    payment_date = db.Column(db.Date)

class Schedules(db.Model):
    __tablename__ = "schedules"

    class_id = db.Column(db.Integer, autoincrement = True, primary_key = True, unique = True, nullable = False)
    school_year = db.Column(db.Integer, nullable = False)
    name = db.Column(db.String(30), nullable = False)
    weekday = db.Column(db.Integer, nullable = False)
    hour = db.Column(db.Time, nullable = False)
    duration = db.Column(db.Integer, nullable = False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = False)
    classroom = db.Column(db.String(30), nullable = False)
    active = db.Column(db.Boolean)

    students = db.relationship('Students', secondary=students_schedules, backref=db.backref('schedules', lazy=True))

class Lessons(db.Model):
    __tablename__ = "lessons"

    lesson_id = db.Column(db.Integer, autoincrement = True, primary_key = True, unique = True, nullable = False)
    class_id = db.Column(db.Integer, db.ForeignKey("schedules.class_id"), nullable = False)
    lesson_date = db.Column(db.Date, nullable = False)
    hour = db.Column(db.Time, nullable = False)
    duration = db.Column(db.Integer, nullable = False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = False)
    classroom = db.Column(db.String(30), nullable = False)
    attendance = db.Column(db.String(30))
    is_compensation = db.Column(db.String(30))
    compensation_id = db.Column(db.Integer)

    students = db.relationship('Students', secondary=lesson_students, backref=db.backref('lessons', lazy=True))


with app.app_context():
    db.create_all()

    #populate_lessons_2324(Schedules, Lessons, Students, students_schedules, lesson_students, db)
    #populate_lessons_2425(Schedules, Lessons, Students, students_schedules, db)
    #populate_tuitions_2425(Students, Tuitions, db)
    #populate_salaries_2425(Teachers, Salaries, db)
    attendance_update(Lessons, db)
    payment_update(Tuitions, db)
    

# Configure app to not save cache (ensures user has up-to-date info)
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Route functions
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register student or staff member"""

    # user reaches via post method
    if request.method == "POST":
        # get input from user
        user = request.form.get("user")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # check existence in db
        new_user = db.session.query(Users).filter(Users.id == user).one_or_none()
        print(new_user.is_registered)
        print(new_user.name)

        if not new_user:
            return NotFound(description="User not found")
        else:
            # check if user already registered
            if new_user.is_registered:
                print(new_user.is_registered)
                return BadRequest(description="User is already registered")
            else:
                if not password:
                    return BadRequestKeyError(arg="Password not valid")
                elif not confirmation or confirmation != password:
                    return BadRequestKeyError(arg="Passwords do not match")
                # update database
                else:
                    hash_password = generate_password_hash(password)
                    new_user.hash_password = hash_password
                    new_user.is_registered = True
                    db.session.commit()
                    return redirect("/login")

    # user reaches via GET method
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # clear session data
    session.clear()

    # user reaches via POST method
    if request.method == "POST":
        # get inputs
        user = request.form.get("user")
        password = request.form.get("password")

        # check if user in database and registered
        user_table = db.session.query(Users).filter(Users.id == user).one_or_none()

        if user_table:
            check_regist = user_table.is_registered
        else:
            return NotFound("User not found")
        
        if not check_regist:
            return NotFound(description="User not registered")
        else:
            # check password
            hash_password = user_table.hash_password
            if not password or not check_password_hash(hash_password, password):
                return BadRequestKeyError(arg="Password not valid")
            else:
                # save user_id in session and redirect to homepage
                session["user_id"] = user
                return redirect("/")

    # user reaches via GET method
    else:
        return render_template("login.html")
    

@app.route("/logout", methods=["GET", "POST"])
def logout():
    """Log user out"""

    session.clear()
    return redirect("/")


@app.route("/", methods =["GET"])
def index():
    """Homepage"""

    if "user_id" in session:
        logged_in=True
    else:
        logged_in=False

    # user logged_in
    if logged_in:

        user = db.session.query(Users).filter(Users.id == session["user_id"]).one_or_none()
        today = datetime.today().date()
        classes_data = []

        if user.role == "teacher":

            classes = db.session.query(Lessons).filter(and_(Lessons.teacher_id == user.id, Lessons.lesson_date == today)).order_by(asc(Lessons.hour)).all()

            if classes:
                
                for item in classes:
                    class_name = db.session.query(Schedules.name).filter(Schedules.class_id == item.class_id).scalar()
                    students = db.session.query(Students).join(lesson_students).filter(lesson_students.c.lesson_id == item.lesson_id).all() 
                    item.hour_formatted = item.hour.strftime('%H:%M')

                    class_data = {
                        'class': item, # all data from Lessons model
                        'name': class_name,
                        'students': students
                    }

                    classes_data.append(class_data)

                return render_template("index.html", logged_in=logged_in, user=user, classes_data=classes_data)
            
            else:
                return render_template("index.html", logged_in=logged_in, user=user, classes_data=None)
            
        elif user.role == "student":

            classes = db.session.query(Lessons).join(lesson_students).filter(and_(lesson_students.c.students_id == user.id, Lessons.lesson_date == today)).order_by(asc(Lessons.hour)).all()

            if classes:
                for item in classes:
                    class_name = db.session.query(Schedules.name).filter(Schedules.class_id == item.class_id).scalar()
                    teacher_name = db.session.query(Users.name).filter(Users.id == item.teacher_id).scalar()
                    item.hour_formatted = item.hour.strftime('%H:%M')

                    class_data = {
                        'class' : item,
                        'name': class_name,
                        'teacher' : teacher_name
                    }

                    classes_data.append(class_data)

                return render_template("index.html", logged_in=logged_in, user=user, classes_data=classes_data)
            
            else:
                return render_template("index.html", logged_in=logged_in, user=user, classes_data=None)
        
        else:

            classes = db.session.query(Lessons).filter(Lessons.lesson_date == today).order_by(asc(Lessons.hour)).all()

            if classes:

                for item in classes:
                    students = db.session.query(Students).join(lesson_students).filter(lesson_students.c.lesson_id == item.lesson_id).all()
                    teacher_name = db.session.query(Users.name).filter(Users.id == item.teacher_id).scalar()
                    class_name = db.session.query(Schedules.name).filter(Schedules.class_id == item.class_id).scalar()
                    item.hour_formatted = item.hour.strftime('%H:%M')
                
                    class_data = {
                        'class': item, # all data from Schedules model
                        'name': class_name,
                        'students': students,
                        'teacher': teacher_name,
                    }

                    classes_data.append(class_data)
           
                return render_template("index.html", logged_in=logged_in, user=user, classes_data=classes_data)
            
            else:
                return render_template("index.html", logged_in=logged_in, user=user, classes_data=None)
    
    # user logged_out
    else:
        return render_template("index.html", logged_in=logged_in)


@app.route("/schedules", methods=["GET", "POST"])
@login_required

def schedules():
    """Display schedules"""

    user = db.session.query(Users).filter(Users.id == session["user_id"]).one_or_none()
  
    classes_data = []

    # User reaches via POST (selected_schedules.html)
    if request.method == "POST":
        
        school_year = request.form.get("school_year")
        school_year_int = int(school_year)
        if school_year_int == 2324:
            school_year_str = "2023/2024"
        else:
            school_year_str = "2024/2025"

        # If user selected current school year, redirect to schedules.html
        if school_year_int == current_school_year:
            return redirect ("/schedules")
        
        else:

            # Get classes from Schedules table
            if user.role == "admin":
                classes = db.session.query(Schedules).filter(Schedules.school_year == school_year_int).order_by(asc(Schedules.weekday), asc(Schedules.hour)).all()

            elif user.role == "teacher":
                classes = db.session.query(Schedules).filter(and_(Schedules.school_year == school_year_int, Schedules.teacher_id == user.id)).order_by(asc(Schedules.weekday), asc(Schedules.hour)).all()

            else:
                classes = db.session.query(Schedules).join(students_schedules).filter(and_(Schedules.school_year == school_year_int, students_schedules.c.students_id == user.id)).order_by(asc(Schedules.weekday), asc(Schedules.hour)).all()

            # If schedules on selected school year
            if classes:
                # Get students and teacher names
                for item in classes:
                    
                    students = db.session.query(Students).join(students_schedules).filter(students_schedules.c.schedule_id == item.class_id).all()
                    teacher = db.session.query(Users.name).filter(Users.id == item.teacher_id).one_or_none()
                    day_name = calendar.day_name[item.weekday]
                    item.hour_formatted = item.hour.strftime('%H:%M')

                    class_data = {
                        'class': item, # all data from lesson model
                        'students': students,
                        'teacher': teacher, 
                        'weekday': day_name
                    }
                    classes_data.append(class_data)

                # Display schedule for selected day
                if user.role == "admin":
                    return render_template("selected_schedules.html", classes_data=classes_data, user=user, school_year=school_year_str)
                
                elif user.role == "teacher":
                    return render_template("selected_schedules.html", classes_data=classes_data, user=user, school_year=school_year_str)
                
                else:
                    return render_template("selected_schedules.html", classes_data=classes_data, user=user, school_year=school_year_str)
            # No classes on selected year
            else:
                return render_template("selected_schedules.html", classes_data=None, user=user)


    # User reaches via GET (schedules.html)
    else:

        # Get all schedules for each user
        if user.role == "admin":
            classes = db.session.query(Schedules).filter(and_(Schedules.school_year == current_school_year, Schedules.active == True)).order_by(asc(Schedules.weekday), asc(Schedules.hour)).all()
        
        elif user.role == "teacher":
            classes = db.session.query(Schedules).filter(and_(Schedules.teacher_id == user.id, Schedules.school_year == current_school_year, Schedules.active == True)).order_by(asc(Schedules.weekday), asc(Schedules.hour)).all()
        
        else:
            classes = db.session.query(Schedules).join(students_schedules).filter(and_(students_schedules.c.students_id == user.id, Schedules.school_year == current_school_year, Schedules.active == True)).order_by(asc(Schedules.weekday), asc(Schedules.hour)).all()

        # If classes on that year
        if classes:
            for item in classes:
                # Get student, teacher and weekday names
                students = db.session.query(Students).join(students_schedules).filter(students_schedules.c.schedule_id == item.class_id).all()
                teacher = db.session.query(Users.name).filter(Users.id == item.teacher_id).one_or_none()
                day_name = calendar.day_name[item.weekday]
                item.hour_formatted = item.hour.strftime('%H:%M')

                class_data = {
                    'class': item,
                    'students': students,
                    'teacher': teacher,
                    'weekday': day_name
                }

                classes_data.append(class_data)
                

            # Display current schedule
            if user.role == "admin":
                active_students = db.session.query(Users).join(Students).filter(Students.active == True).order_by(Users.name).all()
                students = db.session.query(Users).filter(Users.role == "student").order_by(Users.name).all()
                teacher_names = db.session.query(Users.name).filter(Users.role == "teacher").order_by(Users.name).all()

                return render_template("schedules.html", classes_data=classes_data, user=user, students=students, active_students=active_students, teacher_names=teacher_names)
            
            elif user.role == "teacher":
                return render_template("schedules.html", classes_data=classes_data, user=user)
            
            else:
                return render_template("schedules.html", classes_data=classes_data, user=user)
        # No schedules on that year 
        else:
            return render_template("schedules.html", classes_data=None, user=user)


@app.route("/new_class", methods=["POST"])
def new_class():
    """Crete new schedule """
    
    # Get form variables
    class_name = request.form.get("class_name")
    weekday_name = request.form.get("weekday")
    start_time = request.form.get("start_time")
    class_duration = request.form.get("duration")
    teacher_name = request.form.get("teacher")
    students_ids = request.form.getlist("students[]")
    class_classroom = request.form.get("classroom")
    first_lesson_str = request.form.get("first_lesson")

    # Adjust variables to Schedules model types
    weekday_names = list(calendar.day_name)
    if weekday_name in weekday_names:
        weekday_int = weekday_names.index(weekday_name)
    else:
        print("Error translating weekday string to int")
        return redirect("/schedules")
    
    teacher = db.session.query(Users.id).filter(Users.name == teacher_name).scalar()
    if not teacher:
        print("Error finding teacher id")
        return redirect("/schedules")
        
    start_time = datetime.strptime(start_time, '%H:%M').time()
    
    # Create new Schedules instance
    new_schedule = Schedules(
        school_year = current_school_year,
        name = class_name,
        weekday = weekday_int,
        hour = start_time,
        duration = class_duration,
        teacher_id = teacher,
        classroom = class_classroom,
        active = True
    )

    # Add students to new_schedule
    for id in students_ids:
        student = db.session.query(Students).filter(Students.student_id == id).one_or_none()
        new_schedule.students.append(student)

    # Add to database
    db.session.add(new_schedule)
    db.session.commit()

    # Add lessons to Lessons model
    first_lesson = datetime.strptime(first_lesson_str, "%Y-%m-%d").date()
    print("First_lesson:", first_lesson)
    adjust_lessons(new_schedule, Lessons, db, first_lesson)
    attendance_update(Lessons, db)
    
    return redirect("/schedules")


@app.route("/change_class", methods=["POST"])
def change_class():
    """Change class data"""

    class_data = request.get_json()

    new_weekday_str = class_data["weekday"]
    new_time_str = class_data["startTime"].strip()
    # class_name = class_data["className"]
    class_id = class_data["classId"]
    new_teacher = class_data["teacher"].strip()
    new_students = class_data["students"]
    new_duration = class_data["duration"]
    new_classroom = class_data["classroom"]

    # Adjust variable types
    new_teacher_id = db.session.query(Users.id).filter(Users.name == new_teacher).scalar()
    new_time = datetime.strptime(new_time_str, '%H:%M').time()
    new_weekday = None

    weekday_names = list(calendar.day_name)
    if new_weekday_str in weekday_names:
        new_weekday = weekday_names.index(new_weekday_str)
    

    # Get original schedule
    schedule = db.session.query(Schedules).filter(Schedules.class_id == class_id).one_or_none()
    
    if schedule:
        schedule.weekday = new_weekday
        schedule.hour = new_time
        schedule.duration = new_duration
        schedule.teacher_id = new_teacher_id
        schedule.classroom = new_classroom

        if new_students:
            # Delete previous students
            schedule.students.clear()

            # Add new students
            for name in new_students:
                new_student = db.session.query(Students).join(Users).filter(Users.name == name).one_or_none()
                schedule.students.append(new_student)

        db.session.commit()

        edit_date = datetime.now()
        adjust_lessons(schedule, Lessons, db, edit_date)

    else:
        print("There was an error quering the edited schedule")

    schedules_url = url_for("schedules") 
    return jsonify({"redirect": schedules_url})

    

@app.route("/delete_class", methods=["POST"])
@login_required

def delete_class():
    """Change class to inactive"""

    data = request.get_json()
    class_id = int(data.get('classId'))
    delete_date = datetime.now()

    if class_id:
        schedule = db.session.query(Schedules).filter(Schedules.class_id == class_id).one_or_none()

        if schedule:
            # Delete future lessons
            delete_lessons(class_id, Lessons, db, delete_date)
            # Set schedule to inactive
            schedule.active = False

            # Commit changes and redirect
            db.session.commit()

            schedules_url = url_for("schedules")
            return jsonify({"redirect": schedules_url})
        else:
            print("There was an error deleting the schedule")
    else:
        print("There was an error getting class_id from JSON")

    
@app.route("/lessons", methods=["GET", "POST"])
@login_required

def lessons():
    """Display lessons"""

    user = db.session.query(Users).filter(Users.id == session["user_id"]).one_or_none()
    lessons_data = []
    today = datetime.today().date()

    # User reaches via POST (selected_lessons.html)
    if request.method == "POST":

        selected_schedule = request.form.get("schedule")
        print("Selected schedule:", selected_schedule)
        selected_date = request.form.get("date")
        print("Selected date:", selected_date)
        
        # User selected date
        if selected_date:
            date = datetime.strptime(selected_date, "%Y-%m-%d").date()
            date_formatted = date.strftime("%d-%m-%Y")

            # Get lessons from Lessons table
            if user.role == "admin":
                lessons = db.session.query(Lessons).filter(Lessons.lesson_date == date).order_by(asc(Lessons.hour)).all()
                schedules = all_schedules_info(Schedules, Users, db)

            elif user.role == "teacher":
                lessons = db.session.query(Lessons).filter(and_(Lessons.teacher_id == user.id, Lessons.lesson_date == date)).order_by(asc(Lessons.hour)).all()
                schedules = teacher_schedules_info(Schedules, db, user.id)
            else:
                lessons = db.session.query(Lessons).join(lesson_students).filter(and_(lesson_students.c.students_id == user.id, Lessons.lesson_date == date)).order_by(asc(Lessons.hour)).all()
                schedules = schedules = student_schedules_info(Schedules, Users, students_schedules, db, user.id)

            # If lessons on selected day
            if lessons:
                print(lessons)
                # Get students and teacher info
                for item in lessons:
                    students = db.session.query(Students).join(lesson_students).filter(lesson_students.c.lesson_id == item.lesson_id).all()
                    teacher_name = db.session.query(Users.name).filter(Users.id == item.teacher_id).scalar()
                    class_name = db.session.query(Schedules.name).filter(Schedules.class_id == item.class_id).scalar()
                    item.hour_formatted = item.hour.strftime('%H:%M')

                    data = {
                        'lesson': item, # all data from lesson model
                        'students': students,
                        'teacher': teacher_name,
                        'name': class_name
                    }

                    lessons_data.append(data)

                # Display schedule for selected day
                if user.role == "admin":
                    students = db.session.query(Users).filter(Users.role == "student").order_by(Users.name).all()
                    teacher_names = db.session.query(Users.name).filter(Users.role == "teacher").order_by(Users.name).all()
                    
                    return render_template("selected_lessons.html", lessons_data=lessons_data, schedules=schedules, students=students, teacher_names=teacher_names, user=user, date_formatted=date_formatted)
                
                elif user.role == "teacher":

                    return render_template("selected_lessons.html", lessons_data=lessons_data, schedules=schedules, user=user, date_formatted=date_formatted)
                
                else:
                    return render_template("selected_lessons.html", lessons_data=lessons_data, schedules=schedules, user=user, date_formatted=date_formatted)
            # No lessons on selected day
            else:
                return render_template("selected_lessons.html", lessons_data=None, user=user, schedules=schedules)
        
        # User selected schedule
        elif selected_schedule:

            lessons = db.session.query(Lessons).filter(Lessons.class_id == selected_schedule).order_by(asc(Lessons.lesson_date)).all()

            if lessons:
                for item in lessons:
                    students = db.session.query(Students).join(lesson_students).filter(lesson_students.c.lesson_id == item.lesson_id).all()
                    teacher = db.session.query(Users.name).filter(Users.id == item.teacher_id).scalar()
                    class_name = db.session.query(Schedules.name).filter(Schedules.class_id == item.class_id).scalar()
                    weekday = item.lesson_date.weekday()
                    day_name = calendar.day_name[weekday]
                    item.hour_formatted = item.hour.strftime('%H:%M')
                    item.date_formatted = item.lesson_date.strftime("%d-%m-%Y")

                    data = {
                        'lesson': item, # all data from lesson model
                        'students': students,
                        'teacher': teacher,
                        'name': class_name,
                        'weekday': day_name
                    }

                    lessons_data.append(data)

                # Display schedule for selected schedule
                if user.role == "admin":

                    schedules = all_schedules_info(Schedules, Users, db)
                    students = db.session.query(Users).filter(Users.role == "student").order_by(Users.name).all()
                    teacher_names = db.session.query(Users.name).filter(Users.role == "teacher").order_by(Users.name).all()
                    return render_template("selected_lessons.html", lessons_data=lessons_data, schedules=schedules, students=students, teacher_names=teacher_names, user=user, date_formatted=None)
                
                elif user.role == "teacher":

                    schedules = teacher_schedules_info(Schedules, db, user.id)
                    return render_template("selected_lessons.html", lessons_data=lessons_data, schedules=schedules, user=user, date_formatted=None)
                
                else:

                    schedules = student_schedules_info(Schedules, Users, students_schedules, db, user.id)
                    return render_template("selected_lessons.html", lessons_data=lessons_data, schedules=schedules, user=user, date_formatted=None)
                
            # No lessons on selected day
            else:
                schedules = all_schedules_info(Schedules, Users, db)
                return render_template("selected_lessons.html", lessons_data=None, user=user, schedules=schedules)

    # User reaches via GET (lessons.html)  
    else:
        if user.role == "admin":
            lessons = db.session.query(Lessons).filter(Lessons.lesson_date == today).order_by(asc(Lessons.hour)).all()
            schedules = all_schedules_info(Schedules, Users, db)

        elif user.role == "teacher":
            lessons = db.session.query(Lessons).filter(and_(Lessons.teacher_id == user.id, Lessons.lesson_date == today)).order_by(asc(Lessons.hour)).all()
            schedules = teacher_schedules_info(Schedules, db, user.id)
        
        else:
            lessons = db.session.query(Lessons).join(lesson_students).filter(and_(lesson_students.c.students_id == user.id, Lessons.lesson_date == today)).order_by(asc(Lessons.hour)).all()
            schedules = student_schedules_info(Schedules, Users, students_schedules, db, user.id)
        
        if lessons:
            for item in lessons:
                students = db.session.query(Students).join(lesson_students).filter(lesson_students.c.lesson_id == item.lesson_id).all()
                teacher_name = db.session.query(Users.name).filter(Users.id == item.teacher_id).scalar()
                class_name = db.session.query(Schedules.name).filter(Schedules.class_id == item.class_id).scalar()
                item.hour_formatted = item.hour.strftime('%H:%M')
                weekday = db.session.query(Schedules.weekday).filter(Schedules.class_id == item.class_id).scalar()
                day_name = calendar.day_name[weekday]

                data = {
                    'lesson': item, # all data from lesson model
                    'students': students,
                    'teacher': teacher_name,
                    'name': class_name,
                    'weekday': day_name
                }

                lessons_data.append(data)

            # Display schedule for today
            if user.role == "admin":
                students = db.session.query(Users).filter(Users.role == "student").order_by(Users.name).all()
                teacher_names = db.session.query(Users.name).filter(Users.role == "teacher").order_by(Users.name).all()
                
                return render_template("lessons.html", lessons_data=lessons_data, user=user, schedules=schedules, teacher_names=teacher_names, students=students)
            
            elif user.role == "teacher":

                return render_template("lessons.html", lessons_data=lessons_data, schedules=schedules, user=user)
            
            else:
                return render_template("lessons.html", lessons_data=lessons_data, schedules=schedules, user=user)
            
        # No lessons today
        else: 
            return render_template("lessons.html", lessons_data=None, user=user, schedules=schedules)



@app.route("/new_lesson", methods=["POST"])
def new_lesson():
    """Create new lesson"""

    # Get inputs from form
    og_lesson_id = int(request.form.get("lesson_id"))
    lesson_date_str = request.form.get("date")
    start_time_str = request.form.get("start_time")
    duration = int(request.form.get("duration"))
    classroom = request.form.get("classroom").strip()

    # Adjust variables types
    lesson_date = datetime.strptime(lesson_date_str, "%Y-%m-%d").date()
    start_time = datetime.strptime(start_time_str, '%H:%M').time()

    # Get missing values
    class_id = db.session.query(Lessons.class_id).filter(Lessons.lesson_id == og_lesson_id).scalar()
    teacher_id = db.session.query(Lessons.teacher_id).filter(Lessons.lesson_id == og_lesson_id).scalar()
 
    #Create new compensation lesson
    comp_lesson = Lessons(
        class_id = class_id,
        lesson_date = lesson_date,
        hour = start_time,
        duration = duration,
        teacher_id = teacher_id,
        classroom = classroom,
        is_compensation = "true",
        compensation_id = og_lesson_id
    )

    og_lesson = db.session.query(Lessons).filter(Lessons.lesson_id == og_lesson_id).one_or_none()
    
    if og_lesson:

        db.session.add(comp_lesson)

        # Add students
        for student in og_lesson.students:
            comp_lesson.students.append(student)

        db.session.commit()

        added_lesson = db.session.query(Lessons).filter(Lessons.compensation_id == og_lesson_id).one_or_none()

        if added_lesson:

            og_lesson.compensation_id = added_lesson.lesson_id
            og_lesson.is_compensation = "false"

            db.session.commit()

            print("New compensation lesson was added to db")
        else:
            print("Compensation lesson not found")

    else:
        print("Original lesson not found")

    return redirect("/lessons")



@app.route("/edit_lesson", methods=["POST"])   
def edit_lesson():
    """Change lesson data"""

    lesson_data = request.get_json()

    class_id = lesson_data["classId"]
    lesson_id = lesson_data["lessonId"]
    lesson_date_str = lesson_data["lessonDate"].strip()
    new_time_str = lesson_data["startTime"].strip()
    new_teacher = lesson_data["teacher"].strip()
    new_students = lesson_data["students"]
    new_duration = lesson_data["duration"]
    new_classroom = lesson_data["classroom"]
    comp_check = lesson_data["isCompensation"]
    date_format = lesson_data["dateFormat"].strip()

    # Adjust variable types
    new_teacher_id = db.session.query(Users.id).filter(Users.name == new_teacher).scalar()
    new_time = datetime.strptime(new_time_str, '%H:%M').time()

    """OLD WAY
    if date_format == "dd-mm-yyyy":
        print("date format: ", date_format)
        parsed_date = parser.parse(lesson_date_str, dayfirst=True)
    else:
        print("Date format: ", date_format)
        parsed_date = parser.parse(lesson_date_str)

    lesson_date = parsed_date.date()

    print("Lesson date str:", lesson_date_str)
    print("Parsed date:", parsed_date)
    print("Lesson date:", lesson_date, "Type: ", type(lesson_date))"""

    # NEW WAY
    print("Lesson_date_str: ", lesson_date_str)
    lesson_date = datetime.strptime(lesson_date_str, "%Y-%m-%d").date()
    print("Lesson_date: ", lesson_date)

    # Lesson is compensation
    if comp_check == "true":

        # Get original lesson
        og_lesson = db.session.query(Lessons).filter(Lessons.compensation_id == lesson_id).one_or_none()

        if og_lesson:

            comp_lesson = db.session.query(Lessons).filter(Lessons.lesson_id == lesson_id).one_or_none()

            if comp_lesson:
                # Edit existing compensation lesson
                comp_lesson.class_id = class_id
                comp_lesson.lesson_date = lesson_date
                comp_lesson.hour = new_time
                comp_lesson.duration = new_duration
                comp_lesson.teacher_id = new_teacher_id
                comp_lesson.classroom = new_classroom

                if new_students:
                    # Delete previous students data
                    comp_lesson.students.clear()
                    # Add new students
                    for name in new_students:
                        new_student = db.session.query(Students).join(Users).filter(Users.name == name).one_or_none()
                        comp_lesson.students.append(new_student)

                db.session.commit()
                return jsonify({"status": "success"})
            
            else:
                return jsonify({"status": "error", "message": "Comp_check=true but Compensation lesson not found."})
               
        else:
            return jsonify({"status": "error", "message": "Comp_check=true but Original lesson not found."})
        
    # Lesson is not compensation      
    else:
        
        lesson = db.session.query(Lessons).filter(Lessons.lesson_id == lesson_id).one_or_none()

        if lesson:
            # Edit lesson data
            lesson.hour = new_time
            lesson.duration = new_duration
            lesson.teacher_id = new_teacher_id
            lesson.classroom = new_classroom

            if new_students:
                # Delete previous students data
                lesson.students.clear()
                # Add students that attended
                for name in new_students:
                    new_student = db.session.query(Students).join(Users).filter(Users.name == name).one_or_none()
                    lesson.students.append(new_student)

            db.session.commit()
            return jsonify({"status": "success"})
        
        else:
           return jsonify({"status": "error", "message": "No lesson found. Editing failed."})



@app.route("/lesson_attendance", methods=["POST"])
def lesson_attendance():
    """Change lesson attendance"""

    data = request.get_json()
    lesson_id = data.get('lessonId')
    attendance = data.get('attendance')

    lesson = db.session.query(Lessons).filter(Lessons.lesson_id == lesson_id).one_or_none()

    if lesson:
        if attendance == "true" and lesson.attendance != "true":
            lesson.attendance = "true"
        elif attendance == "false" and lesson.attendance != "false":
            lesson.attendance = "false"
        else:
            lesson.attendance = None
    
        db.session.commit()
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Lesson not found"})


@app.route("/delete_lesson", methods=["POST"])
def delete_lesson():
    """Delete lesson"""

    data = request.get_json()
    lesson_id = data.get('lessonId')

    if lesson_id:
        lesson = db.session.query(Lessons).filter(Lessons.lesson_id == lesson_id).one_or_none()

        if lesson:
            # Delete lesson
            db.session.delete(lesson)

            # Commit changes and redirect
            db.session.commit()
            return jsonify({"status": "success"})

        else:
            return jsonify({"status": "error", "message": "Lesson not found"})
    else:
        return jsonify({"status": "error", "message": "lesson_id not found"})


@app.route("/teachers", methods=["GET", "POST"])
def teachers():
    """ Display list of teachers """

    user = db.session.query(Users).filter(Users.id == session["user_id"]).one_or_none()
    teachers_data = []

    if request.method == "GET":
        
        teachers = db.session.query(Teachers).join(Users).filter(Teachers.active == True).order_by(Users.name).all()

        if teachers:
            for item in teachers:
                contacts = []

                email = db.session.query(Users.email).filter(Users.id==item.teacher_id).scalar()
                phone = db.session.query(Users.phone).filter(Users.id==item.teacher_id).scalar()
             
                if email:
                    contacts.append(email)
                if phone:
                    contacts.append(phone)

                data = {
                    'teacher': item,
                    'contacts': contacts
                }

                teachers_data.append(data)
        
            return render_template("teachers.html", user=user, teachers_data=teachers_data)
        else:
            return render_template("teachers.html", user=user, teachers_data=None)
    else:
        return render_template("teachers.html", user=user, teachers_data=None)


@app.route("/new_teacher", methods=["POST"])
def new_teacher():
    """ Add new teacher """

    # users table inputs
    name = request.form.get("name")
    age = request.form.get("age")
    phone = request.form.get("phone")
    email = request.form.get("email")

    # teachers table inputs
    inst = request.form.get("instrument")
    current_salary = request.form.get("salary")

    # Create new Users instance
    new_user = Users(
        name = name,
        age = age,
        phone = phone,
        email = email,
        role = "teacher",
        is_registered = False
    )

    # Add to database
    db.session.add(new_user)
    db.session.commit()
    
    # Create new Teachers instance
    new_teacher = Teachers(
        teacher_id = new_user.id,
        instrument = inst,
        current_salary = current_salary,
        active = True
    )
        
    db.session.add(new_teacher)
    db.session.commit()

    # Get first salary date
    today = datetime.today().date()
    month = today.month
    year = today.year
    salary_date = datetime(year, month, 1)

    # Create new Salaries instance
    new_salary = Salaries(
        teacher_id = new_user.id,
        salary_date = salary_date,
        salary_value = current_salary,
        is_payed = False,
        payment_date = None
    )
    # Add and associate salary with teacher
    db.session.add(new_salary)
    new_teacher.salaries.append(new_salary) 

    db.session.commit()

    return redirect("/teachers")


@app.route("/change_teacher", methods=["POST"])
def change_teacher():
    """ Change teacher info """

    teacher_data = request.get_json()

    teacher_id = teacher_data["id"]
    new_name = teacher_data["name"].strip()
    new_age = teacher_data["age"]
    new_email = teacher_data["email"].strip()
    new_phone = teacher_data["phone"]
    new_inst = teacher_data["instrument"].strip()
    new_salary = teacher_data["salary"].strip()

    # Get original teacher
    users_table = db.session.query(Users).filter(Users.id == teacher_id).one_or_none()
    teachers_table = db.session.query(Teachers).filter(Teachers.teacher_id == teacher_id).one_or_none()

    if users_table and teachers_table:
        # Update Users table
        users_table.name = new_name
        users_table.age = new_age
        users_table.phone = new_phone
        users_table.email = new_email

        # Update Students table
        teachers_table.instrument = new_inst
        teachers_table.current_salary = new_salary

        db.session.commit()

    else:
        print("There was an error quering the edited teacher")

    teachers_url = url_for("teachers") 
    return jsonify({"redirect": teachers_url})


@app.route("/delete_teacher", methods=["POST"])
def delete_teacher():
    """Delete teacher"""
    #TODO: Adjust function to teacher

    data = request.get_json()
    student_id = data.get('studentId')
    today = datetime.today().date()

    if student_id:
        student = db.session.query(Students).filter(Students.student_id == student_id).one_or_none()

        if student:
            schedules_to_remove = []
            lessons_to_remove = []

            for schedule in student.schedules:
                # If schedule is group class
                if len(schedule.students) > 1:
                    # Don't remove directly to not skip iterations
                    schedules_to_remove.append(schedule)
                # If schedule is individual class
                else:
                    schedule.active = False

            # Remove student from group schedules
            for item in schedules_to_remove:
                student.schedules.remove(item)

            for lesson in student.lessons:
                # If lesson is from group class
                if len(lesson.students) > 1:
                    if lesson.lesson_date > today:
                        # Don't remove directly to not skip iterations
                        lessons_to_remove.append(lesson)
                # If lesson is from individual class
                else:
                    if lesson.lesson_date > today:
                        db.session.delete(lesson)
                        
            # Remove student from lessons
            for item in lessons_to_remove:
                student.lessons.remove(item)

            # Delete future tuitions
            for tuition in student.tuitions:
                if tuition.tuition_date > today:
                    db.session.delete(tuition)

            student.active = False

            # Commit changes and redirect
            db.session.commit()

            students_url = url_for("students") 
            return jsonify({"redirect": students_url})
        else:
            print("There was an error deleting teacher")
    else:
        print("There was an error getting teacher_id from JSON")


@app.route("/students", methods=["GET", "POST"])
def students():
    """ Display list of students """

    user = db.session.query(Users).filter(Users.id == session["user_id"]).one_or_none()
    students_data = []

    if request.method == "GET":
        
        students = db.session.query(Students).join(Users).filter(Students.active == True).order_by(Users.name).all()
        teacher_names = db.session.query(Users.name).filter(Users.role == "teacher").order_by(Users.name).all()

        if students:
            for item in students:
                teacher_name = db.session.query(Users.name).filter(Users.id == item.teacher_id).scalar()
                contacts = []

                email = db.session.query(Users.email).filter(Users.id==item.student_id).scalar()
                phone = db.session.query(Users.phone).filter(Users.id==item.student_id).scalar()
             
                if email:
                    contacts.append(email)
                if phone:
                    contacts.append(phone)

                data = {
                    'student': item,
                    'teacher': teacher_name,
                    'contacts': contacts,
                }

                students_data.append(data)
        
            return render_template("students.html", user=user, students_data=students_data, teacher_names=teacher_names)
        
        else:
            return render_template("students.html", user=user, students_data=None)
    else:
        return render_template("students.html", user=user, students_data=None)
    

@app.route("/new_student", methods=["POST"])
def new_student():
    """ Add new student """

    # users table inputs
    name = request.form.get("name")
    age = request.form.get("age")
    phone = request.form.get("phone")
    email = request.form.get("email")
    enroll = request.form.get("enrollment")
    enroll_date = datetime.strptime(enroll, "%Y-%m-%d").date()

    # students table inputs
    course = request.form.get("course")
    inst = request.form.get("instrument")
    teacher_name = request.form.get("teacher")
    fee = request.form.get("monthly_fee")
    teacher_id = db.session.query(Users.id).filter(Users.name == teacher_name).scalar()

    # Create new Users instance
    new_user = Users(
        name = name,
        age = age,
        phone = phone,
        email = email,
        enrollment = enroll_date,
        role = "student",
        is_registered = False
    )

    # Add to database
    db.session.add(new_user)
    db.session.commit()

    new_student = Students(
        student_id = new_user.id,
        course = course,
        instrument = inst,
        teacher_id = teacher_id,
        monthly_fee = fee,
        active = True
    )
    
    db.session.add(new_student)
    db.session.commit()

    student_id = new_user.id
    first_tuition = enroll_date
    add_tuitions(db, Tuitions, Students, student_id, fee, first_tuition, year_finish)

    return redirect("/students")


@app.route("/change_student", methods=["POST"])
def change_student():
    """ Change student info """

    student_data = request.get_json()

    student_id = student_data["id"]
    new_name = student_data["name"].strip()
    new_age = student_data["age"]
    new_email = student_data["email"].strip()
    new_phone = student_data["phone"]
    new_course = student_data["course"]
    new_fee = student_data["fee"]
    new_inst = student_data["instrument"].strip()
    new_teacher_name = student_data["teacher"].strip()
    new_enroll = student_data["enrollment"].strip()

    # Adjust variable types
    new_teacher_id = db.session.query(Users.id).filter(Users.name == new_teacher_name).scalar()
    new_enroll_date = None

    if new_enroll != "None":
        new_enroll_date = datetime.strptime(new_enroll, "%Y-%m-%d").date()

    # Get original student
    users_table = db.session.query(Users).filter(Users.id == student_id).one_or_none()
    students_table = db.session.query(Students).filter(Students.student_id == student_id).one_or_none()

    if users_table and students_table:
        # Update Users table
        users_table.name = new_name
        users_table.age = new_age
        users_table.phone = new_phone
        users_table.email = new_email
        if new_enroll_date:
            users_table.enrollment = new_enroll_date

        # Update Students table
        students_table.course = new_course
        students_table.instrument = new_inst
        students_table.teacher_id = new_teacher_id
        students_table.monthly_fee = new_fee

        db.session.commit()

    else:
        print("There was an error quering the edited student")

    students_url = url_for("students") 
    return jsonify({"redirect": students_url})


@app.route("/delete_student", methods=["POST"])
def delete_student():
    """Delete student"""

    data = request.get_json()
    student_id = data.get('studentId')
    today = datetime.today().date()

    if student_id:
        student = db.session.query(Students).filter(Students.student_id == student_id).one_or_none()

        if student:
            schedules_to_remove = []
            lessons_to_remove = []

            for schedule in student.schedules:
                # If schedule is group class
                if len(schedule.students) > 1:
                    # Don't remove directly to not skip iterations
                    schedules_to_remove.append(schedule)
                # If schedule is individual class
                else:
                    schedule.active = False

            # Remove student from group schedules
            for item in schedules_to_remove:
                student.schedules.remove(item)

            for lesson in student.lessons:
                # If lesson is from group class
                if len(lesson.students) > 1:
                    if lesson.lesson_date > today:
                        # Don't remove directly to not skip iterations
                        lessons_to_remove.append(lesson)
                # If lesson is from individual class
                else:
                    if lesson.lesson_date > today:
                        db.session.delete(lesson)
                        
            # Remove student from lessons
            for item in lessons_to_remove:
                student.lessons.remove(item)

            # Delete future tuitions
            for tuition in student.tuitions:
                if tuition.tuition_date > today:
                    db.session.delete(tuition)

            student.active = False

            # Commit changes and redirect
            db.session.commit()

            students_url = url_for("students") 
            return jsonify({"redirect": students_url})
        else:
            print("There was an error deleting student")
    else:
        print("There was an error getting student_id from JSON")


@app.route("/tuitions", methods=["GET", "POST"])
def tuitions():
    """ Display tuitions """

    user = db.session.query(Users).filter(Users.id == session["user_id"]).one_or_none()

    tuitions_data = []
    
    
    if request.method == "GET":
        
        if user.role == "admin":
            tuitions = db.session.query(Tuitions).join(Users, Tuitions.student_id == Users.id).filter(Tuitions.tuition_date >= begin_date).order_by(Tuitions.tuition_date, Users.name).all()
            students_names = db.session.query(Users.name).filter(Users.role == "student").order_by(Users.name).all()
            
            if tuitions:
                for item in tuitions:
                    student_name = db.session.query(Users.name).filter(Users.id == item.student_id).scalar()

                    data = {
                        'tuition': item,
                        'student': student_name
                    }

                    tuitions_data.append(data)
            
                return render_template("tuitions.html", user=user, tuitions_data=tuitions_data, students_names=students_names)
            else:
                return render_template("tuitions.html", user=user, tuitions_data=None)
        
        elif user.role == "student":
            tuitions = db.session.query(Tuitions).join(student_tuitions).filter(and_(Tuitions.tuition_date >= begin_date, student_tuitions.c.student_id == user.id)).order_by(Tuitions.tuition_date).all()
            
            if tuitions:
                for item in tuitions:
                    tuitions_data.append(item)
                return render_template("tuitions.html", user=user, tuitions_data=tuitions_data)  
            else:
                return render_template("tuitions.html", user=user, tuitions_data=None)
        
        else:
            return render_template("tuitions.html", user=user, tuitions_data=None)
    
    elif request.method == "POST":

        student_name = request.form.get("student")
        month_str = request.form.get("month")

        if student_name:

            student_id = db.session.query(Users.id).filter(Users.name == student_name).scalar()
            tuitions = db.session.query(Tuitions).filter(Tuitions.student_id == student_id).all()

            for item in tuitions:

                data = {
                    'tuition': item,
                    'student': student_name
                }

                tuitions_data.append(data)
            
            students_names = db.session.query(Users.name).filter(Users.role == "student").order_by(Users.name).all()
            return render_template("tuitions.html", user=user, tuitions_data=tuitions_data, students_names=students_names)
        
        elif month_str:

            month=int(month_str)
            
            print("month:", month)
            
            if month >= 9:
                # Get Global scope variable
                year = year_begin 

                # monthrange function returns a tuple (first_day_weekday, number_of_days)
                last_day = calendar.monthrange(year, month)[1] # returns just the number of days
                start_date = datetime(year, month, 1).date()
                end_date = datetime(2024, month, last_day).date()

                print("Start_date:", start_date)
                print("End_date:", end_date)
            else: 
                # Get Global scope variable
                year = year_finish

                last_day = calendar.monthrange(year, month)[1]
                start_date = datetime(year, month, 1).date()
                end_date = datetime(year, month, last_day).date()

                print("Start_date:", start_date)
                print("End_date:", end_date)

            if user.role == "admin":
                tuitions = db.session.query(Tuitions).filter(and_(Tuitions.tuition_date >= start_date, Tuitions.tuition_date <= end_date)).all()
                students_names = db.session.query(Users.name).filter(Users.role == "student").order_by(Users.name).all()

                for item in tuitions:
                    student = db.session.query(Users.name).filter(Users.id == item.student_id).scalar()

                    data = {
                        'tuition': item,
                        'student': student
                    }

                    tuitions_data.append(data)
                    
                students_names = db.session.query(Users.name).filter(Users.role == "student").order_by(Users.name).all()
                return render_template("tuitions.html", user=user, tuitions_data=tuitions_data, students_names=students_names)
            
            elif user.role == "student":
                tuitions = db.session.query(Tuitions).filter(and_(Tuitions.tuition_date >= start_date, Tuitions.tuition_date <= end_date, Tuitions.student_id == user.id)).all()

                for item in tuitions:
                    tuitions_data.append(item)

                return render_template("tuitions.html", user=user, tuitions_data=tuitions_data)
                


@app.route("/change_tuition", methods=["POST"])
def change_tuition():
    """ Change tuition info """

    tuition_data = request.get_json()

    if tuition_data:

        tuition_id = tuition_data["id"]
        new_fee = tuition_data["fee"]
        payment = tuition_data["payment"]
        is_payed = tuition_data["isPayed"].strip()
        print("is_payed str:", is_payed)

        # Adjust variable types
        new_payment_date = None
        is_payed_bool = None
        
        if payment:
            payment=payment.strip()
            new_payment_date = datetime.strptime(payment, "%Y-%m-%d").date()

        if is_payed == "True":
            is_payed_bool = True
        else:
            is_payed_bool = None
        print("is_payed_bool:", is_payed_bool)

        # Get tuition instance
        tuition = db.session.query(Tuitions).filter(Tuitions.tuition_id == tuition_id).scalar()

        if tuition:
            # Update Tuition table
            tuition.tuition_value = new_fee
            tuition.is_payed = is_payed_bool

            if new_payment_date:
                tuition.payment_date = new_payment_date

            db.session.commit()
            return jsonify({"status": "success"})

        else:
            return jsonify({"status": "error", "message": "Original tuition not found"})
    else:
        return jsonify({"status": "error", "message": "Tuition Id not returned by JSON"})
    

@app.route("/new_tuition", methods=["POST"])
def new_tuition():
    """ Add new tuition """

    # Get inputs
    month = int(request.form.get("month"))
    student_name = request.form.get("student")
    fee = request.form.get("fee")
    payment_str = request.form.get("payment")   
    is_payed = None
    payment_date = None

    if payment_str:
        payment_date = datetime.strptime(payment_str, "%Y-%m-%d").date()
        is_payed = True

    # Get student id
    student_id = db.session.query(Users.id).filter(Users.name == student_name).scalar()

    # Get tuition_date
    if month >= 9:
        year = year_begin
        tuition_date = datetime(year, month, 1).date()
    else:
        year = year_finish
        tuition_date = datetime(year, month, 1).date()

    # Create new Tuitions instance
    new_tuition = Tuitions(
        student_id = student_id,
        tuition_date = tuition_date,
        tuition_value = fee,
        is_payed = is_payed,
        payment_date = payment_date
    )

    # Add to database
    db.session.add(new_tuition)
    db.session.commit()

    return redirect("/tuitions")


@app.route("/delete_finance", methods=["POST"])
def delete_finance():
    """Delete tuition or salary """

    data = request.get_json()
    money_doc = data.get('moneyDoc')

    if money_doc == "tuition":
        tuition_id = data.get('tuitionId')

        if tuition_id:
            tuition = db.session.query(Tuitions).filter(Tuitions.tuition_id == tuition_id).one_or_none()

            if tuition:
                db.session.delete(tuition)

                # Commit changes and redirect
                db.session.commit()

                tuitions_url = url_for("tuitions") 
                return jsonify({"redirect": tuitions_url})
            else:
                print("There was an error deleting tuition")
        else:
            print("There was an error getting tuition_id from JSON")
    
    elif money_doc == "salary":
        salary_id = data.get('salaryId')

        if salary_id:
            salary = db.session.query(Salaries).filter(Salaries.salary_id == salary_id).one_or_none()
            
            if salary:
                db.session.delete(salary)

                # Commit changes and redirect
                db.session.commit()

                salaries_url = url_for("salaries") 
                return jsonify({"redirect": salaries_url})
            else:
                print("There was an error deleting salary")
        else:
            print("There was an error getting salary_id from JSON")
    else:
        print("There was an error getting money doc from JSON")


@app.route("/confirm_payment", methods=["POST"])
def confirm_payment():
    """ Confirm payment and date """

    data = request.get_json()

    money_doc = data.get('moneyDoc')

    if money_doc == "tuition":

        tuition_id = data.get('tuitionId')
        payment_date_str = data.get('paymentDate').strip()
        payment_date = datetime.strptime(payment_date_str,"%Y-%m-%d").date()

        tuition = db.session.query(Tuitions).filter(Tuitions.tuition_id == tuition_id).one_or_none()

        if tuition:
            tuition.is_payed = True
            tuition.payment_date = payment_date

            db.session.commit()
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Original tuition not found"})
    
    elif money_doc == "salary":
        salary_id = data.get('salaryId')
        payment_date_str = data.get('paymentDate').strip()
        payment_date = datetime.strptime(payment_date_str,"%Y-%m-%d").date()

        salary = db.session.query(Salaries).filter(Salaries.salary_id == salary_id).one_or_none()

        if salary:
            salary.is_payed = True
            salary.payment_date = payment_date

            db.session.commit()
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Original salary not found"})

    else:
        return jsonify({"status": "error", "message": "Money Doc not found"})


@app.route("/remove_payment", methods=["POST"])
def remove_payment():
    """ Remove payment and date """

    data = request.get_json()

    money_doc = data.get('moneyDoc')

    if money_doc == "tuition":

        tuition_id = data.get('tuitionId')        
        tuition = db.session.query(Tuitions).filter(Tuitions.tuition_id == tuition_id).one_or_none()

        if tuition:
            tuition.is_payed = False
            tuition.payment_date = None

            db.session.commit()
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Original tuition not found"})
    
    elif money_doc == "salary":

        salary_id = data.get('salaryId')
        salary = db.session.query(Salaries).filter(Salaries.salary_id == salary_id).one_or_none()
        
        if salary:
            salary.is_payed = False
            salary.payment_date = None

            db.session.commit()
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Original salary not found"})
    
    else:
        return jsonify({"status": "error", "message": "Money Doc not found"})


@app.route("/salaries", methods=["GET", "POST"])
def salaries():
    """ Display salaries """

    user = db.session.query(Users).filter(Users.id == session["user_id"]).one_or_none()
    year_start_str = "2024-09-01"
    year_start = datetime.strptime(year_start_str, "%Y-%m-%d").date()
    salaries_data = []
    teachers_names = db.session.query(Users.name).filter(Users.role == "teacher").order_by(Users.name).all()
    
    if request.method == "GET":

        if user.role == "admin":
        
            salaries = db.session.query(Salaries).join(Users, Salaries.teacher_id == Users.id).filter(Salaries.salary_date >= year_start).order_by(Salaries.salary_date, Users.name).all()

            if salaries:
                for item in salaries:
                    teacher_name = db.session.query(Users.name).filter(Users.id == item.teacher_id).scalar()

                    data = {
                        'salary': item,
                        'teacher': teacher_name
                    }

                    salaries_data.append(data)
            
                return render_template("salaries.html", user=user, salaries_data=salaries_data, teachers_names=teachers_names)
            
            else:
                return render_template("salaries.html", user=user, salaries_data=None)
            
        elif user.role == "teacher":
            salaries = db.session.query(Salaries).filter(and_(Salaries.teacher_id == user.id, Salaries.salary_date >= year_start)).order_by(Salaries.salary_date).all()

            if salaries:
                for item in salaries:

                    salaries_data.append(item)

                return render_template("salaries.html", user=user, salaries_data=salaries_data)
            
            else:
                return render_template("salaries.html", user=user, salaries_data=None)


    elif request.method == "POST":

        teacher_name = request.form.get("teacher")
        month_str = request.form.get("month")

        if teacher_name:

            print("teacher_name:", teacher_name)
            teacher_id = db.session.query(Users.id).filter(Users.name == teacher_name).scalar()
            salaries = db.session.query(Salaries).filter(Salaries.teacher_id == teacher_id).order_by(Salaries.salary_date).all()

            for item in salaries:

                data = {
                    'salary': item,
                    'teacher': teacher_name
                }

                salaries_data.append(data)
            
            return render_template("salaries.html", user=user, salaries_data=salaries_data, teachers_names=teachers_names)
        
        elif month_str:

            month=int(month_str)
            
            print("month:", month)
            
            if month >= 9:
                # Get Global scope variable
                year = year_begin 

                # monthrange function returns a tuple (first_day_weekday, number_of_days)
                last_day = calendar.monthrange(year, month)[1] # returns just the number of days
                start_date = datetime(year, month, 1).date()
                end_date = datetime(2024, month, last_day).date()

                print("Start_date:", start_date)
                print("End_date:", end_date)
            else: 
                # Get Global scope variable
                year = year_finish

                last_day = calendar.monthrange(year, month)[1]
                start_date = datetime(year, month, 1).date()
                end_date = datetime(year, month, last_day).date()

                print("Start_date:", start_date)
                print("End_date:", end_date)

            salaries = db.session.query(Salaries).join(Users, Salaries.teacher_id == Users.id).filter(and_(Salaries.salary_date >= start_date, Salaries.salary_date <= end_date)).order_by(Salaries.salary_date, Users.name).all()

            for item in salaries:
                teacher = db.session.query(Users.name).filter(Users.id == item.teacher_id).scalar()

                data = {
                    'salary': item,
                    'teacher': teacher
                }

                salaries_data.append(data)

            return render_template("salaries.html", user=user, salaries_data=salaries_data, teachers_names=teachers_names)


@app.route("/change_salary", methods=["POST"])
def change_salary():
    """ Change salary info """

    salary_data = request.get_json()

    if salary_data:

        salary_id = salary_data["id"]
        value = salary_data["salary"]
        payment = salary_data["payment"]
        is_payed = salary_data["isPayed"].strip()
        print("is_payed str:", is_payed)

        # Adjust variable types
        new_payment_date = None
        is_payed_bool = None
        
        if payment:
            payment=payment.strip()
            new_payment_date = datetime.strptime(payment, "%Y-%m-%d").date()

        if is_payed == "True":
            is_payed_bool = True
        else:
            is_payed_bool = None
        print("is_payed_bool:", is_payed_bool)

        # Get salary instance
        salary = db.session.query(Salaries).filter(Salaries.salary_id == salary_id).scalar()

        if salary:
            # Update Salaries table
            salary.salary_value = value
            salary.is_payed = is_payed_bool

            if new_payment_date:
                salary.payment_date = new_payment_date

            db.session.commit()
            return jsonify({"status": "success"})

        else:
            return jsonify({"status": "error", "message": "Original salary not found"})
    else:
        return jsonify({"status": "error", "message": "Salary Id not returned by JSON"})
    

@app.route("/new_salary", methods=["POST"])
def new_salary():
    """ Add new salary """

    # Get inputs
    month = int(request.form.get("month"))
    teacher_name = request.form.get("teacher")
    value = request.form.get("salary")
    payment_str = request.form.get("payment")   
    is_payed = None
    payment_date = None

    if payment_str:
        payment_date = datetime.strptime(payment_str, "%Y-%m-%d").date()
        is_payed = True

    # Get student id
    teacher_id = db.session.query(Users.id).filter(Users.name == teacher_name).scalar()

    # Get salary_date
    if month >= 9:
        year = year_begin
        salary_date = datetime(year, month, 1).date()
    else:
        year = year_finish
        salary_date = datetime(year, month, 1).date()

    # Create new Salaries instance
    new_salary = Salaries(
        teacher_id = teacher_id,
        salary_date = salary_date,
        salary_value = value,
        is_payed = is_payed,
        payment_date = payment_date
    )

    # Add to database
    db.session.add(new_salary)
    db.session.commit()

    return redirect("/salaries")