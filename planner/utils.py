from collections import defaultdict
from datetime import datetime
from pandas import read_csv

def chunkify(arr: list, chunk_size: int):
    for i in range(0, len(arr), chunk_size):
        yield arr[i:i + chunk_size]

def get_airport_to_eclipse_times(filepath: str) -> dict[str, dict[str, datetime]]:
    df = read_csv(filepath)
    
    result = {}

    for index, row in df.iterrows():
        airports = row["airports"].split()
        
        for airport in airports:
            if airport not in result:
                start = datetime.strptime(row["partial_begins"], "%Y-%m-%d %H:%M:%S")
                maximum = datetime.strptime(row["maximum"], "%Y-%m-%d %H:%M:%S")
                end = datetime.strptime(row["partial_ends"], "%Y-%m-%d %H:%M:%S")
                
                result[airport] = dict(start = start, maximum = maximum, end = end)

    return result

def load_airports(filepath: str) -> tuple[list[str], list[str], dict[str, list[str]], dict[str, list[str]]]:
    df = read_csv(filepath)

    sources = df[df["city"] == "Los Angeles"]["airports"].item().split()
    targets = []
    
    city2airports = {}
    airport2cities = defaultdict(list)

    for index, row in df.iterrows():
        city = row["city"]
        airports = row["airports"].split()
        
        # Associate each city with its airports
        city2airports[city] = airports
        
        # Associate each airport with its cities
        for airport in airports:
            airport2cities[airport].append(city)
        
        if city != "Los Angeles":
            for airport in airports:
                if airport not in targets:
                    targets.append(airport)

    return sources, targets, city2airports, airport2cities