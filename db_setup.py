import mysql.connector
from werkzeug.security import generate_password_hash

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'promptkipling',  # Change to your MySQL password
}

# Connect to MySQL
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Create database
cursor.execute("CREATE DATABASE IF NOT EXISTS studentdb")
print("Database created successfully")

# Switch to the database
cursor.execute("USE studentdb")

# Create tables
tables = [
    """
    CREATE TABLE IF NOT EXISTS Students (
        student_id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        registration_number VARCHAR(20) UNIQUE NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Teachers (
        teacher_id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Courses (
        course_id INT PRIMARY KEY AUTO_INCREMENT,
        course_code VARCHAR(20) UNIQUE NOT NULL,
        course_name VARCHAR(100) NOT NULL,
        teacher_id INT NOT NULL,
        FOREIGN KEY (teacher_id) REFERENCES Teachers(teacher_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Enrollments (
        enrollment_id INT PRIMARY KEY AUTO_INCREMENT,
        student_id INT NOT NULL,
        course_id INT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES Students(student_id),
        FOREIGN KEY (course_id) REFERENCES Courses(course_id),
        UNIQUE KEY (student_id, course_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Sessions (
        session_id INT PRIMARY KEY AUTO_INCREMENT,
        course_id INT NOT NULL,
        session_date DATE NOT NULL,
        topic VARCHAR(255),
        FOREIGN KEY (course_id) REFERENCES Courses(course_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Attendance (
        attendance_id INT PRIMARY KEY AUTO_INCREMENT,
        session_id INT NOT NULL,
        student_id INT NOT NULL,
        status ENUM('Present', 'Absent') NOT NULL,
        FOREIGN KEY (session_id) REFERENCES Sessions(session_id),
        FOREIGN KEY (student_id) REFERENCES Students(student_id),
        UNIQUE KEY (session_id, student_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Users (
        user_id INT PRIMARY KEY AUTO_INCREMENT,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role ENUM('Teacher', 'Student') NOT NULL,
        reference_id INT NOT NULL,
        is_active BOOLEAN DEFAULT TRUE
    )
    """
]

for table in tables:
    cursor.execute(table)
print("Tables created successfully")

# Insert sample data
# Add a teacher
cursor.execute("""
    INSERT INTO Teachers (name, email)
    VALUES ('John Smith', 'john.smith@example.com')
""")
teacher_id = cursor.lastrowid

# Add a student
cursor.execute("""
    INSERT INTO Students (name, email, registration_number)
    VALUES ('Jane Doe', 'jane.doe@example.com', 'CS2022001')
""")
student_id = cursor.lastrowid

# Add a course
cursor.execute("""
    INSERT INTO Courses (course_code, course_name, teacher_id)
    VALUES ('CS101', 'Introduction to Programming', %s)
""", (teacher_id,))
course_id = cursor.lastrowid

# Enroll student in course
cursor.execute("""
    INSERT INTO Enrollments (student_id, course_id)
    VALUES (%s, %s)
""", (student_id, course_id))

# Create user accounts
# Teacher account
cursor.execute("""
    INSERT INTO Users (username, password_hash, role, reference_id)
    VALUES ('teacher', %s, 'Teacher', %s)
""", (generate_password_hash('teacher123'), teacher_id))

# Student account
cursor.execute("""
    INSERT INTO Users (username, password_hash, role, reference_id)
    VALUES ('student', %s, 'Student', %s)
""", (generate_password_hash('student123'), student_id))

conn.commit()
print("Sample data inserted successfully")

cursor.close()
conn.close()
print("Database setup complete")