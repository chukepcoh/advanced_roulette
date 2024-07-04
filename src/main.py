import logging

from telegram.ext import ApplicationBuilder, CommandHandler

from handlers import handlers
from settings import BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler('start', handlers.start_game_handler)
    join_handler = CommandHandler('join', handlers.join_lobby_handler)
    use_handler = CommandHandler('use', handlers.use_item_handler)
    make_shot_handler = CommandHandler('shot', handlers.make_shot_handler)
    status_handler = CommandHandler('status', handlers.send_status_handler)
    items_handler = CommandHandler('items', handlers.items_help_handler)
    rules_handler = CommandHandler('rules', handlers.rules_help_handler)
    concede_handler = CommandHandler('concede', handlers.concede_handler)

    application.add_handler(start_handler)
    application.add_handler(join_handler)
    application.add_handler(use_handler)
    application.add_handler(make_shot_handler)
    application.add_handler(status_handler)
    application.add_handler(items_handler)
    application.add_handler(rules_handler)
    application.add_handler(concede_handler)

    application.run_polling()
