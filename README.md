# INTERNAL MANAGEMENT APP
#### Video Demo: [watch here!](https://youtu.be/MA686kF8Ai8)

## Introduction

For my final project, I developed a web application that allows a school to manage its internal affairs. This idea was influenced by my personal experience with all the schools I worked with. 
At one school we had an app to manage our students, their lessons and all kinds of information, although it wasn't remotely user friendly. At my current school, we don't care to much for burocracies, but there are some minimal management necessities, like lesson attendances, that we do control. The problem here is we do it on **PAPER**.

This being said, my main objective was to develop a user-friendly app that allows all users - them being teachers, students or administrators - to easily access and manipulate important information.

This was the first obstacle I encountared. *What exactly is this important information?*

I ended up having to scope down the amount of features I would like to implement (at least for now!). Throughout the development process, I kept being haunted by the same thought over and over again - "*Oh, this would be useful*". I successfully ignored some of those thoughts, and I succumbed to others.

A special thanks to my dear helpers - ChatGPT and W3Schools- who served me a great deal throughout this whole adventure, but most essentially when I needed to center a div. 

## Files and languages

For this web app, I used Flask, a Python framework. On the Project folder we can find the app.py and helpers.py files, the templates folder where I hold every HTML file, the static folder where I saved every design-related file (logo, CSS stylesheet and fonts) and, finally, on the instance folder we can find the SQL database file. 

Initially I had integrated Bootstrap, but I ended up removing it completely and developed the design from scratch using only the CSS stylesheet (*style.css*), although using Boostrap icons svg code. 

On app.py, I integrated SQLAlchemy, which allowed me to generate different ORM Models and Association Tables in my database, and handle queries throughout the app. 
On my templates, I relied on Jinja to interpret data sent from Flask and handle some basic functionality with that same data. Through script tags, I relied on JavaScript and JSON to handle more complex functionality and to communicate back with Flask.

### Database Models and Association Tables

Database management was one of those points that kept being updated and modified until later stages of the development process. 
Because I kept thinking about new features that interfered directly with the database organization, I had to keep adding new tables. 

I ended up with the following Models:
- Users (general info between each type of user)
  - Teachers (relationship to Users)
  - Students (relationship to Users)
- Schedules (many-to-many rleationship with students)
- Lessons (many-to-many relationship with students)
- Salaries (many-to-many relationship with a teacher)
- Tuitions (many-to-many relationship with a student)

And these Association Tables to establish the many-to-many relationships:
- students_schedules
- lesson_students
- student_tuitions
- teacher_salaries

All Models have foreign keys to establish connections between them.

### Helper functions

On helpers.py, besides useful functions, like *all_schedules_info*, *adjust_lessons* and similar ones, that are called on more than one function from app.py, I have four "*populate*" functions that I used in earlier stages for testing purposes. At the moment, these functions serve no purpose as they are not even called/triggered.

## App usage and features

### Register and Login

The only people that are able to register and login at this app, are users that are already present in the database - either manually added by the developer (me) or later added by an admin from inside the app. 

Both register and login processes are made through the user ID, which is unique to each user and autoincrements at each new user that is created. So, in order to even **REGISTER**, the user already needs to have been given a unique ID. 
After this, at the register page (register.html), the user can now choose its password and confirm it, which is then encripted and saved in the database. The login page (login.html) is similar to the register page, although it doesn't have the confirmation input. 

Initially, just with bug testing and functionality in mind, I had general error handlers like "BadRequest" and "NotFound".
Later, for a more graphical error handling, I created login_error.html and register_error.html, both of which display error messages on the screen and/or redirects the user to the correct template. A feature I still want to implement in the future is the "I forgot my password" one, which would send an e-mail with a link to reset the user's password.

### Layout and Translations

On layout.html is where I established the general app layout, this being the head tags, the navbar (which includes the nav items and the user icon) and the footer.

On this template I also implemented the script logic in order to successfully translate the whole app content from english to portuguese and vice-versa. With some help from ChatGPT, in order to know what my options were, I ended up implementing a combination of two methods: 
- displaying/hiding tags based on their class being "lang-en" or "lang-pt", for longer text contents.
- switching between two dictionaries (english and portuguese) with key-value pairs (the key being the same in both dictionaries), for common words.

Here I encountered some **setbacks** and **bugs** I ended up not entirely fixing. Because the main language is english, if the user changes to portuguese, that choice is saved on local storage, so it doesn't go back to english when changing tabs/templates. The problem is, technically, the content does change back to english, but the translation function is called immediatly and it changes back to portuguese. This makes the screen visually flicker between the english text and the portuguese text, even if it's just one time and less than half a second.

### Users permission and features

On this app, each user is assigned a different role: *admin*, *teacher* and *student*.

Initially, I visualized a set of different permissions and features for each user role. In the end, I decided that the teachers and students usage would be merely **informative**. They can only look for information, without changing anything. A future implementation would be to give them the possibility to ask for some modification, and then the admin would review and confirm/deny said modification. 

#### Displayed information 

Both teachers and students have access to *schedules.html*, *selected_shcedules.html*, *lessons.html* and *selected_lessons.html*, where they can check their schedules, either from the current school year (*schedules.html*) or older school years (*selected_schedules.html*), and check all lessons associated to each schedule. On the lessons tab, they can look for lessons from a specific day or from a specific schedule. Both searches will redirect them to the *selected_lessons.html* template, which will display the lessons they searched for. On this template, they are also able to check if each lesson was attended or not, based on the background color of each row. 

Teachers and students can also access their finances (*salaries.html* and *tuitions.html* respectively), where they can check the state of each payment.

#### Administrator features

Besides being able to look at any information related to any teacher and student, throughout all the tabs/templates, an admin can also modify, add and remove basically every element that is displayed. 

With all these modification possibilities, another difficulty I encountered was to be careful to handle **ALL** relationships between this data. A few examples of this being:
- Removing a teacher means deleting its future salaries (and yet keeping older salaries), deleting schedules/classes that they used to teach (although keeping past lessons from that schedule) and to dissociate the students from those same lessons and schedules. 
- Removing a student, besides the same problems as removing a teacher, means also to check for the schedules associated to that student and act accordingly if it's a group or individual class. If it's a group class, we only want to remove the student from that schedule, but if it is an individual class, we want to delete the schedule all together. 
- Adding a new teacher/student means also to add all salaries/tuitions from that day on until the end of the school year (which is a global scope variable).
- Editing any parameter from a schedule means updating every future lesson with that same modification. 

## Final considerations

Although there are still some minor bugs to fix and many features I still plan to implement in the future, this web app already includes a variety of important functionalities that will help a school community organize itself and streamline its internal affairs.









