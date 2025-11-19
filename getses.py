import requests, uuid, random, re, ctypes, json, urllib, hashlib, hmac, urllib.parse, base64, os, string
from time import sleep
import time
import telebot
from telebot import types

BOT_TOKEN = "8294753596:AAEC3vza4ocP6-jsTIBSa8Tt_On5d2JmTKA" # حط توكن بوتك بين علامات الترقيم
bot = telebot.TeleBot(BOT_TOKEN)

user_states = {}

timestamp = str(int(time.time()))

def RandomStringUpper(n=10):
    letters = string.ascii_uppercase + '1234567890'
    return ''.join(random.choice(letters) for i in range(n))

def RandomString(n=10):
    letters = string.ascii_lowercase + '1234567890'
    return ''.join(random.choice(letters) for i in range(n))

def RandomStringChars(n=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(n))

def randomStringWithChar(stringLength=10):
    letters = string.ascii_lowercase + '1234567890'
    result = ''.join(random.choice(letters) for i in range(stringLength - 1))
    return RandomStringChars(1) + result

uu = '83f2000a-4b95-4811-bc8d-0f3539ef07cf'

def generate_DeviceId(ID):
    volatile_ID = "12345"
    m = hashlib.md5()
    m.update(ID.encode('utf-8') + volatile_ID.encode('utf-8'))
    return 'android-' + m.hexdigest()[:16]

class InstagramSession:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.sesstings = self.Sesstings()
        self.coo = None
        self.token = None
        self.mid = None
        self.DeviceID = None
        self.sessionid = None
        self.username = None
        self.passwordd = None
        self.req = None

    class Sesstings:
        def generateUSER_AGENT(self):
            Devices_menu = ['HUAWEI', 'Xiaomi', 'samsung', 'OnePlus']
            DPIs = ['480', '320', '640', '515', '120', '160', '240', '800']
            randResolution = random.randrange(2, 9) * 180
            lowerResolution = randResolution - 180
            DEVICE_SETTINTS = {
                'system': "Android",
                'Host': "Instagram",
                'manufacturer': f'{random.choice(Devices_menu)}',
                'model': f'{random.choice(Devices_menu)}-{randomStringWithChar(4).upper()}',
                'android_version': random.randint(18, 25),
                'android_release': f'{random.randint(1, 7)}.{random.randint(0, 7)}',
                "cpu": f"{RandomStringChars(2)}{random.randrange(1000, 9999)}",
                'resolution': f'{randResolution}x{lowerResolution}',
                'randomL': f"{RandomString(6)}",
                'dpi': f"{random.choice(DPIs)}"
            }
            return '{Host} 155.0.0.37.107 {system} ({android_version}/{android_release}; {dpi}dpi; {resolution}; {manufacturer}; {model}; {cpu}; {randomL}; en_US)'.format(**DEVICE_SETTINTS)

        def generate_DeviceId(self, ID):
            volatile_ID = "12345"
            m = hashlib.md5()
            m.update(ID.encode('utf-8') + volatile_ID.encode('utf-8'))
            return 'android-' + m.hexdigest()[:16]

    def headers_login(self):
        headers = {}
        headers['User-Agent'] = self.sesstings.generateUSER_AGENT()
        headers['Host'] = 'i.instagram.com'
        headers['content-type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        headers['accept-encoding'] = 'gzip, deflate'
        headers['x-fb-http-engine'] = 'Liger'
        headers['Connection'] = 'close'
        return headers

    def checkpoint(self):
        info = requests.get(f"https://i.instagram.com/api/v1{self.req.json()['challenge']['api_path']}", headers=self.headers_login(), cookies=self.coo)
        step_data = info.json()["step_data"]
        choice = None
        if "email" in step_data:
            choice = "1"
        elif "phone_number" in step_data:
            choice = "0"
        
        if choice:
            self.send_choice(choice)
        else:
            bot.send_message(self.chat_id, "Unknown verification method.")
            start(self.chat_id)

    def send_choice(self, choice):
        data = {
            'choice': choice,
            '_uuid': uu,
            '_uid': uu,
            '_csrftoken': 'massing'
        }
        challnge = self.req.json()['challenge']['api_path']
        self.send = requests.post(f"https://i.instagram.com/api/v1{challnge}", headers=self.headers_login(), data=data, cookies=self.coo)
        contact_point = self.send.json()["step_data"]["contact_point"]
        bot.send_message(self.chat_id, f'Code sent to: {contact_point}')
        user_states[self.chat_id]['state'] = 'awaiting_code'

    def get_code(self, code):
        try:
            data = {
                'security_code': code,
                '_uuid': uu,
                '_uid': uu,
                '_csrftoken': 'massing'
            }
            path = self.req.json()['challenge']['api_path']
            send_code = requests.post(f"https://i.instagram.com/api/v1{path}", headers=self.headers_login(), data=data, cookies=self.coo)
            if "logged_in_user" in send_code.text:
                self.coo = send_code.cookies
                self.sessionid = self.coo.get("sessionid")
                bot.send_message(self.chat_id, f'Login Successfully as @{self.username}')
                bot.send_message(self.chat_id, f"Session: `{self.sessionid}`", parse_mode="Markdown")
                start(self.chat_id)
            else:
                regx_error = re.search(r'"message":"(.*?)",', send_code.text).group(1)
                bot.send_message(self.chat_id, regx_error)
                bot.send_message(self.chat_id, "Code is not valid. Please try again.")
        except Exception as e:
            bot.send_message(self.chat_id, f"An error occurred: {e}")
            start(self.chat_id)

    def login(self, username, passwordd):
        self.username = username
        self.passwordd = passwordd
        self.DeviceID = self.sesstings.generate_DeviceId(self.username)
        data = {
            'guid': uu,
            'enc_password': f"#PWD_INSTAGRAM:0:{timestamp}:{self.passwordd}",
            'username': self.username,
            'device_id': self.DeviceID,
            'login_attempt_count': '0'
        }
        self.req = requests.post("https://i.instagram.com/api/v1/accounts/login/", headers=self.headers_login(), data=data)
        if "logged_in_user" in self.req.text:
            self.coo = self.req.cookies
            self.sessionid = self.coo.get("sessionid")
            bot.send_message(self.chat_id, f'Login Successfully as @{self.username}')
            bot.send_message(self.chat_id, f"Session: {self.sessionid}")
            start(self.chat_id)
        elif 'checkpoint_challenge_required' in self.req.text:
            self.coo = self.req.cookies
            bot.send_message(self.chat_id, "Checkpoint challenge required.")
            self.checkpoint()
        else:
            try:
                regx_error = re.search(r'"message":"(.*?)",', self.req.text).group(1)
                bot.send_message(self.chat_id, regx_error)
            except:
                bot.send_message(self.chat_id, self.req.text)
            start(self.chat_id)

def start(chat_id):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    get_session_button = types.KeyboardButton('Get Session')
    convert_session_button = types.KeyboardButton('Convert Session')
    short_session_button = types.KeyboardButton('Short Session')
    stop_button = types.KeyboardButton('Stop')
    keyboard.add(get_session_button, convert_session_button)
    keyboard.add(short_session_button)
    keyboard.add(stop_button)
    bot.send_message(chat_id, "Welcome To Session Grabber V1.0b", reply_markup=keyboard)
    user_states[chat_id] = {'state': 'idle'}

@bot.message_handler(commands=['start'])
def start_command(message):
    start(message.chat.id)

@bot.message_handler(func=lambda message: message.text == 'Get Session')
def get_session_handler(message):
    bot.send_message(message.chat.id, "Please enter your username:")
    user_states[message.chat.id] = {'state': 'awaiting_username', 'session': InstagramSession(message.chat.id)}

@bot.message_handler(func=lambda message: message.text == 'Short Session')
def short_session_handler(message):
    bot.send_message(message.chat.id, "Please send the session to shorten:")
    user_states[message.chat.id] = {'state': 'awaiting_short_session'}

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_short_session')
def receive_short_session(message):
    if message.text.lower() == 'stop':
        start(message.chat.id)
        return
    try:
        decoded_session = urllib.parse.unquote(message.text)
        parts = decoded_session.split(':')
        short_session = f"{parts[0]}:{parts[1]}:{parts[2]}"
        bot.send_message(message.chat.id, f"Short Session: `{short_session}`", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"An error occurred: {e}")
    finally:
        start(message.chat.id)


@bot.message_handler(func=lambda message: message.text == 'Convert Session')
def convert_session_handler(message):
    bot.send_message(message.chat.id, "Please send the session to convert:")
    user_states[message.chat.id] = {'state': 'awaiting_convert_session'}

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_convert_session')
def receive_convert_session(message):
    if message.text.lower() == 'stop':
        start(message.chat.id)
        return
    user_states[message.chat.id]['session_to_convert'] = message.text
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    skip_button = types.KeyboardButton('Skip')
    markup.add(skip_button)
    bot.send_message(message.chat.id, "Please send the mid, or click 'Skip':", reply_markup=markup)
    user_states[message.chat.id]['state'] = 'awaiting_mid'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_mid')
def receive_mid(message):
    if message.text.lower() == 'stop':
        start(message.chat.id)
        return
    
    session_to_convert = user_states[message.chat.id]['session_to_convert']
    
    if message.text.lower() == 'skip':
        bot.send_message(message.chat.id, "Converting session without mid...")
        api_session, err = web_to_api_convert_no_mid(session_to_convert)
    else:
        bot.send_message(message.chat.id, "Converting session with mid...")
        api_session, err = web_to_api_convert(session_to_convert, message.text)

    if err:
        bot.send_message(message.chat.id, f"Conversion failed: {err}")
    else:
        bot.send_message(message.chat.id, "Api Done...")
        bot.send_message(message.chat.id, f"`{api_session}`", parse_mode="Markdown")
    
    start(message.chat.id)

def web_to_api_convert(session_id, mid):
    try:
        user_id = session_id.split("%3A")[0]
        auth_payload = f'{{"ds_user_id":"{user_id}","sessionid":"{session_id}"}}'
        encoded_auth = base64.b64encode(auth_payload.encode()).decode()

        headers = {
            "User-Agent": "Instagram 237.0.0.14.102 Android",
            "X-Mid": mid,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "cookie": f"sessionid={session_id}",
            "X-Bloks-Version-Id": "8ca96ca267e30c02cf90888d91eeff09627f0e3fd2bd9df472278c9a6c022cbb",
            "X-Bloks-Is-Layout-Rtl": "false",
        }

        device_id = f"android-{random.randint(1000000000, 9999999999)}"
        data = {
            "device_id": device_id,
            "authorization_token": f"Bearer IGT:2:{encoded_auth}",
        }

        response = requests.post("https://i.instagram.com/api/v1/accounts/continue_as_instagram_login/", headers=headers, data=data)
        
        if "logged" in response.text:
            for cookie in response.cookies:
                if cookie.name == "sessionid":
                    return cookie.value, None
            
            auth_header = response.headers.get("ig-set-authorization")
            if auth_header:
                parts = auth_header.split(":")
                if len(parts) >= 3:
                    decoded = base64.b64decode(parts[2]).decode()
                    session_match = re.search(r'"sessionid":"([^"]+)"', decoded)
                    if session_match:
                        return session_match.group(1), None

        return None, "Conversion failed - invalid response"
    except Exception as e:
        return None, str(e)

def web_to_api_convert_no_mid(session_id):

    return web_to_api_convert(session_id, "")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_username')
def receive_username(message):
    if message.text.lower() == 'stop':
        start(message.chat.id)
        return
    session = user_states[message.chat.id]['session']
    session.username = message.text
    bot.send_message(message.chat.id, "Please enter your password:")
    user_states[message.chat.id]['state'] = 'awaiting_password'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_password')
def receive_password(message):
    if message.text.lower() == 'stop':
        start(message.chat.id)
        return
    session = user_states[message.chat.id]['session']
    session.passwordd = message.text
    session.login(session.username, session.passwordd)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_code')
def receive_code(message):
    if message.text.lower() == 'stop':
        start(message.chat.id)
        return
    session = user_states[message.chat.id]['session']
    session.get_code(message.text)

@bot.message_handler(func=lambda message: message.text.lower() == 'stop')
def stop_process(message):
    start(message.chat.id)

if __name__ == "__main__":
    bot.polling()
