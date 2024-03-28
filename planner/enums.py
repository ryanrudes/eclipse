from enum import Enum, IntEnum

class TripType(IntEnum):
    DEFAULT = 0
    ROUNDTRIP = 0
    ONEWAY = 1
    MULTICITY = 2

class FlightClass(IntEnum):
    DEFAULT = 3
    ECONOMY = 3
    PREMIUM_ECONOMY = 4
    BUSINESS = 5
    FIRST = 6
    
class FlightDirection(Enum):
    DEPARTING = "departing"
    RETURNING = "returning"