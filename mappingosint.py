import googlemaps
import tweepy
import flickrapi
import requests
import json
from bs4 import BeautifulSoup
import folium
import shodan


GMAPS_API_KEY = 'CODE'
TWITTER_CONSUMER_KEY = 'CODE'
TWITTER_CONSUMER_SECRET = 'CODE'
TWITTER_ACCESS_TOKEN = 'CODE'
TWITTER_ACCESS_TOKEN_SECRET = 'CODE'
FLICKR_API_KEY = 'CODE'
FLICKR_SECRET = 'CODE'


gmaps = googlemaps.Client(key=GMAPS_API_KEY)

auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
twitter_api = tweepy.API(auth)

flickr = flickrapi.FlickrAPI(FLICKR_API_KEY, FLICKR_SECRET, format='parsed-json')

shodan_api_key = 'CODE'

def create_map_with_markers(location, tweets, flickr_photos, insecam_cameras, shodan_devices):
    map_osint = folium.Map(location=[location['lat'], location['lng']], zoom_start=14)

    # Adicione marcadores para os tweets
    for tweet in tweets:
        folium.Marker(
            location=[tweet['coordinates']['coordinates'][1], tweet['coordinates']['coordinates'][0]],
            popup=f'<a href="{tweet["url"]}" target="_blank">Tweet: {tweet["text"]}</a>',
            icon=folium.Icon(color='blue')
        ).add_to(map_osint)

    # Adicione marcadores para as fotos do Flickr
    for photo in flickr_photos:
        folium.Marker(
            location=[photo['latitude'], photo['longitude']],
            popup=f'<a href="{photo["url"]}" target="_blank">Flickr: {photo["title"]}</a>',
            icon=folium.Icon(color='red', icon='camera', prefix='fa')
        ).add_to(map_osint)

    # Adicione marcadores para as câmeras do Insecam
    for camera in insecam_cameras:
        folium.Marker(
            location=[camera['latitude'], camera['longitude']],
            popup=f'<a href="{camera["url"]}" target="_blank">Insecam: {camera["title"]}</a>',
            icon=folium.Icon(color='green', icon='video-camera', prefix='fa')
        ).add_to(map_osint)

    for device in shodan_devices:
        folium.Marker(
            location=[device['latitude'], device['longitude']],
            popup=f"<strong>Dispositivo Shodan:</strong> {device['ip']}<br><strong>Hostnames:</strong> {', '.join(device['hostnames'])}<br><pre>{device['data']}</pre>",
            icon=folium.Icon(color='black')
        ).add_to(map_osint)

    # Salve o mapa como um arquivo HTML
    map_osint.save('osint_map.html')

def get_shodan_devices_near_location(location, shodan_api_key, query='', radius=2):
#def get_shodan_devices_near_location(location, shodan_api_key, query='', limit=100):
    api = shodan.Shodan(shodan_api_key)
    lat, lng = location['lat'], location['lng']
    devices = []

    try:
        results = api.search(f"{query} geo:{lat},{lng},{radius}")
        #results = api.search(f"{query}, geo:{lat}, {lng}, {limit}")
        for result in results['matches']:
            devices.append({
                'ip': result['ip_str'],
                'latitude': result['location']['latitude'],
                'longitude': result['location']['longitude'],
                'hostnames': result.get('hostnames', []),
                'data': result['data']
            })
    except shodan.APIError as e:
        print(f"Erro ao buscar dispositivos Shodan: {e}")

    return devices

    
def get_location_coordinates(address):
    geocode_result = gmaps.geocode(address)
    if geocode_result:
        return geocode_result[0]['geometry']['location']
    else:
        return None

def get_tweets_near_location(location, count=100):
    geocode = f"{location['lat']},{location['lng']},5km"
    tweets = tweepy.Cursor(twitter_api.search_tweets, q="", geocode=geocode, tweet_mode="extended").items(count)
    return [{'text': tweet.full_text, 'coordinates': tweet.coordinates, 'url': f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"} for tweet in tweets if tweet.coordinates is not None]

def get_flickr_photos_near_location(location, per_page=20):
    payload = {
        'api_key': FLICKR_API_KEY,
        'method': 'flickr.photos.search',
        'format': 'json',
        'nojsoncallback': 1,
        'lat': location['lat'],
        'lon': location['lng'],
        'radius': 5,  # 5 km
        'per_page': per_page,
        'extras': 'geo'
    }
    response = requests.get('https://www.flickr.com/services/rest/', params=payload)
    data = response.json()
    if data['stat'] == 'ok':
        return [{'title': photo['title'], 'latitude': float(photo['latitude']), 'longitude': float(photo['longitude']), 'url': f'https://www.flickr.com/photos/{photo["owner"]}/{photo["id"]}'} for photo in data['photos']['photo']]
    else:
        return []

def get_insecam_near_location(location):
    insecam_url = 'http://www.insecam.org/en/bycountry/USA'  
    response = requests.get(insecam_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        camera_elements = soup.find_all('div', class_='thumbnail-box')
        camera_urls = [camera.find('a')['href'] for camera in camera_elements]
        return [{'title': camera['title'], 'latitude': float(camera['latitude']), 'longitude': float(camera['longitude']), 'url': camera['url']} for camera in cameras]
    else:
        return []


if __name__ == '__main__':
    address = input('Digite o endereço: ')
    location = get_location_coordinates(address)
    if location:
        print('Localização:', location)
        tweets = get_tweets_near_location(location)
        print('\nTweets:')
        for tweet in tweets:
            print(f"- {tweet['text']}")

        flickr_photos = get_flickr_photos_near_location(location)
        print('\nFotos do Flickr:')
        for photo in flickr_photos:
            print(f'- {photo}')

        insecam_data = get_insecam_near_location(location)  # Adicionado para obter os dados das câmeras Insecam

        
        shodan_devices = get_shodan_devices_near_location(location, shodan_api_key)

        create_map_with_markers(location, tweets, flickr_photos, insecam_data, shodan_devices)

        print("\nO mapa foi criado como 'osint_map.html'. Abra este arquivo no navegador para visualizar o mapa.")
    else:
        print('Não foi possível encontrar a localização. Tente novamente com um endereço diferente.')
    
    # create_map_with_markers(location, tweets, flickr_photos, insecam_data, shodan_devices)
