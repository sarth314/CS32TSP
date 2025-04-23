import requests
import re

# Replace these with your Spotify Client ID and Client Secret
CLIENT_ID = '19cbf87401f048c9bc646d41a396f716'
CLIENT_SECRET = '2c2f72dd1eeb4544b9be91388a807e46'

# Get an access token (simple authentication for public data)
auth_url = 'https://accounts.spotify.com/api/token'
auth_data = {'grant_type': 'client_credentials'}
auth_response = requests.post(auth_url, auth=(CLIENT_ID, CLIENT_SECRET), data=auth_data)

if auth_response.status_code != 200:
    print(f"Failed to get access token: {auth_response.status_code}")
    exit(1)

access_token = auth_response.json()['access_token']
print("Got access token!")

# Ask for the playlist link
playlist_link = input("Enter your friend's Spotify playlist link (e.g., https://open.spotify.com/playlist/abc123): ")

# Extract the playlist ID from the link
match = re.search(r'open\.spotify\.com/playlist/([a-zA-Z0-9]+)', playlist_link)
if match:
    playlist_id = match.group(1)
else:
    print("Invalid link! Use a Spotify playlist URL like https://open.spotify.com/playlist/abc123")
    exit(1)

# Function to get all songs from the playlist
def get_playlist_songs(playlist_id, access_token):
    songs = []
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    while url:
        response = requests.get(url, headers={'Authorization': f'Bearer {access_token}'})
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            if response.status_code == 404:
                print("Playlist not found—check if it’s public!")
            break
        data = response.json()
        songs.extend(data['items'])
        url = data.get('next')  # Handle playlists with more than 100 songs
    return songs

# Fetch the songs
print("Fetching songs from the playlist...")
tracks = get_playlist_songs(playlist_id, access_token)
if not tracks:
    print("No songs found—playlist might be empty!")
else:
    print(f"Found {len(tracks)} songs in the playlist.")

# Your website’s songs (replace this with your actual list later)
my_songs = [
    {'name': 'Moonlight Sonata', 'artist': 'Beethoven'},
    {'name': 'Clair de Lune', 'artist': 'Debussy'},
    {'name': 'Passionfruit', 'artist': 'Drake'}
]
my_songs_set = set((song['name'].lower(), song['artist'].lower()) for song in my_songs)

# Compare and find matches
matches = []
for item in tracks:
    track = item.get('track')
    if track:
        song_name = track.get('name', '').lower()
        artist_name = track['artists'][0]['name'].lower() if track.get('artists') else ''
        if (song_name, artist_name) in my_songs_set:
            matches.append(f"{track['name']} by {track['artists'][0]['name']}")

# Show the results
print("\n=== Results ===")
print(f"Total songs in playlist: {len(tracks)}")
print(f"Matching songs: {len(matches)}")
if matches:
    print("Songs that match my website:")
    for song in matches:
        print(f"- {song}")
else:
    print("No matching songs found.")
