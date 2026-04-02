import telebot
from telebot import types
from datetime import datetime, timedelta
import random
import sqlite3
import json
from flask import Flask, jsonify, request
from threading import Thread
import time

# --- ১. কনফিগারেশন ---
TOKEN = '8608303923:AAGr0s6c092jd7a5GOlswozxTrqCUbAG5nE'
ADMIN_ID = 8562914479
# আপনার মিনি অ্যাপের HTML ফাইলটি যেখানে হোস্ট করবেন সেই লিঙ্ক এখানে দিন
WEB_APP_URL = "https://your-mini-app-site.vercel.app" 

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- ২. ডাটাবেস ম্যানেজমেন্ট (পারমানেন্ট ডাটা) ---
def init_db():
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (uid INTEGER PRIMARY KEY, data TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS system (id INTEGER PRIMARY KEY, tasks TEXT, withdraws TEXT)''')
    conn.commit()
    return conn

db_conn = init_db()

def get_user(uid, name="User", uname="None"):
    cursor = db_conn.cursor()
    cursor.execute("SELECT data FROM users WHERE uid=?", (uid,))
    row = cursor.fetchone()
    if row: return json.loads(row[0])
    
    user_data = {'name': name, 'username': uname, 'balance': 0.0, 'refers': 0, 'tasks_done': 0, 'total_withdraw': 0.0, 'last_bonus': None, 'done_tasks': [], 'history': [], 'is_verified': False}
    cursor.execute("INSERT INTO users VALUES (?, ?)", (uid, json.dumps(user_data)))
    db_conn.commit()
    return user_data

def save_user(uid, user):
    cursor = db_conn.cursor()
    cursor.execute("UPDATE users SET data=? WHERE uid=?", (json.dumps(user), uid))
    db_conn.commit()

# মেমোরি ডাটা (অস্থায়ী প্রসেসের জন্য)
mem_db = {'pending_captcha': {}, 'tasks': [], 'withdraws': [], 'task_requests': []}

# --- ৩. মিনি অ্যাপ API (Frontend এর জন্য) ---
@app.route('/api/user/<int:uid>')
def api_get_user(uid):
    return jsonify(get_user(uid))

@app.route('/api/tasks')
def api_get_tasks():
    return jsonify(mem_db['tasks'])

# --- ৪. বট হ্যান্ডলার (এডমিন কন্ট্রোল ও স্টার্ট) ---

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    user = get_user(uid, name, message.from_user.username)

    if not user['is_verified']:
        num1, num2 = random.randint(1, 20), random.randint(1, 15)
        mem_db['pending_captcha'][uid] = {'result': num1 + num2, 'ref_by': message.text.split()[1] if len(message.text.split()) > 1 else None}
        bot.send_message(uid, f"👋 স্বাগতম **{name}**!\n🤖 ভেরিফাই করতে উত্তর দিন: `{num1} + {num2} = ?`", parse_mode='Markdown')
        return

    # মেইন মেনু (এডমিন ও ইউজার আলাদা)
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    if uid == ADMIN_ID:
        markup.add('➕ অ্যাড টাস্ক', '📩 টাস্ক ভেরিফাই', '💰 উইথড্র রিকোয়েস্ট', '📊 অ্যাপ স্ট্যাটাস', '⚙️ ব্যালেন্স এডিট', '👥 ইউজার বক্স')
        bot.send_message(uid, "👑 **মাস্টার এডমিন প্যানেল সচল!**", reply_markup=markup)
    else:
        # ইউজার মেনু বাটন এবং মিনি অ্যাপ বাটন
        inline_markup = types.InlineKeyboardMarkup()
        web_info = types.WebAppInfo(url=f"{WEB_APP_URL}?uid={uid}")
        inline_markup.add(types.InlineKeyboardButton(text="🚀 Open Mini App", web_app=web_info))
        
        bot.send_message(uid, "📱 **মেইন মেনু ওপেন হয়েছে।**\nনিচের বাটনটি ক্লিক করে মিনি অ্যাপে প্রবেশ করুন।", reply_markup=inline_markup)

# --- ৫. এডমিন লজিক (টেলিগ্রাম থেকে কন্ট্রোল) ---
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def admin_panel(m):
    if m.text == '📊 অ্যাপ স্ট্যাটাস':
        bot.send_message(ADMIN_ID, f"📈 ইউজার সংখ্যা: {len(mem_db['pending_captcha']) + 1}\n🎯 টাস্ক আছে: {len(mem_db['tasks'])}")
    
    elif m.text == '➕ অ্যাড টাস্ক':
        msg = bot.send_message(ADMIN_ID, "📝 টাস্কের নাম দিন:")
        bot.register_next_step_handler(msg, process_task_name)

def process_task_name(m):
    name = m.text
    msg = bot.send_message(ADMIN_ID, f"💰 '{name}' এর রিওয়ার্ড কত?");
    bot.register_next_step_handler(msg, lambda ms: finalize_task(ms, name))

def finalize_task(m, name):
    try:
        rew = float(m.text)
        mem_db['tasks'].append({'name': name, 'rew': rew, 'link': 'https://t.me/example'})
        bot.send_message(ADMIN_ID, f"✅ ট status: টাস্ক '{name}' মিনি অ্যাপে যোগ হয়েছে।")
    except: bot.send_message(ADMIN_ID, "❌ এমাউন্ট সংখ্যায় দিন।")

# --- ৬. সার্ভার ও বট রান করা ---
def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("🚀 Mini App Backend is Live!")
    while True:
        try:
            bot.infinity_polling(timeout=20)
        except Exception as e:
            time.sleep(5)
