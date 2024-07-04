import copy
import random
from collections import namedtuple
from math import ceil

import static.messages as T
from core.objects.player import Player


class Game:
    Bullet = namedtuple('Bullet', ['emoji', 'damage', 'name'])
    live_bullet = Bullet('🔴', 1, 'боевой')
    blank_bullet = Bullet('⚫', 0, 'холостой')
    all_items = {
        "cig": "🚬", "bee": "🍺", "gla": "🔍", "cuf": "🔗",
        "kni": "🔪", "inv": "🧲", "pil": "💊", "pho": "📱",
    }

    def __init__(
            self,
            chat_id,
            message_thread_id,
            user_id,
            context,
    ):
        self.chat_id = chat_id
        self.message_thread_id = message_thread_id
        self.user_id = user_id
        self.context = context
        self.first_player = None
        self.second_player = None
        self.current_player = None
        self.bullet_sequence = []
        self.info_bullet_sequence = []
        self.shot_bullet_history = []
        self.new_round_add_items_amount = 3
        self.max_item_amount = 8
        self.game_in_progress = False
        self.damage_doubled = False
        self.enemy_player = None

    def __eq__(self, game):
        if isinstance(game, Game):
            return game.chat_id == self.chat_id and game.message_thread_id == self.message_thread_id
        else:
            return False

    async def send_message(self, text):
        await self.context.bot.send_message(
            chat_id=self.chat_id,
            message_thread_id=self.message_thread_id,
            text=text,
        )

    async def send_message_to_player(self, text, user_id):
        await self.context.bot.send_message(
            chat_id=user_id,
            message_thread_id=0,
            text=text,
        )

    async def generate_sequence(self):
        bullets_amount = random.randint(2, 8)
        min_req_bullet_amount = ceil(bullets_amount / 3)
        random_bullet_amount = bullets_amount - 2 * min_req_bullet_amount

        self.bullet_sequence.extend(self.live_bullet for _ in range(min_req_bullet_amount))
        self.bullet_sequence.extend(self.blank_bullet for _ in range(min_req_bullet_amount))
        random_bullets = random.choices([self.live_bullet, self.blank_bullet], k=random_bullet_amount)
        self.bullet_sequence.extend(random_bullets)
        self.info_bullet_sequence = copy.deepcopy(self.bullet_sequence)
        random.shuffle(self.bullet_sequence)

    async def generate_items(self):
        self.first_player.items.extend(
            random.choices(
                list(self.all_items.values()),
                k=self.new_round_add_items_amount,
            ),
        )
        self.second_player.items.extend(
            random.choices(
                list(self.all_items.values()),
                k=self.new_round_add_items_amount
            ),
        )

        if len(self.first_player.items) > self.max_item_amount:
            self.first_player.items = self.first_player.items[:self.max_item_amount]

        if len(self.second_player.items) > self.max_item_amount:
            self.second_player.items = self.second_player.items[:self.max_item_amount]

    async def generate_max_health(self):
        max_health = random.randint(3, 6)
        self.first_player.max_health = max_health
        self.first_player.health = max_health
        self.second_player.max_health = max_health
        self.second_player.health = max_health
        await self.send_message(T.max_health_generated_message.format(health_string='⚡️' * max_health))

    async def send_new_round_info(self):
        await self.send_message(
            T.new_round_info_message.format(
                live_bullet_amount=self.bullet_sequence.count(self.live_bullet),
                blank_bullet_amount=self.bullet_sequence.count(self.blank_bullet),
                first_player_name=self.first_player.user_name,
                second_player_name=self.second_player.user_name,
                first_player_items=' '.join(self.first_player.items),
                second_player_items=' '.join(self.second_player.items),
            )
        )

    async def init_game_values(self):
        self.game_in_progress = True
        await self.generate_sequence()
        await self.generate_items()
        await self.generate_max_health()
        await self.send_new_round_info()
        self.current_player = self.first_player
        self.enemy_player = self.second_player

        await self.send_message(T.current_turn_info_message.format(user_name=self.first_player.user_name))

    async def start_new_round(self):
        await self.generate_sequence()
        self.new_round_add_items_amount += 1
        self.shot_bullet_history = []
        await self.generate_items()
        await self.send_new_round_info()

    async def congrats_winner(self, winner: Player):
        await self.send_message(T.congrats_winner_message.format(user_name=winner.user_name))

    async def change_turn(self):
        if not self.enemy_player.skip_next_turn:
            self.current_player, self.enemy_player = self.enemy_player, self.current_player
        else:
            self.enemy_player.skip_next_turn = False
        await self.send_message(T.current_turn_info_message.format(user_name=self.current_player.user_name))

    async def send_round_status(self):
        await self.send_message(
            T.round_status_message.format(
                live_bullet_amount=self.info_bullet_sequence.count(self.live_bullet),
                blank_bullet_amount=self.info_bullet_sequence.count(self.blank_bullet),
                shot_bullets_history=' '.join(bullet.emoji for bullet in self.shot_bullet_history),
                second_player_name=self.second_player.user_name,
                second_player_health_string='⚡️' * self.second_player.health,
                second_player_lost_health_string='💀' * (self.second_player.max_health - self.second_player.health),
                second_player_items=' '.join(self.second_player.items),
                first_player_name=self.first_player.user_name,
                first_player_health_string='⚡️' * self.first_player.health,
                first_player_lost_health_string='💀' * (self.first_player.max_health - self.first_player.health),
                first_player_items=' '.join(self.first_player.items),
            )
        )

    def is_item_in_inventory(self, used_item):
        return self.all_items.get(used_item) in self.current_player.items

    async def exit_game(self):
        self.game_in_progress = False
        await self.send_message(T.game_finished_message)
