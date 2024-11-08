import telebot
from telebot import types
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
import os

# Папка для зберігання фотографій
PHOTO_DIR = "photos"
os.makedirs(PHOTO_DIR, exist_ok=True)

# Підключаємося до бота
API_TOKEN = "7734785531:AAHZ_RkWkmAUJMeE9Dq462K3k29ORh3wu0g"
bot = telebot.TeleBot(API_TOKEN)

# Налаштовуємо базу даних SQLite
engine = create_engine('sqlite:///users.db', echo=True)
Base = declarative_base()

# Визначаємо модель користувача
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    chat_id = Column(Integer)
    name = Column(String)
    age = Column(Integer)
    city = Column(String)
    interests = Column(String)
    bio = Column(String)
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)
    photo_path = Column(String)
    likes_from_users = Column(String, default="")

# Перевірка таблиці
try:
    Base.metadata.create_all(engine)
except OperationalError:
    print("Помилка при створенні бази даних.")

Session = sessionmaker(bind=engine)

# Змінна для зберігання стану користувачів
user_states = {}

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("📋 Реєстрація")  
    markup.add(item1)
    return markup

# Головне меню 
def registered_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item2 = types.KeyboardButton("👀 Переглянути анкети")
    item3 = types.KeyboardButton("Змінити дані")
    item4 = types.KeyboardButton("👀 Користувачі, які мене лайкнули")
    markup.add(item2, item3, item4)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    session = Session()
    user = session.query(User).filter_by(username=message.from_user.username).first()

    if user:
        bot.send_message(message.chat.id, "Привіт! Ласкаво просимо назад! Виберіть дію:", reply_markup=registered_menu())
    else:
        bot.send_message(message.chat.id, "Привіт! Ласкаво просимо в бот для знайомств. Щоб почати, спочатку зареєструйтесь.", reply_markup=main_menu())
    
    session.close()

@bot.message_handler(commands=['clear'])
def clear_history(message):
    session = Session()
    user = session.query(User).filter_by(username=message.from_user.username).first()
    if user:
        session.delete(user)
        session.commit()
        bot.send_message(message.chat.id, "Ваша інформація була очищена. Ви можете зареєструватись заново за допомогою команди /register.", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "Ви ще не зареєстровані.", reply_markup=registered_menu())
    session.close()

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "📋 Реєстрація":
        register_user(message)
    elif message.text == "👀 Переглянути анкети":
        view_next_profile(message)
    elif message.text == "Змінити дані":
        update_bio(message)
    elif "Лайк" in message.text or "Дизлайк" in message.text:
        handle_vote(message)
    elif message.text == "👀 Користувачі, які мене лайкнули":
        view_likers(message)
    elif message.text == "Головне меню":
        bot.send_message(message.chat.id, "Виберіть дію:", reply_markup=registered_menu())
    else:
        bot.send_message(message.chat.id, "Будь ласка, оберіть дію через меню.", reply_markup=registered_menu())

def view_likers(message):
    session = Session()
    user = session.query(User).filter_by(username=message.from_user.username).first()

    if user and user.likes_from_users:
        likers = user.likes_from_users.strip(",").split(",")  
        if likers:
            likers_list = "\n".join(likers)
            bot.send_message(message.chat.id, f"Користувачі, які поставили вам лайк:\n{likers_list}")
        else:
            bot.send_message(message.chat.id, "Ніхто ще не поставив вам лайк.")
    else:
        bot.send_message(message.chat.id, "Ви ще не отримали лайків.")

    session.close()

@bot.message_handler(commands=['register'])
def register_user(message):
    session = Session()
    user = session.query(User).filter_by(username=message.from_user.username).first()
    if user:
        bot.reply_to(message, "Ви вже зареєстровані.")
    else:
        msg = bot.reply_to(message, "Введіть ваше ім'я:")
        bot.register_next_step_handler(msg, process_name_step, session)

def process_name_step(message, session):
    chat_id = message.chat.id
    name = message.text

    existing_user = session.query(User).filter_by(username=message.from_user.username).first()
    if existing_user:
        bot.reply_to(message, "Ви вже зареєстровані.")
        session.close()
        return

    user = User(username=message.from_user.username, chat_id=chat_id, name=name)
    session.add(user)
    session.commit()

    msg = bot.reply_to(message, "Введіть ваш вік:")
    bot.register_next_step_handler(msg, process_age_step, session)

def process_age_step(message, session):
    try:
        age = int(message.text)
        user = session.query(User).filter_by(username=message.from_user.username).first()
        user.age = age
        session.commit()

        msg = bot.reply_to(message, "Введіть ваше місто:")
        bot.register_next_step_handler(msg, process_city_step, session)
    except ValueError:
        bot.reply_to(message, "Будь ласка, введіть правильний вік.")

def process_city_step(message, session):
    user = session.query(User).filter_by(username=message.from_user.username).first()
    user.city = message.text
    session.commit()

    msg = bot.reply_to(message, "Введіть ваші інтереси:")
    bot.register_next_step_handler(msg, process_interests_step, session)

def process_interests_step(message, session):
    user = session.query(User).filter_by(username=message.from_user.username).first()
    user.interests = message.text
    session.commit()

    msg = bot.reply_to(message, "Будь ласка, надішліть вашу фотографію:")
    bot.register_next_step_handler(msg, process_photo_step, session)

def process_photo_step(message, session):
    if message.photo:
        photo_file = message.photo[-1].file_id
        file_info = bot.get_file(photo_file)
        downloaded_file = bot.download_file(file_info.file_path)

        photo_path = os.path.join(PHOTO_DIR, f"{message.from_user.username}_photo.jpg")
        with open(photo_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        user = session.query(User).filter_by(username=message.from_user.username).first()
        user.photo_path = photo_path
        session.commit()

        bot.reply_to(message, "Реєстрація завершена! Ви можете оновити інформацію за допомогою команди /bio.", reply_markup=registered_menu())
    else:
        bot.reply_to(message, "Будь ласка, надішліть фотографію.")

@bot.message_handler(commands=['bio'])
def update_bio(message):
    msg = bot.reply_to(message, "Введіть коротку інформацію про себе:")
    bot.register_next_step_handler(msg, process_bio_step)

def process_bio_step(message):
    session = Session()
    user = session.query(User).filter_by(username=message.from_user.username).first()
    if user:
        user.bio = message.text
        session.commit()
        bot.reply_to(message, "Ваша біографія оновлена!", reply_markup=registered_menu())
    else:
        bot.reply_to(message, "Спочатку зареєструйтесь за допомогою /register.")
    session.close()

@bot.message_handler(commands=['view_profiles'])
def view_next_profile(message):
    user_states[message.chat.id] = 0
    send_profile(message)

def send_profile(message):
    session = Session()
    current_index = user_states[message.chat.id]
    users = session.query(User).all()

    if current_index >= len(users):
        bot.reply_to(message, "Немає доступних анкет.", reply_markup=registered_menu())
        session.close()
        return

    user = users[current_index]

    if user.photo_path and os.path.exists(user.photo_path):
        bot.send_photo(message.chat.id, photo=open(user.photo_path, 'rb'),
                       caption=f"Ім'я: {user.name}\nВік: {user.age}\nМісто: {user.city}\nІнтереси: {user.interests}\nПро себе: {user.bio}")
    else:
        bot.send_message(message.chat.id, 
                         f"Ім'я: {user.name}\nВік: {user.age}\nМісто: {user.city}\nІнтереси: {user.interests}\nПро себе: {user.bio}\n\nФотографія не доступна.")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    like_button = types.KeyboardButton(f"👍 Лайк ({user.likes})")
    dislike_button = types.KeyboardButton(f"👎 Дизлайк ({user.dislikes})")
    main_menu_button = types.KeyboardButton("Головне меню")
    markup.add(like_button, dislike_button, main_menu_button)

    bot.send_message(message.chat.id, "Що ви хочете зробити?", reply_markup=markup)
    session.close()

def handle_vote(message):
    session = Session()
    if message.chat.id not in user_states:
        user_states[message.chat.id] = 0

    current_index = user_states[message.chat.id]
    users = session.query(User).all()

    if current_index >= len(users):
        bot.reply_to(message, "Немає доступних анкет.", reply_markup=registered_menu())
        session.close()
        return

    user = users[current_index]

    if "Лайк" in message.text:
        user.likes += 1
        session.commit()

        # Додаємо до списку лайкнувших користувачів
        liker = session.query(User).filter_by(username=message.from_user.username).first()
        if liker:
            if liker.username not in user.likes_from_users.split(","):
                user.likes_from_users += f"{liker.username},"
                session.commit()

        bot.send_message(user.chat_id, f"Вас лайкнули! У вас є взаємний лайк, якщо ви також поставите лайк цьому користувачу.")
        
        bot.reply_to(message, "Ви поставили лайк!")
    elif "Дизлайк" in message.text:
        user.dislikes += 1
        session.commit()
        bot.reply_to(message, "Ви поставили дизлайк!")

    user_states[message.chat.id] += 1
    send_profile(message)
    session.close()

bot.polling(none_stop=True)
