import sqlite3

def init_db():
    conn = sqlite3.connect('lms.db')
    c = conn.cursor()

    # Users table (for Admins/Teachers)
    c.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'admin'
        )
    ''')

    # Students table
    c.execute('''
        CREATE TABLE IF NOT EXISTS Students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            date_of_birth TEXT,
            password TEXT NOT NULL
        )
    ''')

    # Courses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS Courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            instructor TEXT
        )
    ''')

    # Enrollments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS Enrollments (
            enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            course_id INTEGER,
            enrollment_date TEXT,
            FOREIGN KEY(student_id) REFERENCES Students(student_id),
            FOREIGN KEY(course_id) REFERENCES Courses(course_id)
        )
    ''')

    # Quizzes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS Quizzes (
            quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            title TEXT NOT NULL,
            instructions TEXT,
            time_limit INTEGER,
            FOREIGN KEY(course_id) REFERENCES Courses(course_id)
        )
    ''')

    # Questions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS Questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question_text TEXT NOT NULL,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            correct_option TEXT,
            FOREIGN KEY(quiz_id) REFERENCES Quizzes(quiz_id)
        )
    ''')

    # Quiz results table
    c.execute('''
        CREATE TABLE IF NOT EXISTS QuizResults (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            quiz_id INTEGER,
            score INTEGER,
            total_questions INTEGER,
            submission_date TEXT,
            FOREIGN KEY(student_id) REFERENCES Students(student_id),
            FOREIGN KEY(quiz_id) REFERENCES Quizzes(quiz_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ LMS database and quiz tables created successfully.")

# Run the function
init_db()