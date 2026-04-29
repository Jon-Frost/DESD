import requests
import math


def get_coordinates(postcode):
    postcode = postcode.replace(' ', '').upper()
    
    try:
        response = requests.get(
            f'https://api.postcodes.io/postcodes/{postcode}',
            timeout=5
        )
        data = response.json()
        
        if response.status_code == 200 and data.get('result'):
            return {
                'lat': data['result']['latitude'],
                'lng': data['result']['longitude']
            }
    except Exception:
        return None
    
    return None


def haversine_distance(coord1, coord2):
    R = 3958.8

    lat1 = math.radians(coord1['lat'])
    lat2 = math.radians(coord2['lat'])
    dlat = math.radians(coord2['lat'] - coord1['lat'])
    dlng = math.radians(coord2['lng'] - coord1['lng'])

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c, 1)


def calculate_food_miles(customer_postcode, producer_postcode):
    if not customer_postcode or not producer_postcode:
        return None

    customer_coords = get_coordinates(customer_postcode)
    producer_coords = get_coordinates(producer_postcode)

    if not customer_coords or not producer_coords:
        return None

    return haversine_distance(customer_coords, producer_coords)