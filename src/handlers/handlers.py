from telegram import Update
from telegram.ext import ContextTypes

from core.game import start_game, join_lobby, make_shot, use_item, items_help, rules_help, concede, send_status


async def start_game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    chat_id = update.effective_chat.id
    await start_game(chat_id, message_thread_id, user_id, context)


async def join_lobby_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    await join_lobby(chat_id, message_thread_id, user_id, user_name, context)


async def make_shot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    arg = context.args[0]
    await make_shot(chat_id, message_thread_id, user_id, user_name, arg, context)


async def use_item_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    arg = context.args[0]
    await use_item(chat_id, message_thread_id, user_id, user_name, arg, context)


async def send_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    await send_status(chat_id, message_thread_id, user_id, user_name, context)


async def items_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    await items_help(chat_id, message_thread_id, context)


async def rules_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    await rules_help(chat_id, message_thread_id, context)


async def concede_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    await concede(chat_id, message_thread_id, user_id, user_name, context)
