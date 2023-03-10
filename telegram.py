import telebot

message_id = 943108396
telegram_token = '5398559257:AAEeOerM_sUbXU-SJxB9iWf4IBa5Cxn_qmI'

bot = telebot.TeleBot(telegram_token)

def send_message(message):
    bot.send_message(message_id, text=f'{message}')

def send_photo(path):
    print(path)
    bot.send_photo(message_id, open(path, 'rb'))