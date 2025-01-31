import os
import subprocess
from datetime import datetime
import threading
import requests
from collections import deque

# Securely retrieve the GitHub token from environment variables
GIT_TOKEN = "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"
GIT_USERNAME = "Votingbotm"
GIT_REPO = "Vote"

# Retrieve bot token and channel ID from environment variables
TOKEN = "7469236370:AAH0_dD-7ZjdbepID5z2YhKjY_FpSX6K6Qg" # Replace 'your_bot_api_key' with default or use environment variable
CHANNEL_ID = "-1002291896465"# Replace with your channel ID or use environment variable
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# Get the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(SCRIPT_DIR, "main.py")

# A deque to hold the recent logs (keeping the last 500 characters)
log_buffer = deque(maxlen=500)

def log_message(message):
    """Adds log message with timestamp to the buffer and sends to Telegram if new."""
    timestamped_message = f"[{datetime.now()}] {message}"
    log_buffer.append(timestamped_message)
    print(timestamped_message)  # Print to the console as well for local logging
    send_new_logs_to_telegram()  # Send logs to Telegram whenever new logs are added

def send_new_logs_to_telegram():
    """Sends only new logs to the Telegram channel"""
    if log_buffer:
        # Get the latest log message
        latest_log = log_buffer[-1]

        # Send the latest log to Telegram
        payload = {
            'chat_id': CHANNEL_ID,
            'text': latest_log
        }
        response = requests.post(TELEGRAM_API_URL, data=payload)
        if response.status_code != 200:
            log_message(f"Failed to send logs to Telegram. Status code: {response.status_code}")
        else:
            log_message("Sent new log to Telegram successfully.")

def send_main_code_to_telegram():
    """Sends the content of main.py to the Telegram channel"""
    try:
        with open(MAIN_SCRIPT, "r") as file:
            main_code = file.read()
        
        # Send the content in chunks if it is too large for a single message
        max_message_length = 4096  # Telegram message limit
        for i in range(0, len(main_code), max_message_length):
            chunk = main_code[i:i + max_message_length]
            payload = {
                'chat_id': CHANNEL_ID,
                'text': chunk
            }
            response = requests.post(TELEGRAM_API_URL, data=payload)
            if response.status_code != 200:
                log_message(f"Failed to send main.py content to Telegram. Status code: {response.status_code}")
            else:
                log_message(f"Sent main.py content to Telegram successfully.")
    except Exception as e:
        log_message(f"Error reading or sending main.py: {e}")

def run_main():
    """Continuously runs main.py and logs output"""
    while True:
        if os.path.exists(MAIN_SCRIPT):
            log_message("Starting main.py...")
            process = subprocess.Popen(["python3", MAIN_SCRIPT], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Log main.py output in real-time
            for line in process.stdout:
                log_message(f"[main.py] {line.strip()}")
            
            for line in process.stderr:
                log_message(f"[main.py ERROR] {line.strip()}")

            process.wait()
            log_message("main.py stopped, restarting in 5 seconds...")

        else:
            log_message("main.py not found in repository.")
        
        time.sleep(5)  # Restart after 5 seconds

def git_push():
    """Commit and push changes using a GitHub token and log output"""
    if not GIT_TOKEN:
        log_message("Error: GitHub token is missing. Set it using 'export GITHUB_TOKEN=your_token'")
        return

    try:
        os.chdir(SCRIPT_DIR)
        remote_url = f"https://{GIT_USERNAME}:{GIT_TOKEN}@github.com/{GIT_USERNAME}/{GIT_REPO}.git"
        os.system("git remote set-url origin " + remote_url)
        
        log_message("Adding changes to Git...")
        os.system("git add .")
        
        commit_message = f"Auto commit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        os.system(f'git commit -m "{commit_message}"')

        log_message("Pushing to GitHub...")
        os.system("git push origin main")  # Change 'main' if using another branch
        
        log_message("Changes pushed successfully!")

    except Exception as e:
        log_message(f"Error: {e}")

# Run main.py in a separate thread
threading.Thread(target=run_main, daemon=True).start()

# Send the content of main.py to Telegram at the start
send_main_code_to_telegram()

# Schedule auto Git push every hour
schedule.every(1).hours.do(git_push)

log_message(f"Git auto-push script running in {SCRIPT_DIR} with main.py...")

# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(1)  # Check every second
                
