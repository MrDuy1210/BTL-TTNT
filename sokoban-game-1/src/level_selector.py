class LevelSelector:
    def __init__(self, levels_directory):
        self.levels_directory = levels_directory
        self.levels = self.load_levels()

    def load_levels(self):
        import os
        import json

        levels = {}
        for filename in os.listdir(self.levels_directory):
            if filename.endswith('.json'):
                with open(os.path.join(self.levels_directory, filename), 'r') as file:
                    levels[filename] = json.load(file)
        return levels

    def display_levels(self):
        print("Available Levels:")
        for index, level in enumerate(self.levels.keys(), start=1):
            print(f"{index}. {level}")

    def select_level(self, choice):
        level_keys = list(self.levels.keys())
        if 1 <= choice <= len(level_keys):
            selected_level = level_keys[choice - 1]
            return self.levels[selected_level]
        else:
            print("Invalid choice. Please select a valid level number.")
            return None

if __name__ == "__main__":
    level_selector = LevelSelector('src/levels')
    level_selector.display_levels()
    choice = int(input("Select a level by number: "))
    selected_level = level_selector.select_level(choice)
    if selected_level:
        print("You have selected:", selected_level)