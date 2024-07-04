class Player:
    def __init__(
            self,
            user_id,
            user_name,
    ):
        self.user_id = user_id
        self.user_name = user_name
        self.items = []
        self.health = 0
        self.max_health = 0
        self.skip_next_turn = False
