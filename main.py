from pip import main
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from bs4 import BeautifulSoup

import bs4findpath

import time


# waiting helper functions
def wait(s):
    time.sleep(s)

def wait_then_close(driver_arg, s):
    time.sleep(s)
    driver_arg.close()


#log in function definition
def linkedin_log_in( driver_p, email, pswd):
    

    #opening linkedIn webpage
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


    


def searchPeople(driver_p, keywords):
    search_bar_element = driver_p.find_element(By.CLASS_NAME, "search-global-typeahead__input")
    search_bar_element.send_keys(keywords)
    search_bar_element.send_keys(Keys.RETURN)
    wait(2)
    peopleButton = driver_p.find_element(By.XPATH, "//button[text()='People']")
    peopleButton.click()



#********************************  CONSTANT VARIABLES  ********************************
#**************************************************************************************

# Creating a webdriver instance
PATH = "C:\Program Files (x86)\chromedriver.exe"




#********************************  TESTING  ********************************
#***************************************************************************


#*****************  Log in test  ***************
#***********************************************

# This instance will be used to log into LinkedIn
main_driver = webdriver.Chrome(PATH)
email = "m_regimbald@hotmail.com"
pswd = "Regma1182!"
linkedin_log_in( main_driver, email, pswd)

searchPeople(main_driver, "developer")


doc = BeautifulSoup(main_driver.page_source, "html.parser" )
print(doc.prettify())


#wait_then_close(main_driver,5)















#*****************  Output  ***************
#***********************************************

# person = {"name": "", "link":"" , "location": "" , "bio": "", "description_keywords":[],  }
# output =[]
