import telebot
from telebot import types
from datetime import datetime, timedelta
import random

# --- কনফিগারেশন ---
TOKEN = '8608303923:AAGr0s6c092jd7a5GOlswozxTrqCUbAG5nE'
ADMIN_ID = 8562914479
bot = telebot.TeleBot(TOKEN)

# ডাটাবেস (মেমোরি ভিত্তিক)
db = {
    'users': {},
    'tasks': [],
    'task_requests': [],
    'withdraws': [],
    'pending_captcha': {} 
}

def get_user(uid, name="User", uname="None"):
    if uid not in db['users']:
        db['users'][uid] = {
            'name': name, 'username': uname, 'balance': 0.0,
            'refers': 0, 'tasks_done': 0, 'total_withdraw': 0.0,
            'last_bonus': None, 'done_tasks': [], 'history': [],
            'is_verified': False 
        }
    return db['users'][uid]

# --- ১. স্টার্ট ও ক্যাপচা সিস্টেম ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    uname = message.from_user.username or "None"
    user = get_user(uid, name, uname)

    if user['is_verified']:
        show_main_menu(uid)
        return

    num1 = random.randint(1, 20)
    num2 = random.randint(1, 15)
    result = num1 + num2
    
    ref_id = message.text.split()[1] if len(message.text.split()) > 1 else None
    db['pending_captcha'][uid] = {'result': result, 'ref_by': ref_id}
    
    bot.send_message(uid, f"👋 স্বাগতম **{name}**!\n\n🤖 বটটি সচল করতে সঠিক উত্তর দিন:\n👉 `{num1} + {num2} = ?`", parse_mode='Markdown')

# --- ২. ক্যাপচা ভেরিফিকেশন ---
@bot.message_handler(func=lambda m: m.from_user.id in db['pending_captcha'])
def verify_captcha(message):
    uid = message.from_user.id
    user = get_user(uid)
    try:
        user_ans = int(message.text)
        correct_ans = db['pending_captcha'][uid]['result']
        if user_ans == correct_ans:
            user['is_verified'] = True
            ref_id = db['pending_captcha'][uid]['ref_by']
            
            if ref_id and str(ref_id).isdigit():
                ref_id = int(ref_id)
                if ref_id != uid and ref_id in db['users'] and 'ref_by' not in user:
                    user['ref_by'] = ref_id
                    db['users'][ref_id]['balance'] += 2.0
                    db['users'][ref_id]['refers'] += 1
                    db['users'][ref_id]['history'].append(f"🎁 রেফার বোনাস: +৳২.০০ ({user['name']})")
                    bot.send_message(ref_id, f"🎊 অভিনন্দন! {user['name']} ভেরিফাই হয়েছে। আপনি ৳২ পেয়েছেন।")
            
            del db['pending_captcha'][uid]
            bot.send_message(uid, "✅ ভেরিফিকেশন সফল হয়েছে!")
            show_main_menu(uid)
        else:
            bot.reply_to(message, "❌ ভুল উত্তর! আবার /start করুন।")
    except:
        bot.reply_to(message, "⚠️ শুধু সংখ্যায় উত্তর দিন।")

def show_main_menu(uid):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    if uid == ADMIN_ID:
        markup.add('➕ অ্যাড টাস্ক', '📩 টাস্ক ভেরিফাই', '💰 উইথড্র রিকোয়েস্ট', '👥 ইউজার বক্স', '⚙️ ব্যালেন্স এডিট', '📊 অ্যাপ স্ট্যাটাস')
        bot.send_message(uid, "👑 **মাস্টার এডমিন প্যানেল সচল!**", reply_markup=markup)
    else:
        markup.add('💳 মাই ওয়ালেট', '🎯 টাস্ক', '🎁 ডেইলি বোনাস', '🔗 রেফার লিঙ্ক', '💸 উইথড্র', '📜 হিস্টোরি', '📞 সাপোর্ট')
        bot.send_message(uid, "📱 **মেইন মেনু ওপেন হয়েছে। নিচের বাটনগুলো ব্যবহার করুন:**", reply_markup=markup)

# --- ৩. মেইন বাটন লজিক ---
@bot.message_handler(func=lambda m: True)
def handle_all_buttons(m):
    uid = m.from_user.id
    user = get_user(uid)

    if not user['is_verified']:
        bot.send_message(uid, "⚠️ আগে ক্যাপচা পূরণ করুন! /start লিখুন।")
        return

    # --- ইউজার বাটন সেকশন ---
    if m.text == '💳 মাই ওয়ালেট':
        msg = (f"👤 **আপনার প্রোফাইল তথ্য**\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               f"📛 নাম: {user['name']}\n"
               f"🆔 আইডি: `{uid}`\n"
               f"💰 ব্যালেন্স: ৳{user['balance']:.2f}\n"
               f"👥 রেফার: {user['refers']} জন\n"
               f"✅ সম্পন্ন টাস্ক: {user['tasks_done']} টি\n"
               f"🏦 মোট উত্তোলন: ৳{user['total_withdraw']:.2f}\n"
               f"━━━━━━━━━━━━━━━━━━")
        bot.send_message(uid, msg, parse_mode='Markdown')

    elif m.text == '🔗 রেফার লিঙ্ক':
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        msg = (f"🔥 **রেফার ইনকাম সিস্টেম**\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               f"প্রতিটি ভ্যালিড রেফারে আপনি পাবেন **৳২.০০**\n\n"
               f"🔗 আপনার রেফার লিঙ্ক:\n`{link}`")
        bot.send_message(uid, msg, parse_mode='Markdown')

    elif m.text == '🎁 ডেইলি বোনাস':
        now = datetime.now()
        if user['last_bonus'] and (now - user['last_bonus']) < timedelta(hours=24):
            bot.reply_to(m, "⏳ আজ বোনাস নিয়েছেন। ২৪ ঘণ্টা পর আবার ট্রাই করুন।")
        else:
            user['balance'] += 0.50
            user['last_bonus'] = now
            user['history'].append("🎁 ডেইলি বোনাস: +৳০.৫০")
            bot.reply_to(m, "🎉 অভিনন্দন! আপনি **৳০.৫০** বোনাস পেয়েছেন।")

    elif m.text == '📜 হিস্টোরি':
        history = "\n".join(user['history'][-10:]) if user['history'] else "লেনদেনের রেকর্ড নেই।"
        bot.send_message(uid, f"📜 **শেষ ১০টি লেনদেন:**\n\n{history}")

    elif m.text == '💸 উইথড্র':
        msg = (f"💸 **উইথড্র ইনফরমেশন**\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               f"💰 ব্যালেন্স: ৳{user['balance']:.2f}\n"
               f"🚀 মিনিমাম উইথড্র: ৳১০.০০")
        if user['balance'] < 10: 
            bot.send_message(uid, f"{msg}\n\n❌ পর্যাপ্ত ব্যালেন্স নেই।", parse_mode='Markdown')
        else:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("বিকাশ", callback_data="w_BKASH"),
                       types.InlineKeyboardButton("নগদ", callback_data="w_NAGAD"))
            bot.send_message(uid, msg, reply_markup=markup, parse_mode='Markdown')

    elif m.text == '🎯 টাস্ক':
        available = False
        for i, t in enumerate(db['tasks']):
            if i not in user['done_tasks'] and t['limit'] > 0:
                available = True
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🔗 লিঙ্ক ওপেন", url=t['link']))
                markup.add(types.InlineKeyboardButton("📤 প্রুফ জমা দিন", callback_data=f"proof_{i}"))
                text = (f"📌 **টাস্ক:** {t['name']}\n"
                        f"📄 **বর্ণনা:** {t['desc']}\n"
                        f"💰 **রিওয়ার্ড:** ৳{t['rew']}\n"
                        f"📊 **বাকি:** {t['limit']} বার")
                if t['img'] != "No": bot.send_photo(uid, t['img'], caption=text, reply_markup=markup, parse_mode='Markdown')
                else: bot.send_message(uid, text, reply_markup=markup, parse_mode='Markdown')
        if not available: bot.send_message(uid, "📭 কোনো কাজ খালি নেই।")

    # --- এডমিন সেকশন (ফিক্সড) ---
    if uid == ADMIN_ID:
        if m.text == '📊 অ্যাপ স্ট্যাটাস':
            bot.send_message(ADMIN_ID, f"📈 **বট রিপোর্ট**\n👥 ইউজার: {len(db['users'])}\n🎯 টাস্ক: {len(db['tasks'])}\n💰 পেন্ডিং উইথড্র: {len([w for w in db['withdraws'] if w['status'] == 'Pending'])}")

        elif m.text == '➕ অ্যাড টাস্ক':
            msg = bot.send_message(ADMIN_ID, "📸 টাস্কের ছবি পাঠান (না থাকলে 'No' লিখুন):")
            bot.register_next_step_handler(msg, t_step1)

        elif m.text == '⚙️ ব্যালেন্স এডিট':
            msg = bot.send_message(ADMIN_ID, "ইউজারের UID দিন:")
            bot.register_next_step_handler(msg, edit_b1)

        elif m.text == '👥 ইউজার বক্স':
            user_list = "👥 **ইউজার লিস্ট:**\n\n"
            for u_id, u_data in db['users'].items():
                user_list += f"🆔 `{u_id}` | 👤 {u_data['name']} | 💰 ৳{u_data['balance']}\n"
            if len(db['users']) == 0: user_list = "📭 কোনো ইউজার নেই।"
            bot.send_message(ADMIN_ID, user_list, parse_mode='Markdown')

        elif m.text == '💰 উইথড্র রিকোয়েস্ট':
            pending_w = [w for w in db['withdraws'] if w['status'] == 'Pending']
            if not pending_w: return bot.send_message(ADMIN_ID, "📭 কোনো পেন্ডিং উইথড্র নেই।")
            for i, w in enumerate(db['withdraws']):
                if w['status'] == 'Pending':
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("✅ পেইড", callback_data=f"paid_{i}"),
                               types.InlineKeyboardButton("❌ রিজেক্ট", callback_data=f"wrej_{i}"))
                    bot.send_message(ADMIN_ID, f"💸 **উইথড্র রিকোয়েস্ট:**\n\n👤 নাম: {db['users'][w['uid']]['name']}\n🆔 UID: `{w['uid']}`\n💰 এমাউন্ট: ৳{w['amt']}\n📱 নাম্বার: `{w['num']}`\n🏦 মেথড: {w['method']}", reply_markup=markup, parse_mode='Markdown')

        elif m.text == '📩 টাস্ক ভেরিফাই':
            pending_t = [r for r in db['task_requests'] if r['status'] == 'Pending']
            if not pending_t: return bot.send_message(ADMIN_ID, "📭 কোনো পেন্ডিং টাস্ক নেই।")
            for i, r in enumerate(db['task_requests']):
                if r['status'] == 'Pending':
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("✅ এপ্রুভ", callback_data=f"tok_{i}"),
                               types.InlineKeyboardButton("❌ রিজেক্ট", callback_data=f"tno_{i}"))
                    # টাস্কের বিস্তারিত তথ্য সহ এডমিনকে পাঠানো
                    info = (f"📩 **নতুন টাস্ক প্রুফ:**\n"
                            f"━━━━━━━━━━━━━━\n"
                            f"👤 ইউজার: {r['u_name']}\n"
                            f"🆔 UID: `{r['uid']}`\n"
                            f"📌 টাস্ক: {r['t_name']}\n"
                            f"💰 রিওয়ার্ড: ৳{r['rew']}\n"
                            f"━━━━━━━━━━━━━━")
                    bot.send_photo(ADMIN_ID, r['proof'], caption=info, reply_markup=markup, parse_mode='Markdown')

# --- ৪. কলব্যাক হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.from_user.id
    
    # টাস্ক প্রুফ সাবমিট শুরু
    if call.data.startswith("proof_"):
        idx = int(call.data.split("_")[1])
        msg = bot.send_message(uid, "📸 আপনার কাজের স্ক্রিনশট (Proof) পাঠান:")
        bot.register_next_step_handler(msg, lambda m: receive_p(m, idx))
    
    # এডমিন টাস্ক এপ্রুভ
    elif call.data.startswith("tok_"):
        rid = int(call.data.split("_")[1])
        req = db['task_requests'][rid]
        if req['status'] == 'Pending':
            req['status'] = 'Approved'
            u = db['users'][req['uid']]
            u['balance'] += req['rew']
            u['tasks_done'] += 1
            u['done_tasks'].append(req['t_idx'])
            u['history'].append(f"✅ টাস্ক ({req['t_name']}): +৳{req['rew']}")
            bot.send_message(req['uid'], f"🎉 অভিনন্দন! **{req['t_name']}** এপ্রুভ হয়েছে। ৳{req['rew']} যোগ হয়েছে।")
            bot.edit_message_caption("🏁 STATUS: APPROVED ✅", call.message.chat.id, call.message.message_id)

    # এডমিন উইথড্র পেইড
    elif call.data.startswith("paid_"):
        wid = int(call.data.split("_")[1])
        withdraw = db['withdraws'][wid]
        if withdraw['status'] == 'Pending':
            withdraw['status'] = 'Paid'
            u = db['users'][withdraw['uid']]
            u['total_withdraw'] += withdraw['amt']
            u['history'].append(f"💸 উইথড্র সফল: -৳{withdraw['amt']}")
            bot.send_message(withdraw['uid'], f"✅ আপনার ৳{withdraw['amt']} উইথড্র সফল হয়েছে।")
            bot.edit_message_text(f"🏁 STATUS: PAID ✅\nUID: {withdraw['uid']}\nAmount: {withdraw['amt']}", call.message.chat.id, call.message.message_id)

    # উইথড্র মেথড সিলেকশন
    elif call.data.startswith("w_"):
        method = call.data.split("_")[1]
        msg = bot.send_message(call.message.chat.id, f"📱 আপনার {method} নাম্বার দিন:")
        bot.register_next_step_handler(msg, lambda m: get_w_amt(m, method))

# --- ৫. সাপোর্টিং ফাংশনস ---

def receive_p(m, idx):
    if not m.photo: return bot.reply_to(m, "❌ শুধু ছবি পাঠান।")
    user = db['users'][m.from_user.id]
    task = db['tasks'][idx]
    # ডাটাতে ইউজারের নাম এবং টাস্কের নাম সেভ করা হচ্ছে ভেরিফাইয়ের সুবিধার জন্য
    db['task_requests'].append({
        'uid': m.from_user.id, 
        'u_name': user['name'],
        't_name': task['name'],
        'proof': m.photo[-1].file_id, 
        'rew': task['rew'], 
        't_idx': idx, 
        'status': 'Pending'
    })
    bot.send_message(m.chat.id, "✅ প্রুফ জমা হয়েছে! এডমিন চেক করছে।")

def get_w_amt(m, method):
    num = m.text
    msg = bot.send_message(m.chat.id, "💵 উত্তোলনের পরিমাণ (৳) দিন:")
    bot.register_next_step_handler(msg, lambda ms: finalize_w(ms, method, num))

def finalize_w(m, method, num):
    try:
        amt = float(m.text)
        user = get_user(m.from_user.id)
        if user['balance'] >= amt:
            user['balance'] -= amt
            db['withdraws'].append({'uid': m.from_user.id, 'amt': amt, 'num': num, 'method': method, 'status': 'Pending'})
            bot.send_message(m.chat.id, "✅ উইথড্র রিকোয়েস্ট পাঠানো হয়েছে।")
        else: bot.send_message(m.chat.id, "❌ ব্যালেন্স নেই।")
    except: bot.send_message(m.chat.id, "❌ সংখ্যা লিখুন।")

# --- টাস্ক এডিং চেইন ---
def t_step1(m):
    img = m.photo[-1].file_id if m.photo else m.text
    msg = bot.send_message(ADMIN_ID, "📝 টাস্কের নাম:")
    bot.register_next_step_handler(msg, lambda ms: t_step2(ms, img))

def t_step2(m, img):
    name = m.text
    msg = bot.send_message(ADMIN_ID, "📄 টাস্কের বর্ণনা দিন:")
    bot.register_next_step_handler(msg, lambda ms: t_step3(ms, img, name))

def t_step3(m, img, name):
    desc = m.text
    msg = bot.send_message(ADMIN_ID, "💰 রিওয়ার্ড এমাউন্ট (৳):")
    bot.register_next_step_handler(msg, lambda ms: t_step4(ms, img, name, desc))

def t_step4(m, img, name, desc):
    try:
        rew = float(m.text)
        msg = bot.send_message(ADMIN_ID, "🔗 লিঙ্ক দিন:")
        bot.register_next_step_handler(msg, lambda ms: t_final(ms, img, name, desc, rew))
    except: bot.send_message(ADMIN_ID, "❌ রিওয়ার্ড সংখ্যায় দিন।")

def t_final(m, img, name, desc, rew):
    db['tasks'].append({'img': img, 'name': name, 'desc': desc, 'rew': rew, 'link': m.text, 'limit': 100})
    bot.send_message(ADMIN_ID, "✅ টাস্ক সফল!")

# --- ব্যালেন্স এডিট ---
def edit_b1(m):
    try:
        target = int(m.text)
        msg = bot.send_message(ADMIN_ID, "এমাউন্ট দিন (যেমন: 50 বা -50):")
        bot.register_next_step_handler(msg, lambda ms: edit_b2(ms, target))
    except: bot.send_message(ADMIN_ID, "❌ ভুল UID!")

def edit_b2(m, target):
    try:
        amt = float(m.text)
        db['users'][target]['balance'] += amt
        bot.send_message(ADMIN_ID, "✅ ব্যালেন্স আপডেট সফল।")
        bot.send_message(target, f"🔔 এডমিন আপনার ব্যালেন্স ৳{amt} পরিবর্তন করেছে।")
    except: bot.send_message(ADMIN_ID, "❌ ভুল এমাউন্ট!")

print("🚀 Bot is Updated & Active!")
bot.polling(none_stop=True)
