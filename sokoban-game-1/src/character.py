class Character:
    def __init__(self, name, symbol, position):
        self.name = name
        self.symbol = symbol
        self.position = position

    def move(self, new_position):
        self.position = new_position

    def get_info(self):
        return {
            "name": self.name,
            "symbol": self.symbol,
            "position": self.position
        }