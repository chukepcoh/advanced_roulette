import inspect

start_game_message = inspect.cleandoc(
    '''
    👋🏻 Добро пожаловать в Advanced Russian Roulette!
    Данная игра полностью копирует идею и концепт игры Buckshot Roulette by Mike Klubnika.
    
    Обозначения:
    ⚡️ - очки здоровья
    💀 - потерянные очки здоровья
    🔴 - боевой патрон
    ⚫️ - холостой патрон
    
    Команды:
    /join - присоединится в лобби
    /shot [me/op] - сделать выстрел
    /use [название предмета] - использовать предмет
    /status - получить информацию о текущих предметах и ед. здоровья
    /items - список предметов
    /rules - правила игры
    
    Правила игры:
    - В начале игры каждый игрок получает равное случайное количество ед. здоровья (3-6) и случайный набор предметов.
    - Первый ход достается игроку, первому вошедшему в лобби.
    - В течение хода можно использовать неограниченное количество предметов (если тому удовлетворяют условия).
    - Использование предмета не завершает текущий ход (кроме случаев проигрыша после использования, например таблетки)
    - Выстрел холостым в себя дает дополнительный ход.
    - Выстрел боевым в себя или боевым/холостым оппонента завершает текущий ход.
    - Когда последовательность патронов заканчивается, генерируется новая, каждому игроку выдается на 1 больше предметов (изн. 3)
    '''
)

game_created_message = inspect.cleandoc(
    '''
    Игра создана.
    Введите /join, чтобы присоединится к лобби.
    Необходимо 2 игрока.
    '''
)

game_already_created_message = inspect.cleandoc(
    '''
    Игра уже создана. Дождитесь завершения.
    '''
)

game_not_created_message = inspect.cleandoc(
    '''
    Игра не создана. Пропишите /start
    '''
)

first_player_joined_message = inspect.cleandoc(
    '''
    Первый игрок присоединился. ({user_name})
    '''
)

second_player_joined_message = inspect.cleandoc(
    '''
    Второй игрок присоединился. ({user_name})
    '''
)

player_already_joined_message = inspect.cleandoc(
    '''
    {user_name}, Вы уже в лобби.
    '''
)

game_commencing_message = inspect.cleandoc(
    '''
    Лобби заполнено.
    Игра начинается.
    '''
)

game_in_progress_message = inspect.cleandoc(
    '''
    Игра в процессе.
    '''
)

max_health_generated_message = inspect.cleandoc(
    '''
    У каждого игрока {health_string} ед. здоровья.
    '''
)

new_round_info_message = inspect.cleandoc(
    '''
    Заряжается дробовик:
    Боевых патронов 🔴 × {live_bullet_amount}
    Холостых патронов ⚫ × {blank_bullet_amount}
    
    {first_player_name}, Ваши предметы:
    {first_player_items}
    
    {second_player_name}, Ваши предметы:
    {second_player_items}
    '''
)

current_turn_info_message = inspect.cleandoc(
    '''
    Текущий ход - {user_name}.
    '''
)

game_not_started_message = inspect.cleandoc(
    '''
    Игра еще не началась.
    '''
)

not_your_turn_message = inspect.cleandoc(
    '''
    {user_name}, сейчас не Ваш ход.
    '''
)

you_are_not_participating_message = inspect.cleandoc(
    '''
    {user_name} Вы не участвуете в данной игре.
    '''
)
make_shot_self_target_message = inspect.cleandoc(
    '''
    {user_name}, выстрел в себя.
    '''
)

make_shot_enemy_target_message = inspect.cleandoc(
    '''
    {user_name}, выстрел в противника.
    '''
)

congrats_winner_message = inspect.cleandoc(
    '''
    {user_name} - победитель.
    '''
)

game_finished_message = inspect.cleandoc(
    '''
    Игра закончена. Чтобы начать новую игру, введите /start
    '''
)

invalid_arg_message = inspect.cleandoc(
    '''
    Некорректный аргумент для команды.
    '''
)

round_status_message = inspect.cleandoc(
    '''
    В начале раунда:
    Боевых патронов 🔴 × {live_bullet_amount}
    Холостых патронов ⚫ × {blank_bullet_amount}
    
    История выстрелов:
    {shot_bullets_history}
    
    {first_player_name}: {first_player_health_string}{first_player_lost_health_string}
    {first_player_items}
    -----------------------
    {second_player_name}: {second_player_health_string}{second_player_lost_health_string}
    {second_player_items}
    '''
)

no_item_in_inventory_message = inspect.cleandoc(
    '''
    У Вас нет этого предмета.
    '''
)

using_item_message = inspect.cleandoc(
    '''
    Использование предмета {item_emoji}
    '''
)

player_current_health_message = inspect.cleandoc(
    '''
    {user_name}: {player_health_string}{player_lost_health_string}
    '''
)

using_glass_message = inspect.cleandoc(
    '''
    Текущий патрон - {bullet_emoji} ({bullet_name})
    '''
)

using_phone_message = inspect.cleandoc(
    '''
    {bullet_index} патрон - {bullet_emoji} ({bullet_name})
    '''
)

already_used_item_message = inspect.cleandoc(
    '''
    Вы уже использовали данный предмет.
    '''
)

items_help_message = inspect.cleandoc(
    '''
    Условные обозначения, принятые в игре:
    ⚡️ - очки здоровья
    🔴 - боевой патрон
    ⚫ - холостой патрон
    🚬 [cigarettes/cigs] - сигареты: восстанавливают 1 ед. здоровья (но не более макс. запаса)
    🍺 [beer] - пиво: изымает текущий патрон
    🔍 [glass] - лупа: позволяет посмотреть текущий патрон
    🔗 [cuffs] - наручники: оппонент пропускает следующий ход
    🔪 [knife] - нож: текущий выстрел наносит двойной урон (если патрон боевой)
    🧲 [inverter] - инвертор: меняет заряд текущего патрона
    💊 [pill] - таблетка: 50% шанс восстановить 2 ед. здоровья (не более макс. запаса) или потерять 1 ед. здоровья
    📱 [phone] - телефон: позволяет узнать рандомный патрон в очереди (N-ый патрон боевой/холостой)
    '''
)

rules_help_message = inspect.cleandoc(
    '''
    Правила игры:
    В начале игры каждый игрок получает равное случайное количество ед. здоровья (3-6).
    Первый ход достается игроку, первому вошедшему в лобби.
    В течение хода можно использовать неограниченное количество предметов
    (однако, нельзя использовать нож или наручники 2 раза за один ход [выстрел]).
    Использование предмета не завершает текущий ход (кроме случаев проигрыша после использования, например таблетки)
    Выстрел холостым в себя дает дополнительный ход.
    Выстрел боевым в себя или боевым/холостым в оппонента завершает текущий ход.
    Когда последовательность патронов заканчивается, генерируется новая последовательность 
    и каждому игроку выдается на 1 больше предметов (изн. 3)
    '''
)
