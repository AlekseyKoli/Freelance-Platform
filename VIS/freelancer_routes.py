from flask import Blueprint, jsonify, request, session, send_from_directory
import sqlite3
import os
from flask_cors import CORS
from flask_session import Session
from werkzeug.utils import secure_filename
import uuid
import os


freelancer_routes = Blueprint('freelancer_routes', __name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DATABASE = 'freelance_platform.db'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def connect_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@freelancer_routes.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@freelancer_routes.route('/api/freelancers/<int:id>', methods=['GET', 'PUT'])
def manage_freelancer(id):
    conn = connect_db()
    cursor = conn.cursor()

    # Получить профиль фрилансера
    if request.method == 'GET':
        freelancer = cursor.execute("""
            SELECT Freelancers.id, Users.name, Freelancers.skills, Freelancers.description, Freelancers.profile_picture, Freelancers.user_id
            FROM Freelancers
            JOIN Users ON Freelancers.user_id = Users.id
            WHERE Freelancers.id = ?
        """, (id,)).fetchone()

        if freelancer:
            return jsonify(dict(freelancer))
        return jsonify({'error': 'Freelancer not found'}), 404

    # Обновить профиль фрилансера
    if request.method == 'PUT':
        if session.get('user_id') != cursor.execute(
            "SELECT user_id FROM Freelancers WHERE id = ?", (id,)
        ).fetchone()['user_id']:
            return jsonify({'error': 'Access denied'}), 403

        data = request.form  # Получаем текстовые данные
        file = request.files.get('file')  # Получаем файл (если есть)
        profile_picture_path = None

        # Если файл есть, сохраняем его, иначе оставляем старое фото
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            profile_picture_path = os.path.join(UPLOAD_FOLDER, f"profile_{id}_{filename}")
            file.save(profile_picture_path)
        else:
            # Если нового файла нет, оставляем старое фото
            profile_picture_path = cursor.execute("""
                SELECT profile_picture FROM Freelancers WHERE id = ?
            """, (id,)).fetchone()['profile_picture']

        # Обновляем информацию о фрилансере
        cursor.execute("""
            UPDATE Freelancers 
            SET skills = ?, description = ?, profile_picture = ?
            WHERE id = ?
        """, (data['skills'], data['description'], profile_picture_path, id))
        conn.commit()

        return jsonify({'status': 'Freelancer profile updated successfully'}), 200

    
@freelancer_routes.route('/api/freelancers', methods=['GET'])
def get_freelancers():
    conn = connect_db()
    cursor = conn.cursor()
    freelancers = cursor.execute("""
        SELECT Freelancers.id, Users.name, Freelancers.skills, Freelancers.description, Freelancers.profile_picture, Users.id AS user_id
        FROM Freelancers
        JOIN Users ON Freelancers.user_id = Users.id
    """).fetchall()

    current_user_id = session.get('user_id')  # ID текущего пользователя из сессии
    response = {
        'current_user_id': current_user_id,
        'freelancers': [dict(row) for row in freelancers]
    }
    return jsonify(response)

@freelancer_routes.route('/api/upload-profile-picture', methods=['POST'])
def upload_profile_picture():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        user_id = session['user_id']
        filepath = os.path.join(UPLOAD_FOLDER, f"profile_{user_id}_{filename}")
        file.save(filepath)

        # Обновляем путь в базе данных
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Freelancers SET profile_picture = ? WHERE user_id = ?
        """, (f"/uploads/{filename}", user_id))
        conn.commit()

        return jsonify({'status': 'Profile picture updated successfully', 'url': f'/uploads/{filename}'}), 200
    return jsonify({'error': 'Invalid file type'}), 400

@freelancer_routes.route('/api/applications', methods=['POST'])
def create_application():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.json
    project_id = data.get('project_id')
    proposal = data.get('proposal')

    # Получаем ID фрилансера, связанного с текущим пользователем
    conn = connect_db()
    cursor = conn.cursor()
    freelancer = cursor.execute("""
        SELECT id FROM Freelancers WHERE user_id = ?
    """, (session['user_id'],)).fetchone()

    if not freelancer:
        return jsonify({'error': 'Freelancer profile not found'}), 404

    freelancer_id = freelancer['id']

    # Создание заявки
    cursor.execute("""
        INSERT INTO Applications (project_id, freelancer_id, proposal)
        VALUES (?, ?, ?)
    """, (project_id, freelancer_id, proposal))
    conn.commit()

    return jsonify({'status': 'Application created successfully'}), 201
