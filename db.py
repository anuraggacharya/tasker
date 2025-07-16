import mysql.connector
from flask import  jsonify
from config import Config
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from logging import debug



def get_db_connection():
    try:
        return mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        raise

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create tasks table if not exists
    cursor.execute("""
        CREATE TABLE if not exists
          `users` (
            `id` int NOT NULL AUTO_INCREMENT,
            `username` varchar(50) NOT NULL,
            `password` varchar(255) NOT NULL,
            `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            `email` varchar(255) NOT NULL,
            PRIMARY KEY (`id`),
            UNIQUE KEY `username` (`username`)
          ) ENGINE = InnoDB AUTO_INCREMENT = 2 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci
    """)

    cursor.execute("""
        CREATE TABLE if not exists
          `tasks` (
            `id` int NOT NULL AUTO_INCREMENT,
            `title` varchar(100) NOT NULL,
            `description` text,
            `uc_name` varchar(255) DEFAULT NULL,
            `created_date` datetime DEFAULT NULL,
            `due_date` date DEFAULT NULL,
            `assignee` varchar(100) DEFAULT NULL,
            `start_date` date DEFAULT NULL,
            `close_date` date DEFAULT NULL,
            `task_class` varchar(255) DEFAULT NULL,
            `status` varchar(20) DEFAULT NULL,
            PRIMARY KEY (`id`)
          ) ENGINE = InnoDB AUTO_INCREMENT = 15 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci
    """)

    conn.commit()
    cursor.close()
    conn.close()

def get_all_tasks():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT
        id,
        title,
        description,
        uc_name,
        DATE_FORMAT(created_date, '%Y-%m-%d %H:%i') as created_date,
        DATE_FORMAT(start_date, '%Y-%m-%d') as start_date,
        DATE_FORMAT(due_date, '%Y-%m-%d') as due_date,
        DATE_FORMAT(close_date, '%Y-%m-%d') as close_date,
        task_class,
        assignee,
        status
    FROM tasks
    ORDER BY created_date DESC
    """)

    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    return tasks

def create_task(title, description, due_date, assignee,start_date,close_date,task_class,uc_name, status='To Do'):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO tasks (title, description, due_date, assignee,start_date,close_date,task_class,uc_name, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (title, description, due_date, assignee, start_date, close_date, task_class,uc_name, status))

    task_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return task_id

def update_task(task_id, title=None, description=None, due_date=None, assignee=None,start_date=None,close_date=None,task_class=None,uc_name=None, status=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Build dynamic update query
    updates = []
    params = []

    if title is not None:
        updates.append("title = %s")
        params.append(title)
    if description is not None:
        updates.append("description = %s")
        params.append(description)
    if start_date is not None:
        updates.append("start_date = %s")
        params.append(start_date)
    if due_date is not None:
        updates.append("due_date = %s")
        params.append(due_date)
    if close_date is not None:
        updates.append("close_date = %s")
        params.append(close_date)
    if task_class is not None:
        updates.append("task_class = %s")
        params.append(task_class)
    if assignee is not None:
        updates.append("assignee = %s")
        params.append(assignee)
    if status is not None:
        updates.append("status = %s")
        params.append(status)
    if uc_name is not None:
        updates.append("uc_name = %s")
        params.append(uc_name)

    if updates:
        query = "UPDATE tasks SET " + ", ".join(updates) + " WHERE id = %s"
        params.append(task_id)
        cursor.execute(query, tuple(params))
        conn.commit()

    cursor.close()
    conn.close()

def delete_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()

    cursor.close()
    conn.close()


def get_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
        SELECT
            id,
            title,
            description,
            uc_name,
            DATE_FORMAT(created_date, '%Y-%m-%d %H:%i') as created_date,
            DATE_FORMAT(start_date, '%Y-%m-%d') as start_date,
            DATE_FORMAT(due_date, '%Y-%m-%d') as due_date,
            DATE_FORMAT(close_date, '%Y-%m-%d') as close_date,
            task_class,
            assignee,
            status
        FROM tasks
        WHERE id = %s
        """, (task_id,))

        task = cursor.fetchone()
        if task:
            # Replace None values with empty strings
            return {k: v if v is not None else "" for k, v in task.items()}
        return None
    except mysql.connector.Error as err:
        print(f"Database error in get_task: {err}")
        raise
    finally:
        cursor.close()
        conn.close()



def check_creds(data):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s",
                    (data['username'],))
        user = cursor.fetchone()

        if not user or not check_password_hash(user['password'], data['password']):
            return jsonify({'message': 'Invalid credentials'}), 401

        token = jwt.encode({
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'exp': datetime.utcnow() + timedelta(hours=1)
        },
        Config.SECRET_KEY,
        algorithm="HS256")

        return jsonify({'token': token,'user_id': user['id'],'username':user['username']})

    except Exception as e:
        print("Exception occured in login route:",str(e))
        return jsonify({'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()



def register_user(data):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if username or email already exists
        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s",
                        (data['username'], data['email']))
        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({'message': 'Username or email already exists'}), 400

        hashed_password = generate_password_hash(
            data['password'], method='sha256')

        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (data['username'], data['email'], hashed_password)
        )
        conn.commit()

        return jsonify({'message': 'User registered successfully'}), 201

    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()



# Dashboard-specific queries
import mysql.connector
from config import Config
from datetime import datetime

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        raise

def get_completion_metrics():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
        SELECT
            COUNT(*) as total_tasks,
            SUM(CASE WHEN status = 'Done' THEN 1 ELSE 0 END) as completed_tasks
        FROM tasks
        """)
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def get_ontime_delivery_metrics():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
        SELECT
            COUNT(*) as total_completed,
            SUM(CASE WHEN status = 'Done' AND
                (due_date IS NULL OR due_date >= created_date)
                THEN 1 ELSE 0 END) as on_time
        FROM tasks
        WHERE status = 'Done'
        """)
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def get_avg_completion_time():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
        SELECT
            AVG(DATEDIFF(NOW(), created_date)) as avg_days
        FROM tasks
        WHERE status = 'Done'
        """)
        result = cursor.fetchone()
        return round(result['avg_days'], 1) if result['avg_days'] else 0
    finally:
        cursor.close()
        conn.close()

def get_workload_distribution():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
        SELECT
            assignee,
            COUNT(*) as task_count,
            SUM(CASE WHEN status != 'Done' THEN 1 ELSE 0 END) as pending_tasks
        FROM tasks
        GROUP BY assignee
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_status_distribution():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
        SELECT
            status,
            COUNT(*) as count
        FROM tasks
        GROUP BY status
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_overdue_tasks():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
        SELECT
            id,
            title,
            assignee,
            due_date,
            DATEDIFF(NOW(), due_date) as days_overdue
        FROM tasks
        WHERE status != 'Done'
        AND due_date IS NOT NULL
        AND due_date < NOW()
        ORDER BY days_overdue DESC
        LIMIT 10
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
