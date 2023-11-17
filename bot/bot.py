from selenium import webdriver
from selenium.webdriver.common.by import By
import json
import getopt, sys
import numpy as np
import time

# cheater global types
types = ['Normal', 'Fire', 'Water', 'Grass', 'Electric', 'Ice', 'Fighting', 'Poison', 'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Dark', 'Steel', 'Fairy', 'None']
type_dict = {}
for i, t in enumerate(types):
    type_dict[t] = i

def main(daily=False):
    pokedex, names = load_json()
    pokedex = process_pokedex_json(pokedex)
    bot = Bot(pokedex, names, daily=daily, verbose=1, initial_guess=616)
    bot.run()
    exit(0)
    
def sim():
    now = time.time()
    orig_pokedex, names = load_json()
    processed = process_pokedex_json(orig_pokedex)
    results = []
    for i in range(len(orig_pokedex)):
        if i % 100 == 0 and i > 0:
            print('i = ' + str(i))
        row = []
        for j in range(len(orig_pokedex)):
            pokedex = processed
            bot = Bot(pokedex, names, web=False, initial_guess=i)
            row.append(bot.sim(j))
        results.append(row)
    # with open('out.txt', 'w') as f:
    #     json.dump(results, f)
    results = np.array(results)
    averages = np.average(results, axis=1)
    out = {}
    avg_out = {}
    for name, res in zip(names, results):
        out[name] = res.tolist()
    for name, avg in zip(names, averages):
        avg_out[name] = avg
    try:

        with open('avg.json', 'w') as fi:
            json.dump(avg_out, fi)
        with open('res.json', 'w') as f:
            json.dump(out, f)
        print ('saved to avg.json and res.json')
    except Exception as e:
        print ('error in saving file')
        print (e)
    print ('time elapsed ' + str(time.time() - now))
    exit(0)

# main class
class Bot:
    def __init__(self, pokedex, names, web=True, daily=False, verbose=0, initial_guess=692):
        url = "http://squirdle.fireblend.com/daily.html" if daily else "http://squirdle.fireblend.com/"
        self.verbose = verbose
        self.pokedex = pokedex
        self.names = names
        self.initial_guess = initial_guess
        self.guess_number = 0
        self.guess_list = []
        self.history = []
        self.fields = ['gen', 'type1', 'type2', 'height', 'weight']
        if web:
            self.options = webdriver.ChromeOptions()
            self.options.add_extension("data/adblock.crx")
            self.options.add_experimental_option('excludeSwitches', ['enable-logging'])
            self.driver = webdriver.Chrome(
                options=self.options
            )
            self.driver.implicitly_wait(5)
            self.driver.get(url)
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

    def sim_guess(self, guess):
        # print (self.names[guess])
        guess_stats = self.get_by_name(guess)
        target_stats = self.get_by_name(self.target)
        feedback = ['','','','','']
        for i in range(1, len(guess_stats)):
            if guess_stats[i] == target_stats[i]:
                feedback[i-1] = 'correct'
        if guess_stats[1] > target_stats[1]:
            feedback[0] = 'down'
        elif guess_stats[1] < target_stats[1]:
            feedback[0] = 'up'
        if guess_stats[2] == target_stats[3]:
            feedback[1] = 'wrongpos'
        elif guess_stats[2] != target_stats[2]:
            feedback[1] = 'wrong'
        if guess_stats[3] == target_stats[2]:
            feedback[2] = 'wrongpos'
        elif guess_stats[3] != target_stats[3]:
            feedback[2] = 'wrong'
        if guess_stats[4] > target_stats[4]:
            feedback[3] = 'down'
        elif guess_stats[4] < target_stats[4]:
            feedback[3] = 'up'
        if guess_stats[5] > target_stats[5]:
            feedback[4] = 'down'
        elif guess_stats[5] < target_stats[5]:
            feedback[4] = 'up'
        self.history.append(self.get_by_name(guess))
        self.remove_by_name(guess)
        return feedback

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
                self.pokedex = np.delete(self.pokedex, np.where(self.pokedex[:,pos + 1] != val), 0)

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
        self.guess_list.append(self.initial_guess)
        while self.guess_number < 8:
            self.make_guess(self.guess_list[self.guess_number])
            feedback = self.read_guess()
            if self.check_done(feedback):
                input('We win! It only took ' + str(self.guess_number + 1) + " tries. Press <<Enter>> to exit...")
                return
            self.update_pokedex(feedback)
            guess = self.select_guess()
            self.guess_list.append(guess[0])
            self.guess_number += 1
        input("Failed. Press <<Enter>> to exit...")

    def sim(self, target):
        self.guess_list.append(self.initial_guess)
        self.target = target
        while self.guess_number < 8:
            feedback = self.sim_guess(self.guess_list[self.guess_number])
            if self.check_done(feedback):
                return self.guess_number + 1
            self.update_pokedex(feedback)
            guess = self.select_guess()
            self.guess_list.append(guess[0])
            self.guess_number += 1
        return 1000000
    
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
    argumentList = sys.argv[1:]
    options = "ds"
    long_options = ["daily", "sim"]
    try:
        arguments, values = getopt.getopt(argumentList, options, long_options)
        for currentArgument, currentValue in arguments:
            if currentArgument in ("-d", "--daily"):
                main(daily=True)
            elif currentArgument in ('-s', "--sim"):
                sim()
        
        main()
    except getopt.error as err:
        print (str(err))

