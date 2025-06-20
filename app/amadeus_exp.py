import requests

Base_URL = "test.api.amadeus.com"

def get_amadeus_access_token(client_id: str, client_secret: str) -> str:
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()  # Raises error if status code != 200
    access_token = response.json().get("access_token")
    return access_token

token = get_amadeus_access_token("G1EGTW8dwgReXa9mcVFGipP8M3BxJPDa", "nLm8sHURyXI5VPbx")

def get_flight_destinations(access_token: str, destination : str = "MAD", origin: str = "PAR"):
    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    params = {
        "originLocationCode": "PAR",
        "destinationLocationCode": "MAD",
        "departureDate": "2025-06-20",
        "adults": 1,
        "max": 1
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response.status_code, response.text)
        return None
    
# output = get_flight_destinations(token)
# print(output['data'])
def get_iata_codes(access_token:str, city: str):
    """Fetch IATA codes for a given city using the Amadeus API."""
    url = "https://test.api.amadeus.com/v1/reference-data/locations"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    params = {
        "keyword": city,
        "subType": "CITY",
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Error:", response.status_code, response.text)
        return []
    
output = get_iata_codes(token, "Jodhpur")
print(output['data'])