from planner.utils import get_airport_to_eclipse_times, load_airports
from planner.flight import RoundTrip

from collections import defaultdict
from datetime import timedelta

import pickle

with open("output/departing.pkl", "rb") as file:
    departing_flights = pickle.load(file)

with open("output/returning.pkl", "rb") as file:
    returning_flights = pickle.load(file)

print("%d departing flights were found" % len(departing_flights))
print("%d returning flights were found" % len(returning_flights))

num_duplicate_departing_flights = len(departing_flights) - len(set(departing_flights))
num_duplicate_returning_flights = len(returning_flights) - len(set(returning_flights))

assert num_duplicate_departing_flights == 0, "Duplicate departing flights were found"
assert num_duplicate_returning_flights == 0, "Duplicate returning flights were found"

# Load origin and eclipse viewing airports
origin_airports, viewing_airports, city2airports, airport2cities = load_airports("data/processed.csv")

# Get eclipse event times at each airport
localized_events = get_airport_to_eclipse_times("data/processed.csv")

# Define the minimum and maximum allowed setup and cleanup times
min_setup_time = timedelta(hours = 2)
max_setup_time = timedelta(hours = 8)
min_cleanup_time = timedelta(hours = 2)
max_cleanup_time = timedelta(hours = 8)

# Filter out flights which do not have enough time to setup and cleanup
departing_flights = [flight for flight in departing_flights if min_setup_time <= flight.leeway_time <= max_setup_time]
returning_flights = [flight for flight in returning_flights if min_cleanup_time <= flight.leeway_time <= max_cleanup_time]

print("%d departing flights remain after filtering for leeway time" % len(departing_flights))
print("%d returning flights remain after filtering for leeway time" % len(returning_flights))

# Organize returning flights by the airport they are departing from
returning_departures = defaultdict(list)

for flight in returning_flights:
    returning_departures[flight.departure_airport].append(flight)

# Compute all possible round trips
trips = set()

for departing_flight in departing_flights:
    # We are arriving at some airport to view the eclipse. Let's get all of the cities
    # which share this airport.
    for city in airport2cities[departing_flight.arrival_airport]:
        # Then, get all of the airports used by all of these cities. This is 
        # effectively the list of airports we can use for returning home.
        for airport in city2airports[city]:
            for returning_flight in returning_departures[airport]:
                trip = RoundTrip(departing_flight, returning_flight)
                trips.add(trip)

# Sort trips by total cost.
trips = sorted(trips, key = lambda trip: (trip.cost, trip.travel_time), reverse = True)
print("%d possible round trips were found" % len(trips))

# All trips will work a follows:
#  1. You leave from a home airport
#  2. You arrive at an airport to view the eclipse with sufficient time to
#     set up and clean up afterwords
#  3. You view the eclipse
#  4. You depart at some airport in the eclipse viewing city (not necessarily
#     the same airport you arrived at)
#  5. You arrive back at some home airport (also not necessarily the same
#     airport you left from originally)

for trip in trips:
    print(trip, end = '\n\n')