from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from user_routes import user_routes
from freelancer_routes import freelancer_routes
from flask_cors import CORS
from flask import session
from flask_session import Session
from flask import send_from_directory
from flask_migrate import Migrate
from freelancer_routes import freelancer_routes
from user_routes import connect_db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess
import xml.etree.ElementTree as ET
import sqlite3


app = Flask(__name__)
CORS(app)
CORS(app, resources={r"/*": {"origins": "*"}})
# Настройка сессий
app.config['SECRET_KEY'] = 'aleksey'  # Укажите секретный ключ
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///freelance_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
Session(app)

# Регистрация Blueprints
app.register_blueprint(user_routes)
app.register_blueprint(freelancer_routes)


# Главная страница
@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('profile.html')  # Страница с профилем
    return render_template('index.html')  # Страница с регистрацией

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

@app.route('/freelancers')
def freelancers():
    return render_template('freelancers.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/freelancer-profile')
def freelancer_profile():
    return render_template('freelancer-profile.html')

@app.route('/project-profile')
def project_profile():
    return render_template('project-profile.html')



@app.route('/api/freelancers', methods=['GET', 'POST'])
def manage_freelancers():
    conn = connect_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute(
            "INSERT INTO Freelancers (user_id, skills, description) VALUES (?, ?, ?)",
            (data['user_id'], data['skills'], data['description'])
        )
        conn.commit()
        return jsonify({'status': 'Freelancer added successfully'}), 201
    else:
        freelancers = cursor.execute("SELECT * FROM Freelancers").fetchall()
        return jsonify([dict(row) for row in freelancers])
@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.json
    conn = connect_db()
    cursor = conn.cursor()
    user = cursor.execute(
        "SELECT * FROM Users WHERE email = ? AND password = ?",
        (data['email'], data['password'])
    ).fetchone()

    if user:
        session['user_id'] = user['id']  # Сохраняем ID пользователя в сессии
        session['user_name'] = user['name']  # Сохраняем имя пользователя в сессии
        return jsonify({'status': 'Login successful', 'user': {'id': user[0], 'name': user[1]}}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/logout', methods=['POST'])
def logout_user():
    session.clear()  # Очистка сессии
    return jsonify({'status': 'Logged out successfully'}), 200

@app.route('/edit-freelancer')
def edit_freelancer():
    return render_template('edit-freelancer.html')

@app.route('/api/projects', methods=['POST'])
def create_project():
    try:
        data = request.json
        print("Received data:", data)  # Лог входных данных
        title = data.get('title')
        description = data.get('description')
        budget = data.get('budget')
        required_skills = ','.join(data.get('required_skills', []))

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Projects (title, description, budget, required_skills)
            VALUES (?, ?, ?, ?)
        """, (title, description, budget, required_skills))
        conn.commit()

        return jsonify({'status': 'Project created successfully'}), 201
    except Exception as e:
        print("Error:", e)  # Логирование ошибки
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

@app.route('/api/projects', methods=['GET', 'POST'])
def manage_projects():
    if request.method == 'GET':
        # Получение списка проектов
        conn = connect_db()
        cursor = conn.cursor()
        projects = cursor.execute("SELECT * FROM Projects").fetchall()
        return jsonify([dict(row) for row in projects]), 200

    elif request.method == 'POST':
        # Создание нового проекта
        try:
            data = request.json
            title = data.get('title')
            description = data.get('description')
            budget = data.get('budget')
            required_skills = ','.join(data.get('required_skills', []))

            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Projects (title, description, budget, required_skills)
                VALUES (?, ?, ?, ?)
            """, (title, description, budget, required_skills))
            conn.commit()

            return jsonify({'status': 'Project created successfully'}), 201
        except Exception as e:
            return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500
        
@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    conn = connect_db()
    cursor = conn.cursor()
    project = cursor.execute("""
        SELECT id, title, description, budget, required_skills
        FROM Projects
        WHERE id = ?
    """, (project_id,)).fetchone()

    if project:
        # Преобразуем данные в словарь и возвращаем
        project_dict = dict(project)
        project_dict['required_skills'] = project_dict['required_skills'].split(',')  # Преобразуем строку в список
        return jsonify(project_dict), 200
    else:
        return jsonify({'error': 'Project not found'}), 404

@app.route('/send-message', methods=['POST'])
def send_message():
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        message = data.get('message')

        # Команда отправки письма
        command = f"echo '{message}' | mail -s 'Message from {name}' freelanceplatfrom@gmail.com"
        subprocess.run(command, shell=True, check=True)

        return jsonify({'status': 'Message sent successfully!'}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Failed to send message.', 'details': str(e)}), 500
    
@app.route('/api/submit-application', methods=['POST'])
def submit_application():
    project_id = request.json.get('project_id')
    freelancer_id = request.json.get('freelancer_id')
    proposal = request.json.get('proposal')
    profile_picture = request.json.get('profile_picture')  # Это можно передать как URL или путь к файлу

    if not project_id or not freelancer_id or not proposal:
        return jsonify({'error': 'Missing required fields'}), 400

    # Сохранение данных в базе
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Applications (project_id, freelancer_id, profile_picture, proposal)
        VALUES (?, ?, ?, ?)
    """, (project_id, freelancer_id, profile_picture, proposal))
    conn.commit()

    return jsonify({'status': 'Application submitted successfully'}), 201

@app.route('/api/projects/<int:project_id>/applications', methods=['GET'])
def get_applications_for_project(project_id):
    conn = connect_db()
    cursor = conn.cursor()
    applications = cursor.execute("""
        SELECT Applications.id, Applications.proposal, Applications.profile_picture, Freelancers.name
        FROM Applications
        JOIN Freelancers ON Applications.freelancer_id = Freelancers.id
        WHERE Applications.project_id = ?
    """, (project_id,)).fetchall()

    # Преобразуем результаты в список словарей
    result = []
    for app in applications:
        result.append({
            'id': app[0],
            'proposal': app[1],
            'profile_picture': app[2],
            'freelancer_name': app[3]
        })

    return jsonify(result), 200

@app.route('/api/applications', methods=['GET'])
def get_applications():
    conn = connect_db()
    cursor = conn.cursor()
    applications = cursor.execute("SELECT * FROM Applications").fetchall()
    return jsonify([dict(row) for row in applications]), 200

@app.route('/api/current-user', methods=['GET'])
def get_current_user():
    if 'user_id' in session:
        conn = connect_db()
        cursor = conn.cursor()
        user = cursor.execute("SELECT * FROM Users WHERE id = ?", (session['user_id'],)).fetchone()
        if user:
            return jsonify({'logged_in': True, 'user': {'id': user[0], 'name': user[1]}}), 200
    return jsonify({'logged_in': False}), 200

def save_to_xml(project_id, title, description, budget, skills):
    try:
        root = ET.Element("Projects")
        project = ET.SubElement(root, "Project", id=str(project_id))
        ET.SubElement(project, "Title").text = title
        ET.SubElement(project, "Description").text = description
        ET.SubElement(project, "Budget").text = budget
        ET.SubElement(project, "Skills").text = ",".join(skills)

        tree = ET.ElementTree(root)
        tree.write("projects.xml")  # Имя файла для сохранения
        print("XML файл успешно сохранён как projects.xml")
    except Exception as e:
        print(f"Ошибка при сохранении XML: {e}")



def read_from_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    for project in root.findall("Project"):
        print(project.find("Title").text)

def export_projects_to_xml(db_path, xml_path):
    # Подключаемся к SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Извлекаем данные из таблицы Projects
    cursor.execute("SELECT id, title, description, budget, required_skills FROM Projects")
    projects = cursor.fetchall()

    # Создаём корневой элемент XML
    root = ET.Element("Projects")

    # Добавляем проекты в XML
    for project in projects:
        project_element = ET.SubElement(root, "Project", id=str(project[0]))
        ET.SubElement(project_element, "Title").text = project[1]
        ET.SubElement(project_element, "Description").text = project[2]
        ET.SubElement(project_element, "Budget").text = project[3] if project[3] else "N/A"
        ET.SubElement(project_element, "Skills").text = project[4] if project[4] else "None"

    # Сохраняем XML в файл
    tree = ET.ElementTree(root)
    tree.write(xml_path)
    print(f"Данные успешно экспортированы в {xml_path}")

# Используем функцию
export_projects_to_xml("freelance_platform.db", "projects.xml")

if __name__ == '__main__':
    app.run(debug=True)
