
from flask import Flask, request, jsonify, render_template
import mysql.connector
from storagemgmtserv import StorageMgmtServ
from idntyaccmgmtserv import IdentityAccessManagementService
from usagemntrserv import UsageMonitorService
from viewgeneratorserv import ViewGeneratorService
from werkzeug.utils import secure_filename
from flask import session

import os

import logging

logging.basicConfig(filename='application.log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')




app = Flask(__name__)
app.secret_key = '0492325ebca2094b1df9a58947be957c'
# Database connection parameters
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'osintRoot@786',
    'database': 'aws_cloud'
}

def get_db_connection():
    connection = mysql.connector.connect(**db_config)
    return connection

@app.route('/')
def index():
    # Serve the main page
    return render_template('index.html')

# def get_authenticated_user_id():
#     """Retrieves the authenticated user's ID from the session."""
#     return session.get('user_id')
def get_authenticated_user_id():
    """Retrieves the authenticated user's ID from the session."""
    return session.get('user_id')

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user_id from session
    return jsonify({'message': 'User logged out successfully'})


@app.route('/protected-resource')
def protected_resource():
    user_id = get_authenticated_user_id()
    if user_id is None:
        return jsonify({'error': 'Unauthorized'}), 401
    # Proceed with handling the request knowing `user_id` is the authenticated user's ID
    return jsonify({'message': 'Access granted to protected resource'})




@app.route('/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    user_id = get_authenticated_user_id()
    if user_id is None:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First, check if the file belongs to the user
    cursor.execute("SELECT * FROM files WHERE id = %s AND user_id = %s", (file_id, user_id))
    file = cursor.fetchone()
    if file is None:
        return jsonify({'error': 'File not found or access denied'}), 404

    # If file belongs to user, proceed to delete
    cursor.execute("DELETE FROM files WHERE id = %s", (file_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': 'File deleted successfully'})


@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')  # Directly use the password without hashing
    
    # Insert into database
    try:
        IdentityAccessManagementService.signup(username, email, password)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    return jsonify({"message": "User registered successfully", "status": "success"}), 201



@app.route('/signin', methods=['POST'])
def signin():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    try:
        user_id, is_successful = IdentityAccessManagementService.signin(username, password)
        if is_successful:
            # Optionally, store the user_id in the session or use it as needed
            session['user_id'] = user_id
            
            # Return JSON including user ID with message and redirect information
            return jsonify({"message": "User signed in successfully", "user_id": user_id, "redirect": "/upload-page"})
        else:
            return jsonify({"message": "Invalid username or password"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/upload-page')
def upload_page():
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    user_id = get_authenticated_user_id()
    if user_id is None:
        return jsonify({'error': 'Unauthorized'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if not StorageMgmtServ.check_storage_limit(user_id, file_size):
        return jsonify({'error': 'Storage limit exceeded'}), 400

    if not UsageMonitorService.check_daily_bandwidth(user_id):
        return jsonify({'error': '25MB daily bandwidth limit reached'}), 400
    
    if not StorageMgmtServ.check_storage_limit(user_id, file_size):
        return jsonify({'error': 'Storage limit exceeded'}), 400
    
    filename = secure_filename(file.filename)
    file_path = os.path.join('Users_data', filename)
    
    file.save(file_path)  # Save file to disk
    
    # Update storage usage and log the usage
    StorageMgmtServ.update_storage_usage(user_id, file_size)
    UsageMonitorService.track_usage(user_id, file_size)
    
    # Implement a function in StorageMgmtServ to save file metadata
    StorageMgmtServ.save_file_info(user_id, filename, file_size, file_path)
    
    return jsonify({'message': 'File uploaded successfully'}), 201
@app.route('/files', methods=['GET'])
def list_files():
    user_id = get_authenticated_user_id()  # Implement this function based on your authentication
    if user_id is None:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()  # Your function to establish a DB connection
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, filename, filesize, upload_date FROM files WHERE user_id = %s", (user_id,))
    files = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(files)

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='0.0.0.0',port=5000)
