from flask import redirect, session
from functools import wraps
from datetime import datetime, date
from dateutil.rrule import rrule, DAILY, MONTHLY
from sqlalchemy import and_, desc, asc
import calendar

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def all_schedules_info(Schedules, Users, db):

    all_schedules = db.session.query(Schedules).order_by(desc(Schedules.school_year),asc(Schedules.weekday), asc(Schedules.hour)).all()
    schedules=[]

    for item in all_schedules:
        if item.school_year == 2324:
            school_year_str = "2023/2024"
        else:
            school_year_str = "2024/2025"

        day_name = calendar.day_name[item.weekday]
        teacher = db.session.query(Users.name).filter(Users.id == item.teacher_id).scalar()
        item.hour_formatted = item.hour.strftime('%H:%M')

        students_names = []

        for student in item.students:
            student_name = student.user.name
            students_names.append(student_name)

        schedule_data = {
            'schedule': item,
            'school_year': school_year_str,
            'teacher': teacher,
            'weekday': day_name,
            'students': students_names
        }

        schedules.append(schedule_data)
    
    return schedules


def teacher_schedules_info(Schedules, db, user_id):

    teacher_schedules = db.session.query(Schedules).filter(Schedules.teacher_id == user_id).order_by(desc(Schedules.school_year),asc(Schedules.weekday), asc(Schedules.hour)).all()
    schedules=[]

    for item in teacher_schedules:
        if item.school_year == 2324:
            school_year_str = "2023/2024"
        else:
            school_year_str = "2024/2025"

        day_name = calendar.day_name[item.weekday]
        item.hour_formatted = item.hour.strftime('%H:%M')

        students_names = []

        for student in item.students:
            student_name = student.user.name
            students_names.append(student_name)

        schedule_data = {
            'schedule': item,
            'school_year': school_year_str,
            'weekday': day_name,
            'students': students_names
        }

        schedules.append(schedule_data)
    
    return schedules


def student_schedules_info(Schedules, Users, students_schedules, db, user_id):

    student_schedules = db.session.query(Schedules).join(students_schedules).filter(students_schedules.c.students_id == user_id).order_by(desc(Schedules.school_year), asc(Schedules.weekday), asc(Schedules.hour)).all()
    schedules=[]

    for item in student_schedules:
        if item.school_year == 2324:
            school_year_str = "2023/2024"
        else:
            school_year_str = "2024/2025"

        day_name = calendar.day_name[item.weekday]
        item.hour_formatted = item.hour.strftime('%H:%M')
        teacher_name = db.session.query(Users.name).filter(Users.id == item.teacher_id).scalar()

        students_names = []

        for student in item.students:
            student_name = student.user.name
            students_names.append(student_name)

        schedule_data = {
            'schedule': item,
            'school_year': school_year_str,
            'weekday': day_name,
            'teacher': teacher_name,
            'students': students_names
        }

        schedules.append(schedule_data)
    
    return schedules


def populate_tuitions_2425(Students, Tuitions, db):
    """ Add tuitions to Tuitions model """
    
    # Check if tuitions already exist
    if not Tuitions.query.first():

        # Generate months list
        start_date = datetime(2024, 9, 1)
        end_date = datetime(2025, 7, 1)
        months = rrule(freq=MONTHLY, dtstart=start_date, until=end_date)

        for date in months:

            students = db.session.query(Students).filter(Students.active == True).all()

            for student in students:

                # Add new tuition to Tuitions model
                tuition = Tuitions(
                    student_id = student.student_id,
                    tuition_date = date,
                    tuition_value = student.monthly_fee
                )

                db.session.add(tuition)

                # Add tuition to student_tuitions associate table
                student.tuitions.append(tuition) 

        db.session.commit()
        print("Tuitions successfully added.")
    else:
        print("No tuitions were added. Entries already exist.")


def populate_salaries_2425(Teachers, Salaries, db):
    """ Add tuitions to Tuitions model """
    
    # Check if tuitions already exist
    if not Salaries.query.first():

        # Generate months list
        start_date = datetime(2024, 9, 28)
        end_date = datetime(2025, 7, 28)
        months = rrule(freq=MONTHLY, dtstart=start_date, until=end_date)

        for date in months:

            teachers = db.session.query(Teachers).filter(Teachers.active == True).all()

            for teacher in teachers:

                # Add new tuition to Tuitions model
                salary = Salaries(
                    teacher_id = teacher.teacher_id,
                    salary_date = date,
                    salary_value = teacher.current_salary
                )

                db.session.add(salary)

                # Add tuition to student_tuitions associate table
                teacher.salaries.append(salary) 

        db.session.commit()
        print("Salaries successfully added.")
    else:
        print("No salaries were added. Entries already exist.")


def populate_lessons_2324(Schedules, Lessons, Students, students_schedules, lesson_students, db):
    """ Add lessons to Lessons model """
    
    if not Lessons.query.first():

        start_date = datetime(2023, 9, 1)
        end_date = datetime(2024, 7, 31)
        school_year = rrule(freq=DAILY, dtstart=start_date, until=end_date)

        for date in school_year:
            weekday = date.weekday()

            schedule_info = db.session.query(Schedules).filter(Schedules.weekday == weekday).all()

            if schedule_info:
                for item in schedule_info:
                    # Create new lesson in Lessons Model
                    lesson = Lessons(
                        class_id = item.class_id,
                        lesson_date = date,
                        hour = item.hour,
                        duration = item.duration,
                        teacher_id = item.teacher_id,
                        classroom = item.classroom
                    )
                    db.session.add(lesson)

        db.session.commit()

    """ Add students to each lesson """

    if not db.session.query(lesson_students).first():
        lessons = Lessons.query.all()

        for item in lessons:
            
            # Check there aren't already students assigned 
            if not item.students:
                # Get all students in that class (schedule)
                students = db.session.query(Students).join(students_schedules).filter(students_schedules.c.schedule_id == item.class_id).all()
  
                # Add each student to the same lesson
                for student in students:
                    item.students.append(student)  

        db.session.commit()

            
def populate_lessons_2425(Schedules, Lessons, Students, students_schedules, db):
    """ Add lessons to Lessons model """
    
    if not db.session.query(Lessons).filter(Lessons.lesson_date > datetime(2024, 8, 1)).all():

        start_date = datetime(2024, 9, 2)
        end_date = datetime(2025, 7, 31)
        school_year = rrule(freq=DAILY, dtstart=start_date, until=end_date)

        for date in school_year:
            weekday = date.weekday()

            schedule_info = db.session.query(Schedules).filter(and_(Schedules.weekday == weekday, Schedules.school_year == 2425)).all()

            if schedule_info:
                for item in schedule_info:
                    # Create new lesson in Lessons Model
                    lesson = Lessons(
                        class_id = item.class_id,
                        lesson_date = date,
                        hour = item.hour,
                        duration = item.duration,
                        teacher_id = item.teacher_id,
                        classroom = item.classroom
                    )
                    db.session.add(lesson)

        db.session.commit()

        
    """ Add students to each lesson """

    lessons = db.session.query(Lessons).filter(Lessons.lesson_date > datetime(2024, 8, 1)).all()

    if lessons:
    
        for item in lessons:

            # Check there aren't already students assigned 
            if not item.students:

                # Get all students in that class (schedule)
                students = db.session.query(Students).join(students_schedules).filter(students_schedules.c.schedule_id == item.class_id).all()

                # Add each student to the same lesson
                for student in students:
                    item.students.append(student)
            
        db.session.commit()
    
    else:
        print("No students were added")

def attendance_update(Lessons, db):
    """ Change past lessons' attendance to True """

    today = datetime.today().date()

    lessons = db.session.query(Lessons).filter(Lessons.lesson_date <= today).all()

    if lessons:
        print("Checkpoint before lessons iteration")
        for item in lessons:
            if item.attendance in ("", None):
                item.attendance = "true"
    else:
        print("No lessons found")
    
    db.session.commit()

def payment_update(Tuitions, db):
    """ Adjust is_payed Boolean """

    today = datetime.today().date()

    tuitions = db.session.query(Tuitions).filter(Tuitions.tuition_date <= today).all()

    for item in tuitions:
        if item.payment_date in ("", None):
            item.is_payed = False

    db.session.commit()


def adjust_lessons(schedule, Lessons, db, change_date):
    """ Adjust lessons in Lesson model after specific date """

    #start_date = datetime.strptime(change_date, "%Y-%m-%d")
    # Get correct lessons info
    class_id = schedule.class_id
    lessons = db.session.query(Lessons).filter(and_(Lessons.class_id == class_id, Lessons.lesson_date >= change_date)).all()
    
    if lessons:
        # Clear future lessons
        for item in lessons:
            debug = item.lesson_date
            print("Lesson date: ", debug)
            db.session.delete(item)


        db.session.commit()
    else:
        print("There are no lessons to clear")
        
    # Get rest of school year since changed_date
    end_date = datetime(2025, 7, 31)

    print("Start_date", change_date)
    print("End_date", end_date)
    school_year = rrule(freq=DAILY, dtstart=change_date, until=end_date)

    # Create new lesson data in Lessons model
    for date in school_year:
        weekday = date.weekday()

        if weekday == schedule.weekday:
            lesson = Lessons(
                class_id = schedule.class_id,
                lesson_date = date,
                hour = schedule.hour,
                duration = schedule.duration,
                teacher_id = schedule.teacher_id,
                classroom = schedule.classroom,
            )

            print("Lesson iteration: ", date)

            # Append students
            for student in schedule.students:
                lesson.students.append(student)
    
            db.session.add(lesson)
    
    db.session.commit()


def delete_lessons(class_id, Lessons, db, delete_date):
    """ Delete lessons record from specific schedule """
    
    # Get correct lessons info
    lessons = db.session.query(Lessons).filter(and_(Lessons.class_id == class_id, Lessons.lesson_date >= delete_date)).all()
    
    if lessons:
        # Delete from record
        print("Lessons delete iteration started")
        for item in lessons:
            db.session.delete(item)

        db.session.commit()
    else:
        print("There are no lessons to delete")


def add_tuitions(db, Tuitions, Students, student_id, fee, first_tuition, year_finish):
    """ Add tuitions after enrolling new student """

    # Generate months list
    first_month = first_tuition.month
    first_year = first_tuition.year
    start_date = datetime(first_year, first_month, 1)
    end_date = datetime(year_finish, 7, 1)
    months = rrule(freq=MONTHLY, dtstart=start_date, until=end_date)

    student = db.session.query(Students).filter(Students.student_id == student_id).scalar()

    for date in months:

        # Add new tuition to Tuitions model
        tuition = Tuitions(
            student_id = student_id,
            tuition_date = date,
            tuition_value = fee,
            is_payed = None,
            payment_date = None
        )

        db.session.add(tuition)

        # Add tuition to student_tuitions associate table
        student.tuitions.append(tuition) 

        payment_update(Tuitions, db)

    db.session.commit()
    print("Tuitions successfully added.")


def add_salaries(db, Salaries, Teachers, teacher_id, curr_salary, year_finish):
    """ Add salaries after creating new teacher """

    today=datetime.today().date()

    # Generate months list
    first_month = today.month
    first_year = today.year
    start_date = datetime(first_year, first_month, 1)
    end_date = datetime(year_finish, 7, 1)
    months = rrule(freq=MONTHLY, dtstart=start_date, until=end_date)

    teacher = db.session.query(Teachers).filter(Teachers.teacher_id == teacher_id).scalar()

    for date in months:

        # Add new salary to Salaries model
        salary = Salaries(
            teacher_id = teacher_id,
            salary_date = date,
            salary_value = curr_salary,
            is_payed = None,
            payment_date = None
        )

        db.session.add(salary)

        # Add salary to teacher_salaries associate table
        teacher.salaries.append(salary) 

    db.session.commit()
    print("Salaries successfully added.")

