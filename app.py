from flask import Flask, render_template, request, redirect, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = '998877'

# --- Database Connection ---
def get_db():
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Public Routes ---
@app.route('/')
def home():
    return render_template('home.html')

# --- Admin Signup/Login ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            with get_db() as conn:
                conn.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                flash("✅ Account created successfully.")
                return redirect('/login')
        except sqlite3.IntegrityError:
            flash("❌ Username already exists.")
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM Users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("✅ Logged in successfully.")
            return redirect('/dashboard')
        else:
            flash("❌ Invalid username or password.")
    return render_template('login.html')

# --- Admin Dashboard ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("⚠️ Please log in to continue.")
        return redirect('/login')
    return render_template('index.html')

# --- Student CRUD (Admin) ---
@app.route('/add-student', methods=['GET', 'POST'])
def add_student():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        sid = request.form['student_id']
        name = request.form['name']
        email = request.form['email']
        dob = request.form['dob']
        try:
            with get_db() as conn:
                conn.execute("INSERT INTO Students (student_id, name, email, date_of_birth) VALUES (?, ?, ?, ?)",
                             (sid, name, email, dob))
                conn.commit()
                flash("✅ Student added successfully.")
        except sqlite3.IntegrityError:
            flash("❌ Student ID or Email already exists.")
    return render_template('add_student.html')

@app.route('/view-students')
def view_students():
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    raw_students = cursor.execute("SELECT * FROM Students").fetchall()
    student_data = []

    for s in raw_students:
        student_id = s['student_id']

        # Get enrolled courses
        enrolled_courses = cursor.execute('''
            SELECT c.title
            FROM Courses c
            JOIN Enrollments e ON c.course_id = e.course_id
            WHERE e.student_id = ?
        ''', (student_id,)).fetchall()

        # Get quiz results
        results = cursor.execute('''
            SELECT score, total_questions
            FROM QuizResults
            WHERE student_id = ?
        ''', (student_id,)).fetchall()

        attempted = len(results)
        total_score = sum([r['score'] for r in results])
        total_possible = sum([r['total_questions'] for r in results])
        avg_percent = round((total_score / total_possible) * 100, 2) if total_possible > 0 else None

        student_data.append({
            'student_id': s['student_id'],
            'name': s['name'],
            'email': s['email'],
            'date_of_birth': s['date_of_birth'],
            'courses': [c['title'] for c in enrolled_courses],
            'quizzes_attempted': attempted,
            'average_percent': avg_percent
        })

    conn.close()
    return render_template('view_students.html', students=student_data)

@app.route('/delete-student/<int:student_id>')
def delete_student(student_id):
    if 'user_id' not in session:
        return redirect('/login')
    with get_db() as conn:
        conn.execute("DELETE FROM Students WHERE student_id = ?", (student_id,))
        conn.commit()
        flash("🗑️ Student deleted successfully.")
    return redirect('/view-students')

# --- Course Management ---
@app.route('/add-course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        instructor = request.form.get('instructor')
        video_url = request.form.get('video_url')  # 🆕 added field

        conn = sqlite3.connect('lms.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Courses (title, description, instructor, video_url)
            VALUES (?, ?, ?, ?)
        ''', (title, description, instructor, video_url))
        conn.commit()
        conn.close()
        flash("✅ Course added successfully!")
        return redirect('/view-courses')

    return render_template('add_course.html')

@app.route('/view-courses')
def view_courses():
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    courses = conn.execute("SELECT * FROM Courses").fetchall()
    conn.close()
    return render_template('view_courses.html', courses=courses)
@app.route('/delete-course/<int:course_id>', methods=['GET', 'POST'])
def delete_course(course_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    course = conn.execute("SELECT * FROM Courses WHERE course_id = ?", (course_id,)).fetchone()

    if request.method == 'POST':
        conn.execute("DELETE FROM Courses WHERE course_id = ?", (course_id,))
        conn.commit()
        flash("🗑️ Course deleted successfully.")
        return redirect('/view-courses')

    return render_template('delete_course.html', course=course)

# --- Student Auth & Dashboard ---
@app.route('/student-signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        try:
            with get_db() as conn:
                conn.execute("INSERT INTO Students (name, email, date_of_birth, password) VALUES (?, ?, '', ?)",
                             (name, email, password))
                conn.commit()
                flash("✅ Student account created. Please log in.")
                return redirect('/student-login')
        except sqlite3.IntegrityError:
            flash("❌ Email already registered.")
    return render_template('student_signup.html')

@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        with get_db() as conn:
            student = conn.execute("SELECT * FROM Students WHERE email = ? AND password = ?",
                                   (email, password)).fetchone()
        if student:
            session['student_id'] = student['student_id']
            session['student_name'] = student['name']
            flash("✅ Logged in as student.")
            return redirect('/student-dashboard')
        else:
            flash("❌ Invalid student credentials.")
    return render_template('student_login.html')
@app.route('/student-dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect('/student-login')

    with get_db() as conn:
        all_courses = conn.execute("SELECT * FROM Courses").fetchall()

        # Get enrolled course IDs for the student
        enrolled = conn.execute("SELECT course_id FROM Enrollments WHERE student_id = ?", (session['student_id'],)).fetchall()
        enrolled_ids = [e['course_id'] for e in enrolled]

        # Filter enrolled courses (optional)
        enrolled_courses = [c for c in all_courses if c['course_id'] in enrolled_ids]
        total_courses = len(all_courses)

        # ✅ Fetch quizzes linked to student's enrolled courses
        quizzes = conn.execute('''
            SELECT q.quiz_id, q.title, c.title AS course_title
            FROM Quizzes q
            JOIN Courses c ON q.course_id = c.course_id
            WHERE q.course_id IN (
                SELECT course_id FROM Enrollments WHERE student_id = ?
            )
        ''', (session['student_id'],)).fetchall()

    return render_template(
        'student_dashboard.html',
        courses=all_courses,
        enrolled_ids=enrolled_ids,
        enrolled_courses=enrolled_courses,
        total_courses=total_courses,
        quizzes=quizzes  # ✅ passing quizzes to template
    )

@app.route('/enroll-course/<int:course_id>')
def enroll_course(course_id):
    if 'student_id' not in session:
        return redirect('/student-login')
    with get_db() as conn:
        conn.execute("INSERT INTO Enrollments (student_id, course_id, enrollment_date) VALUES (?, ?, DATE('now'))",
                     (session['student_id'], course_id))
        conn.commit()
        flash("✅ Enrolled in course.")
    return redirect('/student-dashboard')

@app.route('/drop-course/<int:course_id>')
def drop_course(course_id):
    if 'student_id' not in session:
        return redirect('/student-login')
    with get_db() as conn:
        conn.execute("DELETE FROM Enrollments WHERE student_id = ? AND course_id = ?",
                     (session['student_id'], course_id))
        conn.commit()
        flash("❌ Course removed.")
    return redirect('/student-dashboard')

@app.route('/student-enrollments')  # 👈 matches your link
def student_enrollments():
    if 'student_id' not in session:
        return redirect('/student-login')
    with get_db() as conn:
        courses = conn.execute("""
            SELECT c.*
            FROM Courses c
            JOIN Enrollments e ON c.course_id = e.course_id
            WHERE e.student_id = ?
        """, (session['student_id'],)).fetchall()
    return render_template('student_enrollments.html', courses=courses)
@app.route('/create-questions', methods=['GET', 'POST'])
def create_questions():
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch quizzes to let admin choose where to add questions
    cursor.execute("SELECT quiz_id, title FROM Quizzes")
    quizzes = cursor.fetchall()

    if request.method == 'POST':
        quiz_id = request.form['quiz_id']
        question_text = request.form['question_text']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_option = request.form['correct_option']

        cursor.execute('''
            INSERT INTO Questions (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option))

        conn.commit()
        conn.close()
        return redirect('/create-questions')  # Allow adding multiple questions

    conn.close()
    return render_template('create_questions.html', quizzes=quizzes)
@app.route('/student-profile')
def student_profile():
    if 'student_id' not in session:
        return redirect('/student-login')

    student_id = session['student_id']
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch student info
    student = conn.execute("SELECT * FROM Students WHERE student_id = ?", (student_id,)).fetchone()

    # Fetch quiz results
    quiz_scores = conn.execute('''
        SELECT q.title AS quiz_title, qr.score, qr.total_questions
        FROM QuizResults qr
        JOIN Quizzes q ON qr.quiz_id = q.quiz_id
        WHERE qr.student_id = ?
    ''', (student_id,)).fetchall()

    conn.close()
    return render_template('student_profile.html', student=student, quiz_scores=quiz_scores)
@app.route('/start-quiz/<int:quiz_id>', methods=['GET', 'POST'])
def start_quiz(quiz_id):
    student_id = session.get('student_id')
    if not student_id:
        flash("⚠️ Please log in first.")
        return redirect('/student-login')

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check if already attempted
    cursor.execute('SELECT * FROM QuizResults WHERE student_id = ? AND quiz_id = ?', (student_id, quiz_id))
    attempted = cursor.fetchone()

    # Fetch quiz
    cursor.execute("SELECT title, instructions, time_limit FROM Quizzes WHERE quiz_id = ?", (quiz_id,))
    quiz = cursor.fetchone()

    # Fetch questions
    cursor.execute("SELECT * FROM Questions WHERE quiz_id = ?", (quiz_id,))
    questions = cursor.fetchall()
    total_questions = len(questions)

    score = None

    if request.method == 'POST' and not attempted:
        score = 0
        for q in questions:
            submitted = request.form.get(str(q['question_id']))
            if submitted and submitted == q['correct_option']:
                score += 1

        cursor.execute('''
            INSERT INTO QuizResults (student_id, quiz_id, score, total_questions)
            VALUES (?, ?, ?, ?)
        ''', (student_id, quiz_id, score, total_questions))
        conn.commit()

    conn.close()

    return render_template('quiz_page.html',
                           quiz=quiz,
                           questions=questions,
                           quiz_id=quiz_id,
                           score=score,
                           attempted=attempted,
                           total=total_questions)
@app.route('/create-quiz', methods=['GET', 'POST'])
def create_quiz():
    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get list of courses to associate quiz with
    cursor.execute("SELECT course_id, title FROM Courses")
    courses = cursor.fetchall()

    if request.method == 'POST':
        title = request.form['title']
        instructions = request.form['instructions']
        time_limit = request.form['time_limit']
        course_id = request.form['course_id']

        cursor.execute('''
            INSERT INTO Quizzes (course_id, title, instructions, time_limit)
            VALUES (?, ?, ?, ?)
        ''', (course_id, title, instructions, time_limit))

        conn.commit()
        conn.close()
        return redirect('/create-questions')  # Optional: send to add questions

    conn.close()
    return render_template('create_quiz.html', courses=courses)

@app.route('/courses-enrolled')
def courses_enrolled():
    student_id = session.get('student_id')
    if not student_id:
        return "Unauthorized Access", 403  # Or redirect to login

    conn = sqlite3.connect('lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT c.title, c.instructor, e.enrollment_date
        FROM Enrollments e
        JOIN Courses c ON e.course_id = c.course_id
        WHERE e.student_id = ?
    ''', (student_id,))
    rows = cursor.fetchall()
    conn.close()

    enrolled_courses = []
    for row in rows:
        # Extract only date portion (ignore time if present)
        date_clean = row['enrollment_date'].split(' ')[0]
        parts = date_clean.split('-')  # 'YYYY-MM-DD'
        formatted_date = f"{parts[2]} {parts[1]} {parts[0]}"  # 'DD MM YYYY'

        enrolled_courses.append({
            'name': row['title'],
            'instructor': row['instructor'],
            'enrollment_date': formatted_date,
            'progress': 70,
            'status': 'Active'
        })

    return render_template('courses_enrolled.html', enrolled_courses=enrolled_courses)

# --- Logout ---
@app.route('/logout')
def logout():
    session.clear()
    flash("✅ You have been logged out.")
    return redirect('/')

# --- Run ---
if __name__ == '__main__':
    app.run(debug=True)