from flask import Flask, render_template, request, jsonify
from datetime import datetime
import db
import config

app = Flask(__name__)
app.config.from_object(config.Config)

# Initialize database
db.init_db()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# API Endpoints
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = db.get_all_tasks()

    return jsonify(tasks)


@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_single_task(task_id):
    try:
        task = db.get_task(task_id)
        if task:
            return jsonify(task)
        return jsonify({"error": "Task not found"}), 404
    except Exception as e:
        print(f"Error in get_single_task: {str(e)}")
        return jsonify({"error": "Server error"}), 500

@app.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    task_id = db.create_task(
        title=data['title'],
        description=data['description'],
        due_date=data['due_date'],
        assignee=data['assignee']
    )
    return jsonify({'id': task_id}), 201

@app.route('/api/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    data = request.get_json()
    db.update_task(
        task_id=id,
        title=data.get('title'),
        description=data.get('description'),
        due_date=data.get('due_date'),
        assignee=data.get('assignee'),
        status=data.get('status')
    )
    return jsonify({'message': 'Task updated'}), 200

@app.route('/api/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    db.delete_task(id)
    return jsonify({'message': 'Task deleted'}), 200

if __name__ == '__main__':
    app.run(debug=True)
