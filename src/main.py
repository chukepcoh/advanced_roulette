import copy
import inspect
import logging
import random
import time
from collections import namedtuple
from math import ceil

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

from settings import BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

GAME_INIT_VALUES = {
    'first_player': {
        'user_id': 0,
        'user_name': '',
        'items': [],
        'health': 0,
        'skip_next_turn': False,
    },
    'second_player': {
        'user_id': 0,
        'user_name': '',
        'items': [],
        'health': 0,
        'skip_next_turn': False,
    },
    'bullet_sequence': [],
    'current_player': dict,
    'max_health': 0,
    'items_amount': 3,
    'damage_doubled': False,
    'shot_bullets': [],
}

DATA = {}

items_help_message = inspect.cleandoc(
    '''
    Условные обозначения, принятые в игре:
    ⚡️ - очки здоровья
    🔴 - боевой патрон
    ⚫ - холостой патрон
    🚬 [cigs] - сигареты: восстанавливают 1 ед. здоровья (но не более максимального запаса)
    🍺 [beer] - пиво: изымает текущий патрон
    🔍 [glass] - лупа: позволяет посмотреть текущий патрон
    🔗 [cuff] - наручники: оппонент пропускает следующий ход
    🔪 [knife] - нож: текущий выстрел наносит двойной урон (если патрон боевой)
    🧲 [inv] - инвертор: меняет заряд текущего патрона
    💊 [pill] - таблетка: 50% шанс восстановить 2 ед. здоровья (не более максимального запаса) или потерять 1 ед. здоровья
    📱 [phone] - телефон: позволяет узнать рандомный патрон в очереди (N-ый патрон боевой/пустой)
    '''
)

rules_help_message = inspect.cleandoc(
    '''
    Правила игры:
    В начале игры каждый игрок получает равное случайное количество ед. здоровья (3-6).
    Первый ход достается игроку, первому вошедшему в лобби.
    В течение хода можно использовать неограниченное количество предметов (если тому удовлетворяют условия).
    Использование предмета не завершает текущий ход (кроме случаев проигрыша после использования, например таблетки)
    Выстрел холостым в себя дает дополнительный ход.
    Выстрел боевым в себя или боевым/холостым оппонента завершает текущий ход.
    Когда последовательность патронов заканчивается, генерируется новая и каждому игроку выдается на 1 больше предметов (изн. 3)
    '''
)

Bullet = namedtuple('Bullet', ['emoji', 'damage', 'name'])
live_bullet = Bullet('🔴', 1, 'боевой')
blank_bullet = Bullet('⚫', 0, 'холостой')
item_dict = {
    'cig': "🚬", "bee": "🍺", "gla": "🔍", "cuf": "🔗",
    "kni": "🔪", "inv": "🧲", "pil": "💊", "pho": "📱",
}


async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    chat_id = update.effective_chat.id
    with open('static.txt', 'r', encoding='utf8') as file:
        start_text = file.read()

    if chat_id in DATA.keys():
        if message_thread_id in DATA[chat_id].keys():
            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=message_thread_id,
                text='Игра уже создана. Дождитесь завершения.',
            )
            return
        DATA[chat_id][message_thread_id] = copy.deepcopy(GAME_INIT_VALUES)
        DATA[chat_id][message_thread_id]['start_user'] = user.id
    else:
        DATA[chat_id] = {}
        DATA[chat_id][message_thread_id] = copy.deepcopy(GAME_INIT_VALUES)
        DATA[chat_id][message_thread_id]['start_user'] = user.id

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        message_thread_id=message_thread_id,
        text=start_text,
    )
    await context.bot.send_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        text=f'Игра создана.\n'
             f'Введите /join, чтобы присоединится к лобби.\n'
             f'Необходимо 2 игрока.',
    )


async def join_lobby(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)

    if chat_id not in DATA.keys():
        await send_game_not_created_message(update, context)
        return

    lobby_data = DATA[chat_id][message_thread_id]

    if not lobby_data['first_player'].get('user_id'):
        lobby_data['first_player']['user_id'] = user.id
        lobby_data['first_player']['user_name'] = user.first_name
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=f'Первый игрок присоединился. ({user.first_name})',
        )

    elif not lobby_data['second_player'].get('user_id'):
        if user.id == lobby_data['first_player'].get('user_id'):
            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=message_thread_id,
                text=f'{user.first_name}, Вы уже в лобби.',
            )
        else:
            lobby_data['second_player']['user_id'] = user.id
            lobby_data['second_player']['user_name'] = user.first_name
            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=message_thread_id,
                text=f'Второй игрок присоединился. ({user.first_name})',
            )
            time.sleep(1)
            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=message_thread_id,
                text=f'Лобби заполнено...\n'
                     f'Игра начинается.',
            )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=f'Игра в процессе.',
        )
        return

    if lobby_data['first_player'].get('user_id') and lobby_data['second_player'].get('user_id'):
        await game(update, context)


async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    lobby_data = DATA[chat_id][message_thread_id]

    await generate_sequence(update)
    await generate_items(update)
    await generate_health(update, context)
    await send_new_round_info(update, context)

    lobby_data['current_player'] = lobby_data['first_player']
    await context.bot.send_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        text=f'Текущий ход - {lobby_data['first_player']['user_name']}'
    )


async def start_new_round(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)

    await generate_sequence(update)
    await generate_items(update)
    await send_new_round_info(update, context)
    DATA[chat_id][message_thread_id]['shot_bullets'] = []


async def generate_sequence(update: Update):
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    lobby_data = DATA[chat_id][message_thread_id]

    bullets_amount = random.randint(2, 8)
    min_req_bullet_amount = ceil(bullets_amount / 3)
    random_bullet_amount = bullets_amount - 2 * min_req_bullet_amount

    bullet_sequence = []
    bullet_sequence.extend(live_bullet for _ in range(min_req_bullet_amount))
    bullet_sequence.extend(blank_bullet for _ in range(min_req_bullet_amount))
    random_bullets = random.choices([live_bullet, blank_bullet], k=random_bullet_amount)
    bullet_sequence.extend(random_bullets)
    random.shuffle(bullet_sequence)
    lobby_data['bullet_sequence'] = bullet_sequence


async def generate_items(update: Update):
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    lobby_data = DATA[chat_id][message_thread_id]
    first_player = lobby_data['first_player']
    second_player = lobby_data['second_player']

    all_items = ['🚬', '🍺', '🔍', '🔗', '🔪', '🧲', '💊', '📱']
    first_player_items = random.choices(all_items, k=lobby_data['items_amount'])
    second_player_items = random.choices(all_items, k=lobby_data['items_amount'])

    first_player['items'].extend(first_player_items)
    if len(first_player['items']) > 8:
        first_player['items'] = first_player['items'][:9]

    second_player['items'].extend(second_player_items)
    if len(second_player['items']) > 8:
        second_player['items'] = second_player['items'][:9]


async def generate_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    lobby_data = DATA[chat_id][message_thread_id]

    health = random.randint(3, 6)

    lobby_data['max_health'] = health
    lobby_data['first_player']['health'] = health
    lobby_data['second_player']['health'] = health

    await context.bot.send_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        text=f'У каждого игрока {'⚡️' * lobby_data['max_health']} ед. здоровья',
    )


async def send_new_round_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    lobby_data = DATA[chat_id][message_thread_id]
    first_player = lobby_data['first_player']
    second_player = lobby_data['second_player']

    await context.bot.send_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        text=f'Заряжается дробовик:\n'
             f'Боевых патронов {live_bullet.emoji} × {lobby_data['bullet_sequence'].count(live_bullet)}\n'
             f'Холостых патронов {blank_bullet.emoji} × {lobby_data['bullet_sequence'].count(blank_bullet)}\n'
             f'\n'
             f'{first_player['user_name']}, Ваши предметы:\n'
             f'{'  '.join(first_player['items'])}\n'
             f'\n'
             f'{second_player['user_name']}, Ваши предметы:\n'
             f'{'  '.join(second_player['items'])}\n',
    )


async def make_shot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    if chat_id not in DATA.keys():
        await send_game_not_created_message(update, context)
        return
    lobby_data = DATA[chat_id][message_thread_id]
    first_player = lobby_data['first_player']
    second_player = lobby_data['second_player']
    current_player = lobby_data['current_player']

    if not second_player['user_id']:
        await send_game_not_started_message(update, context)
        return

    if user.id != current_player['user_id']:
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=f'{user.first_name}, сейчас не Ваш ход.',
        )
        return

    if ''.join(context.args[0]).lower() == 'me':
        current_bullet = lobby_data['bullet_sequence'].pop(0)
        lobby_data['shot_bullets'].append(current_bullet)

        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=f'{user.first_name}, выстрел в себя',
        )
        time.sleep(0.5)
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=f'{current_bullet.emoji}',
        )

        if current_bullet.damage == 0:
            lobby_data['damage_doubled'] = False
            if len(lobby_data['bullet_sequence']) == 0:
                await start_new_round(update, context)
            return

        if lobby_data['damage_doubled']:
            current_player['health'] -= current_bullet.damage * 2
            lobby_data['damage_doubled'] = False
        else:
            current_player['health'] -= current_bullet.damage

        if current_player['health'] <= 0:
            if current_player == first_player:
                await congrats_winner(update, context, winner=second_player)
            elif current_player == second_player:
                await congrats_winner(update, context, winner=first_player)
            await exit_game(update, context)
            return

    elif ''.join(context.args[0]).lower() == 'op':
        current_bullet = lobby_data['bullet_sequence'].pop(0)
        lobby_data['shot_bullets'].append(current_bullet)

        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=f'{user.first_name}, выстрел в противника',
        )
        time.sleep(0.5)
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=f'{current_bullet.emoji}',
        )

        if current_player == first_player:
            if lobby_data['damage_doubled']:
                second_player['health'] -= current_bullet.damage * 2
                lobby_data['damage_doubled'] = False
            else:
                second_player['health'] -= current_bullet.damage

            if second_player['health'] <= 0:
                await congrats_winner(update, context, winner=first_player)
                await exit_game(update, context)
                return

        elif current_player == second_player:
            if lobby_data['damage_doubled']:
                first_player['health'] -= current_bullet.damage * 2
                lobby_data['damage_doubled'] = False
            else:
                first_player['health'] -= current_bullet.damage

            if first_player['health'] <= 0:
                await congrats_winner(update, context, winner=second_player)
                await exit_game(update, context)
                return

    else:
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=f'Некорректный аргумент. Для выстрела: /shot me | /shot op]',
        )
        return

    if len(lobby_data['bullet_sequence']) == 0:
        await start_new_round(update, context)
    await send_status(update, context)
    await change_turn(update, context)
    return


async def use_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    if chat_id not in DATA.keys():
        await send_game_not_created_message(update, context)
        return
    lobby_data = DATA[chat_id][message_thread_id]
    first_player = lobby_data['first_player']
    second_player = lobby_data['second_player']
    current_player = lobby_data['current_player']

    item = ''.join(context.args[0]).lower()[:3]

    if not second_player['user_id']:
        await send_game_not_started_message(update, context)
        return

    if user.id != current_player['user_id']:
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=f'{user.first_name}, сейчас не Ваш ход.',
        )
        return

    if not is_item_in_inventory(item, item_dict, lobby_data=lobby_data):
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=f'У Вас нет этого предмета',
        )
        return

    await context.bot.send_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        text=f'Использование предмета {item_dict[item]}',
    )

    current_player['items'].remove(item_dict[item])

    if item.startswith('cig'):
        current_player['health'] += 1
        if current_player['health'] > lobby_data['max_health']:
            current_player['health'] = lobby_data['max_health']
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=f'{user.first_name}: '
                 f'{'⚡️' * current_player['health']}{'💀' * (lobby_data['max_health'] - current_player['health'])}',
        )

    elif item.startswith('bee'):
        current_bullet = lobby_data['bullet_sequence'].pop(0)
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=f'{current_bullet.emoji}',
        )
        if len(lobby_data['bullet_sequence']) == 0:
            await start_new_round(update, context)

    elif item.startswith('inv'):
        if lobby_data['bullet_sequence'][0] == blank_bullet:
            lobby_data['bullet_sequence'][0] = live_bullet
        elif lobby_data['bullet_sequence'][0] == live_bullet:
            lobby_data['bullet_sequence'][0] = blank_bullet

    elif item.startswith('pil'):
        hp_add = random.choice([-1, 2])
        current_player['health'] += hp_add

        if current_player['health'] > lobby_data['max_health']:
            current_player['health'] = lobby_data['max_health']

        elif current_player['health'] <= 0:
            if current_player == first_player:
                await congrats_winner(update, context, winner=second_player)
            elif current_player == second_player:
                await congrats_winner(update, context, winner=first_player)
            await exit_game(update, context)
            return

        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=f'{user.first_name}: {'⚡️' * current_player['health']}{'💀' * (lobby_data['max_health'] - current_player['health'])}',
        )

    elif item.startswith('gla'):
        current_bullet = lobby_data['bullet_sequence'][0]

        await context.bot.send_message(
            chat_id=current_player['user_id'],
            message_thread_id=0,
            text=f'Текущий патрон - {current_bullet.emoji} ({current_bullet.name})'
        )

    elif item.startswith('pho'):
        random_bullet_index = random.randint(0, len(lobby_data['bullet_sequence']) - 1)
        random_bullet = lobby_data['bullet_sequence'][random_bullet_index]

        await context.bot.send_message(
            chat_id=current_player['user_id'],
            message_thread_id=0,
            text=f'{random_bullet_index + 1} патрон - {random_bullet.emoji} ({random_bullet.name})'
        )

    elif item.startswith('kni'):
        if lobby_data['damage_doubled']:
            await context.bot.send_message(
                chat_id=chat_id, message_thread_id=message_thread_id,
                text=f'Вы уже использовали данный предмет'
            )
            return
        lobby_data['damage_doubled'] = True

    elif item.startswith('cuf'):
        if first_player['skip_next_turn'] or second_player['skip_next_turn']:
            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=message_thread_id,
                text=f'Вы уже использовали данный предмет',
            )
            return

        if current_player == first_player:
            second_player['skip_next_turn'] = True

        elif current_player == second_player:
            first_player['skip_next_turn'] = True

    else:
        await context.bot.send_message(
            chat_id=chat_id, message_thread_id=message_thread_id,
            text=f'Введен неверный предмет'
        )


def is_item_in_inventory(item: str, item_dict: dict, lobby_data: dict) -> bool:
    current_player = lobby_data['current_player']
    return item_dict[item] in current_player['items']


async def change_turn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    lobby_data = DATA[chat_id][message_thread_id]
    first_player = lobby_data['first_player']
    second_player = lobby_data['second_player']
    current_player = lobby_data['current_player']

    if current_player == first_player:  # если сейчас был ход 1-го
        if second_player['skip_next_turn']:
            lobby_data['current_player'] = first_player
            second_player['skip_next_turn'] = False
        else:
            lobby_data['current_player'] = second_player

    elif current_player == second_player:  # если сейчас был ход 2-го
        if first_player['skip_next_turn']:
            lobby_data['current_player'] = second_player
            first_player['skip_next_turn'] = False
        else:
            lobby_data['current_player'] = first_player

    await context.bot.send_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        text=f'Ход {lobby_data['current_player']['user_name']}',
    )


async def send_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    lobby_data = DATA[chat_id][message_thread_id]
    first_player = lobby_data['first_player']
    second_player = lobby_data['second_player']

    decor_string_len = max(len('  '.join(first_player['items'])), len('  '.join(second_player['items'])))

    await context.bot.send_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        text=f'История выстрелов:\n'
             f'{'  '.join(bullet.emoji for bullet in lobby_data['shot_bullets'])}\n'
             f'\n'
             f'{second_player['user_name']} - {'⚡️' * second_player['health']}'
             f'{'💀' * (lobby_data['max_health'] - second_player['health'])}\n'
             f'{'  '.join(second_player['items'])}\n'
             f'{"-" * decor_string_len * 5}\n'
             f'{first_player['user_name']} - {'⚡️' * first_player['health']}'
             f'{'💀' * (lobby_data['max_health'] - first_player['health'])}\n'
             f'{'  '.join(first_player['items'])}',
    )


async def delete_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


async def items_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)

    await context.bot.send_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        text=items_help_message,
    )


async def rules_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)

    await context.bot.send_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        text=rules_help_message,
    )


async def send_game_not_started_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)

    await context.bot.send_message(
        chat_id=chat_id, message_thread_id=message_thread_id,
        text='Игра еще не началась.'
    )


async def send_game_not_created_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)

    await context.bot.send_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        text='Игра не создана. Пропишите /start',
    )


async def congrats_winner(update: Update, context: ContextTypes.DEFAULT_TYPE, winner):
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)

    await context.bot.send_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        text=f'{winner['user_name']} - победитель.',
    )


async def concede(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    if chat_id not in DATA.keys():
        await send_game_not_created_message(update, context)
        return
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)
    lobby_data = DATA[chat_id][message_thread_id]

    if not lobby_data['second_player']['user_id']:
        await send_game_not_started_message(update, context)
        return

    if user.id == lobby_data['first_player']['user_id']:
        await congrats_winner(update, context, winner=lobby_data['second_player'])
    elif user.id == lobby_data['second_player']['user_id']:
        await congrats_winner(update, context, winner=lobby_data[lobby_data['first_player']])
    await exit_game(update, context)


async def exit_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message.to_dict()
    message_thread_id = message.get('message_thread_id', 0)

    DATA[chat_id][message_thread_id] = copy.deepcopy(GAME_INIT_VALUES)

    await context.bot.send_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        text=f'Игра закончена. Чтобы начать новую игру, введите /start',
    )
    del DATA[chat_id]


if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler('start', start_game)
    join_handler = CommandHandler('join', join_lobby)
    use_handler = CommandHandler('use', use_item)
    make_shot_handler = CommandHandler('shot', make_shot)
    items_handler = CommandHandler('items', items_help)
    rules_handler = CommandHandler('rules', rules_help)
    concede_handler = CommandHandler('concede', concede)

    application.add_handler(start_handler)
    application.add_handler(join_handler)
    application.add_handler(use_handler)
    application.add_handler(make_shot_handler)
    application.add_handler(items_handler)
    application.add_handler(rules_handler)
    application.add_handler(concede_handler)

    application.run_polling()
