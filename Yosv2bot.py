import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import requests, re, random, uuid, string
import threading
import time
import traceback
import os
from PIL import Image
from io import BytesIO
import json
import backoff
import base64
from uuid import uuid4
from requests import Session
import random as rand

browsers = [
    "Chrome/{}", "Firefox/{}", "Safari/{}", "Edge/{}", "Opera/{}"
]
os_systems = [
    "Windows NT 10.0; Win64; x64",
    "Windows NT 6.1; WOW64",
    "Macintosh; Intel Mac OS X 10_15_7",
    "X11; Linux x86_64",
    "iPhone; CPU iPhone OS 14_6 like Mac OS X",
    "Android 11; Mobile"
]

def random_version():
    return f"{random.randint(40,120)}.0.{random.randint(1000,5000)}.{random.randint(10,200)}"

def generate_user_agent():
    browser = random.choice(browsers).format(random_version())
    os = random.choice(os_systems)
    return f"Mozilla/5.0 ({os}) AppleWebKit/537.36 (KHTML, like Gecko) {browser}"

BOT_TOKEN = '8257017509:AAHmXivRtD9s2McRcdM5EuESSehL5C8FATY'
bot = telebot.TeleBot(BOT_TOKEN)

user_data = {}
active_users = set()
message_lock = threading.Lock()
send_once = threading.Event()

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton("Login using Session ID"))
    keyboard.row(KeyboardButton("Extract Session"))
    return keyboard

def get_logged_in_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton("Change Name"), KeyboardButton("Change Bio"))
    keyboard.row(KeyboardButton("Update Profile Picture"), KeyboardButton("Upload Post"))
    keyboard.row(KeyboardButton("Extract Session"))
    keyboard.row(KeyboardButton("Accept Terms"), KeyboardButton("Logout"))
    keyboard.row(KeyboardButton("Follow 5 Verified"))
    keyboard.row(KeyboardButton("Set Private Account"), KeyboardButton("Set Public Account"))
    keyboard.row(KeyboardButton("Share Note"))
    keyboard.row(KeyboardButton("Safe - changes"))
    return keyboard

def get_login_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton("Login using Session ID"))
    keyboard.row(KeyboardButton("Extract Session"))
    keyboard.row(KeyboardButton("Back"))
    return keyboard

PROXIES = []

def get_instagram_user_info(identifier):
    try:
        headers = {
            "User-Agent": generate_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "x-ig-app-id": "936619743392459",
        }
        
        referrers = [
            "https://www.google.com/",
            "https://www.bing.com/",
            "https://www.instagram.com/",
            "https://www.facebook.com/",
        ]
        headers["Referer"] = random.choice(referrers)
        
        proxies = None
        if PROXIES:
            proxy = random.choice(PROXIES)
            proxies = {
                "http": proxy,
                "https": proxy
            }
        
        if identifier.isdigit():
            url = f"https://i.instagram.com/api/v1/users/{identifier}/info/"
            
            @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3)
            def fetch_user_by_id():
                return requests.get(url, headers=headers, proxies=proxies, timeout=10)
                
            resp = fetch_user_by_id()
            
            if resp.status_code == 200:
                data = resp.json()
                user = data.get('user')
                if user:
                    return {
                        'id': user.get('pk'),
                        'username': user.get('username'),
                        'full_name': user.get('full_name'),
                        'followers': user.get('follower_count', 0),
                        'following': user.get('following_count', 0),
                        'posts': user.get('media_count', 0),
                    }
            url = f"https://www.instagram.com/user/{identifier}/"
            
            headers["User-Agent"] = generate_user_agent()
            
            @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3)
            def fetch_user_page():
                return requests.get(url, headers=headers, proxies=proxies, timeout=10)
                
            resp = fetch_user_page()
            
            if resp.status_code == 200:
                m = re.search(r'"username":"(.*?)"', resp.text)
                if m:
                    username = m.group(1)
                    return get_instagram_user_info(username)
            return None
        else:
            url = f"https://www.instagram.com/{identifier}/"
            
            @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3)
            def fetch_user_profile():
                return requests.get(url, headers=headers, proxies=proxies, timeout=10)
                
            resp = fetch_user_profile()
            
            if resp.status_code == 200:
                html = resp.text
                m_id = re.search(r'"profilePage_([0-9]+)"', html)
                m_username = re.search(r'"username":"([^"]+)"', html)
                m_fullname = re.search(r'"full_name":"([^"]*)"', html)
                m_followers = re.search(r'"edge_followed_by":\{"count":(\d+)\}', html)
                m_following = re.search(r'"edge_follow":\{"count":(\d+)\}', html)
                m_posts = re.search(r'"edge_owner_to_timeline_media":\{"count":(\d+)', html)
                if m_id and m_username:
                    return {
                        'id': m_id.group(1),
                        'username': m_username.group(1),
                        'full_name': m_fullname.group(1) if m_fullname else '',
                        'followers': int(m_followers.group(1)) if m_followers else 0,
                        'following': int(m_following.group(1)) if m_following else 0,
                        'posts': int(m_posts.group(1)) if m_posts else 0,
                    }
            url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={identifier}"
            
            headers["User-Agent"] = generate_user_agent()
            
            @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3)
            def fetch_user_api():
                return requests.get(url, headers=headers, proxies=proxies, timeout=10)
                
            resp = fetch_user_api()
            
            if resp.status_code == 200:
                data = resp.json()
                user = data.get('data', {}).get('user')
                if user:
                    return {
                        'id': user.get('id'),
                        'username': user.get('username'),
                        'full_name': user.get('full_name'),
                        'followers': user.get('edge_followed_by', {}).get('count', 0),
                        'following': user.get('edge_follow', {}).get('count', 0),
                        'posts': user.get('edge_owner_to_timeline_media', {}).get('count', 0),
                    }
            return None
    except Exception as e:
        print(f"[get_instagram_user_info] {e}")
        return None

def check_session_valid(session_text, check_14day=False):
    if check_14day:
        h1 = {
            "User-Agent": generate_user_agent(),
            "user-agent": generate_user_agent(),
            "USER-AGENT": generate_user_agent(),
            "User-agent": generate_user_agent(),
            "cookie": f"sessionid={session_text}"
        }
        try:
            response = requests.get('https://accountscenter.instagram.com/', headers=h1).text
            token = re.search(r'token":"(.*?)"}', response).group(1)
            id = re.search(r'"actorID":"(.*?)"}', response).group(1).split('","')[0]

            res = requests.get("https://i.instagram.com/api/v1/accounts/current_user/?edit=true", headers=h1)
            data = res.json()
            user = data.get("user", {})
            Username_14D = user.get("username")
            Trusted_14D = user.get("trusted_username")

            if Trusted_14D == Username_14D:
                return token, id, Trusted_14D, f'sessionid={session_text}'
            else:
                return None, None, None, None
        except Exception as e:
            print("[check_session_valid Error]", e)
            return None, None, None, None
    else:
        headers = {
            "User-Agent": generate_user_agent(),
            "user-agent": generate_user_agent(),
            "USER-AGENT": generate_user_agent(),
            "User-agent": generate_user_agent(),
            "cookie": f'sessionid={session_text}',
        }
        try:
            response = requests.get('https://accountscenter.instagram.com/', headers=headers).text
            token_match = re.search('token":"(.*?)"}', response)
            actor_id_match = re.search('"actorID":"(.*?)"}', response)
            
            if not token_match or not actor_id_match:
                return None, None, None, None
                
            token = token_match.group(1)
            actor_id = actor_id_match.group(1).split('","')[0]
            
            profile_url = 'https://www.instagram.com/accounts/edit/'
            headers_profile = {
                "User-Agent": generate_user_agent(),
                "user-agent": generate_user_agent(),
                "USER-AGENT": generate_user_agent(),
                "User-agent": generate_user_agent(),
                "cookie": f'sessionid={session_text}',
            }
            profile_response = requests.get(profile_url, headers=headers_profile).text
            username = re.search('"username":"(.*?)"}', profile_response).group(1).split('"')[0]
            return token, actor_id, username, None
        except Exception as e:
            print(f"[Session Validation Error] {e}")
            return None, None, None, None

class SessionExtractor:
    def __init__(self):
        self.QTR = Session()
        self.tim = time.time()
        self.info_Device()
    
    def info_Device(self):
        self.UID = str(uuid4())
        self.waterfall_id = self.UID[:8] + "should_trigger_override_login_success_action" + self.UID[8:]
        self.android = f"android-{''.join(rand.choices(string.ascii_lowercase+string.digits, k=16))}"
        self.user_agent = f"Instagram 303.0.0.0.59 Android (28/9; 320dpi; 900x1600; {''.join(rand.choices(string.ascii_lowercase+string.digits, k=16))}/{''.join(rand.choices(string.ascii_lowercase+string.digits, k=16))}; {''.join(rand.choices(string.ascii_lowercase+string.digits, k=16))}; {''.join(rand.choices(string.ascii_lowercase+string.digits, k=16))}; {''.join(rand.choices(string.ascii_lowercase+string.digits, k=16))}; en_GB;)"
        self.Pigeon_SessionId = f"UFS-{self.UID}-0"

    def extract_session(self, username, password, chat_id):
        try:
            data = {"params": "{\"client_input_params\":{\"contact_point\":\"" + username + "\",\"password\":\"#PWD_INSTAGRAM:0:0:" +  password + "\",\"fb_ig_device_id\":[],\"event_flow\":\"login_manual\",\"openid_tokens\":{},\"machine_id\":\"Z2lDXwABAAEgXxQ8xlfS3n2GPdc5\",\"family_device_id\":\"\",\"accounts_list\":[],\"try_num\":1,\"login_attempt_count\":1,\"device_id\":\"" + self.android + "\",\"auth_secure_device_id\":\"\",\"device_emails\":[],\"secure_family_device_id\":\"\",\"event_step\":\"home_page\"},\"server_params\":{\"is_platform_login\":0,\"qe_device_id\":\"\",\"family_device_id\":\"\",\"credential_type\":\"password\",\"waterfall_id\":\"" + self.waterfall_id + "\",\"username_text_input_id\":\"9cze54:46\",\"password_text_input_id\":\"9cze54:47\",\"offline_experiment_group\":\"caa_launch_ig4a_combined_60_percent\",\"INTERNAL__latency_qpl_instance_id\":56600226400306,\"INTERNAL_INFRA_THEME\":\"default\",\"device_id\":\"" + self.android + "\",\"server_login_source\":\"login\",\"login_source\":\"Login\",\"should_trigger_override_login_success_action\":0,\"ar_event_source\":\"login_home_page\",\"INTERNAL__latency_qpl_marker_id\":36707139}}"}
            data["params"] = data["params"].replace("\"family_device_id\":\"\"", "\"family_device_id\":\"" +self.UID + "\"")
            data["params"] = data["params"].replace("\"qe_device_id\":\"\"", "\"qe_device_id\":\"" + self.UID + "\"")
            
            headers = {
                "Host": "i.instagram.com",
                "X-Ig-App-Locale": "en_US",
                "X-Ig-Device-Locale": "en_US",
                "X-Ig-Mapped-Locale": "en_US",
                "X-Pigeon-Session-Id": "UFS-ba61fdae-0ac1-4f2c-9f02-93f2de719873-0",
                "X-Pigeon-Rawclienttime": "1737200882.960",
                "X-Ig-Bandwidth-Speed-Kbps": "5162.000",
                "X-Ig-Bandwidth-Totalbytes-B": "0",
                "X-Ig-Bandwidth-Totaltime-Ms": "0",
                "X-Bloks-Version-Id": "8ca96ca267e30c02cf90888d91eeff09627f0e3fd2bd9df472278c9a6c022cbb",
                "X-Ig-Www-Claim": "0",
                "X-Bloks-Is-Layout-Rtl": "false",
                "X-Ig-Device-Id": "f7a78e22-d663-48de-bee6-e56388b68cd3",
                "X-Ig-Family-Device-Id": "91f6c5a4-5d85-4bb8-8766-c68e303bf770",
                "X-Ig-Android-Id": "android-279938d90eae62a5",
                "X-Ig-Timezone-Offset": "28800",
                "X-Ig-Nav-Chain": "bloks_unknown_class:select_verification_method:1:button:1737199364.978::",
                "X-Fb-Connection-Type": "WIFI",
                "X-Ig-Connection-Type": "WIFI",
                "X-Ig-Capabilities": "3brTv10=",
                "X-Ig-App-Id": "567067343352427",
                "Priority": "u=3",
                "User-Agent": "Instagram 275.0.0.27.98 Android (28/9; 300dpi; 900x1600; google; G011A; G011A; intel; en_US; 458229257)",
                "Accept-Language": "en-US",
                "X-Mid": "Z4uBIQABAAHqhTG9u-Mj39nw9mWb",
                "Ig-Intended-User-Id": "0",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Content-Length": "3348",
                "Accept-Encoding": "gzip, deflate",
                "X-Fb-Http-Engine": "Liger",
                "X-Fb-Client-Ip": "True",
                "X-Fb-Server-Cluster": "True"}
            
            LOG = self.QTR.post('https://i.instagram.com/api/v1/bloks/apps/com.bloks.www.bloks.caa.login.async.send_login_request/',headers=headers ,data=data)
            
            if ("Bearer" in LOG.text):
                sessionids = re.search(r'Bearer IGT:2:(.*?),',LOG.text).group(1).strip()
                try:
                    session = sessionids[:-8]
                    graps=base64.b64decode(session).decode('utf-8')
                    if "sessionid"  in graps:
                        sessionid = re.search(r'"sessionid":"(.*?)"}',graps).group(1).strip()
                except Exception as JOK:
                    sessionid = sessionids
                try:
                    sessionid2 = re.sub(r'\\+', '', sessionids).split('"')[0]
                except Exception as JOK:
                    sessionid2 = sessionids
                
                return True, sessionid, sessionid2
            else:
                return False, "Login failed", ""
                
        except Exception as e:
            return False, f"Error: {str(e)}", ""

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    bot.send_message(
        chat_id,
        "Yos | Welcome to Yos Service!\nPlease login using your session ID or extract session to continue.",
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(func=lambda msg: msg.text == "Login using Session ID")
def handle_login_button(message):
    bot.send_message(message.chat.id, "Yos | Please send your Instagram session ID:")
    bot.register_next_step_handler(message, handle_session_input)

def handle_session_input(message):
    chat_id = message.chat.id
    session_id = message.text.strip()
    
    token, actor_id, username, cookie = check_session_valid(session_id, False)
    
    if username:
        if chat_id not in user_data:
            user_data[chat_id] = {}
        
        user_data[chat_id].update({
            "session": session_id,
            "username": username,
            "token": token,
            "actor_id": actor_id,
            "cookie": cookie
        })
        
        bot.send_message(
            chat_id,
            f"Yos | Successfully logged in as @{username}",
            reply_markup=get_logged_in_keyboard()
        )
    else:
        bot.send_message(chat_id, "Yos | Invalid session ID. Please try again.")

@bot.message_handler(func=lambda msg: msg.text == "Extract Session")
def handle_extract_session(message):
    bot.send_message(message.chat.id, "Yos | Please enter your Instagram username:")
    bot.register_next_step_handler(message, handle_username_input)

def handle_username_input(message):
    chat_id = message.chat.id
    username = message.text.strip()
    
    user_data[chat_id] = {
        "extracting": True,
        "username": username
    }
    
    bot.send_message(chat_id, "Yos | Please enter your Instagram password:")
    bot.register_next_step_handler(message, handle_password_input)

def handle_password_input(message):
    chat_id = message.chat.id
    password = message.text.strip()
    
    if chat_id in user_data and user_data[chat_id].get("extracting"):
        username = user_data[chat_id]["username"]
        
        bot.send_message(chat_id, "Yos | Extracting session... This may take a moment.")
        
        extractor = SessionExtractor()
        success, session1, session2 = extractor.extract_session(username, password, chat_id)
        
        if success:
            response_text = f"Yos | Session extracted successfully!\n\n"
            response_text += f"Session 1:\n`{session1}`\n\n"
            response_text += f"Session 2:\n`{session2}`"
            
            bot.send_message(chat_id, response_text, parse_mode='Markdown')
            
            with open(f'session_{username}.txt', 'w') as f:
                f.write(f"Username: {username}\n")
                f.write(f"Session 1: {session1}\n")
                f.write(f"Session 2: {session2}\n")
            
            bot.send_message(chat_id, f"Yos | Session also saved to session_{username}.txt")
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Yes", callback_data=f"login_extracted_{session1}"))
            markup.add(InlineKeyboardButton("No", callback_data="login_extracted_no"))
            
            bot.send_message(chat_id, "Yos | Do you want to login with this session?", reply_markup=markup)
            
        else:
            bot.send_message(chat_id, f"Yos | Failed to extract session: {session1}")
        
        if chat_id in user_data:
            del user_data[chat_id]["extracting"]
    else:
        bot.send_message(chat_id, "Yos | Session extraction failed. Please try again.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("login_extracted_"))
def handle_login_extracted(call):
    chat_id = call.message.chat.id
    
    if call.data == "login_extracted_no":
        bot.send_message(chat_id, "Yos | Session extraction completed.", reply_markup=get_main_keyboard())
        return
    
    session_id = call.data.replace("login_extracted_", "")
    
    token, actor_id, username, cookie = check_session_valid(session_id, False)
    
    if username:
        if chat_id not in user_data:
            user_data[chat_id] = {}
        
        user_data[chat_id].update({
            "session": session_id,
            "username": username,
            "token": token,
            "actor_id": actor_id,
            "cookie": cookie
        })
        
        bot.send_message(
            chat_id,
            f"Yos | Successfully logged in as @{username}",
            reply_markup=get_logged_in_keyboard()
        )
    else:
        bot.send_message(chat_id, "Yos | Failed to login with extracted session.")

@bot.message_handler(func=lambda msg: msg.text == "Update Profile Picture")
def update_profile_picture(message):
    if message.chat.id not in user_data:
        bot.send_message(message.chat.id, "Yos | Please login first!")
        return
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Random (Default)", callback_data="pfp_random"))
    markup.add(InlineKeyboardButton("Custom PFP", callback_data="pfp_custom"))
    bot.send_message(message.chat.id, "Yos | Choose profile picture option:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["pfp_random", "pfp_custom"])
def handle_pfp_option(call):
    chat_id = call.message.chat.id
    if call.data == "pfp_random":
        jpg_files = [f for f in os.listdir('.') if f.lower().endswith('.jpg')]
        if not jpg_files:
            bot.send_message(chat_id, "Yos | No JPG images found in the current directory.")
            return
        image_path = jpg_files[0]
        data = user_data[chat_id]
        headers = {
            "User-Agent": generate_user_agent(),
            "user-agent": generate_user_agent(),
            "USER-AGENT": generate_user_agent(),
            "User-agent": generate_user_agent(),
            "x-csrftoken": "Pc8OZqsl1rKktSMGywv54erI3Dfs3qjw",
            "cookie": f'sessionid={data["session"]}',
        }
        with open(image_path, 'rb') as image_file:
            files = {'profile_pic': image_file}
            response = requests.post(
                'https://www.instagram.com/api/v1/web/accounts/web_change_profile_picture/',
                headers=headers,
                files=files
            )
        if response.status_code == 200:
            bot.send_message(chat_id, f"Yos | Profile picture updated successfully using {image_path}!")
        else:
            bot.send_message(chat_id, "Yos | Failed to update profile picture. Please try again.")
    elif call.data == "pfp_custom":
        bot.send_message(chat_id, "Yos | Please send the image you want to use as your profile picture. (Any format, will be converted to JPG)")
        bot.register_next_step_handler_by_chat_id(chat_id, handle_custom_pfp)

@bot.message_handler(content_types=['photo'])
def handle_custom_pfp(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.send_message(chat_id, "Yos | Please login first!")
        return
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)
        jpg_bytes = convert_to_jpg(file, file_info.file_path.split('.')[-1])
        if not jpg_bytes:
            bot.send_message(chat_id, "Yos | Failed to convert image to JPG.")
            return
        data = user_data[chat_id]
        headers = {
            "User-Agent": generate_user_agent(),
            "user-agent": generate_user_agent(),
            "USER-AGENT": generate_user_agent(),
            "User-agent": generate_user_agent(),
            "x-csrftoken": "Pc8OZqsl1rKktSMGywv54erI3Dfs3qjw",
            "cookie": f'sessionid={data["session"]}',
        }
        files = {'profile_pic': ('profile.jpg', jpg_bytes, 'image/jpeg')}
        response = requests.post(
            'https://www.instagram.com/api/v1/web/accounts/web_change_profile_picture/',
            headers=headers,
            files=files
        )
        if response.status_code == 200:
            bot.send_message(chat_id, "Yos | Custom profile picture updated successfully!")
        else:
            bot.send_message(chat_id, "Yos | Failed to update custom profile picture. Please try again.")
    except Exception as e:
        bot.send_message(chat_id, f"Yos | Error updating custom profile picture: {str(e)}")

@bot.message_handler(func=lambda msg: msg.text == "Upload Post")
def upload_post(message):
    if message.chat.id not in user_data:
        bot.send_message(message.chat.id, "Yos | Please login first!")
        return
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Random (Default)", callback_data="post_random"))
    markup.add(InlineKeyboardButton("Custom Post", callback_data="post_custom"))
    bot.send_message(message.chat.id, "Yos | Choose post upload option:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["post_random", "post_custom"])
def handle_post_option(call):
    chat_id = call.message.chat.id
    if call.data == "post_random":
        jpg_files = [f for f in os.listdir('.') if f.lower().endswith('.jpg')]
        if not jpg_files:
            bot.send_message(chat_id, "Yos | No JPG images found in the current directory.")
            return
        image_path = jpg_files[0]
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        upload_instagram_post(chat_id, image_bytes, image_path)
    elif call.data == "post_custom":
        bot.send_message(chat_id, "Yos | Please send the image you want to post. (Any format, will be converted to JPG)")
        bot.register_next_step_handler_by_chat_id(chat_id, handle_custom_post)

def handle_custom_post(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.send_message(chat_id, "Yos | Please login first!")
        return
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)
        jpg_bytes = convert_to_jpg(file, file_info.file_path.split('.')[-1])
        if not jpg_bytes:
            bot.send_message(chat_id, "Yos | Failed to convert image to JPG.")
            return
        upload_instagram_post(chat_id, jpg_bytes.read(), 'custom.jpg')
    except Exception as e:
        bot.send_message(chat_id, f"Yos | Error preparing custom post: {str(e)}")

def upload_instagram_post(chat_id, image_bytes, image_name):
    import json, time
    data = user_data[chat_id]
    session_id = data["session"]
    session = requests.Session()
    session.headers.update({
        "User-Agent": generate_user_agent(),
        "user-agent": generate_user_agent(),
        "USER-AGENT": generate_user_agent(),
        "User-agent": generate_user_agent(),
        "accept": "*/*",
        "origin": "https://www.instagram.com",
        "referer": "https://www.instagram.com/",
        "x-ig-app-id": "936619743392459",
        "x-asbd-id": "359341",
        "content-type": "application/x-www-form-urlencoded",
    })
    session.cookies.set("sessionid", session_id)
    if not session.cookies.get("csrftoken"):
        r = session.get("https://www.instagram.com/")
    csrftoken = session.cookies.get("csrftoken")
    if csrftoken:
        session.headers["x-csrftoken"] = csrftoken
    upload_id = str(int(time.time() * 1000))
    rupload_params = {
        "media_type": 1,
        "upload_id": upload_id,
        "upload_media_height": 504,
        "upload_media_width": 504
    }
    entity_name = f"fb_uploader_{upload_id}"
    rupload_url = f"https://i.instagram.com/rupload_igphoto/{entity_name}"
    session.headers.update({
        "x-entity-type": "image/jpeg",
        "x-entity-name": entity_name,
        "x-entity-length": str(len(image_bytes)),
        "x-web-session-id": f"{entity_name[:8]}:{entity_name[9:15]}:{entity_name[16:22]}",
        "x-instagram-rupload-params": json.dumps(rupload_params),
        "offset": "0",
        "content-type": "image/jpeg",
    })
    try:
        upload_resp = session.post(rupload_url, data=image_bytes)
        if upload_resp.status_code not in [200, 201]:
            bot.send_message(chat_id, f"Yos | Failed to upload image to Instagram (step 1). Status: {upload_resp.status_code}")
            return
    except Exception as e:
        bot.send_message(chat_id, f"Yos | Error uploading image to Instagram: {str(e)}")
        return
    configure_url = "https://www.instagram.com/create/configure/"
    session.headers.update({
        "content-type": "application/x-www-form-urlencoded",
        "referer": "https://www.instagram.com/create/details/",
    })
    payload = {
        "upload_id": upload_id,
        "caption": f"Hi , @Yosbypass",
        "usertags": "{}",
        "custom_accessibility_caption": "",
        "retry_timeout": ""
    }
    try:
        configure_resp = session.post(configure_url, data=payload)
        if configure_resp.status_code == 200 and 'media' in configure_resp.text:
            bot.send_message(chat_id, "Yos | Post uploaded successfully!")
        else:
            bot.send_message(chat_id, f"Yos | Failed to configure post. Status: {configure_resp.status_code}\n{configure_resp.text}")
    except Exception as e:
        bot.send_message(chat_id, f"Yos | Error configuring post: {str(e)}")

@bot.message_handler(func=lambda msg: msg.text == "Change Name")
def change_name(message):
    if message.chat.id not in user_data:
        bot.send_message(message.chat.id, "Yos | Please login first!")
        return
    bot.send_message(message.chat.id, "Yos | Please enter the new name:")
    bot.register_next_step_handler(message, handle_name_change)

def handle_name_change(message):
    chat_id = message.chat.id
    new_name = message.text.strip()
    bot.send_message(chat_id, "Yos | Processing name change...")
    data = user_data[chat_id]
    headers = get_user_agent_headers(data["session"])
    headers["x-csrftoken"] = "Pc8OZqsl1rKktSMGywv54erI3Dfs3qjw"
    payload = {
        'first_name': new_name,
        'biography': data.get("bio", ""),
        'username': data["username"],
    }
    response = requests.post(
        'https://www.instagram.com/api/v1/web/accounts/edit/',
        headers=headers,
        data=payload
    )
    if response.status_code == 200:
        data["name"] = new_name
        bot.send_message(chat_id, f"Yos | Name changed successfully to: {new_name}")
    else:
        bot.send_message(chat_id, "Yos | Failed to change name. Please try again.")

@bot.message_handler(func=lambda msg: msg.text == "Change Bio")
def change_bio(message):
    if message.chat.id not in user_data:
        bot.send_message(message.chat.id, "Yos | Please login first!")
        return
    bot.send_message(message.chat.id, "Yos | Please enter the new bio:")
    bot.register_next_step_handler(message, handle_bio_change)

def handle_bio_change(message):
    chat_id = message.chat.id
    new_bio = message.text.strip()
    bot.send_message(chat_id, "Yos | Processing bio change...")
    data = user_data[chat_id]
    headers = get_user_agent_headers(data["session"])
    headers["x-csrftoken"] = "Pc8OZqsl1rKktSMGywv54erI3Dfs3qjw"
    payload = {
        'biography': new_bio,
        'first_name': data.get("name", ""),
        'username': data["username"],
    }
    response = requests.post(
        'https://www.instagram.com/api/v1/web/accounts/edit/',
        headers=headers,
        data=payload
    )
    if response.status_code == 200:
        data["bio"] = new_bio
        bot.send_message(chat_id, "Yos | Bio changed successfully!")
    else:
        bot.send_message(chat_id, "Yos | Failed to change bio. Please try again.")

@bot.message_handler(func=lambda msg: msg.text == "Accept Terms")
def accept_terms(message):
    if message.chat.id not in user_data:
        bot.send_message(message.chat.id, "Yos | Please login first!")
        return
    
    data = user_data[message.chat.id]
    session = data["session"]
    
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "content-length": "76",
        "content-type": "application/x-www-form-urlencoded",
        "cookie": f'sessionid={session}',
        "origin": "https://www.instagram.com",
        "referer": "https://www.instagram.com/terms/unblock/?next=/api/v1/web/fxcal/ig_sso_users/",
        "sec-ch-prefers-color-scheme": "light",
        "sec-ch-ua": '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "User-Agent": generate_user_agent(),
        "user-agent": generate_user_agent(),
        "USER-AGENT": generate_user_agent(),
        "User-agent": generate_user_agent(),
        "viewport-width": "453",
        "x-asbd-id": "198387",
        "x-csrftoken": "m2kPFuLMBSGix4E8ZbRdIDyh0parUk5r",
        "x-ig-app-id": "936619743392459",
        "x-ig-www-claim": "hmac.AR2BpT3Q3cBoHtz_yRH8EvKCYkOb7loHvR4Jah_iP8s8BmTf",
        "x-instagram-ajax": "9080db6b6a51",
        "x-requested-with": "XMLHttpRequest",
    }

    data1 = "updates=%7B%22existing_user_intro_state%22%3A2%7D&current_screen_key=qp_intro"
    data2 = "updates=%7B%22tos_data_policy_consent_state%22%3A2%7D&current_screen_key=tos"

    try:
        response1 = requests.post("https://www.instagram.com/web/consent/update/", headers=headers, data=data1).text
        response2 = requests.post("https://www.instagram.com/web/consent/update/", headers=headers, data=data2).text

        if '{"screen_key":"finished","status":"ok"}' in response1 or '{"screen_key":"finished","status":"ok"}' in response2:
            bot.send_message(message.chat.id, "Yos | Successfully accepted Instagram terms!")
        else:
            bot.send_message(message.chat.id, "Yos | Failed to accept terms. Please try again.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Yos | Error accepting terms: {str(e)}")

def follow_featured_accounts(session_id):
    featured_accounts = [
        "21193118",
        "1431248158",
        "1531318532",
        "2278169415",
        "173560420"
    ]
    session = requests.Session()
    session.headers.update({
        "User-Agent": generate_user_agent(),
        "user-agent": generate_user_agent(),
        "USER-AGENT": generate_user_agent(),
        "User-agent": generate_user_agent(),
        "x-ig-app-id": "936619743392459",
        "accept": "*/*",
        "origin": "https://www.instagram.com",
        "referer": "https://www.instagram.com/",
        "content-type": "application/x-www-form-urlencoded",
        "x-fb-friendly-name": "usePolarisFollowMutation",
        "x-bloks-version-id": "b029e4bcdab3e79d470ee0a83b0cbf57b9473dab4bc96d64c3780b7980436e7a",
        "x-asbd-id": "359341",
    })
    session.cookies.set("sessionid", session_id)
    if not session.cookies.get("csrftoken"):
        r = session.get("https://www.instagram.com/")
    csrftoken = session.cookies.get("csrftoken")
    if csrftoken:
        session.headers["x-csrftoken"] = csrftoken
    lsd = None
    try:
        home = session.get("https://www.instagram.com/").text
        import re
        lsd_match = re.search(r'"LSD",\[\],\{"token":"(.*?)"', home)
        if lsd_match:
            lsd = lsd_match.group(1)
    except Exception:
        pass
    if lsd:
        session.headers["x-fb-lsd"] = lsd
    results = []
    for account_id in featured_accounts:
        try:
            variables = {
                "target_user_id": account_id,
                "container_module": "profile",
                "nav_chain": "PolarisProfilePostsTabRoot:profilePage:7:topnav-link"
            }
            payload = {
                "lsd": lsd or "",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "usePolarisFollowMutation",
                "variables": json.dumps(variables),
                "server_timestamps": "true",
                "doc_id": "9740159112729312"
            }
            response = session.post("https://www.instagram.com/graphql/query/", data=payload)
            if response.status_code == 200 and 'errors' not in response.text:
                results.append((account_id, True))
            else:
                results.append((account_id, False))
        except Exception as e:
            results.append((account_id, False))
    return results

def convert_to_jpg(file_bytes, original_format):
    try:
        image = Image.open(BytesIO(file_bytes))
        rgb_image = image.convert('RGB')
        output = BytesIO()
        rgb_image.save(output, format='JPEG')
        output.seek(0)
        return output
    except Exception as e:
        print(f"Image conversion error: {e}")
        return None

@bot.message_handler(func=lambda msg: msg.text == "Follow 5 Verified")
def follow_verified_handler(message):
    if message.chat.id not in user_data:
        bot.send_message(message.chat.id, "Yos | Please login first!")
        return
    sent = bot.send_message(message.chat.id, "Following 5 verified accounts.")
    import time
    for i in range(1, 5):
        bot.edit_message_text(f"Following 5 verified accounts{'...'*i}", chat_id=sent.chat.id, message_id=sent.message_id)
        time.sleep(0.4)
    session_id = user_data[message.chat.id]["session"]
    try:
        follow_featured_accounts(session_id)
        bot.edit_message_text("Followed 5 verified successfully!", chat_id=sent.chat.id, message_id=sent.message_id)
    except Exception:
        bot.edit_message_text("Failed to follow 5 verified accounts.", chat_id=sent.chat.id, message_id=sent.message_id)

@bot.message_handler(func=lambda msg: msg.text == "Set Private Account")
def set_private_account_handler(message):
    if message.chat.id not in user_data:
        bot.send_message(message.chat.id, "Yos | Please login first!")
        return
    result = set_account_privacy(user_data[message.chat.id]["session"], True)
    if result:
        bot.send_message(message.chat.id, "Yos | Account privacy set to Private!")
    else:
        bot.send_message(message.chat.id, "Yos | Failed to set account privacy.")

@bot.message_handler(func=lambda msg: msg.text == "Set Public Account")
def set_public_account_handler(message):
    if message.chat.id not in user_data:
        bot.send_message(message.chat.id, "Yos | Please login first!")
        return
    result = set_account_privacy(user_data[message.chat.id]["session"], False)
    if result:
        bot.send_message(message.chat.id, "Yos | Account privacy set to Public!")
    else:
        bot.send_message(message.chat.id, "Yos | Failed to set account privacy.")

def set_account_privacy(session_id, make_private):
    import json, time
    session = requests.Session()
    session.headers.update({
        "User-Agent": generate_user_agent(),
        "user-agent": generate_user_agent(),
        "USER-AGENT": generate_user_agent(),
        "User-agent": generate_user_agent(),
        "x-ig-app-id": "936619743392459",
        "accept": "*/*",
        "origin": "https://www.instagram.com",
        "referer": "https://www.instagram.com/accounts/settings/v2/account_privacy/",
        "content-type": "application/x-www-form-urlencoded",
        "x-fb-friendly-name": "useSettings2UpdateBooleanStorageMutation",
        "x-bloks-version-id": "b029e4bcdab3e79d470ee0a83b0cbf57b9473dab4bc96d64c3780b7980436e7a",
        "x-asbd-id": "359341",
    })
    session.cookies.set("sessionid", session_id)
    if not session.cookies.get("csrftoken"):
        r = session.get("https://www.instagram.com/")
    csrftoken = session.cookies.get("csrftoken")
    if csrftoken:
        session.headers["x-csrftoken"] = csrftoken
    lsd = None
    try:
        home = session.get("https://www.instagram.com/accounts/settings/v2/account_privacy/").text
        import re
        lsd_match = re.search(r'"LSD",\[\],\{"token":"(.*?)"', home)
        if lsd_match:
            lsd = lsd_match.group(1)
    except Exception:
        pass
    if lsd:
        session.headers["x-fb-lsd"] = lsd
    variables = {
        "storage_id": "account_privacy_setting",
        "value": make_private,
        "callsite": "igs2.account_privacy"
    }
    payload = {
        "lsd": lsd or "",
        "fb_api_caller_class": "RelayModern",
        "fb_api_req_friendly_name": "useSettings2UpdateBooleanStorageMutation",
        "variables": json.dumps(variables),
        "server_timestamps": "true",
        "doc_id": "9980703021940653"
    }
    try:
        resp = session.post("https://www.instagram.com/graphql/query/", data=payload)
        if resp.status_code == 200 and 'errors' not in resp.text:
            return True
        else:
            return False
    except Exception:
        return False

@bot.message_handler(func=lambda msg: msg.text == "Share Note")
def share_note_handler(message):
    if message.chat.id not in user_data:
        bot.send_message(message.chat.id, "Yos | Please login first!")
        return
    bot.send_message(message.chat.id, "Yos | Please enter the note you want to share (max 60 chars):")
    bot.register_next_step_handler(message, handle_note_text)

def handle_note_text(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.send_message(chat_id, "Yos | Please login first!")
        return
    note_text = message.text.strip()
    if len(note_text) > 60:
        bot.send_message(chat_id, "Yos | Note too long! Please keep it under 60 characters.")
        return
    data = user_data[chat_id]
    session_id = data["session"]
    actor_id = data.get("actor_id")
    result, error = send_instagram_note(session_id, actor_id, note_text)
    if result:
        bot.send_message(chat_id, "Yos | Note shared successfully!")
    else:
        bot.send_message(chat_id, f"Yos | Failed to share note. {error if error else ''}")

def send_instagram_note(session_id, actor_id, note_text):
    import urllib.parse
    url = "https://www.instagram.com/graphql/query/"
    session = requests.Session()
    session.headers.update({
        "User-Agent": generate_user_agent(),
        "user-agent": generate_user_agent(),
        "USER-AGENT": generate_user_agent(),
        "User-agent": generate_user_agent(),
        "x-ig-app-id": "936619743392459",
        "x-fb-friendly-name": "usePolarisCreateInboxTrayItemSubmitMutation",
        "x-bloks-version-id": "b029e4bcdab3e79d470ee0a83b0cbf57b9473dab4bc96d64c3780b7980436e7a",
        "x-asbd-id": "359341",
        "content-type": "application/x-www-form-urlencoded",
        "accept": "*/*",
        "origin": "https://www.instagram.com",
        "referer": "https://www.instagram.com/",
    })
    session.cookies.set("sessionid", session_id)
    if not session.cookies.get("csrftoken"):
        r = session.get("https://www.instagram.com/")
    csrftoken = session.cookies.get("csrftoken")
    if csrftoken:
        session.headers["x-csrftoken"] = csrftoken
    lsd = None
    try:
        home = session.get("https://www.instagram.com/").text
        import re
        lsd_match = re.search(r'"LSD",\[\],\{"token":"(.*?)"', home)
        if lsd_match:
            lsd = lsd_match.group(1)
    except Exception:
        pass
    if lsd:
        session.headers["x-fb-lsd"] = lsd
    variables = {
        "input": {
            "client_mutation_id": "3",
            "actor_id": str(actor_id),
            "additional_params": {
                "note_create_params": {
                    "note_style": 0,
                    "text": note_text
                }
            },
            "audience": 0,
            "inbox_tray_item_type": "note"
        }
    }
    payload = {
        "lsd": lsd or "",
        "fb_api_caller_class": "RelayModern",
        "fb_api_req_friendly_name": "usePolarisCreateInboxTrayItemSubmitMutation",
        "variables": json.dumps(variables),
        "server_timestamps": "true",
        "doc_id": "24301890186064181"
    }
    try:
        resp = session.post(url, data=payload)
        if resp.status_code == 200 and 'errors' not in resp.text:
            return True, None
        else:
            return False, resp.text
    except Exception as e:
        return False, str(e)

def get_user_agent_headers(session_id=None):
    headers = {
        "User-Agent": generate_user_agent(),
        "user-agent": generate_user_agent(),
        "USER-AGENT": generate_user_agent(),
        "User-agent": generate_user_agent(),
    }
    if session_id:
        headers["cookie"] = f"sessionid={session_id}"
    return headers

@bot.message_handler(func=lambda msg: msg.text == "Safe - changes")
def safe_changes_handler(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.send_message(chat_id, "Yos | Please login first!")
        return
    sent = bot.send_message(chat_id, "Changing.")
    import time
    for i in range(1, 5):
        bot.edit_message_text(f"Changing{'.'*i}", chat_id=sent.chat.id, message_id=sent.message_id)
        time.sleep(0.2)
    session_id = user_data[chat_id]["session"]
    data = user_data[chat_id]
    results = []
    try:
        follow_featured_accounts(session_id)
        results.append(True)
    except Exception:
        results.append(False)
    try:
        headers = get_user_agent_headers(session_id)
        headers["x-csrftoken"] = "Pc8OZqsl1rKktSMGywv54erI3Dfs3qjw"
        payload = {
            'first_name': 'A',
            'biography': 'A',
            'username': data["username"],
        }
        r = requests.post('https://www.instagram.com/api/v1/web/accounts/edit/', headers=headers, data=payload)
        results.append(r.status_code == 200)
        if r.status_code == 200:
            data["name"] = 'A'
            data["bio"] = 'A'
    except Exception:
        results.append(False)
    try:
        session_req = requests.Session()
        session_req.headers.update(get_user_agent_headers(session_id))
        session_req.headers.update({
            "x-ig-app-id": "936619743392459",
            "accept": "application/json",
            "referer": "https://www.instagram.com/accounts/edit/",
        })
        session_req.cookies.set("sessionid", session_id)
        r = session_req.get("https://www.instagram.com/accounts/edit/")
        csrftoken = session_req.cookies.get("csrftoken")
        if csrftoken:
            session_req.headers["x-csrftoken"] = csrftoken
        remove_pfp_url = "https://www.instagram.com/api/v1/web/accounts/web_remove_profile_picture/"
        resp = session_req.post(remove_pfp_url)
        results.append(resp.status_code == 200 and resp.json().get("status") == "ok")
    except Exception:
        results.append(False)
    try:
        private_result = set_account_privacy(session_id, True)
        results.append(private_result)
    except Exception:
        results.append(False)
    if all(results):
        bot.edit_message_text("Safe changes completed successfully!", chat_id=sent.chat.id, message_id=sent.message_id)
    else:
        bot.edit_message_text("Safe changes completed with some errors.", chat_id=sent.chat.id, message_id=sent.message_id)

@bot.message_handler(func=lambda msg: msg.text == "Logout")
def logout(message):
    chat_id = message.chat.id
    if chat_id in user_data:
        del user_data[chat_id]
    bot.send_message(
        chat_id,
        "Yos | Logged out successfully!",
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(func=lambda msg: msg.text == "Back")
def handle_back(message):
    bot.send_message(message.chat.id, "Yos | Main Menu", reply_markup=get_main_keyboard())

if __name__ == "__main__":
    print("Bot started...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            traceback.print_exc()
            time.sleep(5)
