from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import os
from datetime import timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'promptkipling',  # Change to your MySQL password
    'database': 'studentdb'
}

# Create database connection
def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn, conn.cursor(dictionary=True)

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'Teacher':
            flash('Access denied: Teacher privileges required', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'Student':
            flash('Access denied: Student privileges required', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'Teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn, cursor = get_db_connection()
        
        # Find user in database
        cursor.execute("""
            SELECT u.user_id, u.username, u.password_hash, u.role, u.reference_id,
                   CASE 
                       WHEN u.role = 'Teacher' THEN t.name
                       WHEN u.role = 'Student' THEN s.name
                   END as name
            FROM Users u
            LEFT JOIN Teachers t ON u.role = 'Teacher' AND u.reference_id = t.teacher_id
            LEFT JOIN Students s ON u.role = 'Student' AND u.reference_id = s.student_id
            WHERE u.username = %s AND u.is_active = TRUE
        """, (username,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['name'] = user['name']
            session['reference_id'] = user['reference_id']
            session.permanent = True
            
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

# Teacher Routes
@app.route('/teacher/dashboard')
@login_required
@teacher_required
def teacher_dashboard():
    conn, cursor = get_db_connection()
    
    # Get courses taught by teacher
    cursor.execute("""
        SELECT course_id, course_code, course_name
        FROM Courses
        WHERE teacher_id = %s
    """, (session['reference_id'],))
    
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('teacher/dashboard.html', courses=courses)

@app.route('/teacher/attendance', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher_attendance():
    course_id = request.args.get('course_id')
    date = request.args.get('date')
    
    conn, cursor = get_db_connection()
    
    # Get all courses taught by teacher
    cursor.execute("""
        SELECT course_id, course_code, course_name
        FROM Courses
        WHERE teacher_id = %s
    """, (session['reference_id'],))
    
    courses = cursor.fetchall()
    
    if course_id and date:
        # Check if session exists
        cursor.execute("""
            SELECT session_id FROM Sessions 
            WHERE course_id = %s AND session_date = %s
        """, (course_id, date))
        
        session_result = cursor.fetchone()
        session_id = None
        
        # Create session if it doesn't exist
        if not session_result:
            cursor.execute("""
                INSERT INTO Sessions (course_id, session_date, topic)
                VALUES (%s, %s, 'Class')
            """, (course_id, date))
            conn.commit()
            session_id = cursor.lastrowid
        else:
            session_id = session_result['session_id']
        
        # Get students enrolled in the course
        cursor.execute("""
            SELECT s.student_id, s.name, s.registration_number,
                   (SELECT status FROM Attendance 
                    WHERE session_id = %s AND student_id = s.student_id) as status
            FROM Students s
            JOIN Enrollments e ON s.student_id = e.student_id
            WHERE e.course_id = %s
            ORDER BY s.name
        """, (session_id, course_id))
        
        students = cursor.fetchall()
        
        # If POST request, mark attendance
        if request.method == 'POST':
            present_students = request.form.getlist('present')
            
            for student in students:
                status = 'Present' if str(student['student_id']) in present_students else 'Absent'
                
                # Check if attendance already marked
                cursor.execute("""
                    SELECT attendance_id FROM Attendance
                    WHERE session_id = %s AND student_id = %s
                """, (session_id, student['student_id']))
                
                if cursor.fetchone():
                    # Update existing record
                    cursor.execute("""
                        UPDATE Attendance
                        SET status = %s
                        WHERE session_id = %s AND student_id = %s
                    """, (status, session_id, student['student_id']))
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO Attendance (session_id, student_id, status)
                        VALUES (%s, %s, %s)
                    """, (session_id, student['student_id'], status))
            
            conn.commit()
            flash('Attendance marked successfully', 'success')
            return redirect(url_for('teacher_attendance', course_id=course_id, date=date))
        
        # Get course details
        cursor.execute("""
            SELECT course_code, course_name FROM Courses WHERE course_id = %s
        """, (course_id,))
        course = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return render_template(
            'teacher/attendance.html',
            courses=courses,
            course=course,
            students=students,
            session_id=session_id,
            selected_date=date
        )
    
    cursor.close()
    conn.close()
    
    return render_template('teacher/attendance.html', courses=courses)

@app.route('/teacher/analysis')
@login_required
@teacher_required
def teacher_analysis():
    course_id = request.args.get('course_id')
    
    conn, cursor = get_db_connection()
    
    # Get all courses taught by teacher
    cursor.execute("""
        SELECT course_id, course_code, course_name
        FROM Courses
        WHERE teacher_id = %s
    """, (session['reference_id'],))
    
    courses = cursor.fetchall()
    
    attendance_data = []
    course = None
    
    if course_id:
        # Get course details
        cursor.execute("""
            SELECT course_code, course_name FROM Courses WHERE course_id = %s
        """, (course_id,))
        course = cursor.fetchone()
        
        # Get attendance statistics
        cursor.execute("""
            SELECT 
                s.student_id,
                s.name,
                s.registration_number,
                COUNT(DISTINCT sess.session_id) AS total_sessions,
                SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
                ROUND((SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / 
                      COUNT(DISTINCT sess.session_id)) * 100, 2) AS attendance_percentage
            FROM Students s
            JOIN Enrollments e ON s.student_id = e.student_id
            JOIN Sessions sess ON e.course_id = sess.course_id
            LEFT JOIN Attendance a ON sess.session_id = a.session_id AND s.student_id = a.student_id
            WHERE e.course_id = %s
            GROUP BY s.student_id
            ORDER BY attendance_percentage DESC
        """, (course_id,))
        
        attendance_data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template(
        'teacher/analysis.html',
        courses=courses,
        course=course,
        attendance_data=attendance_data
    )

# Student Routes
@app.route('/student/dashboard')
@login_required
@student_required
def student_dashboard():
    conn, cursor = get_db_connection()
    
    # Get courses the student is enrolled in
    cursor.execute("""
        SELECT c.course_id, c.course_code, c.course_name, t.name AS teacher_name,
               COUNT(DISTINCT s.session_id) AS total_sessions,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
               ROUND((SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / 
                     COUNT(DISTINCT s.session_id)) * 100, 2) AS attendance_percentage
        FROM Enrollments e
        JOIN Courses c ON e.course_id = c.course_id
        JOIN Teachers t ON c.teacher_id = t.teacher_id
        LEFT JOIN Sessions s ON c.course_id = s.course_id
        LEFT JOIN Attendance a ON s.session_id = a.session_id AND a.student_id = e.student_id
        WHERE e.student_id = %s
        GROUP BY c.course_id
    """, (session['reference_id'],))
    
    courses = cursor.fetchall()
    
    # Get recent attendance records
    cursor.execute("""
        SELECT c.course_code, c.course_name, s.session_date, a.status
        FROM Attendance a
        JOIN Sessions s ON a.session_id = s.session_id
        JOIN Courses c ON s.course_id = c.course_id
        WHERE a.student_id = %s
        ORDER BY s.session_date DESC
        LIMIT 10
    """, (session['reference_id'],))
    
    recent_attendance = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template(
        'student/dashboard.html',
        courses=courses,
        recent_attendance=recent_attendance
    )

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)