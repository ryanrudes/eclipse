from planner.enums import TripType, FlightClass
from planner.utils import chunkify

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from datetime import datetime
from bs4 import BeautifulSoup

from typing import Union, Optional
from time import sleep

import logging
import re

logger = logging.getLogger(__name__)
    
class API:
    endpoint = "https://www.google.com/travel/flights/search"
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        
        options = webdriver.ChromeOptions()
        
        if not debug:
            options.add_argument("--headless=new")
            
        options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(options = options)
        self.driver.implicitly_wait(30)
    
    def search(
        self,
        departing_from: Union[str, list[str]],
        arriving_to: Union[str, list[str]],
        departure_date: Union[datetime, list[datetime]],
        trip: TripType = TripType.ROUNDTRIP,
        flight_class: FlightClass = FlightClass.ECONOMY,
        return_date: Optional[datetime] = None,
        adults: int = 1,
        children: int = 0,
        infants_in_seat: int = 0,
        infants_on_lap: int = 0,
    ):
        if isinstance(departing_from, str):
            departing_from = [departing_from]
        
        if isinstance(arriving_to, str):
            arriving_to = [arriving_to]
            
        if isinstance(departure_date, datetime):
            departure_date = [departure_date]
            
        if trip == TripType.MULTICITY:
            raise NotImplementedError("Multi-city trips are not yet supported.")
        elif trip == TripType.ROUNDTRIP and return_date is None:
            raise ValueError("Return date must be specified for round-trip flights.")
        
        if adults < 1:
            raise ValueError("At least one adult must be present.")
        
        if children < 0:
            raise ValueError("Cannot have a negative number of children.")
        
        if infants_in_seat < 0 or infants_on_lap < 0:
            raise ValueError("Cannot have a negative number of infants.")
        
        # We can only query up to 7 airports at a time, so chunk the airports
        # into groups of 7
        for departing_group in chunkify(departing_from, 7):
            for arriving_group in chunkify(arriving_to, 4):
                for date in departure_date:
                    yield from self._search(
                        departing_from = departing_group,
                        arriving_to = arriving_group,
                        departure_date = date,
                        trip = trip,
                        flight_class = flight_class,
                        return_date = return_date,
                        adults = adults,
                        children = children,
                        infants_in_seat = infants_in_seat,
                        infants_on_lap = infants_on_lap,
                    )
    
    def _search(
        self,
        departing_from: Union[str, list[str]],
        arriving_to: Union[str, list[str]],
        departure_date: datetime,
        trip: TripType = TripType.ROUNDTRIP,
        flight_class: FlightClass = FlightClass.ECONOMY,
        return_date: Optional[datetime] = None,
        adults: int = 1,
        children: int = 0,
        infants_in_seat: int = 0,
        infants_on_lap: int = 0,
    ):
        driver = self.driver
        driver.get(self.endpoint)
        
        actions = ActionChains(driver)
        
        # Select trip type
        if trip != TripType.DEFAULT:
            trip_type_dropdown_menu_button = driver.find_elements(By.CLASS_NAME, "VfPpkd-TkwUic")[0]
            trip_type_dropdown_menu_button.click()
            trip_type_button = driver.find_elements(By.CLASS_NAME, "VfPpkd-rymPhb-ibnC6b-OWXEXe-SfQLQb-Woal0c-RWgCYc")[trip.value]
            trip_type_button.click()
        
        # Select flight class
        if flight_class != FlightClass.DEFAULT:
            flight_class_dropdown_menu_button = driver.find_elements(By.CLASS_NAME, "VfPpkd-TkwUic")[1]
            flight_class_dropdown_menu_button.click()
            flight_class_button = driver.find_elements(By.CLASS_NAME, "VfPpkd-rymPhb-ibnC6b-OWXEXe-SfQLQb-Woal0c-RWgCYc")[flight_class.value]
            flight_class_button.click()
        
        # Select passengers
        if adults > 1 or children or infants_in_seat or infants_on_lap != 0:
            passengers_dropdown_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, "Hj7hq")))
            passengers_dropdown_button.click()
            
            increment_buttons = driver.find_elements(By.CLASS_NAME, "g2ZhCc")
            
            # Add adults
            if adults > 1:
                increment_adults_button = increment_buttons[1]
                
                for _ in range(adults - 1):
                    increment_adults_button.click()
                    
            # Add children
            if children:
                increment_children_button = increment_buttons[3]
                
                for _ in range(children):
                    increment_children_button.click()
                    
            # Add infants in seat
            if infants_in_seat:
                increment_infants_in_seat_button = increment_buttons[5]
                
                for _ in range(infants_in_seat):
                    increment_infants_in_seat_button.click()
                    
            # Add infants on lap
            if infants_on_lap:
                increment_infants_on_lap_button = increment_buttons[7]
                
                for _ in range(infants_on_lap):
                    increment_infants_on_lap_button.click()
            
            # Click "Done"
            done_button = driver.find_elements(By.CLASS_NAME, "sIWnMc")[2]
            done_button.click()
        
        # Get departure and arrival time fields
        departure_arrival_time_fields = driver.find_elements(By.CLASS_NAME, "GYgkab")

        # Enter departure date
        departure_time_field = departure_arrival_time_fields[0]
        departure_time_field.click()
        
        departure_time_field = driver.find_elements(By.CLASS_NAME, "TP4Lpb")[2]
        departure_time_field.click()
        departure_time_field.send_keys(departure_date.strftime("%Y-%m-%d"))
        departure_time_field.send_keys(Keys.RETURN)
        
        # Enter return date
        if trip == TripType.ROUNDTRIP:
            return_time_field = driver.find_elements(By.CLASS_NAME, "TP4Lpb")[3]
            return_time_field.click()
            return_time_field.send_keys(return_date.strftime("%Y-%m-%d"))
            return_time_field.send_keys(Keys.RETURN)
        
        # Click "Done"
        done_button = driver.find_element(By.CLASS_NAME, "WXaAwc")
        done_button.click()
        
        # Enter departure and arrival locations
        departure_arrival_fields = driver.find_elements(By.CLASS_NAME, "II2One")
        
        departure_field = departure_arrival_fields[0]
        arrival_field = departure_arrival_fields[2]
        
        # Enter departure locations
        departure_field.click()
        actions.key_down(Keys.COMMAND).send_keys('A').key_up(Keys. COMMAND).perform()
        actions.key_down(Keys.DELETE).perform()
        
        for airport_code in departing_from:
            driver.find_elements(By.CLASS_NAME, "II2One")[3].send_keys(airport_code)
            sleep(0.3)
            actions.key_down(',').perform()
            sleep(0.3)
        
        # Click the checkmark button
        checkmark_button_selector = "button.VfPpkd-Bz112c-LgbsSe.yHy1rc.eT1oJ.mN1ivc.evEd9e[data-tooltip-id=\"tt-i26\"]"
        checkmark_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, checkmark_button_selector)))
        checkmark_button.click()
        
        # Enter arrival locations
        arrival_field.click()
        actions.key_down(Keys.COMMAND).send_keys('A').key_up(Keys. COMMAND).perform()
        actions.key_down(Keys.DELETE).perform()
        
        for airport_code in arriving_to:
            driver.find_elements(By.CLASS_NAME, "II2One")[3].send_keys(airport_code)
            
            sleep(0.3)
            actions.key_down(',').perform()
            sleep(0.3)
        
        # Click the checkmark button
        checkmark_button = driver.find_elements(By.CLASS_NAME, "VfPpkd-Bz112c-LgbsSe")[6]
        checkmark_button.click()
        
        # Click "Explore"
        explore_button = driver.find_element(By.CLASS_NAME, "xFFcie")
        explore_button.click()
        
        needs_expanding = False
        
        try:
            # Expand to show all flights
            driver.find_element(By.CSS_SELECTOR, "div.zISZ5c.QB2Jof").click()
            needs_expanding = True
        except:
            pass
        
        if needs_expanding:
            # Get number of flights before expanding
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            
            num_flights = len(soup.find_all("li", {"class": "pIav2d"}))
            
            # Wait until all flights are loaded
            while True:
                try:
                    hide_button = driver.find_element(By.CSS_SELECTOR, "button.VfPpkd-LgbsSe.VfPpkd-LgbsSe-OWXEXe-k8QpJ.VfPpkd-LgbsSe-OWXEXe-Bz112c-M1Soyc.VfPpkd-LgbsSe-OWXEXe-dgl2Hf.nCP5yc.AjY5Oe.LQeN7.nJawce.OTelKf.iIo4pd")
                    aria_label = hide_button.get_attribute("aria-label")
                except:
                    logging.info("Waiting for flights to load...")
                    continue
                
                html = driver.page_source
                soup = BeautifulSoup(html, "html.parser")
                
                num_expanded_flights = len(soup.find_all("li", {"class": "pIav2d"}))
            
                if aria_label.startswith("Hide") and num_expanded_flights > num_flights:
                    logging.info("Waiting for flights to load...")
                    break
        
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        
        flights = soup.find_all("li", {"class": "pIav2d"})
        
        logging.info("Found %d flights" % len(flights))
        
        departure_airports = soup.select("div.G2WY5c.sSHqwe.ogfYpf.tPgKwe")
        arrival_airports = soup.select("div.c8rWCd.sSHqwe.ogfYpf.tPgKwe")
        
        departure_times = soup.select("div.wtdjmc.YMlIz.ogfYpf.tPgKwe")
        arrival_times = soup.select("div.XWcVob.YMlIz.ogfYpf.tPgKwe")

        price_expr = re.compile("\$(\d+,?\d+)")
        prices = soup.select("div.BVAVmf.I11szd.Qr8X4d")
        
        for departing_airport, arriving_airport, departure_time, arrival_time, price in zip(departure_airports, arrival_airports, departure_times, arrival_times, prices):
            departure_time = datetime.strptime(departure_time.text, "%I:%M %p")
            departure_time = departure_time.replace(day = departure_date.day, month = departure_date.month, year = departure_date.year)
            
            arrival_time = arrival_time.text

            if '+' in arrival_time:
                arrival_time, added_days = arrival_time.split('+')
                added_days = int(added_days)
            else:
                added_days = 0
                
            arrival_time = datetime.strptime(arrival_time, "%I:%M\u202f%p")
            arrival_time = arrival_time.replace(day = departure_date.day + added_days, month = departure_date.month, year = departure_date.year)
    
            matches = re.findall(price_expr, price.text)
            price = int(matches[0].replace(',', '')) if matches else None
            
            yield (departing_airport.text, arriving_airport.text), (departure_time, arrival_time), price