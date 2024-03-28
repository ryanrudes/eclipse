from planner.enums import FlightDirection

from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class Flight:
    """A one-way flight"""
    departure_airport: str
    arrival_airport: str
    departure_time: datetime
    arrival_time: datetime
    leeway_time: timedelta
    direction: FlightDirection
    cost: int
    
    @property
    def travel_time(self) -> timedelta:
        return self.arrival_time - self.departure_time
    
    def __eq__(self, other):
        return self.departure_airport == other.departure_airport and \
               self.arrival_airport == other.arrival_airport and \
               self.departure_time == other.departure_time and \
               self.arrival_time == other.arrival_time and \
               self.direction == other.direction and \
               self.cost == other.cost
               
    def __hash__(self):
        return hash((self.departure_airport, self.arrival_airport,
                     self.departure_time, self.arrival_time, self.leeway_time,
                     self.direction, self.cost))
    
    def __str__(self):
        # Format: "on April 8 at 12:00 PM"
        formatted_departure_time = self.departure_time.strftime("%B %-d at %-I:%M %p")
        formatted_arrival_time = self.arrival_time.strftime("%B %-d at %-I:%M %p")
        
        return f"Take a {self.direction.value} flight from {self.departure_airport} on {formatted_departure_time} to {self.arrival_airport}, arriving on {formatted_arrival_time} for a cost of ${self.cost}."
    
@dataclass
class RoundTrip:
    """A round trip flight plan for viewing the eclipse"""
    departing_flight: FlightDirection
    returning_flight: FlightDirection

    @property
    def travel_time(self) -> timedelta:
        return self.departing_flight.travel_time + self.returning_flight.travel_time
    
    @property
    def setup_time(self) -> timedelta:
        return self.departing_flight.leeway_time
    
    @property
    def cleanup_time(self) -> timedelta:
        return self.returning_flight.leeway_time
    
    @property
    def cost(self) -> int:
        return self.departing_flight.cost + self.returning_flight.cost
    
    def __hash__(self) -> int:
        return hash((self.departing_flight, self.returning_flight))
    
    def __str__(self):
        return f"{self.departing_flight} {self.returning_flight} You will have {self.setup_time} to setup and {self.cleanup_time} to cleanup. The total travel time is {self.travel_time} and the total cost of the trip will be ${self.cost}."