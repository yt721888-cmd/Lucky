import os
import json
import time
import random
import requests
import threading
import sys
from datetime import datetime
from telebot import TeleBot, types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from http.server import HTTPServer, BaseHTTPRequestHandler

# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
ADMIN_IDS = [OWNER_ID]
PORT = int(os.environ.get("PORT", 10000))

if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN not set!")
    sys.exit(1)

if OWNER_ID == 0:
    print("❌ ERROR: OWNER_ID not set!")
    sys.exit(1)

print("✅ Bot token loaded!")
print(f"👑 Owner ID: {OWNER_ID}")

bot = TeleBot(BOT_TOKEN)

# ============================================================
# SIMPLE HTTP SERVER FOR RENDER HEALTH CHECKS
# ============================================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"✅ FF BAN BOT is running!")
    
    def log_message(self, format, *args):
        # Suppress logs to keep output clean
        pass

def run_http_server():
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
        print(f"✅ HTTP server running on port {PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"⚠️ HTTP server error: {e}")

# ============================================================
# FILES & DATA
# ============================================================
USERS_FILE = "users.json"
SETTINGS_FILE = "settings.json"
PENDING_FILE = "pending.json"

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    users = {
        str(OWNER_ID): {
            "id": OWNER_ID, 
            "username": "NEPHRON_NXT", 
            "name": "OWNER", 
            "joined": datetime.now().isoformat(),
            "unlimited": False,
            "banned": False,
            "ban_trials": 0,
            "num_trials": 0,
            "ban_paid": False,
            "ban_paid_used": 0,
            "approved": False
        }
    }
    save_users(users)
    return users

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def load_settings():
    default = {
        "price": 149,
        "num_price": 39,
        "ban_price": 15,
        "upi": "nephron-here@ptyes",
        "upi_qr": "https://quickchart.io/qr?text=upi://pay?pa=nephron-here@ptyes&am=149&cu=INR&size=300",
        "developer": "@NEPHRON_NXT",
        "support": "@NEPHRON_NXT",
        "welcome_image": "https://iili.io/C8DNTyQ.jpg",
        "token_link": "https://www.fftools.site/free-fire-token-generator"
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                for key, val in default.items():
                    if key not in data:
                        data[key] = val
                return data
        except:
            pass
    return default

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

def load_pending():
    if os.path.exists(PENDING_FILE):
        try:
            with open(PENDING_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_pending(pending):
    with open(PENDING_FILE, "w") as f:
        json.dump(pending, f, indent=2)

def register_user(user_id, username=None, first_name=None):
    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {
            "id": user_id,
            "username": username,
            "name": first_name or "Unknown",
            "joined": datetime.now().isoformat(),
            "unlimited": False,
            "banned": False,
            "ban_trials": 0,
            "num_trials": 0,
            "ban_paid": False,
            "ban_paid_used": 0,
            "approved": False
        }
        save_users(users)
        
        try:
            total_users = len(users)
            msg = f"""✅ NEW USER JOINED!

👤 Name: {first_name}
🆔 ID: {user_id}
👤 @{username or 'N/A'}
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Total Users: {total_users}"""
            bot.send_message(OWNER_ID, msg)
        except:
            pass
    
    return users[str(user_id)]

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_owner(user_id):
    return user_id == OWNER_ID

def get_user(user_id):
    users = load_users()
    return users.get(str(user_id), {})

def update_user(user_id, key, value):
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)][key] = value
        save_users(users)

# ============================================================
# QR CODE GENERATION
# ============================================================
def generate_qr(upi, amount):
    qr_data = f"upi://pay?pa={upi}&am={amount}&cu=INR"
    return f"https://quickchart.io/qr?text={qr_data}&size=300"

def send_payment_qr(chat_id, amount=149, service_type="UNLIMITED ACCESS"):
    try:
        settings = load_settings()
        upi = settings.get("upi", "nephron-here@ptyes")
        upi_qr = settings.get("upi_qr", generate_qr(upi, amount))
        developer = settings.get("developer", "@NEPHRON_NXT")
        
        payment_text = f"""
💎 PAYMENT FOR {service_type} 💎

UPI ID: `{upi}`
AMOUNT: Rs.{amount}

SCAN QR CODE TO PAY

PAY AND SEND SCREENSHOT 

FOR HELP - {developer}

👨‍💻 {developer}
"""
        
        keyboard = [
            [InlineKeyboardButton("✅ I HAVE PAID", callback_data=f"paid_{chat_id}_{amount}")],
            [InlineKeyboardButton("❌ CANCEL", callback_data="cancel_payment")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        
        try:
            bot.send_photo(chat_id, photo=upi_qr, caption=payment_text, reply_markup=markup, parse_mode='Markdown')
        except:
            bot.send_message(chat_id, payment_text, reply_markup=markup, parse_mode='Markdown')
            
    except Exception as e:
        print(f"❌ Payment QR error: {e}")
        settings = load_settings()
        bot.send_message(chat_id, f"💎 Pay Rs.{amount} to:\nUPI: {settings.get('upi', 'nephron-here@ptyes')}\n\nFOR HELP - {settings.get('developer', '@NEPHRON_NXT')}")

# ============================================================
# MENUS
# ============================================================
def get_user_menu():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row(KeyboardButton("🔥 BAN ACCOUNT"))
    markup.row(KeyboardButton("💎 UNLIMITED ACCESS"))
    markup.row(KeyboardButton("📊 UID TO INFO"))
    markup.row(KeyboardButton("🔑 HOW TO GET TOKEN"))
    markup.row(KeyboardButton("🆘 SUPPORT"), KeyboardButton("❓ HELP"))
    markup.row(KeyboardButton("ℹ️ ABOUT"))
    return markup

def get_admin_menu():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row(KeyboardButton("📊 STATS"), KeyboardButton("👥 USERS"))
    markup.row(KeyboardButton("💰 PRICE"), KeyboardButton("🏦 UPI"))
    markup.row(KeyboardButton("➕ ADD ADMIN"), KeyboardButton("📋 COMMANDS"))
    markup.row(KeyboardButton("👤 USERNAME"))
    return markup

# ============================================================
# START COMMAND
# ============================================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        
        settings = load_settings()
        price = settings.get("price", 149)
        developer = settings.get("developer", "@NEPHRON_NXT")
        
        user = register_user(user_id, username, first_name)
        
        if user.get("banned", False):
            bot.send_message(message.chat.id, "❌ You are banned from using this bot!")
            return
        
        users = load_users()
        total_users = len(users)
        
        ban_trials = user.get("ban_trials", 0)
        num_trials = user.get("num_trials", 0)
        ban_trials_left = 1 - ban_trials if ban_trials < 1 else 0
        num_trials_left = 3 - num_trials if num_trials < 3 else 0
        
        ban_paid = user.get("ban_paid", False)
        unlimited = user.get("unlimited", False)
        approved = user.get("approved", False)
        
        welcome_text = f"""
🌟 WELCOME TO FF BAN BOT 🌟

👋 User: {first_name}
🆔 ID: {user_id}
👤 @{username or 'N/A'}
👥 Total Users: {total_users}

📱 -----------------------

🔥 Ban any Free Fire account
💎 Unlimited access - Rs.{price}
📊 UID TO INFO - Get player details

🎁 YOUR FREE TRIALS:
• BAN ACCOUNT: {ban_trials_left} use{'s' if ban_trials_left != 1 else ''} left
• UID TO INFO: {num_trials_left} use{'s' if num_trials_left != 1 else ''} left

💳 PAID SERVICES:
• BAN ACCOUNT: {'✅ Active' if ban_paid else '❌ Inactive'}
• UNLIMITED ACCESS: {'✅ Active' if unlimited else '❌ Inactive'}
• APPROVED: {'✅ Yes' if approved else '❌ No'}

👨‍💻 Developer: {developer}
"""
        
        if is_admin(user_id):
            markup = get_admin_menu()
        else:
            markup = get_user_menu()
        
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
        
        if not is_admin(user_id):
            try:
                bot.send_message(OWNER_ID, f"🔄 User @{username or 'N/A'} started the bot\n🆔 ID: {user_id}\n👥 Total Users: {total_users}")
            except:
                pass
                
    except Exception as e:
        print(f"❌ Start error: {e}")

# ============================================================
# BAN ACCOUNT
# ============================================================
@bot.message_handler(func=lambda m: m.text and "BAN ACCOUNT" in m.text)
def ban_account_start(message):
    try:
        user_id = message.from_user.id
        user = get_user(user_id)
        
        if user.get("banned", False):
            bot.send_message(message.chat.id, "❌ You are banned!")
            return
        
        if user.get("unlimited", False):
            bot.send_message(message.chat.id, "✅ You have unlimited access! Send token to ban:")
            bot.register_next_step_handler(message, get_ban_token)
            return
        
        if user.get("ban_paid", False):
            bot.send_message(message.chat.id, "✅ You have paid ban access! Send token to ban:")
            bot.register_next_step_handler(message, get_ban_token)
            return
        
        ban_trials = user.get("ban_trials", 0)
        if ban_trials >= 1:
            bot.send_message(message.chat.id, "💳 Your free trial is over!\nPay Rs.15 for single ban access:")
            send_payment_qr(message.chat.id, 15, "BAN ACCESS (SINGLE USE)")
            return
        
        bot.send_message(message.chat.id, "🎁 FREE TRIAL AVAILABLE! (1 use)\nSend token to ban:")
        bot.register_next_step_handler(message, get_ban_token)
        
    except Exception as e:
        print(f"❌ Ban error: {e}")

def get_ban_token(message):
    try:
        user_id = message.from_user.id
        token = message.text.strip()
        
        if len(token) < 30:
            bot.send_message(message.chat.id, "❌ Invalid token! Send a valid access token.")
            return
        
        bot.send_message(message.chat.id, "⏳ Processing ban...")
        
        try:
            ban_success = False
            result_text = ""
            account_uid = "N/A"
            status = "UNKNOWN"
            account_name = "N/A"
            
            # Try multiple ban APIs
            try:
                url1 = f"https://ffidbanapi.vercel.app/ban-account?access-token={token}"
                response1 = requests.get(url1, timeout=30)
                if response1.status_code == 200:
                    data = response1.json()
                    if data:
                        account_uid = data.get('uid', 'N/A')
                        status = data.get('status', 'BANNED')
                        account_name = data.get('name', 'N/A')
                        result_text = f"""
🎯 BAN RESULT 🎯

👤 Name: {account_name}
🎮 UID: {account_uid}
📊 Status: {status}

👨‍💻 {load_settings().get('developer', '@NEPHRON_NXT')}
"""
                        ban_success = True
            except:
                pass
            
            if not ban_success:
                try:
                    url2 = f"https://ffbanapi.vercel.app/ban?token={token}"
                    response2 = requests.get(url2, timeout=30)
                    if response2.status_code == 200:
                        data = response2.json()
                        if data:
                            account_uid = data.get('uid', 'N/A')
                            status = data.get('status', 'BANNED')
                            account_name = data.get('name', 'N/A')
                            result_text = f"""
🎯 BAN RESULT 🎯

👤 Name: {account_name}
🎮 UID: {account_uid}
📊 Status: {status}

👨‍💻 {load_settings().get('developer', '@NEPHRON_NXT')}
"""
                            ban_success = True
                except:
                    pass
            
            if ban_success:
                bot.send_message(message.chat.id, result_text)
                
                users = load_users()
                if str(user_id) in users:
                    user_data = users[str(user_id)]
                    
                    if user_data.get("unlimited", False):
                        pass
                    elif user_data.get("ban_paid", False):
                        user_data["ban_paid_used"] = user_data.get("ban_paid_used", 0) + 1
                        if user_data["ban_paid_used"] >= 1:
                            user_data["ban_paid"] = False
                            user_data["ban_paid_used"] = 0
                            try:
                                bot.send_message(user_id, "📢 Your paid ban access has been used!\n\nTo use again, please pay Rs.15.")
                            except:
                                pass
                    elif user_data.get("ban_trials", 0) < 1:
                        user_data["ban_trials"] = user_data.get("ban_trials", 0) + 1
                    
                    save_users(users)
            else:
                bot.send_message(message.chat.id, "❌ Ban API failed. Please try again later.")
            
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error: {str(e)}")
    except Exception as e:
        print(f"❌ Get token error: {e}")

# ============================================================
# UNLIMITED ACCESS
# ============================================================
@bot.message_handler(func=lambda m: m.text and "UNLIMITED ACCESS" in m.text)
def unlimited_cmd(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if user.get("banned", False):
        bot.send_message(message.chat.id, "❌ You are banned!")
        return
    
    if user.get("unlimited", False):
        bot.send_message(message.chat.id, "✅ You already have unlimited access!")
        return
    
    send_payment_qr(message.chat.id, 149, "UNLIMITED ACCESS")

# ============================================================
# UID TO INFO - IMPROVED API WITH FALLBACK
# ============================================================
@bot.message_handler(func=lambda m: m.text and "UID TO INFO" in m.text)
def num_to_info_start(message):
    try:
        user_id = message.from_user.id
        user = get_user(user_id)
        
        if user.get("banned", False):
            bot.send_message(message.chat.id, "❌ You are banned!")
            return
        
        if user.get("unlimited", False):
            bot.send_message(message.chat.id, "✅ You have unlimited access! Send player UID:")
            bot.register_next_step_handler(message, process_num_to_info)
            return
        
        num_trials = user.get("num_trials", 0)
        if num_trials >= 3:
            bot.send_message(message.chat.id, "❌ You've used all 3 free trials!\n💎 Pay Rs.39 for UID TO INFO access")
            send_payment_qr(message.chat.id, 39, "UID TO INFO ACCESS")
            return
        
        remaining = 3 - num_trials
        bot.send_message(message.chat.id, f"🎁 FREE TRIAL AVAILABLE! ({remaining} uses left)\nSend player UID:")
        bot.register_next_step_handler(message, process_num_to_info)
        
    except Exception as e:
        print(f"❌ UID error: {e}")

def process_num_to_info(message):
    try:
        user_id = message.from_user.id
        uid_input = message.text.strip()
        
        if not uid_input.isdigit() or len(uid_input) < 8:
            bot.send_message(message.chat.id, "❌ Invalid UID! Send 8-10 digits.")
            return
        
        bot.send_message(message.chat.id, f"⏳ Fetching info for {uid_input}...")
        
        try:
            player_data = None
            data_source = None
            
            # API 1: FF ID API
            try:
                url1 = f"https://api.ffidapi.com/v1/player/{uid_input}"
                headers1 = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json'
                }
                response1 = requests.get(url1, headers=headers1, timeout=15)
                if response1.status_code == 200:
                    data1 = response1.json()
                    if data1 and data1.get('data'):
                        player_data = data1.get('data')
                        data_source = "FF ID API"
                        print(f"✅ API 1 success for UID: {uid_input}")
            except Exception as e:
                print(f"API 1 error: {e}")
            
            # API 2: Dictech API
            if not player_data:
                try:
                    url2 = f"https://api.dictech.dev/ff/player?id={uid_input}"
                    response2 = requests.get(url2, timeout=15)
                    if response2.status_code == 200:
                        data2 = response2.json()
                        if data2:
                            if data2.get('player'):
                                player_data = data2.get('player')
                            elif data2.get('data'):
                                player_data = data2.get('data')
                            else:
                                player_data = data2
                            data_source = "Dictech API"
                            print(f"✅ API 2 success for UID: {uid_input}")
                except Exception as e:
                    print(f"API 2 error: {e}")
            
            # API 3: Garena API
            if not player_data:
                try:
                    url3 = f"https://ff.garena.com/api/antiban/player?uid={uid_input}"
                    headers3 = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                    response3 = requests.get(url3, headers=headers3, timeout=15)
                    if response3.status_code == 200:
                        data3 = response3.json()
                        if data3 and data3.get('data'):
                            player_data = data3.get('data')
                            data_source = "Garena API"
                            print(f"✅ API 3 success for UID: {uid_input}")
                except Exception as e:
                    print(f"API 3 error: {e}")
            
            # API 4: Dictech Info API
            if not player_data:
                try:
                    url4 = f"https://api.dictech.dev/ff/info?id={uid_input}"
                    response4 = requests.get(url4, timeout=15)
                    if response4.status_code == 200:
                        data4 = response4.json()
                        if data4 and data4.get('player'):
                            player_data = data4.get('player')
                            data_source = "Dictech Info API"
                            print(f"✅ API 4 success for UID: {uid_input}")
                except Exception as e:
                    print(f"API 4 error: {e}")
            
            # API 5: Another fallback
            if not player_data:
                try:
                    url5 = f"https://api.dictech.dev/ff/profile?id={uid_input}"
                    response5 = requests.get(url5, timeout=15)
                    if response5.status_code == 200:
                        data5 = response5.json()
                        if data5:
                            player_data = data5
                            data_source = "Dictech Profile API"
                            print(f"✅ API 5 success for UID: {uid_input}")
                except Exception as e:
                    print(f"API 5 error: {e}")
            
            if player_data:
                # Build info dictionary with all possible fields
                info = {}
                
                # Try to extract all possible fields
                field_mappings = {
                    '👤 Name': ['name', 'player_name', 'nickname', 'userName', 'username', 'fullName'],
                    '🎮 UID': ['uid', 'player_id', 'id', 'userId', 'accountId'],
                    '📈 Level': ['level', 'player_level', 'lv', 'userLevel'],
                    '🌍 Region': ['region', 'player_region', 'reg', 'regionCode'],
                    '🌐 Country': ['country', 'player_country', 'cnt', 'countryCode', 'countryName'],
                    '🏆 Rank': ['rank', 'rank_name', 'rankName', 'tier'],
                    '⭐ Prime Level': ['prime_level', 'prime', 'prime_lv', 'primeLevel', 'primeStatus'],
                    '🚫 Ban Status': ['ban', 'ban_status', 'is_banned', 'banned', 'banStatus'],
                    '📅 Created': ['created', 'created_at', 'join_date', 'joinDate', 'createdAt', 'registrationDate']
                }
                
                # Also try to get ban duration and expiry
                ban_duration = None
                ban_expiry = None
                
                for key in ['ban_duration', 'ban_time', 'duration', 'banDuration', 'banPeriod']:
                    if key in player_data and player_data[key] and player_data[key] != "N/A" and player_data[key] != "":
                        ban_duration = player_data[key]
                        break
                
                for key in ['ban_expiry', 'expiry', 'banExpiry', 'expire']:
                    if key in player_data and player_data[key] and player_data[key] != "N/A" and player_data[key] != "":
                        ban_expiry = player_data[key]
                        break
                
                # Extract each field
                for display_name, possible_keys in field_mappings.items():
                    value = "N/A"
                    for key in possible_keys:
                        if key in player_data and player_data[key] and player_data[key] != "N/A" and player_data[key] != "":
                            value = player_data[key]
                            break
                    
                    # Special handling for ban status
                    if display_name == '🚫 Ban Status':
                        if str(value).lower() in ["true", "yes", "1", "banned"]:
                            ban_text = "🚫 BANNED"
                            if ban_duration and ban_duration != "" and ban_duration != "N/A":
                                ban_text += f" (Duration: {ban_duration})"
                            elif ban_expiry and ban_expiry != "" and ban_expiry != "N/A":
                                ban_text += f" (Expires: {ban_expiry})"
                            else:
                                ban_text += " (Permanent)"
                            info[display_name] = ban_text
                        else:
                            info[display_name] = "✅ NOT BANNED"
                    else:
                        info[display_name] = value if value and value != "N/A" else "N/A"
                
                # Get avatar if available
                avatar = None
                for key in ['avatar', 'profile_pic', 'photo', 'profilePicture', 'avatarUrl']:
                    if key in player_data and player_data[key] and player_data[key] != "" and player_data[key] != "N/A":
                        avatar = player_data[key]
                        break
                
                # Build response text - only include fields that have data
                text_lines = ["📊 PLAYER INFO 📊", ""]
                found_data = False
                
                for display_name, value in info.items():
                    if value and value != "N/A" and value != "":
                        text_lines.append(f"{display_name}: {value}")
                        found_data = True
                
                if not found_data:
                    text_lines.append("⚠️ No player data found for this UID")
                
                text_lines.append("")
                text_lines.append(f"👨‍💻 {load_settings().get('developer', '@NEPHRON_NXT')}")
                
                text = "\n".join(text_lines)
                
                # Try to send with avatar if available
                if avatar and avatar != "" and avatar != "N/A" and avatar != "None":
                    try:
                        bot.send_photo(message.chat.id, photo=avatar, caption=text)
                    except:
                        bot.send_message(message.chat.id, text)
                else:
                    bot.send_message(message.chat.id, text)
                
                # Update trial usage
                users = load_users()
                if str(user_id) in users:
                    users[str(user_id)]["num_trials"] = users[str(user_id)].get("num_trials", 0) + 1
                    save_users(users)
                    
            else:
                # If no API worked
                bot.send_message(message.chat.id, f"""⚠️ Unable to fetch player info at this moment.

📊 UID: {uid_input}

The Free Fire API servers might be busy or down.
Please try again after a few minutes.

If the issue continues, please contact support.

👨‍💻 {load_settings().get('developer', '@NEPHRON_NXT')}""")
                
                users = load_users()
                if str(user_id) in users:
                    users[str(user_id)]["num_trials"] = users[str(user_id)].get("num_trials", 0) + 1
                    save_users(users)
                    
        except Exception as e:
            print(f"❌ Process UID error: {e}")
            bot.send_message(message.chat.id, "⚠️ Error fetching info. Please try again later.")
            
    except Exception as e:
        print(f"❌ Process UID error: {e}")
        bot.send_message(message.chat.id, "❌ An error occurred. Please try again.")

# ============================================================
# HOW TO GET TOKEN
# ============================================================
@bot.message_handler(func=lambda m: m.text and "HOW TO GET TOKEN" in m.text)
def how_to_get_token(message):
    settings = load_settings()
    developer = settings.get("developer", "@NEPHRON_NXT")
    
    text = f"""
🔑 HOW TO GET TOKEN 🔑

1️⃣ GO ON GOOGLE AND SEARCH FF EAT TOKEN
2️⃣ CLICK ON FIRST LINK AND GENERATE EAT TOKEN
3️⃣ FROM EAT TOKEN GENERATE ACCESS TOKEN AND PASTE ON BOT TO BAN ACCOUNT
4️⃣ LINK: https://www.fftools.site/free-fire-token-generator

FOR HELP - {developer}
"""
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔗 GENERATE TOKEN", url="https://www.fftools.site/free-fire-token-generator"))
    keyboard.add(InlineKeyboardButton("📩 CONTACT SUPPORT", url=f"https://t.me/{developer.replace('@', '')}"))
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard)

# ============================================================
# SUPPORT
# ============================================================
@bot.message_handler(func=lambda m: m.text and "SUPPORT" in m.text)
def support_cmd(message):
    settings = load_settings()
    developer = settings.get("developer", "@NEPHRON_NXT")
    
    text = f"""
🆘 SUPPORT 🆘

For any issues or queries:
📧 Contact: {developer}

Response time: Within 24 hours

👨‍💻 Developer: {developer}
"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📩 CONTACT SUPPORT", url=f"https://t.me/{developer.replace('@', '')}"))
    bot.send_message(message.chat.id, text, reply_markup=keyboard)

# ============================================================
# HELP
# ============================================================
@bot.message_handler(func=lambda m: m.text and "HELP" in m.text)
def help_cmd(message):
    settings = load_settings()
    developer = settings.get("developer", "@NEPHRON_NXT")
    
    text = f"""
❓ HELP ❓

🔥 BAN ACCOUNT - Ban Free Fire account (1 free trial)
💎 UNLIMITED ACCESS - Get unlimited access (Rs.149)
📊 UID TO INFO - Get player details (3 free trials)
🔑 HOW TO GET TOKEN - Learn to get token

📱 -----------------------

🎁 Free Trials:
• BAN ACCOUNT: 1 use
• UID TO INFO: 3 uses

💎 Paid Features:
• Unlimited Access: Rs.149 (All services unlimited)
• BAN ACCOUNT after trial: Rs.15 per use
• UID TO INFO after trials: Rs.39

👨‍💻 {developer}
"""
    bot.send_message(message.chat.id, text)

# ============================================================
# ABOUT
# ============================================================
@bot.message_handler(func=lambda m: m.text and "ABOUT" in m.text)
def about_cmd(message):
    settings = load_settings()
    developer = settings.get("developer", "@NEPHRON_NXT")
    upi = settings.get("upi", "nephron-here@ptyes")
    price = settings.get("price", 149)
    num_price = settings.get("num_price", 39)
    ban_price = settings.get("ban_price", 15)
    
    text = f"""
ℹ️ ABOUT ℹ️

Best Free Fire Ban Bot

🔥 Ban any Free Fire account
📊 UID TO INFO - Player details
💎 Unlimited & Paid options
🆘 24/7 Support

📱 -----------------------

💎 Unlimited Access: Rs.{price}
🔥 BAN ACCOUNT (per use): Rs.{ban_price}
📊 UID TO INFO: Rs.{num_price}
🏦 UPI: {upi}

👨‍💻 Developer: {developer}
🔥 Thank you for choosing us! ❤️
"""
    bot.send_message(message.chat.id, text)

# ============================================================
# PAYMENT CALLBACKS
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("paid_"))
def paid_callback(call):
    try:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        parts = call.data.split("_")
        amount = int(parts[2]) if len(parts) > 2 else 149
        
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
        
        bot.send_message(chat_id, "📸 SEND SCREENSHOT")
        bot.register_next_step_handler(call.message, receive_payment_screenshot, amount)
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"❌ Paid callback error: {e}")

@bot.callback_query_handler(func=lambda c: c.data == "cancel_payment")
def cancel_payment_callback(call):
    try:
        user_id = call.from_user.id
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        bot.send_message(call.message.chat.id, "❌ Payment cancelled! Returning to main menu...")
        
        if is_admin(user_id):
            markup = get_admin_menu()
        else:
            markup = get_user_menu()
        
        settings = load_settings()
        user = get_user(user_id)
        ban_trials = user.get("ban_trials", 0)
        num_trials = user.get("num_trials", 0)
        ban_trials_left = 1 - ban_trials if ban_trials < 1 else 0
        num_trials_left = 3 - num_trials if num_trials < 3 else 0
        ban_paid = user.get("ban_paid", False)
        unlimited = user.get("unlimited", False)
        approved = user.get("approved", False)
        
        welcome_text = f"""
🌟 WELCOME TO FF BAN BOT 🌟

👋 User: {call.from_user.first_name}
🆔 ID: {user_id}
👤 @{call.from_user.username or 'N/A'}

📱 -----------------------

🔥 Ban any Free Fire account
💎 Unlimited access - Rs.{settings.get('price', 149)}
📊 UID TO INFO - Get player details

🎁 YOUR FREE TRIALS:
• BAN ACCOUNT: {ban_trials_left} use{'s' if ban_trials_left != 1 else ''} left
• UID TO INFO: {num_trials_left} use{'s' if num_trials_left != 1 else ''} left

💳 PAID SERVICES:
• BAN ACCOUNT: {'✅ Active' if ban_paid else '❌ Inactive'}
• UNLIMITED ACCESS: {'✅ Active' if unlimited else '❌ Inactive'}
• APPROVED: {'✅ Yes' if approved else '❌ No'}

👨‍💻 {settings.get('developer', '@NEPHRON_NXT')}
"""
        bot.send_message(call.message.chat.id, welcome_text, reply_markup=markup)
        
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"❌ Cancel payment error: {e}")

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("approve_"))
def approve_payment_callback(call):
    try:
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "❌ Unauthorized!")
            return
        
        user_id = int(call.data.split("_")[1])
        
        pending = load_pending()
        amount = 149
        
        if str(user_id) in pending:
            amount = pending[str(user_id)].get("amount", 149)
            del pending[str(user_id)]
            save_pending(pending)
        
        update_user(user_id, "approved", True)
        
        if amount == 15:
            update_user(user_id, "ban_paid", True)
            update_user(user_id, "ban_paid_used", 0)
            update_user(user_id, "ban_trials", 1)
            
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, f"✅ User {user_id} approved for single ban access!")
            
            try:
                bot.send_message(user_id, """🎉 CONGRATULATIONS 👑👑 YOU ARE APPROVED BY OWNER!

You now have access to BAN ACCOUNT (1 use)!

Send your token to ban an account:
🔥 BAN ACCOUNT

Thank you for choosing us! ❤️

👨‍💻 @NEPHRON_NXT""")
            except:
                pass
                
        elif amount == 39:
            update_user(user_id, "num_paid_uses", 10)
            
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, f"✅ User {user_id} approved for UID TO INFO access!")
            
            try:
                bot.send_message(user_id, """🎉 CONGRATULATIONS 👑👑 YOU ARE APPROVED BY OWNER!

You now have access to UID TO INFO (10 uses)!

Send a player UID to get info:
📊 UID TO INFO

Thank you for choosing us! ❤️

👨‍💻 @NEPHRON_NXT""")
            except:
                pass
                
        else:
            update_user(user_id, "unlimited", True)
            update_user(user_id, "ban_trials", 0)
            update_user(user_id, "num_trials", 0)
            update_user(user_id, "ban_paid", False)
            update_user(user_id, "ban_paid_used", 0)
            
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, f"✅ User {user_id} approved for unlimited access!")
            
            try:
                bot.send_message(user_id, """🎉 CONGRATULATIONS 👑👑 YOU ARE APPROVED BY OWNER!

You now have unlimited access to:
✅ Ban unlimited Free Fire accounts
✅ Unlimited UID TO INFO
✅ All services unlimited

Thank you for choosing us! ❤️

👨‍💻 @NEPHRON_NXT""")
            except:
                pass
        
        user_info = get_user(user_id)
        username = user_info.get('username', 'N/A')
        name = user_info.get('name', 'Unknown')
        
        owner_msg = f"""✅ User Approved!

👤 Name: {name}
🆔 ID: {user_id}
👤 @{username}
💰 Amount: Rs.{amount}
📱 Service: {'BAN ACCESS' if amount==15 else 'UID ACCESS' if amount==39 else 'UNLIMITED'}"""

        remove_keyboard = InlineKeyboardMarkup()
        remove_keyboard.add(InlineKeyboardButton(f"❌ REMOVE {user_id}", callback_data=f"remove_{user_id}"))
        
        try:
            bot.send_message(OWNER_ID, owner_msg, reply_markup=remove_keyboard)
        except:
            pass
        
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"❌ Approve payment error: {e}")

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("reject_"))
def reject_payment_callback(call):
    try:
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "❌ Unauthorized!")
            return
        
        user_id = int(call.data.split("_")[1])
        
        pending = load_pending()
        if str(user_id) in pending:
            del pending[str(user_id)]
            save_pending(pending)
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, f"❌ User {user_id} payment rejected!")
        
        try:
            bot.send_message(user_id, "❌ Payment verification failed.\n\nPlease contact @NEPHRON_NXT for support.")
        except:
            pass
        
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"❌ Reject payment error: {e}")

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("remove_"))
def remove_user_callback(call):
    try:
        if not is_owner(call.from_user.id):
            bot.answer_callback_query(call.id, "❌ Only owner can remove approvals!")
            return
        
        user_id = int(call.data.split("_")[1])
        
        update_user(user_id, "approved", False)
        update_user(user_id, "unlimited", False)
        update_user(user_id, "ban_paid", False)
        update_user(user_id, "ban_paid_used", 0)
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        bot.send_message(call.message.chat.id, f"❌ DE APPROVED User {user_id}!")
        
        try:
            bot.send_message(user_id, "❌ YOUR APPROVAL IS REVERSED BY OWNER!\n\nYour access has been revoked.")
        except:
            pass
        
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"❌ Remove user error: {e}")

def receive_payment_screenshot(message, amount=149):
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        
        if message.photo:
            file_id = message.photo[-1].file_id
            
            pending = load_pending()
            pending[str(user_id)] = {
                "user_id": user_id,
                "username": username,
                "name": first_name,
                "screenshot": file_id,
                "amount": amount,
                "time": datetime.now().isoformat()
            }
            save_pending(pending)
            
            bot.send_message(message.chat.id, "✅ WAIT FOR APPROVAL")
            
            if amount == 15:
                service = "BAN ACCOUNT (SINGLE USE)"
            elif amount == 39:
                service = "UID TO INFO ACCESS"
            else:
                service = "UNLIMITED ACCESS"
            
            caption = f"""📸 NEW PAYMENT SCREENSHOT

👤 User: {first_name}
🆔 ID: {user_id}
👤 @{username or 'N/A'}
💰 Amount: Rs.{amount}
📱 Service: {service}
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please verify and approve/reject:"""
            
            keyboard = [
                [InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{user_id}")],
                [InlineKeyboardButton("❌ REJECT", callback_data=f"reject_{user_id}")]
            ]
            markup = InlineKeyboardMarkup(keyboard)
            
            try:
                bot.send_photo(OWNER_ID, photo=file_id, caption=caption, reply_markup=markup)
            except:
                bot.send_message(OWNER_ID, caption, reply_markup=markup)
                
        else:
            bot.send_message(message.chat.id, "❌ Please send a photo/screenshot!")
    except Exception as e:
        print(f"❌ Screenshot error: {e}")

# ============================================================
# ADMIN COMMANDS (Buttons)
# ============================================================
@bot.message_handler(func=lambda m: m.text and "USERNAME" in m.text and is_admin(m.from_user.id))
def username_btn(message):
    settings = load_settings()
    current_username = settings.get("developer", "@NEPHRON_NXT")
    bot.send_message(message.chat.id, f"👤 Current username: {current_username}\n\nUse /username <NEW_USERNAME> to change\nExample: /username @NEW_NAME")

@bot.message_handler(func=lambda m: m.text and "STATS" in m.text and is_admin(m.from_user.id))
def stats_cmd(message):
    users = load_users()
    settings = load_settings()
    pending = load_pending()
    total_users = len(users)
    unlimited_users = sum(1 for u in users.values() if u.get("unlimited", False))
    banned_users = sum(1 for u in users.values() if u.get("banned", False))
    ban_paid_users = sum(1 for u in users.values() if u.get("ban_paid", False))
    approved_users = sum(1 for u in users.values() if u.get("approved", False))
    
    text = f"""
📊 STATS 📊

👥 Total Users: {total_users}
💎 Unlimited Users: {unlimited_users}
🔥 Ban Paid Users: {ban_paid_users}
✅ Approved Users: {approved_users}
🚫 Banned Users: {banned_users}
⏳ Pending Payments: {len(pending)}

💰 Unlimited Price: Rs.{settings.get('price', 149)}
📊 UID Price: Rs.{settings.get('num_price', 39)}
🔥 BAN Price (per use): Rs.{settings.get('ban_price', 15)}
🏦 UPI: {settings.get('upi', 'nephron-here@ptyes')}
👤 Username: {settings.get('developer', '@NEPHRON_NXT')}

📱 -----------------------
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text and "USERS" in m.text and is_admin(m.from_user.id))
def users_cmd(message):
    users = load_users()
    text = "📊 ALL USERS 📊\n\n"
    count = 0
    for uid, data in users.items():
        count += 1
        status = "✅"
        if data.get("banned", False):
            status = "🚫"
        if data.get("unlimited", False):
            status = "💎"
        elif data.get("ban_paid", False):
            status = "🔥"
        elif data.get("approved", False):
            status = "👑"
        text += f"{count}. {data.get('name')} (@{data.get('username', 'N/A')}) {status}\n"
        
        if len(text) > 3500:
            bot.send_message(message.chat.id, text)
            text = ""
    
    if text:
        text += f"\n📊 Total: {len(users)} users"
        bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text and "PRICE" in m.text and is_admin(m.from_user.id))
def price_btn(message):
    settings = load_settings()
    bot.send_message(message.chat.id, f"💰 Current prices:\nUnlimited: Rs.{settings.get('price', 149)}\nUID TO INFO: Rs.{settings.get('num_price', 39)}\nBAN (per use): Rs.{settings.get('ban_price', 15)}\n\nUse /price <amount> to change unlimited price\nUse /numprice <amount> to change UID price\nUse /banprice <amount> to change BAN price")

@bot.message_handler(func=lambda m: m.text and "UPI" in m.text and is_admin(m.from_user.id))
def upi_btn(message):
    bot.send_message(message.chat.id, "🏦 Send your new UPI ID along with QR code image to update")

@bot.message_handler(func=lambda m: m.text and "ADD ADMIN" in m.text and is_admin(m.from_user.id))
def add_admin_btn(message):
    bot.send_message(message.chat.id, "💡 /addadmin <USER_ID>\n\nGet user ID from @userinfobot")

@bot.message_handler(func=lambda m: m.text and "COMMANDS" in m.text and is_admin(m.from_user.id))
def commands_btn(message):
    text = """
📋 ADMIN COMMANDS 📋

/start - Start bot
/username <NAME> - Change username
/price <AMT> - Change unlimited price
/numprice <AMT> - Change UID price
/banprice <AMT> - Change BAN price
/upi <UPI> - Change UPI
/addadmin <ID> - Add admin
/removeadmin <ID> - Remove admin
/reverseuser <ID> - Reverse user approval
/approve <ID> - Approve user
/ban <ID> - Ban user
/unban <ID> - Unban user
/users - List all users
/broadcast <MSG> - Send to all

📱 -----------------------
👨‍💻 @NEPHRON_NXT
"""
    bot.send_message(message.chat.id, text)

# ============================================================
# ADMIN COMMANDS (Slash)
# ============================================================
@bot.message_handler(commands=['username'])
def username_cmd(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, f"👤 Current username: {load_settings().get('developer', '@NEPHRON_NXT')}\n\nUse /username <NEW_USERNAME> to change\nExample: /username @NEW_NAME")
        return
    
    new_username = parts[1]
    if not new_username.startswith('@'):
        new_username = '@' + new_username
    
    settings = load_settings()
    settings["developer"] = new_username
    settings["support"] = new_username
    save_settings(settings)
    
    bot.send_message(message.chat.id, f"✅ Username updated to {new_username}")
    bot.send_message(message.chat.id, f"All references (developer, support, help) now show {new_username}")

@bot.message_handler(commands=['price'])
def price_cmd(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, f"💰 Current price: Rs.{load_settings().get('price', 149)}")
        return
    try:
        price = int(parts[1])
        settings = load_settings()
        settings["price"] = price
        save_settings(settings)
        bot.send_message(message.chat.id, f"✅ Unlimited price set to Rs.{price}")
    except:
        bot.send_message(message.chat.id, "❌ Invalid amount!")

@bot.message_handler(commands=['numprice'])
def numprice_cmd(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, f"💰 Current UID price: Rs.{load_settings().get('num_price', 39)}")
        return
    try:
        price = int(parts[1])
        settings = load_settings()
        settings["num_price"] = price
        save_settings(settings)
        bot.send_message(message.chat.id, f"✅ UID TO INFO price set to Rs.{price}")
    except:
        bot.send_message(message.chat.id, "❌ Invalid amount!")

@bot.message_handler(commands=['banprice'])
def banprice_cmd(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, f"💰 Current BAN price: Rs.{load_settings().get('ban_price', 15)}")
        return
    try:
        price = int(parts[1])
        settings = load_settings()
        settings["ban_price"] = price
        save_settings(settings)
        bot.send_message(message.chat.id, f"✅ BAN price set to Rs.{price}")
    except:
        bot.send_message(message.chat.id, "❌ Invalid amount!")

@bot.message_handler(commands=['upi'])
def upi_cmd(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "📤 SEND YOUR UPI ID ALONG WITH QR CODE IMAGE\n\nSend your new UPI ID and QR code in this format:\nUPI: your-upi@paytm\n(attach QR code image)")

@bot.message_handler(content_types=['photo', 'text'])
def handle_upi_update(message):
    try:
        if not is_admin(message.from_user.id):
            return
        
        if message.photo and message.caption:
            if "UPI:" in message.caption:
                lines = message.caption.split('\n')
                upi_id = None
                for line in lines:
                    if line.startswith("UPI:"):
                        upi_id = line.replace("UPI:", "").strip()
                        break
                
                if upi_id:
                    file_id = message.photo[-1].file_id
                    
                    settings = load_settings()
                    settings["upi"] = upi_id
                    settings["upi_qr"] = file_id
                    save_settings(settings)
                    
                    bot.send_message(message.chat.id, f"✅ UPI updated successfully!\n\nNew UPI ID: {upi_id}\nQR Code: {file_id}\n\nTest the payment to confirm.")
                else:
                    bot.send_message(message.chat.id, "❌ Please send UPI in this format:\nUPI: your-upi@paytm\n(attach QR code image)")
        
        elif message.text and message.text.startswith("UPI:") and not message.photo:
            upi_id = message.text.replace("UPI:", "").strip()
            if upi_id:
                qr_url = generate_qr(upi_id, load_settings().get('price', 149))
                
                settings = load_settings()
                settings["upi"] = upi_id
                settings["upi_qr"] = qr_url
                save_settings(settings)
                
                bot.send_message(message.chat.id, f"✅ UPI updated successfully!\n\nNew UPI ID: {upi_id}\nQR Code generated automatically.\n\nTest the payment to confirm.")
            else:
                bot.send_message(message.chat.id, "❌ Invalid UPI format. Send: UPI: your-upi@paytm")
            
    except Exception as e:
        print(f"❌ UPI update error: {e}")

@bot.message_handler(commands=['addadmin'])
def add_admin_cmd(message):
    if not is_owner(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Only owner can add admins!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ /addadmin <USER_ID>\nGet user ID from @userinfobot")
        return
    try:
        user_id = int(parts[1])
        if user_id not in ADMIN_IDS:
            ADMIN_IDS.append(user_id)
            bot.send_message(message.chat.id, f"✅ ADMIN PROMOTED! User {user_id} is now an admin!")
            
            try:
                bot.send_message(user_id, "✅ YOU ARE NOW AN ADMIN!\n\nYou have admin rights for the bot.")
            except:
                pass
        else:
            bot.send_message(message.chat.id, "⚠️ Already an admin!")
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

@bot.message_handler(commands=['removeadmin'])
def remove_admin_cmd(message):
    if not is_owner(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Only owner can remove admins!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        admin_list = "📋 ADMIN LIST 📋\n\n"
        for admin_id in ADMIN_IDS:
            if admin_id != OWNER_ID:
                user = get_user(admin_id)
                name = user.get('name', 'Unknown')
                username = user.get('username', 'N/A')
                admin_list += f"🆔 {admin_id} - {name} (@{username})\n"
        
        if len(ADMIN_IDS) <= 1:
            admin_list += "No other admins except owner."
        
        bot.send_message(message.chat.id, f"{admin_list}\n\nUse /removeadmin <USER_ID> to remove an admin")
        return
    
    try:
        user_id = int(parts[1])
        
        if user_id == OWNER_ID:
            bot.send_message(message.chat.id, "❌ Cannot remove the owner!")
            return
        
        if user_id in ADMIN_IDS:
            ADMIN_IDS.remove(user_id)
            bot.send_message(message.chat.id, f"✅ ADMIN DEMOTED! User {user_id} is no longer an admin!")
            
            try:
                bot.send_message(user_id, "❌ YOU ARE DEMOTED!\n\nYou are no longer an admin.")
            except:
                pass
        else:
            bot.send_message(message.chat.id, "❌ User is not an admin!")
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

@bot.message_handler(commands=['reverseuser'])
def reverse_user_cmd(message):
    if not is_owner(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Only owner can reverse approvals!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ /reverseuser <USER_ID>")
        return
    
    try:
        user_id = int(parts[1])
        user = get_user(user_id)
        
        if not user:
            bot.send_message(message.chat.id, "❌ User not found!")
            return
        
        update_user(user_id, "approved", False)
        update_user(user_id, "unlimited", False)
        update_user(user_id, "ban_paid", False)
        update_user(user_id, "ban_paid_used", 0)
        
        bot.send_message(message.chat.id, f"❌ DE APPROVED User {user_id}!")
        
        try:
            bot.send_message(user_id, "❌ YOUR APPROVAL IS REVERSED BY OWNER!\n\nYour access has been revoked.")
        except:
            pass
        
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

@bot.message_handler(commands=['approve'])
def approve_user(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ /approve <USER_ID>")
        return
    try:
        user_id = int(parts[1])
        user = get_user(user_id)
        if user:
            update_user(user_id, "approved", True)
            update_user(user_id, "unlimited", True)
            update_user(user_id, "ban_trials", 0)
            update_user(user_id, "num_trials", 0)
            update_user(user_id, "ban_paid", False)
            update_user(user_id, "ban_paid_used", 0)
            bot.send_message(message.chat.id, f"✅ User {user_id} approved for unlimited access!")
            try:
                bot.send_message(user_id, "🎉 CONGRATULATIONS 👑👑 YOU ARE APPROVED BY OWNER!\n\nYou now have unlimited access to all services!")
            except:
                pass
        else:
            bot.send_message(message.chat.id, "❌ User not found!")
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

@bot.message_handler(commands=['ban'])
def ban_user_cmd(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ /ban <USER_ID>")
        return
    try:
        user_id = int(parts[1])
        user = get_user(user_id)
        if user:
            update_user(user_id, "banned", True)
            bot.send_message(message.chat.id, f"🚫 User {user_id} banned!")
            try:
                bot.send_message(user_id, "🚫 You have been banned from using this bot!")
            except:
                pass
        else:
            bot.send_message(message.chat.id, "❌ User not found!")
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

@bot.message_handler(commands=['unban'])
def unban_user_cmd(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ /unban <USER_ID>")
        return
    try:
        user_id = int(parts[1])
        user = get_user(user_id)
        if user:
            update_user(user_id, "banned", False)
            bot.send_message(message.chat.id, f"✅ User {user_id} unbanned!")
            try:
                bot.send_message(user_id, "✅ You have been unbanned!")
            except:
                pass
        else:
            bot.send_message(message.chat.id, "❌ User not found!")
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

@bot.message_handler(commands=['users'])
def users_list_cmd(message):
    if not is_admin(message.from_user.id):
        return
    users = load_users()
    text = "📊 ALL USERS 📊\n\n"
    count = 0
    for uid, data in users.items():
        count += 1
        status = "✅"
        if data.get("banned", False):
            status = "🚫"
        if data.get("unlimited", False):
            status = "💎"
        elif data.get("ban_paid", False):
            status = "🔥"
        elif data.get("approved", False):
            status = "👑"
        text += f"{count}. {data.get('name')} (@{data.get('username', 'N/A')}) {status}\n"
        
        if len(text) > 3500:
            bot.send_message(message.chat.id, text)
            text = ""
    
    if text:
        text += f"\n📊 Total: {len(users)} users"
        bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ /broadcast <MESSAGE>")
        return
    msg = parts[1]
    users = load_users()
    sent = 0
    failed = 0
    
    bot.send_message(message.chat.id, f"📢 Broadcasting to {len(users)} users...")
    
    for user_id in users.keys():
        try:
            bot.send_message(int(user_id), f"📢 {msg}")
            sent += 1
            time.sleep(0.05)
        except:
            failed += 1
    
    bot.send_message(message.chat.id, f"✅ Broadcast complete!\n📊 Sent: {sent}\n❌ Failed: {failed}")

# ============================================================
# ERROR HANDLING
# ============================================================
@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, "❌ Unknown command!\nType /start to see available commands.")

# ============================================================
# MAIN - WITH HTTP SERVER FOR RENDER
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("✅ FF BAN BOT Starting...")
    print(f"👑 Owner ID: {OWNER_ID}")
    print(f"🏦 UPI: nephron-here@ptyes")
    print(f"👨‍💻 Developer: @NEPHRON_NXT")
    print(f"🌐 Port: {PORT}")
    print("🔄 Using long polling...")
    print("=" * 50)
    
    # Start HTTP server in background for Render health checks
    try:
        http_thread = threading.Thread(target=run_http_server)
        http_thread.daemon = True
        http_thread.start()
        print("✅ HTTP server thread started")
    except Exception as e:
        print(f"⚠️ HTTP server error: {e}")
    
    # Remove webhook
    try:
        bot.remove_webhook()
        print("✅ Webhook removed")
    except Exception as e:
        print(f"⚠️ Could not remove webhook: {e}")
    
    print("🔄 Bot polling started...")
    print("=" * 50)
    
    # Continuous polling with auto-restart
    while True:
        try:
            # Use simple polling instead of infinity_polling
            bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e:
            print(f"❌ Polling error: {e}")
            print("🔄 Restarting polling in 5 seconds...")
            time.sleep(5)
            continue
        except KeyboardInterrupt:
            print("⏹️ Bot stopped by user")
            break
        except:
            print("❌ Unknown error occurred")
            print("🔄 Restarting polling in 5 seconds...")
            time.sleep(5)
            continue
