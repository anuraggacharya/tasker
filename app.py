from flask import Flask, render_template, request, jsonify,Blueprint,g
from datetime import datetime
import db
import config
from middleware import token_required
protected_bp = Blueprint('protected', __name__)
from flask_cors import CORS, cross_origin
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(config.Config)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://127.0.0.1:5001",'"http://localhost:5001"'],
        "methods": ["GET", "POST", "PUT", "DELETE",'OPTIONS'],
        "allow_headers":["Content-Type", "Authorization"],
        "supports_credentials": True,
        "expose_headers": ["Authorization"]
    }
})
# Initialize database
db.init_db()


# @app.after_request
# def after_request(response):
#     # Ensure responses to credentialed requests don't use wildcard
#     if request.headers.get('Origin') and request.headers.get('Origin') in [
#         "http://127.0.0.1:5001",
#         "http://localhost:5001"
#     ]:
#         response.headers.add('Access-Control-Allow-Origin', request.headers['Origin'])
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#     return response

# Route
#
#
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    required_fields = ['username', 'email', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    if len(data['password']) < 8:
        return jsonify({'message': 'Password must be at least 8 characters'}), 400

    registration_status= db.register_user(data)
    return registration_status


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    auth_token= db.check_creds(data)
    return auth_token


@app.route('/')
def auth_home():
    return render_template('auth.html')


@app.route('/dashboard',methods=['POST',])
@cross_origin(origin='http://127.0.0.1:5001',headers=['Authorization', 'Content-Type'],supports_credentials=True)
@token_required
def index():

    return render_template('index.html',username=g.current_user['username'])

# API Endpoints
@app.route('/api/tasks', methods=['GET'])
@cross_origin(origin='http://127.0.0.1:5001',headers=['Authorization', 'Content-Type'],supports_credentials=True)
@token_required
def get_tasks():
    tasks = db.get_all_tasks()
    return jsonify(tasks)


@app.route('/api/tasks/<int:task_id>', methods=['GET'])
@token_required
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
@token_required
#@roles_required('admin')
def create_task():
    data = request.get_json()
    print("this isdata",data)
    data = {k: (v if v != '' else None) for k, v in data.items()}
    task_id = db.create_task(
        title=data['title'],
        description=data['description'],
        uc_name = data['uc_name'],
        due_date=data['due_date'],
        assignee=data['assignee'],
        start_date=data['task_start_date'],
        close_date = data['task_close_date'],
        task_class = data['task_class'],

    )
    return jsonify({'id': task_id}), 201

@app.route('/api/tasks/<int:id>', methods=['PUT'])
@token_required
def update_task(id):
    data = request.get_json()
    print(data)
    data = {k: (v if v != '' else None) for k, v in data.items()}
    db.update_task(
        task_id=id,
        title=data.get('title'),
        uc_name = data.get('uc_name'),
        description=data.get('description'),
        due_date=data.get('due_date'),
        assignee=data.get('assignee'),
        status=data.get('status'),
        start_date=data.get('task_start_date'),
        close_date = data.get('task_close_date'),
        task_class = data.get('task_class'),
    )
    return jsonify({'message': 'Task updated'}), 200

@app.route('/api/tasks/<int:id>', methods=['DELETE'])
@token_required
def delete_task(id):
    db.delete_task(id)
    return jsonify({'message': 'Task deleted'}), 200


@app.route('/api/dashboard/metrics')
def get_dashboard_metrics():
    try:
        metrics = {}

        # 1. Completion Rate
        completion = db.get_completion_metrics()
        metrics['completion_rate'] = {
            'completed': completion['completed_tasks'],
            'total': completion['total_tasks'],
            'percentage': round((completion['completed_tasks'] / completion['total_tasks']) * 100, 2)
                         if completion['total_tasks'] > 0 else 0
        }

        # 2. On-Time Delivery
        on_time = db.get_ontime_delivery_metrics()
        metrics['on_time_delivery'] = {
            'on_time': on_time['on_time'],
            'total': on_time['total_completed'],
            'percentage': round((on_time['on_time'] / on_time['total_completed']) * 100, 2)
                         if on_time['total_completed'] > 0 else 0
        }

        # 3. Task Aging
        metrics['avg_completion_time'] = db.get_avg_completion_time()

        # 4. Workload Distribution
        metrics['workload'] = db.get_workload_distribution()

        # 5. Status Distribution
        metrics['status_distribution'] = db.get_status_distribution()

        # 6. Overdue Tasks
        metrics['overdue_tasks'] = db.get_overdue_tasks()

        return jsonify(metrics)

    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        return jsonify({"error": "Failed to load dashboard metrics"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
