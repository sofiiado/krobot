import telebot
import random
import logging

# Токен бота
BOT_TOKEN = "7884011496:AAHtSVTxWh15d44tDz1N8vuaOq0tbOTuf2s"
bot = telebot.TeleBot(BOT_TOKEN)

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Глобальні змінні для гри
words_pool = ["rewolucja", "historia", "egzamin", "nauka", "kultura"]
current_word = ""
current_leader = None
players_scores = {}

# Команда /start
@bot.message_handler(commands=["start"])
def start_game(message):
    global current_word, current_leader

    # Отримуємо список учасників групи
    chat_members = bot.get_chat_administrators(message.chat.id)
    joined_players = [member.user.id for member in chat_members]

    if not joined_players:
        bot.reply_to(message, "Nie ma graczy w grze. Dodaj uczestników do grupy, aby rozpocząć.")
        return

    current_leader = random.choice(joined_players)
    current_word = random.choice(words_pool)

    # Надсилаємо слово ведучому
    bot.send_message(current_leader, f"Twoje słowo: {current_word}")
    bot.reply_to(
        message,
        f"Gra rozpoczęta! Prowadzący: {message.from_user.first_name}. Pozostali gracze zgadują słowo.",
    )
    logger.info(f"Gra rozpoczęta. Prowadzący: {current_leader}, słowo: {current_word}")

# Обробка текстових повідомлень для відгадування слова
@bot.message_handler(func=lambda message: True)
def guess_word(message):
    global current_word, current_leader

    if not current_word:
        bot.reply_to(message, "Gra jeszcze się nie rozpoczęła. Użyj /start, aby zacząć.")
        return

    if message.from_user.id == current_leader and message.text.strip().lower() == current_word.lower():
        # Ведучий не може писати своє слово
        current_word = random.choice(words_pool)
        bot.send_message(current_leader, f"Napisałeś/łaś słowo, które miałeś wyjaśnić! Twoje nowe słowo to: {current_word}")
        logger.info(f"Prowadzący {message.from_user.first_name} próbował zgadnąć swoje słowo.")
        return

    if message.text.strip().lower() == current_word.lower():
        players_scores[message.from_user.id] = players_scores.get(message.from_user.id, 0) + 1
        bot.reply_to(
            message,
            f"Brawo, {message.from_user.first_name}! Odgadłeś/łaś słowo! Zostałeś/łaś nowym prowadzącym.",
        )

        # Встановлюємо нового ведучого
        if message.from_user.id != current_leader:
            current_leader = message.from_user.id
            current_word = random.choice(words_pool)

            # Надсилаємо нове слово ведучому
            bot.send_message(current_leader, f"Twoje nowe słowo: {current_word}")
            logger.info(f"{message.from_user.first_name} odgadł(a) słowo i otrzymał nowe słowo.")
    else:
        logger.info(f"{message.from_user.first_name} napisał(a) niepoprawne słowo.")

# Команда /stop
@bot.message_handler(commands=["stop"])
def stop_game(message):
    global current_word, current_leader

    current_word = ""
    current_leader = None
    bot.reply_to(message, "Gra została zakończona.")
    logger.info("Gra została zakończona.")

# Команда /score
@bot.message_handler(commands=["score"])
def show_score(message):
    if not players_scores:
        bot.reply_to(message, "Nie ma jeszcze wyników.")
        return

    scores = "\n".join(
        [f"{bot.get_chat(message.chat.id).get_member(player).user.first_name}: {score}"
         for player, score in players_scores.items()]
    )
    bot.reply_to(message, f"Wyniki:\n{scores}")

# Запуск бота
if __name__ == "__main__":
    logger.info("Bot is starting...")
    bot.polling()        