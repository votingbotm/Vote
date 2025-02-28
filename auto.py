import os
import base64
import requests
import time
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import threading

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7469236370:AAH0_dD-7ZjdbepID5z2YhKjY_FpSX6K6Qg"

# GitHub Credentials
GIT_TOKEN = os.getenv("GH_TOKEN")  # GitHub token stored in Heroku environment
GIT_USERNAME = "Votingbotm"
GIT_REPO = "Vote"
GIT_API_URL = "https://api.github.com"
GIT_BRANCH = "main"

if not GIT_TOKEN:
    raise ValueError("❌ GitHub token is missing in environment variables!")

# Function to upload a file to GitHub
def upload_to_github(file_path, github_path):
    """Uploads a file (SQLite DB) to GitHub using the API."""
    
    url = f"{GIT_API_URL}/repos/{GIT_USERNAME}/{GIT_REPO}/contents/{github_path}"
    headers = {"Authorization": f"token {GIT_TOKEN}", "Accept": "application/vnd.github.v3+json"}

    # Read the file and encode it as Base64
    try:
        with open(file_path, "rb") as file:
            content = base64.b64encode(file.read()).decode("utf-8")
    except FileNotFoundError:
        print(f"⚠ File not found: {file_path}")
        return None

    # Get the latest SHA of the file (required for updating an existing file)
    response = requests.get(url, headers=headers)
    sha = None
    if response.status_code == 200:  # File exists, get SHA
        sha = response.json().get("sha")

    # Prepare commit data
    commit_message = f"📦 Auto Backup: {os.path.basename(file_path)} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    data = {
        "message": commit_message,
        "content": content,
        "branch": GIT_BRANCH
    }
    if sha:
        data["sha"] = sha  # Required for updating an existing file

    # Upload file to GitHub
    upload_response = requests.put(url, json=data, headers=headers)
    
    if upload_response.status_code in [200, 201]:
        print(f"✅ Successfully uploaded {file_path} to GitHub.")
        return upload_response.json()
    else:
        print(f"❌ Upload failed for {file_path}: {upload_response.json()}")
        return None

# Function to backup database files
def backup_databases():
    """Backs up both SQLite database files to GitHub."""
    files_to_backup = {
        "vote_bot.db": "vote_bot.db",
        "bot_main.db": "bot_main.db"
    }
    
    for local_path, github_path in files_to_backup.items():
        upload_to_github(local_path, github_path)

# Auto backup function with initial 1-hour delay
def auto_backup():
    """Waits for 1 hour before starting, then backs up every 1 hour."""
    print("🕒 Waiting 6 hour before first commit...")
    time.sleep(21600)  # Wait for 1 hour

    while True:
        print("🔄 Running backup...")
        backup_databases()
        time.sleep(21600)  # Wait for 1 hour before the next commit

# Telegram command to manually trigger backup
async def backup_command(update: Update, context: CallbackContext):
    """Telegram command to manually trigger backup."""
    await update.message.reply_text("⏳ Backing up database files...")

    backup_databases()
    await update.message.reply_text("✅ Database backup completed!")

# Setup Telegram bot
async def bash_command(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Usage: /bash <command>")
        return
    
    command = " ".join(context.args)  # Join arguments into a single command
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        output = result.stdout if result.stdout else result.stderr
    except Exception as e:
        output = str(e)
    
    # Ensure output is within Telegram's message limit
    if len(output) > 4000:
        output = output[:4000] + "\n\n[Output Truncated]"
    
    await update.message.reply_text(f"```\n{output}\n```", parse_mode="Markdown")
import os
import glob
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

async def upload_files(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Usage: /ul <filename_pattern>\nExample: /ul vote_bot*")
        return
    
    pattern = " ".join(context.args)  # Get the pattern from user input
    files = glob.glob(pattern)  # Find matching files
    
    if not files:
        await update.message.reply_text("No matching files found.")
        return

    for file_path in files:
        if os.path.isfile(file_path):
            try:
                await update.message.reply_document(document=open(file_path, "rb"))
            except Exception as e:
                await update.message.reply_text(f"Error uploading {file_path}: {str(e)}")

app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("backup", backup_command)) 
app.add_handler(CommandHandler("bash", bash_command))
app.add_handler(CommandHandler("ul", upload_files))# Telegram command: /backup

# Start auto backup in a separate thread
threading.Thread(target=auto_backup, daemon=True).start()

# Run the bot
app.run_polling()
