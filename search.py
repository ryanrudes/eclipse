from planner.flight import FlightDirection, Flight
from planner.api import API, TripType, FlightClass
from planner.utils import get_airport_to_eclipse_times, load_airports

from datetime import datetime, timedelta
from typing import Generator

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

def fetch_departing_flights(
    localized_events: dict[str, dict[str, datetime]],
    *,
    departing_airports: list[str],
    returning_airports: list[str],
    api: API,
) -> Generator[Flight, None, None]:
    # Get departing flights
    results = api.search(
        departing_from = departing_airports,
        arriving_to = returning_airports,
        departure_date = [datetime(2024, 4, 7), datetime(2024, 4, 8)],
        trip = TripType.ONEWAY,
    )

    for (departure_code, arrival_code), (takeoff_time, landing_time), cost in results:
        # If the cost is not available, skip this flight
        if cost is None:
            continue
        
        # Determine when the eclipse begins at the airport we are flying to
        eclipse_begins = localized_events[arrival_code]["start"]
        
        # If the eclipse begins before the airplane lands, skip this flight
        if eclipse_begins < landing_time:
            continue
        
        # Calculate the time available to setup the equipment
        setup_time = eclipse_begins - landing_time
        
        # This is a potential flight option, so let's store it
        flight = Flight(departure_code, arrival_code,
                        takeoff_time, landing_time,
                        leeway_time = setup_time,
                        direction = FlightDirection.DEPARTING,
                        cost = cost)
        
        yield flight

def fetch_returning_flights(
    localized_events: dict[str, dict[str, datetime]],
    *,
    departing_airports: list[str],
    returning_airports: list[str],
    api: API,
) -> Generator[Flight, None, None]:
    # Get returning flights
    results = api.search(
        departing_from = departing_airports,
        arriving_to = returning_airports,
        departure_date = [datetime(2024, 4, 8)],
        trip = TripType.ONEWAY,
    )

    for (departure_code, arrival_code), (takeoff_time, landing_time), cost in results:
        # If the cost is not available, skip this flight
        if cost is None:
            continue
        
        # Determine when the eclipse ends at the airport we are flying home from
        eclipse_ends = localized_events[departure_code]["end"]
        
        # If the eclipse begins before the airplane lands, skip this flight
        if takeoff_time < eclipse_ends:
            continue
        
        # Calculate the time available to cleanup the equipment and get on the plane
        cleanup_time = takeoff_time - eclipse_ends
        
        # This is a potential flight option, so let's store it
        flight = Flight(departure_code, arrival_code,
                        takeoff_time, landing_time,
                        leeway_time = cleanup_time,
                        direction = FlightDirection.RETURNING,
                        cost = cost)
        
        yield flight

def search(debug: bool = False) -> tuple[list[Flight], list[Flight]]:
    # Initialize API
    api = API(debug = debug)
    
    # Load origin and eclipse viewing airports
    origin_airports, viewing_airports, city2airports, airport2cities = load_airports("data/processed.csv")
    
    # Get eclipse event times at each airport
    localized_events = get_airport_to_eclipse_times("data/processed.csv")

    # Create progress bar
    progress = Progress(
        SpinnerColumn(),
        *Progress.get_default_columns(),
        TextColumn("[blue]{task.completed} flights"),
        TimeElapsedColumn(),
    )
        
    with progress:
        # Create progress bar task for departing flights
        departing_task = progress.add_task("[green]Searching for departing flights...", total = None)
    
        # Query the API for departing flights
        results = fetch_departing_flights(localized_events,
                                          departing_airports = origin_airports,
                                          returning_airports = viewing_airports,
                                          api = api)
        
        # Fetch departing flights
        departing_flights = set()
        
        for flight in results:
            if flight in departing_flights:
                continue

            departing_flights.add(flight)
            
            # Update progress bar
            progress.update(departing_task, advance = 1)
        
        # End the departing flights task
        progress.stop_task(departing_task)
        
        # Determine airports we can use to return home after viewing the eclipse
        #
        # NOTE: If a city has multiple airports, we can view the eclipse at one and depart from another.
        #       For example, Dallas has two airports: DFW and DAL. We can view the eclipse at DFW and
        #       depart for home from DAL.
        returning_airports = set()
        
        for flight in departing_flights:
            # We are arriving at some airport to view the eclipse. Let's get all of the cities
            # which share this airport.
            for city in airport2cities[flight.arrival_airport]:
                # Then, get all of the airports used by all of these cities. This is 
                # effectively the list of airports we can use for returning home.
                for airport in city2airports[city]:
                    returning_airports.add(airport)
                    
        returning_airports = list(returning_airports)
        
        # Create progress bar task for returning flights
        returning_task = progress.add_task("[red]Searching for returning flights...", total = None)
        
        # Query the API for returning flights
        results = fetch_returning_flights(localized_events,
                                          departing_airports = returning_airports,
                                          returning_airports = origin_airports,
                                          api = api)
        
        # Fetch returning flights
        returning_flights = set()
        
        for flight in results:
            if flight in returning_flights:
                continue
            
            returning_flights.add(flight)
            
            # Update progress bar
            progress.update(returning_task, advance = 1)
        
        # End the returning flights task
        progress.stop_task(returning_task)
        
    # Sort flights by cost
    get_cost = lambda flight: flight.cost
    
    departing_flights = sorted(departing_flights, key = get_cost)
    returning_flights = sorted(returning_flights, key = get_cost)
    
    return departing_flights, returning_flights

if __name__ == "__main__":
    import pickle
    
    departing_flights, returning_flights = search()
    
    with open("output/departing.pkl", "wb") as file:
        pickle.dump(departing_flights, file)
    
    with open("output/returning.pkl", "wb") as file:
        pickle.dump(returning_flights, file)