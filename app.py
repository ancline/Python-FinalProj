from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
import os
import base64
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key_123"

# =========================================
# DATABASE PATH
# =========================================
DB_PATH = "db/school.db"

# =========================================
# UPLOAD FOLDER FOR PHOTOS
# =========================================
UPLOAD_FOLDER = 'photos'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# =========================================
# INITIALIZE DATABASE
# =========================================
def init_db():
    """Initialize database tables if they don't exist"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create attendance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idno TEXT NOT NULL,
                lastname TEXT NOT NULL,
                firstname TEXT NOT NULL,
                course TEXT NOT NULL,
                level TEXT NOT NULL,
                time_in TEXT NOT NULL,
                date TEXT NOT NULL
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_attendance_date 
            ON attendance(date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_attendance_idno 
            ON attendance(idno)
        """)
        
        conn.commit()
        conn.close()
        print("✓ Database initialized successfully!")
    except Exception as e:
        print(f"✗ Error initializing database: {e}")

# Initialize database on startup
init_db()

# =========================================
# ROUTES
# =========================================

@app.route('/')
def home():
    return render_template('index.html')

# FIXED: Separate routes for new student and edit student
@app.route('/student')
def student():
    if "user_id" not in session:
        flash("Please login to continue.", "error")
        return redirect(url_for("login"))
    return render_template('student.html', student=None)

@app.route('/student/<int:id>')
def student_page(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Fetch student by ID
    c.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = c.fetchone()
    conn.close()

    return render_template('student.html', student=student)


@app.route('/studentmngt')
def studentmngt():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM students")
    students = c.fetchall()

    conn.close()

    return render_template('studentmngt.html', students=students)

# FIXED: This should UPDATE the student, not just fetch and render
@app.route("/update-student/<int:id>", methods=["POST"])
def update_student(id):
    data = request.get_json()
    idno = data.get("idno")
    lastname = data.get("lastname")
    firstname = data.get("firstname")
    course = data.get("course")
    level = data.get("level")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Actually UPDATE the student record
        cursor.execute(
            "UPDATE students SET idno=?, lastname=?, firstname=?, course=?, level=? WHERE id=?",
            (idno, lastname, firstname, course, level, id)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        print("DB error:", e)
        return jsonify({"success": False, "message": str(e)})


# -------------------------------
# LOGIN PAGE + BACKEND
# -------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Check if there's a record with this email AND password
        c.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            # Store info in session
            session['user_id'] = user[0]
            session['email'] = user[1]
            return redirect('/admin')
        else:
            flash("Invalid email or password!", "error")
            return redirect(url_for('login'))

    return render_template('login.html')


# -------------------------------
# REGISTER PAGE + BACKEND
# -------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if password != confirm:
            flash("Passwords do not match!", "error")
            return redirect(url_for("register"))

        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO users (email, password) VALUES (?, ?)",
                      (email, password))
            conn.commit()
            conn.close()

            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Email already exists!", "error")
            return redirect(url_for("register"))

    return render_template('Register.html')


@app.route('/admin')
def admin():
    if "user_id" not in session:
        return redirect(url_for('login'))

    # Get all users from DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, email, password FROM users")
    users = c.fetchall()
    conn.close()

    return render_template('admin.html', users=users)


# -------------------------------
# LOGOUT
# -------------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))


# -------------------------------
# UPLOAD PHOTO
# -------------------------------
@app.route('/upload-photo', methods=['POST'])
def upload_photo():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400

        idno = data.get('idno')
        photoData = data.get('photoData')
        if not photoData or not idno:
            return jsonify({'success': False, 'message': 'Missing data'}), 400

        if 'data:image' in photoData:
            base64_data = photoData.split(',')[1]
        else:
            base64_data = photoData

        image_data = base64.b64decode(base64_data)
        filename = f"{idno}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'wb') as f:
            f.write(image_data)

        return jsonify({
            'success': True,
            'message': 'Photo uploaded successfully',
            'photoUrl': f'/photos/{filename}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# -------------------------------
# GET PHOTO
# -------------------------------
@app.route('/get-photo/<idno>')
def get_photo(idno):
    try:
        filename = f"{idno}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='image/jpeg')
        else:
            return jsonify({'error': 'Photo not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------------
# SAVE STUDENT (NEW)
# -------------------------------
@app.route("/save-student", methods=["POST"])
def save_student():
    data = request.get_json()
    idno = data.get("idno")
    lastname = data.get("lastname")
    firstname = data.get("firstname")
    course = data.get("course")
    level = data.get("level")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if IDNO already exists
        cursor.execute("SELECT idno FROM students WHERE idno = ?", (idno,))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return jsonify({"success": False, "message": f"Student with IDNO {idno} already exists!"})
        
        cursor.execute(
            "INSERT INTO students (idno, lastname, firstname, course, level) VALUES (?, ?, ?, ?, ?)",
            (idno, lastname, firstname, course, level),
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        print("DB error:", e)
        return jsonify({"success": False, "message": str(e)})


# -------------------------------
# DELETE STUDENT
# -------------------------------
@app.route('/deletestudent/<int:id>', methods=['POST', 'GET'])
def delete_student(id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Delete the student record
        cursor.execute("DELETE FROM students WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        
        # If it's a GET request (redirect), go back to student management
        if request.method == 'GET':
            flash("Student deleted successfully!", "success")
            return redirect(url_for('studentmngt'))
        
        # If it's a POST request (AJAX), return JSON
        return jsonify({"success": True, "message": "Student deleted successfully"})
    except Exception as e:
        print("Delete error:", e)
        if request.method == 'GET':
            flash(f"Error deleting student: {str(e)}", "error")
            return redirect(url_for('studentmngt'))
        return jsonify({"success": False, "message": str(e)}), 500


# -------------------------------
# ATTENDANCE ROUTES
# -------------------------------
@app.route('/attendance')
def attendance():
    return render_template('attendance.html')


# -------------------------------
# SAVE ATTENDANCE (When QR is scanned)
# -------------------------------
@app.route('/save-attendance', methods=['POST'])
def save_attendance():
    try:
        data = request.get_json()
        idno = data.get('idno')
        
        if not idno:
            return jsonify({"success": False, "message": "Missing IDNO"}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if student exists
        cursor.execute("SELECT idno, lastname, firstname, course, level FROM students WHERE idno = ?", (idno,))
        student = cursor.fetchone()
        
        if not student:
            conn.close()
            return jsonify({"success": False, "message": "Student not found"}), 404
        
        # Get current timestamp
        time_in = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_only = datetime.now().strftime("%Y-%m-%d")
        
        # Check if already logged in today
        cursor.execute("SELECT id FROM attendance WHERE idno = ? AND date = ?", (idno, date_only))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return jsonify({
                "success": False, 
                "message": f"{student[2]} {student[1]} has already logged attendance today!",
                "student": {
                    "idno": student[0],
                    "lastname": student[1],
                    "firstname": student[2],
                    "course": student[3],
                    "level": student[4]
                }
            })
        
        # Insert attendance record
        cursor.execute(
            "INSERT INTO attendance (idno, lastname, firstname, course, level, time_in, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (student[0], student[1], student[2], student[3], student[4], time_in, date_only)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": "Attendance recorded successfully!",
            "student": {
                "idno": student[0],
                "lastname": student[1],
                "firstname": student[2],
                "course": student[3],
                "level": student[4]
            }
        })
    except Exception as e:
        print("Attendance error:", e)
        return jsonify({"success": False, "message": str(e)}), 500


# -------------------------------
# GET ATTENDANCE RECORDS (Filter by date)
# -------------------------------
@app.route('/get-attendance', methods=['GET'])
def get_attendance():
    try:
        date = request.args.get('date')
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if date:
            cursor.execute("SELECT * FROM attendance WHERE date = ? ORDER BY time_in ASC", (date,))
        else:
            cursor.execute("SELECT * FROM attendance ORDER BY date DESC, time_in DESC LIMIT 100")
        
        records = cursor.fetchall()
        conn.close()
        
        attendance_list = []
        for record in records:
            attendance_list.append({
                "id": record['id'],
                "idno": record['idno'],
                "lastname": record['lastname'],
                "firstname": record['firstname'],
                "course": record['course'],
                "level": record['level'],
                "time_in": record['time_in'],
                "date": record['date']
            })
        
        return jsonify({"success": True, "records": attendance_list})
    except Exception as e:
        print("Get attendance error:", e)
        return jsonify({"success": False, "message": str(e)}), 500


# -------------------------------
# GET ALL USERS (Admin Table)
# -------------------------------
@app.route('/get-users', methods=['GET'])
def get_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, email, password FROM users")
    rows = c.fetchall()
    conn.close()

    users = []
    for r in rows:
        users.append({
            "id": r[0],
            "email": r[1],
            "password": r[2]
        })

    return jsonify(users)


# -------------------------------
# USER MANAGEMENT (Admin Page)
# -------------------------------
@app.route('/add-user', methods=['POST'])
def add_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"success": False, "message": "Missing fields"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "User added successfully"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Email already exists!"}), 409

@app.route('/edit-user/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required!"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET email = ?, password = ? WHERE id = ?", (email, password, user_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "User updated successfully!"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Email already exists!"}), 409

@app.route('/delete-user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "User deleted successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# =========================================
# START APP
# =========================================
if __name__ == '__main__':
    app.run(debug=True)