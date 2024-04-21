from selenium import webdriver
from bs4 import BeautifulSoup
import time
from selenium.webdriver.firefox.options import Options


def reverse_geocode(latitude,longitude):
    options = Options()
    options.add_argument("--headless")

    driver = webdriver.Firefox(options=options)

    #lat = 22.625822
    #lon = 88.379289

    # URL of the website
    url = f"https://developers-dot-devsite-v2-prod.appspot.com/maps/documentation/utils/geocoder#q%3D{latitude}%252C{longitude}"  

    # Load the webpage
    driver.get(url)

    # Wait for the dynamic content to load (adjust sleep time as needed)
    time.sleep(5)  # You might need to adjust this time depending on how long it takes for the content to load

    # Parse the HTML content after the JavaScript has executed
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Find all elements with class 'result-formatted-address'


    address = soup.find_all(class_='result-formatted-address')[1]
    locality = soup.find('td', class_='vtop', string='locality').find_next_sibling()
    state = soup.find('td', class_='vtop', string='administrative_area_level_1').find_next_sibling()
    country = soup.find('td', class_='vtop', string='country').find_next_sibling()

    address = address.contents[2].strip()
    locality = locality.contents[0].strip()
    state = state.contents[0].strip()
    country = country.contents[0].strip()

    driver.quit()

    ADDR = [f"{locality}, {state}, {country}", address]

    print(ADDR)
    return ADDR

#print(reverse_geocode(22.625822,88.379289))
