# import pokebase as pb
from selenium import webdriver
from selenium.webdriver.common.by import By

# init pokemon information


options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver = webdriver.Chrome(
    options=options
)
driver.get("http://squirdle.fireblend.com/daily.html")


w_input_box = driver.find_element(by=By.CSS_SELECTOR, value='input')
w_guesses = driver.find_element(by=By.ID, value='guesses')

guess_list = ["Swanna"]
guess_number = 0
correct = False
while guess_number < 8 and not correct:
    guess = guess_list[guess_number]
    guess_number += 1
    w_input_box.send_keys(guess)
    w_input_box.submit()
    driver.implicitly_wait(2)
    guess_list = w_guesses.find_elements(by=By.ID, value='guess*')
    for e in guess_list:
        print (guess_list)
    
# print("guess text: " + guesses.text)


