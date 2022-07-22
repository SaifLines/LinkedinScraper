from subprocess import TimeoutExpired
from pip import main
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

import bs4findpath

import time




# ********************************************* HELPER FUNCTIONS *********************************************
# *************************************************************************************************************


# ************** WAIT FUNCTIONS *************

# pause the program for s seconds
def wait(s):
    time.sleep(s)


# pause the program for s seconds then close the webpage
def wait_then_close(driver_arg, s):
    time.sleep(s)
    driver_arg.close()




# ************** URL FUNCTIONS *************
def get_second_part_url(s):
    # gets a str like "2&sid=Mqu" as input. (the second part of a url)
    # returns "3&sid=Mqu" if max_pages >= 3 else return None because there is no url that has "3&sid=Mqu"
    
    n_str=""
    for character in s:
        if character.isdigit():
            n_str += character
        else:
            break
    n = int(n_str)
    
    return str(n + 1) + s[len(n_str):]


#replace the page=n in the old page by page=n+1 to go to the next page
def get_next_url(old_url):
    url_splitted = old_url.split("page=")
    second_part_url = get_second_part_url(url_splitted[1])
    return url_splitted[0] + "page=" +  second_part_url









# ****************************************** MAIN SCRIPT FUNCTIONS ****************************************
#**********************************************************************************************************
     


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
    peopleButton = WebDriverWait(driver_p, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='People']"))
        )
    peopleButton.click()

    #check if there are results to the searched keywords or not
    try:
        WebDriverWait(driver_p, 3).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "artdeco-empty-state__message"))
        )
    except TimeoutException:
        return True #there are results to the search keywords
    else:
        return False #the search result is empty



def get_people_links_page(driver_p):
    #initialize list variable to fill up with links and to be returned in the end
    links_list_page = []


    #sometimes linkedIn shows an error page to get in the way of the bot
    # if that s the case the ul tag woth class "reusable-search__entity-result-list" will not be present in the source code
    # in that case, keep on reloading the page untill the results show
    while True:
        try:
            doc = BeautifulSoup(driver_p.page_source, "html.parser")
            ul_element = doc.find("ul",class_="reusable-search__entity-result-list")
            profiles_li_elements = ul_element.find_all("li")

        except AttributeError:
            wait(2)
            driver_p.refresh()
            print("Reloading page")
            wait(5)
            continue
        else:
            break

    for li in profiles_li_elements:
        # if the profile is part of the user's network add it to the list
        if li.find("span", class_="artdeco-button__text") is not None:
            link = li.find("span", class_="entity-result__title-text").find("a")['href']
            links_list_page.append(link)

    
    print(f"{len(links_list_page)} profiles added to the list")
    print()
    return links_list_page



def get_max_pages(driver_p):
    # getting the maximum number of pages for the given search

    # check if there is a Next button
    try:
        driver_p.execute_script("window.scrollTo(0,  document.body.scrollHeight);")
        WebDriverWait(driver_p, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "artdeco-pagination__button--next"))
        )
    
    # if there is not then, the results are only in one page
    except TimeoutException:
        print(-1)
        return -1
    
    # if there is a next button, then there are at least 2 pages
    # get the the number of pages by targeting the last <li> tag in the pagination <ul> 
    else:
        doc = BeautifulSoup(driver_p.page_source, "html.parser")
        ul_element = doc.find("ul",class_="artdeco-pagination__pages")
        max_pages = int(ul_element.find_all("li")[-1].button.span.string)
        print(f"Max pages is {max_pages}")
        return max_pages


def click_next(driver_p):
    #Simply click on next
    #Assumption: the Next button exists, otherwise an error winn be raised
    driver_p.execute_script("window.scrollTo(0,  document.body.scrollHeight);")
    element_next_button = WebDriverWait(driver_p, 5).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "artdeco-pagination__button--next"))
    )
    element_next_button.click()
    



def get_people_links_all(driver_p):
    # get all profile results links from all the pages


    # list toi be returned in the end 
    all_links =[]

    #get the numbe of pages after doing the search
    max_pages = get_max_pages(driver_p)

    # there is only one page
    if max_pages == -1 :
        print("Scanning results page #1")
        return get_people_links_page(driver_p)

    #there re at least 2 pages
    else:
        #get the links from the first page
        print("Scanning results page #1")
        links_list_page = get_people_links_page(driver_p)
        all_links = all_links + links_list_page
        click_next(driver_p)
        wait(3)

        #get the links from second to max_pages'th page
        for i in range(1,max_pages):
            #get the list of links from page i
            print(f"Scanning results page {i+1}")
            links_list_page = get_people_links_page(driver_p)
            all_links = all_links + links_list_page
            #concatenate the lisy of the page woth the list of previous pages
            wait(2) 

            if i+1 == max_pages:
                break
            else:
                old_url = driver_p.current_url
                driver_p.get(get_next_url(old_url))
                wait(2)

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

#search tests:
# journalist IRAQ USA -> 2 pages
# developer python psychology Canada -> 19 pages
# developer python psychology mexico -> 5 pages
search_results = search_people(main_driver, "developer python psychology mexico")
wait(2)

if search_results:
    final_list = get_people_links_all(main_driver)
    print(final_list)
    print(f"finally, the total length of the list is {len(final_list)}")
else:
    print("No results found for your search. Try other keywords.")









# *****************  Output  ***************
# ***********************************************

# person = {"name": "", "link":"" , "location": "" , "bio": "", "description_keywords":[],  }
# output =[]
