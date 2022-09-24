from flask import Flask, request
from json import dump, load
import base64
import os
from datetime import datetime
import pytest


BASE_TARGET_FOLDER = 'tmp'
PYTEST_ASSESSMENT_FOLDER = 'python-assessment'
MAX_ATTEMPTS = 45

def validate_user_directory(key):
    target_folder = os.path.join(
        BASE_TARGET_FOLDER,
        key.split('/')[0]
    )    
    if not os.path.isdir(target_folder):
        os.mkdir(target_folder)


def validate_attempt(key, email_address):
    path_attempt_file = os.path.join(
        BASE_TARGET_FOLDER,
        key.split('/')[0],
        'attempt.json'
    )
    data = {'attempt': 0, 'last_attempt': None, 'email_address': email_address}
    if os.path.isfile(path_attempt_file):
        with open(path_attempt_file, 'r') as f:
            data = load(f)

    if int(data['attempt']) > MAX_ATTEMPTS:
        raise Exception('Too many attempts')
    attempts = int(data['attempt'])

    data['attempt'] = attempts + 1
    data['last_attempt'] = datetime.now().strftime("%Y%m%d_%H%M%S")

    with open(path_attempt_file, 'w') as f:
        dump(data, f)
    return attempts, data['last_attempt']

def write(key, value):
    path_key = os.path.join(
        BASE_TARGET_FOLDER,
        key
    )
    target_folder = os.path.join(
        BASE_TARGET_FOLDER,
        *(key.split('/')[:-1])
    )
    if not os.path.isdir(target_folder):
        os.makedirs(target_folder)

    with open(path_key, "w", encoding='utf-8') as f:
        f.write(value)
app = Flask(__name__)

@app.route("/submit", methods=["POST"])
def submission():
    try:
        data = request.get_json()
        keys = data.keys()
        error = []
        if "email_address" not in keys:
            error.append('Email address required')
        if "python_basics.py" not in keys:
            error.append('Python file missing')
        if "sql_basics.py" not in keys:
            error.append('Python file missing')
        
        if len(error) > 0:
            return {
                "success": False, 
                "error": ", ".join(error)}
        
        email = data["email_address"]
        python = data["python_basics.py"]
        sql = data["sql_basics.py"]

        python = base64.b64decode(python).decode('utf-8')
        sql = base64.b64decode(sql).decode('utf-8')
        name = email.replace('@', '_').replace('.', '_')

        validate_user_directory(name)   
        attempts, last_attempt = validate_attempt(name, email)
        write(f"{name}/{attempts}/{last_attempt}/python_basics.py", python)
        write(f"{name}/{attempts}/{last_attempt}/sql_basics.py", sql)

        from subprocess import run
        try:
            result = run("pytest -p no:terminal", shell=True, cwd=PYTEST_ASSESSMENT_FOLDER, 
            text=True, capture_output=True)
            output = result.stdout
            output = output.rstrip().split(',')
            if len(output) == 2:
                passed, failed = map(int, output)
            else:
                failed = passed = None
        except Exception as e:
            return {
                "success": False, 
                "error": str(e)}
        
        return {"success": True, "passed": passed, "failed": failed}

    except Exception as e:
        return {"success": False, "error": str(e)}
