import random
import time
from collections import defaultdict

import static.messages as T
from core.objects.game import Game
from core.objects.player import Player

DATA = defaultdict(dict)


def get_game(chat_id, message_thread_id) -> Game:
    if chat_id in DATA.keys():
        return DATA[chat_id].get(message_thread_id)


async def start_game(chat_id, message_thread_id, user_id, context):
    if chat_id in DATA.keys():
        if message_thread_id in DATA[chat_id].keys():
            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=message_thread_id,
                text=T.game_already_created_message,
            )
            return

    game = Game(chat_id, message_thread_id, user_id, context)
    DATA[chat_id][message_thread_id] = game

    await game.send_message(T.start_game_message)
    await game.send_message(T.game_created_message)


async def join_lobby(chat_id, message_thread_id, user_id, user_name, context):
    game = get_game(chat_id, message_thread_id)
    if not game:
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=T.game_not_created_message,
        )
        return

    if not game.first_player:
        game.first_player = Player(user_id, user_name)
        await game.send_message(T.first_player_joined_message.format(user_name=game.first_player.user_name))

    elif not game.second_player:
        if user_id == game.first_player.user_id:
            await game.send_message(T.player_already_joined_message.format(user_name=game.first_player.user_name))
        else:
            game.second_player = Player(user_id, user_name)
            await game.send_message(T.second_player_joined_message.format(user_name=game.second_player.user_name))
            await game.send_message(T.game_commencing_message)

    else:
        await game.send_message(T.game_in_progress_message)
        return

    if game.first_player and game.second_player:
        await game.init_game_values()


async def make_shot(chat_id, message_thread_id, user_id, user_name, target, context):
    game = get_game(chat_id, message_thread_id)
    if not game:
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=T.game_not_created_message,
        )
        return

    if not game.game_in_progress:
        await game.send_message(T.game_not_started_message)
        return

    if user_id != game.current_player.user_id:
        if user_id != game.enemy_player.user_id:
            await game.send_message(T.you_are_not_participating_message.format(user_name=user_name))
            return
        await game.send_message(T.not_your_turn_message.format(user_name=user_name))
        return

    current_bullet = game.bullet_sequence.pop(0)
    game.shot_bullet_history.append(current_bullet)

    if target.lower() == 'me':
        await game.send_message(T.make_shot_self_target_message.format(user_name=game.current_player.user_name))
        time.sleep(1)
        await game.send_message(current_bullet.emoji)

        if current_bullet.damage == 0:
            game.damage_doubled = False
            if len(game.bullet_sequence) == 0:
                await game.start_new_round()
            return

        if game.damage_doubled:
            game.current_player.health -= current_bullet.damage * 2
            game.damage_doubled = False
        else:
            game.current_player.health -= current_bullet.damage

        if game.current_player.health <= 0:
            await game.congrats_winner(winner=game.enemy_player)
            await game.exit_game()
            del DATA[chat_id][message_thread_id]
            return

    elif target.lower() == 'op':
        await game.send_message(T.make_shot_enemy_target_message.format(user_name=game.current_player.user_name))
        time.sleep(1)
        await game.send_message(current_bullet.emoji)

        if game.damage_doubled:
            game.enemy_player.health -= current_bullet.damage * 2
            game.damage_doubled = False
        else:
            game.enemy_player.health -= current_bullet.damage

        if game.enemy_player.health <= 0:
            await game.congrats_winner(winner=game.current_player)
            await game.exit_game()
            del DATA[chat_id][message_thread_id]
            return

    else:
        await game.send_message(T.invalid_arg_message)
        return

    time.sleep(0.5)
    if len(game.bullet_sequence) == 0:
        await game.start_new_round()
    else:
        await game.send_round_status()
    await game.change_turn()
    return


async def use_item(chat_id, message_thread_id, user_id, user_name, item_name, context):
    game = get_game(chat_id, message_thread_id)
    if not game:
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=T.game_not_created_message,
        )
        return

    if not game.game_in_progress:
        await game.send_message(T.game_not_started_message)
        return

    if user_id != game.current_player.user_id:
        if user_id != game.enemy_player.user_id:
            await game.send_message(T.you_are_not_participating_message.format(user_name=user_name))
            return
        await game.send_message(T.not_your_turn_message.format(user_name=user_name))
        return

    item_name = item_name.lower()[:3]

    if not game.all_items.get(item_name):
        await game.send_message(T.invalid_arg_message)
        return

    if not game.is_item_in_inventory(item_name):
        await game.send_message(T.no_item_in_inventory_message)
        return

    await game.send_message(T.using_item_message.format(item_emoji=game.all_items[item_name]))
    game.current_player.items.remove(game.all_items[item_name])

    if item_name.startswith('cig'):
        game.current_player.health += 1
        if game.current_player.health > game.current_player.max_health:
            game.current_player.health = game.current_player.max_health
        await game.send_message(
            T.player_current_health_message.format(
                user_name=game.current_player.user_name,
                player_health_string='⚡️' * game.current_player.health,
                player_lost_health_string='💀' * (game.current_player.max_health - game.current_player.health),
            )
        )

    elif item_name.startswith('bee'):
        current_bullet = game.bullet_sequence.pop(0)
        game.shot_bullet_history.append(current_bullet)
        await game.send_message(current_bullet.emoji)
        if len(game.bullet_sequence) == 0:
            await game.start_new_round()

    elif item_name.startswith('inv'):
        if game.bullet_sequence[0] == game.blank_bullet:
            game.bullet_sequence[0] = game.live_bullet

        elif game.bullet_sequence[0] == game.live_bullet:
            game.bullet_sequence[0] = game.blank_bullet

    elif item_name.startswith('pil'):
        hp_add = random.choice([-1, 2])
        game.current_player.health += hp_add

        if game.current_player.health > game.current_player.max_health:
            game.current_player.health = game.current_player.max_health

        elif game.current_player.health <= 0:
            await game.congrats_winner(winner=game.enemy_player)
            await game.exit_game()
            del DATA[chat_id][message_thread_id]
            return

        await game.send_message(
            T.player_current_health_message.format(
                user_name=game.current_player.user_name,
                player_health_string='⚡️' * game.current_player.health,
                player_lost_health_string='💀' * (game.current_player.max_health - game.current_player.health),
            )
        )

    elif item_name.startswith('gla'):
        current_bullet = game.bullet_sequence[0]

        await game.send_message_to_player(
            T.using_glass_message.format(
                bullet_emoji=current_bullet.emoji,
                bullet_name=current_bullet.name,
            ),
            game.current_player.user_id,
        )

    elif item_name.startswith('pho'):
        random_bullet_index = random.randint(0, len(game.bullet_sequence) - 1)
        random_bullet = game.bullet_sequence[random_bullet_index]

        await game.send_message_to_player(
            T.using_phone_message.format(
                bullet_index=random_bullet_index + 1,
                bullet_emoji=random_bullet.emoji,
                bullet_name=random_bullet.name,
            ),
            game.current_player.user_id,
        )

    elif item_name.startswith('kni'):
        if game.damage_doubled:
            await game.send_message(T.already_used_item_message)
        else:
            game.damage_doubled = True

    elif item_name.startswith('cuf'):
        if game.enemy_player.skip_next_turn:
            await game.send_message(T.already_used_item_message)
        else:
            game.enemy_player.skip_next_turn = True


async def send_status(chat_id, message_thread_id, user_id, user_name, context):
    game = get_game(chat_id, message_thread_id)
    if not game:
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=T.game_not_created_message,
        )
        return

    if not game.game_in_progress:
        await game.send_message(T.game_not_started_message)
        return

    if user_id != game.current_player.user_id and user_id != game.enemy_player.user_id:
        await game.send_message(T.you_are_not_participating_message.format(user_name=user_name))
        return

    await game.send_round_status()


async def items_help(chat_id, message_thread_id, context):
    game = get_game(chat_id, message_thread_id)
    if not game:
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=T.game_not_created_message,
        )
        return

    await game.send_message(T.items_help_message)


async def rules_help(chat_id, message_thread_id, context):
    game = get_game(chat_id, message_thread_id)
    if not game:
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=T.game_not_created_message,
        )
        return

    await game.send_message(T.rules_help_message)


async def concede(chat_id, message_thread_id, user_id, user_name, context):
    game = get_game(chat_id, message_thread_id)
    if not game:
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=T.game_not_created_message,
        )
        return

    if not game.game_in_progress:
        await game.send_message(T.game_not_started_message)
        return

    if user_id != game.current_player.user_id and user_id != game.enemy_player.user_id:
        await game.send_message(T.you_are_not_participating_message.format(user_name=user_name))
        return

    if user_id == game.current_player.user_id:
        await game.congrats_winner(winner=game.enemy_player)
    elif user_id == game.enemy_player.user_id:
        await game.congrats_winner(winner=game.current_player)
    await game.exit_game()
    del DATA[chat_id][message_thread_id]
    return
