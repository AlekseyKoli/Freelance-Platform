from flask import Blueprint, jsonify, request, session
import sqlite3
from flask_cors import CORS

# Blueprint для маршрутов пользователя
user_routes = Blueprint('user_routes', __name__)
DATABASE = 'freelance_platform.db'

def connect_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# API: регистрация пользователя
@user_routes.route('/api/users', methods=['POST'])
def register_user():
    data = request.json
    conn = connect_db()
    cursor = conn.cursor()

    # Проверяем, существует ли уже пользователь с таким email
    existing_email = cursor.execute("SELECT * FROM Users WHERE email = ?", (data['email'],)).fetchone()
    if existing_email:
        return jsonify({'error': 'Email already exists'}), 400

    # Проверяем, существует ли уже пользователь с таким именем
    existing_name = cursor.execute("SELECT * FROM Users WHERE name = ?", (data['name'],)).fetchone()
    if existing_name:
        return jsonify({'error': 'Name already exists'}), 400

    try:
        # Создаем нового пользователя
        cursor.execute(
            "INSERT INTO Users (name, email, password) VALUES (?, ?, ?)",
            (data['name'], data['email'], data['password'])
        )
        user_id = cursor.lastrowid  # Получаем ID нового пользователя

        # Автоматически создаем профиль фрилансера
        cursor.execute(
            "INSERT INTO Freelancers (user_id, skills, description) VALUES (?, ?, ?)",
            (user_id, "New Freelancer", "This is a new freelancer profile.")
        )
        conn.commit()

        return jsonify({'status': 'User and freelancer profile created successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Internal Server Error'}), 500
    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500


# API: вход пользователя
@user_routes.route('/api/login', methods=['POST'])
def login_user():
    data = request.json
    conn = connect_db()
    cursor = conn.cursor()
    user = cursor.execute(
        "SELECT * FROM Users WHERE email = ? AND password = ?",
        (data['email'], data['password'])
    ).fetchone()
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        return jsonify({'status': 'Login successful', 'redirect': '/'}), 200  # Здесь важен redirect
    else:
        return jsonify({'error': 'Invalid credentials'}), 401


@user_routes.route('/api/current-user', methods=['GET'])
def get_current_user():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'user_name': session.get('user_name')})
    return jsonify({'logged_in': False})

@user_routes.route('/api/profile', methods=['GET'])
def get_user_profile():
    if 'user_id' in session:
        conn = connect_db()
        cursor = conn.cursor()
        user_id = session['user_id']
        profile = cursor.execute("""
            SELECT Freelancers.id AS freelancer_id, Users.name, Freelancers.skills, Freelancers.description, Freelancers.profile_picture
            FROM Freelancers
            JOIN Users ON Freelancers.user_id = Users.id
            WHERE Users.id = ?
        """, (user_id,)).fetchone()

        if profile:
            return jsonify(dict(profile)), 200
        return jsonify({'error': 'Profile not found'}), 404

    return jsonify({'error': 'Not logged in'}), 401


