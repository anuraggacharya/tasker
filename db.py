import mysql.connector

from config import Config

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
    CREATE TABLE IF NOT EXISTS tasks (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(100) NOT NULL,
        description TEXT,
        created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        due_date DATE,
        assignee VARCHAR(100),
        status VARCHAR(20) DEFAULT 'To Do'
    )
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
        DATE_FORMAT(created_date, '%Y-%m-%d %H:%i') as created_date,
        DATE_FORMAT(due_date, '%Y-%m-%d') as due_date,
        assignee,
        status
    FROM tasks
    ORDER BY created_date DESC
    """)

    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    return tasks

def create_task(title, description, due_date, assignee, status='To Do'):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO tasks (title, description, due_date, assignee, status)
    VALUES (%s, %s, %s, %s, %s)
    """, (title, description, due_date, assignee, status))

    task_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return task_id

def update_task(task_id, title=None, description=None, due_date=None, assignee=None, status=None):
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
    if due_date is not None:
        updates.append("due_date = %s")
        params.append(due_date)
    if assignee is not None:
        updates.append("assignee = %s")
        params.append(assignee)
    if status is not None:
        updates.append("status = %s")
        params.append(status)

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
            DATE_FORMAT(created_date, '%Y-%m-%d %H:%i') as created_date,
            DATE_FORMAT(due_date, '%Y-%m-%d') as due_date,
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
