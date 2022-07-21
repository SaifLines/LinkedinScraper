from pip import main
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from bs4 import BeautifulSoup

import bs4findpath

import time




# waiting helper functions
def wait(s):
    time.sleep(s)


def wait_then_close(driver_arg, s):
    time.sleep(s)
    driver_arg.close()




# log in function definition
def linkedin_log_in(driver_p, email, pswd):
    # opening linkedIn webpage
    driver_p.get("https://linkedin.com/uas/login")

    wait(3)
    # entering username
    username = driver_p.find_element(By.ID, "username")
    username.send_keys(email)

    # entering password
    pword = driver_p.find_element(By.ID, "password")
    pword.send_keys(pswd)

    # Clicking on the log in button
    driver_p.find_element(By.XPATH, "//button[@type='submit']").click()




def search_people(driver_p, keywords):

    # input in the search bar and enter
    search_bar_element = driver_p.find_element(By.CLASS_NAME, "search-global-typeahead__input")
    search_bar_element.send_keys(keywords)
    search_bar_element.send_keys(Keys.RETURN)

    #click on "people" filter
    try:
        peopleButton = WebDriverWait(driver_p, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='People']"))
        )
    except TimeoutException:
        driver_p.refresh()
        peopleButton = WebDriverWait(driver_p, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='People']"))
        )
    peopleButton.click()






def get_people_links_page(driver_p, links_list):

    while True:
        try:
            doc = BeautifulSoup(driver_p.page_source, "html.parser")
            ul_element = doc.find("ul",class_="reusable-search__entity-result-list")
            profiles_li_elements = ul_element.find_all("li")

        except AttributeError:
            wait(2)
            driver_p.refresh()
            print("asbaaaaaaaaaaaaaaaaaa")
            wait(5)
            continue
        else:
            break

    for li in profiles_li_elements:
        if li.find("span", class_="artdeco-button__text") is not None:
            link = li.find("span", class_="entity-result__title-text").find("a")['href']
            links_list.append(link)

    print()
    print(len(links_list))



def click_next(driver_p):
    driver_p.execute_script("window.scrollTo(0,  document.body.scrollHeight);")
    element = WebDriverWait(driver_p, 5).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "artdeco-pagination__button--next"))
    )
    element.click()



def get_people_links_all(driver_p):

    all_links =[]

    for i in range(100):
        get_people_links_page(driver_p, all_links)
        wait(1)
        if i < 99:
            click_next(driver_p)
        wait(2)

    print(f"finally, the total length of the list is {len(all_links)}")
    return all_links


# ********************************  CONSTANT VARIABLES  ********************************
# **************************************************************************************

# Creating a webdriver instance
PATH = "C:\Program Files (x86)\chromedriver.exe"

# ********************************  TESTING  ********************************
# ***************************************************************************


# *****************  Log in test  ***************
# ***********************************************

# This instance will be used to log into LinkedIn
main_driver = webdriver.Chrome(PATH)
email = "m_regimbald@hotmail.com"
pswd = "Regma1182!"
linkedin_log_in(main_driver, email, pswd)

search_people(main_driver, "journalist")

wait(3)




# scrape all profile results in a single page, next page, scrape, next page, scrape, etc (untill there are no more pages)
all_links_list = get_people_links_all(main_driver)

# wait_then_close(main_driver,5)












# *****************  Output  ***************
# ***********************************************

# person = {"name": "", "link":"" , "location": "" , "bio": "", "description_keywords":[],  }
# output =[]
