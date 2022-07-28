from subprocess import TimeoutExpired
from pip import main
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

from bs4 import BeautifulSoup
import bs4findpath

import re

import time
from datetime import date
import json


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

    n_str = ""
    for character in s:
        if character.isdigit():
            n_str += character
        else:
            break
    n = int(n_str)

    return str(n + 1) + s[len(n_str):]


# replace the page=n in the old page by page=n+1 to go to the next page
def get_next_url(old_url):
    url_splitted = old_url.split("page=")
    second_part_url = get_second_part_url(url_splitted[1])
    return url_splitted[0] + "page=" + second_part_url


def get_first_n(s):
    n_str = ""
    for character in s:
        if character.isdigit():
            n_str += character
        else:
            break
    return int(n_str)


def show_all_section_page(driver_p, section_name):
    while True:
        try:
            driver_p.get(driver_p.current_url + f"details/{section_name}")
            wait(2)
            driver_p.execute_script("window.scrollTo(0,  document.body.scrollHeight);")
            wait(1)
            secondary_doc = BeautifulSoup(driver_p.page_source, "html.parser")
            li_elements = secondary_doc.find("main", id="main").find("ul").find_all("li",
                                                                                    class_="pvs-list__paged-list-item artdeco-list__item pvs-list__item--line-separated")
        except AttributeError:
            print("RELOADING THE SHOW ALL PAGE")
            continue
        else:
            break
    return li_elements


# ****************************************** MAIN SCRIPT FUNCTIONS ****************************************
# **********************************************************************************************************


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

    # click on "people" filter
    peopleButton = WebDriverWait(driver_p, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//button[text()='People']"))
    )
    peopleButton.click()

    # check if there are results to the searched keywords or not
    try:
        WebDriverWait(driver_p, 3).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "artdeco-empty-state__message"))
        )
    except TimeoutException:
        return True  # there are results to the search keywords
    else:
        return False  # the search result is empty


def get_people_links_page(driver_p):
    # initialize list variable to fill up with links and to be returned in the end
    links_list_page = []

    # sometimes linkedIn shows an error page to get in the way of the bot
    # if that s the case the ul tag woth class "reusable-search__entity-result-list" will not be present in the source code
    # in that case, keep on reloading the page untill the results show
    while True:
        try:
            doc = BeautifulSoup(driver_p.page_source, "html.parser")
            ul_element = doc.find("ul", class_="reusable-search__entity-result-list")
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
        ul_element = doc.find("ul", class_="artdeco-pagination__pages")
        max_pages = int(ul_element.find_all("li")[-1].button.span.string)
        print(f"Max pages is {max_pages}")
        return max_pages


def click_next(driver_p):
    # Simply click on next
    # Assumption: the Next button exists, otherwise an error winn be raised
    driver_p.execute_script("window.scrollTo(0,  document.body.scrollHeight);")
    element_next_button = WebDriverWait(driver_p, 5).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "artdeco-pagination__button--next"))
    )
    element_next_button.click()


def get_people_links_all(driver_p):
    # get all profile results links from all the pages

    # list toi be returned in the end
    all_links = []

    # get the numbe of pages after doing the search
    max_pages = get_max_pages(driver_p)

    # there is only one page
    if max_pages == -1:
        print("Scanning results page #1")
        return get_people_links_page(driver_p)

    # there re at least 2 pages
    else:
        # get the links from the first page
        print("Scanning results page #1")
        links_list_page = get_people_links_page(driver_p)
        all_links = all_links + links_list_page
        click_next(driver_p)
        wait(3)

        # get the links from second to max_pages'th page
        for i in range(1, max_pages):
            # get the list of links from page i
            print(f"Scanning results page {i + 1}")
            links_list_page = get_people_links_page(driver_p)
            all_links = all_links + links_list_page
            # concatenate the lisy of the page woth the list of previous pages
            wait(2)

            if i + 1 == max_pages:
                break
            else:
                old_url = driver_p.current_url
                driver_p.get(get_next_url(old_url))
                wait(2)

    return all_links


def scrape_profile(driver_p, url):
    person = {"link": "",
              "added_on": "",
              "name": "",
              "title": "",
              "location": "",
              "about": "",
              "is_looking_for_job": True,  # toDev
              "experience": {},
              "education": {},
              "licenses_and_certifications": {},
              "skills": {},
              "high_endorsement": True,
              # toDev (if person has endorsements from big companies or have more than 20(or n ) endorsements, set to True )
              "projects": 0,  # mention only the number of projects
              "courses": [],
              "languages": [],
              "volunteering_experience": {}
              }

    while True:
        try:
            driver_p.get(url)
        except WebDriverException:
            print("WE CATCHED THE EXCEPTION ")
            continue
        else:
            break

    wait(2)

    doc = BeautifulSoup(driver_p.page_source, "html.parser")

    # get link
    person["link"] = url

    # get date
    person["added_on"] = date.today().strftime("%m/%d/%y")

    # get name
    name = doc.find("h1", class_="text-heading-xlarge").string
    person["name"] = name

    # get title
    title = doc.find("div", class_="text-body-medium break-words").string.strip('\n').strip(" ").strip('\n')
    person["title"] = title

    # get location
    location = doc.find("span", class_="text-body-small inline t-black--light break-words").string.strip('\n').strip(
        " ").strip('\n')
    person["location"] = location

    # GET THE REST THE OTHER SECTIONS
    main_element = doc.find("main", id="main")
    section_elements = main_element.find_all("section", class_="artdeco-card ember-view relative break-words pb3 mt2")

    for section in section_elements:

        if section.div['id'] == "about":
            span_element = section.find("div", class_="display-flex ph5 pv3").find("span")
            about_text = "".join("".join((str(span_element)[33:-15]).split("<br/>")).split("<!-- -->"))
            person["about"] = about_text


        elif section.div['id'] == "experience":

            show_all = section.find("span", class_="pvs-navigation__text")

            if show_all is None:
                companies = section.find("ul").find_all("li",
                                                        class_="artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column")
                for company in companies:
                    a_element = company.find("div", class_="display-flex flex-row justify-space-between").find("a")

                    if a_element is None:  # one job at that company
                        job = str(company.find("span", class_="mr1 t-bold").span)[33:-15]
                        try:
                            company_name = str(company.find("span", class_="t-14 t-normal").span)[33:-15]
                        except AttributeError:
                            company_name: "Unavailable"
                        person["experience"][company_name] = job
                    else:
                        jobs = []
                        try:
                            company_name = str(company.find("span", class_="mr1 hoverable-link-text t-bold").span)[
                                           33:-15]
                        except AttributeError:
                            company_name: "Unavailable"

                        jobs_list_elements = company.find("ul", class_="pvs-list").find_all("li", class_="")
                        for job_element in jobs_list_elements:
                            if job_element.find_all(recursive=False)[0].name == "span":
                                job = str(
                                    job_element.find("a").find("span", class_="mr1 hoverable-link-text t-bold").span)[
                                      33:-15]
                                jobs.append(job)
                        person["experience"][company_name] = jobs

            else:
                driver_p.get(driver_p.current_url + "details/experience")
                wait(1)
                driver_p.execute_script("window.scrollTo(0,  document.body.scrollHeight);")
                wait(2)
                secondary_doc = BeautifulSoup(driver_p.page_source, "html.parser")

                companies = secondary_doc.find("main", id="main").find("ul").find_all("li",
                                                                                      class_="pvs-list__paged-list-item artdeco-list__item pvs-list__item--line-separated")
                for company in companies:
                    a_element = company.find("div", class_="display-flex flex-row justify-space-between").find("a")

                    if a_element is None:  # one job at that company
                        job = str(company.find("span", class_="mr1 t-bold").span)[33:-15]
                        company_name = str(company.find("span", class_="t-14 t-normal").span)[33:-15]
                        person["experience"][company_name] = job
                    else:
                        jobs = []
                        company_name = str(a_element.find("span", class_="mr1 hoverable-link-text t-bold").span)[33:-15]
                        jobs_list_elements = company.find("ul", class_="pvs-list").find_all("li",
                                                                                            class_="pvs-list__paged-list-item")
                        for job_element in jobs_list_elements:
                            if job_element.find_all(recursive=False)[0].name == "span":
                                job = str(
                                    job_element.find("a").find("span", class_="mr1 hoverable-link-text t-bold").span)[
                                      33:-15]
                                jobs.append(job)
                        person["experience"][company_name] = jobs
                driver_p.back()
                wait(1)



        elif section.div['id'] == "education":

            show_all = section.find("span", class_="pvs-navigation__text")
            if show_all is None:
                schools = section.find("ul").find_all("li",
                                                      class_="artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column")
                for school_element in schools:
                    school_name = str(school_element.find("span", class_="mr1 hoverable-link-text t-bold").span)[33:-15]
                    try:
                        degree = str(school_element.find("span", class_="t-14 t-normal").span)[33:-15]
                    except AttributeError:
                        degree = "degree unavailable"
                    person["education"][school_name] = degree

            else:
                driver_p.get(driver_p.current_url + "details/education")
                wait(1)
                driver_p.execute_script("window.scrollTo(0,  document.body.scrollHeight);")
                wait(2)
                secondary_doc = BeautifulSoup(driver_p.page_source, "html.parser")
                universities = secondary_doc.find("main", id="main").find("ul").find_all("li",
                                                                                         class_="pvs-list__paged-list-item artdeco-list__item pvs-list__item--line-separated")
                for school_element in universities:
                    school_name = str(school_element.find("span", class_="mr1 hoverable-link-text t-bold").span)[33:-15]
                    try:
                        degree = str(school_element.find("span", class_="t-14 t-normal").span)[33:-15]
                    except AttributeError:
                        degree = "degree unavailable"
                    person["education"][school_name] = degree

                driver_p.back()
                wait(1)


        elif section.div['id'] == "licenses_and_certifications":
            show_all = section.find("span", class_="pvs-navigation__text", text=re.compile("Show all"))
            if show_all is None:

                certifications = section.find("ul").find_all("li",
                                                             class_="artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column")
                for certificate_element in certifications:
                    provider = str(certificate_element.find("span", class_="mr1 t-bold").span)[33:-15]
                    certificate = str(certificate_element.find("span", class_="t-14 t-normal").span)[33:-15]
                    person["licenses_and_certifications"][provider] = certificate

            else:
                driver_p.get(driver_p.current_url + "details/certifications")
                wait(1)
                driver_p.execute_script("window.scrollTo(0,  document.body.scrollHeight);")
                wait(2)
                secondary_doc = BeautifulSoup(driver_p.page_source, "html.parser")
                certifications = secondary_doc.find("main", id="main").find("ul").find_all("li",
                                                                                           class_="pvs-list__paged-list-item artdeco-list__item pvs-list__item--line-separated")
                for certification_element in certifications:
                    certificate = str(certification_element.find("span", {"class":["mr1", "hoverable-link-text", "t-bold"]}).span)[33:-15]
                    provider = str(certification_element.find("span", class_="t-14 t-normal").span)[33:-15]
                    person["education"][provider] = certificate

                driver_p.back()
                wait(1)

        elif section.div['id'] == "skills":

            show_all = section.find("span", class_="pvs-navigation__text")

            if show_all is None:
                skills = section.find("ul").find_all("li",
                                                     class_="artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column")
                for skill_element in skills:
                    the_skill = str(skill_element.find("span", class_="mr1 t-bold").span)[33:-15]
                    spans_list = skill_element.find_all("span")
                    n_endorsements = 0
                    for span_element in spans_list:
                        if "endorsement" in str(span_element):
                            n_endorsements_str = str(span_element)[33:-15]
                            n_endorsements = get_first_n(n_endorsements_str)
                            break
                    person["skills"][the_skill] = n_endorsements
            else:

                skills = show_all_section_page(driver_p, "skills")
                for skill_element in skills:
                    the_skill = str(skill_element.find("span", class_="mr1 t-bold").span)[33:-15]
                    spans_list = skill_element.find_all("span")
                    n_endorsements = 0
                    for span_element in spans_list:
                        if "endorsement" in str(span_element):
                            n_endorsements_str = str(span_element)[33:-15]
                            n_endorsements = get_first_n(n_endorsements_str)
                            break
                    person["skills"][the_skill] = n_endorsements
                driver_p.back()
                wait(1)

            print("hi")


        elif section.div['id'] == "courses":
            show_all = section.find("span", class_="pvs-navigation__text")

            if show_all is None:
                courses = section.find("ul").find_all("li",
                                                      class_="artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column")
                for course_element in courses:
                    course_title = str(course_element.find("span", class_="mr1 t-bold").span)[33:-15]
                    person["courses"].append(course_title)

            else:
                driver_p.get(driver_p.current_url + "details/courses")
                wait(1)
                driver_p.execute_script("window.scrollTo(0,  document.body.scrollHeight);")
                wait(2)
                secondary_doc = BeautifulSoup(driver_p.page_source, "html.parser")
                courses = secondary_doc.find("main", id="main").find("ul").find_all("li",
                                                                                    class_="pvs-list__paged-list-item artdeco-list__item pvs-list__item--line-separated")
                for course_element in courses:
                    course_title = str(course_element.find("span", class_="mr1 t-bold").span)[33:-15]
                    person["courses"].append(course_title)
                driver_p.back()
                wait(1)


        elif section.div['id'] == "projects":
            projects = section.find("ul").find_all("li",
                                                   class_="artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column")
            person["projects"] = len(projects)


        elif section.div['id'] == "languages":
            languages = section.find("ul").find_all("li",
                                                    class_="artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column")
            for language_element in languages:
                language = str(language_element.find("span", class_="mr1 t-bold").span)[33:-15]
                person["languages"].append(language)


        elif section.div['id'] == "volunteering_experience":
            volunteering = section.find("ul").find_all("li",
                                                       class_="artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column")
            for volunteering_element in volunteering:
                volunteering_exp = str(volunteering_element.find("span", class_="mr1 t-bold").span)[33:-15]
                volunteering_org = str(volunteering_element.find("span", class_="t-14 t-normal").span)[33:-15]
                person["volunteering_experience"][volunteering_org] = volunteering_exp


        else:  # Multiple jobs at that company
            continue

    return person


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

url_test = "https://www.linkedin.com/in/anushikad5/"
url_muj = "https://www.linkedin.com/in/ouatheksghairi/"
url_alex = "https://www.linkedin.com/in/alex-kozak1/"
url_kim = "https://www.linkedin.com/in/kim-fontaine-skronski-a458806a/"
# scrape_profile(main_driver, url_test)

# search tests:
# journalist IRAQ USA -> 2 pages
# developer python psychology Canada -> 19 pages
# developer python psychology mexico -> 5 pages
# search_results = search_people(main_driver, "journalist IRAQ USA")


# if search_results:
#     final_list = get_people_links_all(main_driver)
#     print(final_list)
#     print(f"finally, the total length of the list is {len(final_list)}")
# else:
#     final_list= []
#     print("No results found for your search. Try other keywords.")

final_list_orgnl = [
    'https://www.linkedin.com/in/kelly-kennedy-5072303?miniProfileUrn=urn%3Ali%3Afs_miniProfile%3AACoAAACRPdcBTv_Zujs7InZUwnveaJvDpAY_Ayk',
    'https://www.linkedin.com/in/ingrid-lund-7585ba?miniProfileUrn=urn%3Ali%3Afs_miniProfile%3AACoAAAAWvrQBWWaN5AQYWuwTvYVb_XKUIYETtoI',
    'https://www.linkedin.com/in/viviansalama?miniProfileUrn=urn%3Ali%3Afs_miniProfile%3AACoAAAKeYDEBOhJKYRFcGPvW8eMBnKPSEAfjaUs',
    'https://www.linkedin.com/in/david-ruiz-de-la-torre-1ab05b48?miniProfileUrn=urn%3Ali%3Afs_miniProfile%3AACoAAAn5YFMB6u91Dl9JBR5JlCQa0hmR8HfjKLM',
    'https://www.linkedin.com/in/%D8%AE%D8%A7%D9%84%D8%AF-%D8%A7%D9%84%D9%86%D8%AC%D8%A7%D8%B1-khilednajar-8a554263?miniProfileUrn=urn%3Ali%3Afs_miniProfile%3AACoAAA1tgn0BF2Xd0OzJ-LzXcD89-nd7-3sgl-A',
    'https://www.linkedin.com/in/aaronglantz?miniProfileUrn=urn%3Ali%3Afs_miniProfile%3AACoAAABYPhUBhun4yrzM_oR1XUBxSuW0awxycYI',
    'https://www.linkedin.com/in/marine-olivesi-471539b?miniProfileUrn=urn%3Ali%3Afs_miniProfile%3AACoAAAIJXlUBwHzaLzUrSo1x5U_M90h0QrGA1Nc',
    'https://www.linkedin.com/in/boushra-mahfoud-62077697?miniProfileUrn=urn%3Ali%3Afs_miniProfile%3AACoAABSUpvgB72_yc7nubQ_YDGvcEAxvFjhtkOM',
    'https://www.linkedin.com/in/ryanhudziak?miniProfileUrn=urn%3Ali%3Afs_miniProfile%3AACoAAAGQvXABLjaSLmmBp6KYHsTnYdKC3HiuNeU',
    'https://www.linkedin.com/in/hughan?miniProfileUrn=urn%3Ali%3Afs_miniProfile%3AACoAAAHXXacB17-BonhGV3l_aamrY7GceK148Xc',
    'https://www.linkedin.com/in/denis-chaudr%C3%A9-6b1b2522?miniProfileUrn=urn%3Ali%3Afs_miniProfile%3AACoAAATLK6UB28-r47kMXbMruGbnWHqzujuqfnk',
    'https://www.linkedin.com/in/arfan-majeed-2a3b6674?miniProfileUrn=urn%3Ali%3Afs_miniProfile%3AACoAAA_VVBsB-jQGHAcD5HJmDZRXGLwGmuXcZNM',
    'https://www.linkedin.com/in/kareem-botane-5b60b1214?miniProfileUrn=urn%3Ali%3Afs_miniProfile%3AACoAADYehRoBZgzrt1yvzZYgLxADaKnScvN-2aw']
final_list = [
    'https://www.linkedin.com/in/boushra-mahfoud-62077697?miniProfileUrn=urn%3Ali%3Afs_miniProfile%3AACoAABSUpvgB72_yc7nubQ_YDGvcEAxvFjhtkOM',
    'https://www.linkedin.com/in/ryanhudziak?miniProfileUrn=urn%3Ali%3Afs_miniProfile%3AACoAAAGQvXABLjaSLmmBp6KYHsTnYdKC3HiuNeU',
    ]

output_list = []

if final_list:
    for profile_url in final_list:
        output_list.append(scrape_profile(main_driver, profile_url))

text_file = open("sample.txt", "w")
output_json_str = json.dumps(output_list)
text_file.write(output_json_str)

