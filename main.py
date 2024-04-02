import time
from telethon.sync import TelegramClient, events
from telethon.tl.types import User
from sqlalchemy import create_engine, Column, Integer, String, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Ваши данные API
TELEGRAM_API_ID = 7248451
TELEGRAM_API_HASH = 'db9b16eff233ee8dfd7c218138cb2e10'

# Название файла, куда будут сохраняться сессии пользователей
session_file = 'session_name.session'

# Создаем экземпляр TelegramClient
client = TelegramClient(session_file, TELEGRAM_API_ID, TELEGRAM_API_HASH)
engine = create_engine('sqlite:///message_count.db')
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    message_count = Column(Integer, default=0)
    last_message_time = Column(Integer, default=0)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Обработчик событий на получение новых сообщений в чате
@client.on(events.NewMessage)
async def count_messages(event):
    sender = await event.get_sender()
    user_id = sender.id
    username = sender.username
    current_time = time.time()
    # Получаем пользователя из базы данных или создаем нового, если он отсутствует
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        user = User(id=user_id, username=username)
        session.add(user)
        session.commit()
    
    # Проверяем, прошло ли более 1 секунды с момента последнего сообщения
    if current_time - user.last_message_time > 1:
        # Увеличиваем количество сообщений пользователя и обновляем время последнего сообщения
        user.message_count += 1
        user.last_message_time = current_time
        session.commit()
        await event.reply(f"Ты получил 1 поинт за сообщение. Текущий счет: {user.message_count}")
    else:
        await event.reply("Не спамь ")

# Команда /leaders
@client.on(events.NewMessage(pattern='/leaders'))
async def get_leaders(event):
    leaders = session.query(User).order_by(desc(User.message_count)).limit(10).all()
    leaders_info = "Топ 10 участников:\n\n"
    for index, leader in enumerate(leaders, start=1):
        leaders_info += f"{index}. {leader.username}: {leader.message_count} поинтов\n"
    await event.reply(leaders_info)


# Запускаем клиента
client.start()
client.run_until_disconnected()
