#— — — — — — — — — — — — —

import requests, telebot
from telebot import types

#— — — — — — — — — — — — —
bot = telebot.TeleBot(input(' - Enter Token : '))

#— — — — — — — — — — — — —
@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(m.chat.id, "Enter Username : ")
    bot.register_next_step_handler(m, info)

#— — — — — — — — — — — — —
def info(m):
    u = m.text.strip()
    d = requests.get(f"https://sherifbots.serv00.net/Api/insta.php?user={u}").json()["data"]["data"]
    cap = f"""<b>— — — — — — — — — — — — —\nName : {d.get('full_name')}
User : {d.get('username')}
ID : {d.get('id')}
Followers : {d.get('follower_count')}
Following : {d.get('following_count')}
Posts : {d.get('media_count')}
Private : {"نعم" if d.get("is_private") else "لا"}
Verified : {"نعم" if d.get("is_verified") else "لا"}
Bio : {d.get('biography')}
External : {d.get('external_url')}
\n— — — — — — — — — — — — —</b>"""
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(" - YOSEIF - ", url="https://t.me/yoseifinstaa")
    markup.add(btn)
    bot.send_photo(
        m.chat.id,
        d.get("profile_pic_url_hd"),
        caption=cap,
        parse_mode="HTML",
        reply_markup=markup)
bot.infinity_polling()