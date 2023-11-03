from selenium import webdriver
from selenium.webdriver.common.by import By
import json
import numpy as np

# cheater global types
types = ['Normal', 'Fire', 'Water', 'Grass', 'Electric', 'Ice', 'Fighting', 'Poison', 'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Dark', 'Steel', 'Fairy', 'None']
type_dict = {}
for i, t in enumerate(types):
    type_dict[t] = i

def main(filename="data/pokedex.json"):
    pokedex, names = load_json(filename)
    pokedex = process_pokedex_json(pokedex)
    bot = Bot(pokedex, names, verbose=1)
    bot.run()

# main class
class Bot:
    def __init__(self, pokedex, names, verbose=0):
        self.verbose = verbose
        self.pokedex = pokedex
        self.names = names
        self.guess_number = 0
        self.guess_list = [692]
        self.history = []
        self.fields = ['gen', 'type1', 'type2', 'height', 'weight']
        self.options = webdriver.ChromeOptions()
        self.options.add_extension("data/adblock.crx")
        self.options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = webdriver.Chrome(
            options=self.options
        )
        self.driver.implicitly_wait(5)
        self.driver.get("http://squirdle.fireblend.com/daily.html")
        self.w_input_box = self.driver.find_element(by=By.CSS_SELECTOR, value='input')
        self.w_guesses = self.driver.find_element(by=By.ID, value='guesses')
        self.w_submit_button = self.driver.find_element(by=By.ID, value='guess_submit')
        self.w_out = self.driver.find_element(by=By.CLASS_NAME, value='bodyrow')

    def make_guess(self, guess):
        self.w_input_box.send_keys(self.names[guess])
        self.w_out.click()
        self.w_submit_button.click()
        self.history.append(self.get_by_name(guess))
        self.remove_by_name(guess)

    def read_guess(self):
        feedback = []
        w_guess_row = self.driver.find_element(by=By.ID, value="guess" + str(self.guess_number))
        w_columns = w_guess_row.find_elements(by=By.CLASS_NAME, value="column")
        for _, w_column in zip(self.fields, w_columns):
            src = w_column.find_element(by=By.TAG_NAME, value='img').get_attribute('src')
            src = src[src.rindex("/")+1:-4]
            feedback.append(src)
        return feedback
    
    def update_pokedex(self, feedback):
        guess = self.history[self.guess_number][:]
        for i in range(len(feedback)):
            current = feedback[i]
            val = guess[i+1]
            if current == "down":
                self.pokedex = np.delete(self.pokedex, np.where(self.pokedex[:,1+i] >= val), 0)
            elif current == "up":
                self.pokedex = np.delete(self.pokedex, np.where(self.pokedex[:,1+i] <= val), 0)
            elif current == "correct":
                self.pokedex = np.delete(self.pokedex, np.where(self.pokedex[:,1+i] != val), 0)
            elif current == "wrong":
                self.pokedex = np.delete(self.pokedex, np.where(self.pokedex[:,1+i] == val), 0)
            elif current == "wrongpos":
                pos = i
                if i == 1:
                    pos = 2
                else:
                    pos = 1
                self.pokedex = np.delete(self.pokedex, np.where(self.pokedex[:,1+pos] != val), 0)

    def select_guess(self):
        self.pokedex = self.pokedex[np.argsort(self.pokedex[:,4])]
        self.pokedex = self.pokedex[np.argsort(self.pokedex[:,5])]
        self.pokedex = self.pokedex[np.argsort(self.pokedex[:,1])]
        return self.pokedex[len(self.pokedex) // 2]
    
    def remove_by_name(self, pokemon_name):
        self.pokedex = np.delete(self.pokedex, np.where(self.pokedex[:,0] == pokemon_name), 0)

    def get_by_name(self, name):
        mask = self.pokedex[:, 0] == name
        return self.pokedex[mask, :][0]
    
    def check_done(self, feedback):
        for col in feedback:
            if col != 'correct':
                return False
        return True

    def run(self):
        while self.guess_number < 8:
            self.make_guess(self.guess_list[self.guess_number])
            feedback = self.read_guess()
            if self.check_done(feedback):
                input('We win! It only took ' + str(self.guess_number + 1) + "tries. Press <<Enter>> to exit...")
                return
            self.update_pokedex(feedback)
            guess = self.select_guess()
            self.guess_list.append(guess[0])
            self.guess_number += 1
        input("Failed. Press <<Enter>> to exit...")

def process_pokedex_json(pokedex):
    output = []
    i = 0
    for pokemon in pokedex:
        data = pokedex[pokemon]
        entry = [i, data[0], data[1], data[2], data[3], data[4]]
        output.append(entry)
        i += 1
    return np.array(output)
def load_json(filename="data/pokedex.json"):
    pokedex = {}
    names = []
    with open(filename, 'r') as file:
        pokedex = json.load(file)
        i = 0
        for name in pokedex:
            names.append(name)
            pokemon = pokedex[name]
            pokemon[3] *= 10
            pokemon[4] *= 10
            pokemon[3] = int(pokemon[3])
            pokemon[4] = int(pokemon[4])
            if pokemon[2] == '':
                pokemon[2] = 'None'
            pokemon[1] = type_dict[pokemon[1]]
            pokemon[2] = type_dict[pokemon[2]]
            i += 1
    return pokedex, names

if __name__ == "__main__":
    main()

