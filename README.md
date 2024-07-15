# Student Manager App

![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![Jinja](https://img.shields.io/badge/jinja-white.svg?style=for-the-badge&logo=jinja&logoColor=black)
![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)

### Video Demo: https://www.youtube.com/watch?v=wGO86OT3_Yk

## Genesis

Back in 2022, I was taking part in a bootcamp where we were challenged to think of a fictional web app to manage students.
We prepared a List of Requirements, and eventually created a mockup of our web app in Figma.

However, due to time constraints I would end up not implementing some of those ideas ... until now.

### Functionalities

- **Manage Ongoing and Archived classes**
- **Manage students from a specific class;**
- **Import students from a csv file onto a newly created class;**

## Development

### First steps

<!-- <img src="./flaskr/static/img/banner.png"/> -->

I started off by designing the database, thinking about the different tables I would need. Defining each of those tables. For example: I would need students, classes - but what exactly would a student be? Or a class?

As the project kept growing, so did my needs. For example, I would have to start differentiating between 'ongoing' and 'archived' classes. So I changed the 'class' table.

Originally there was a 1-to-1 relationship between the 'student' and 'class tables'. However, when I started implementing the 'advancement' functionaliy, where a teacher would be able to manually advance students, I got stuck precisely because of that 1-to-1 relationship!
After doing some research, it became clear it was instead a many-to-many relationship and that I would need a junction table.

### Prototyping

After designing the database, I began thinking about how I wanted the web app to look like, the user flow, etc.
For that, I started off by using good old pen and paper, looking up real universites' websites, playing around in Figma, etc. The design has changed a lot over the past month, as I kept finding certain flows awkward, or inneficient.

When I was structure in mind, I started working on the implementation itself.

### Project Layout

This project follows the project layout found in Flask's documentation:

```bash
├── README.md
├── data
│   └── dummy_data.csv
├── flaskr
│   ├── __pycache__
│   ├── app.py
│   ├── database.db
│   ├── populate.py
│   ├── static
│   │   ├── img
│   │   ├── scripts
│   │   └── styles
│   ├── templates
│   │   ├── archived_classes
│   │   ├── course_classes
│   │   ├── feedback_msg
│   │   ├── homepage
│   │   ├── index
│   │   ├── layout.html
│   │   ├── student
│   │   └── user_feedback
│   └── utils.py
└── requirements.txt
```

- **flaskr/** is the directory that contains the application's folders and files;
- **templates/** is a directory that holds several other directories, each containing an html template;
- **populate.py** is a file I created so I could more easily create and populate the database;
- **utils.py** is a file I created where I had a function or constant variables that I would use in different places;
- **requirements.txt** is a file I created that lets you install all dependencies necessary for the project to run;

## How it works

This project assumes that an admin would create an account for a teacher, and then giving said teacher the account's credentials.

The teacher would then be able to login onto a homepage.

On the homepage, the teacher can then see **ongoing classes**. Selecting one, will take them to a page where all students are listed. Each student can be **Edited** or **Deleted** from the class. If there are spots available, then the teacher can **Add** someone to the class.

Furthermore, if it's an **Intro class**, the teacher may select students for advancement into the **Advanced classes**.

Classes themselves may be **Created**, **Archived** or **Deleted**.
When a newly created class is selected, it's empty. The teacher can either manually add students to it, or **import** students from a csv file.

When **Archived**, they will be visible on a separated page - 'Archived Classes'.
On this page, the teacher can use a search bar or search manually for a specific archived class. If selected, the users inside of it can't be advanced - as it's not an ongoing class.

## Future implementations

In the future, I would like to create a backoffice for an admin.

The admin would be able to see who created/deleted classes and also create new accoutns for new users.
