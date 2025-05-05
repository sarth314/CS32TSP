import requests
import re
import os
import time
from datetime import datetime

# Spotify API credentials - Replace these with your own from Spotify Developer Dashboard
CLIENT_ID = '19cbf87401f048c9bc646d41a396f716'
CLIENT_SECRET = '2c2f72dd1eeb4544b9be91388a807e46'

# Constants
SONG_LIST_FILE = 'my_songs.txt'
RESULTS_FILE = 'comparison_results.txt'
HISTORY_FILE = 'comparison_history.txt'

def get_access_token():
    """Fetch Spotify API access token using client credentials."""
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_data = {'grant_type': 'client_credentials'}
    response = requests.post(auth_url, auth=(CLIENT_ID, CLIENT_SECRET), data=auth_data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print(f"Failed to get access token: {response.status_code}")
        exit(1)

def get_playlist_tracks(playlist_id, access_token):
    """Retrieve all tracks from a Spotify playlist with progress feedback."""
    tracks = []
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    print("Fetching tracks", end="")
    while url:
        response = requests.get(url, headers={'Authorization': f'Bearer {access_token}'})
        if response.status_code != 200:
            print(f"\nError fetching tracks: {response.status_code}")
            return []
        data = response.json()
        tracks.extend(data['items'])
        url = data.get('next')
        print(".", end="", flush=True)
        time.sleep(0.1)  # Simulate progress
    print(f"\nFetched {len(tracks)} tracks successfully.")
    return tracks

def read_my_songs(filename):
    """Read songs from a file into a list of dictionaries."""
    songs = []
    try:
        with open(filename, 'r') as file:
            for line in file:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    songs.append({'name': parts[0].strip(), 'artist': parts[1].strip()})
                else:
                    print(f"Invalid line in {filename}: {line.strip()}")
    except FileNotFoundError:
        print(f"{filename} not found. Creating an empty one.")
        open(filename, 'w').close()
    return songs

def write_my_songs(filename, songs):
    """Write the song list back to the file."""
    with open(filename, 'w') as file:
        for song in songs:
            file.write(f"{song['name']},{song['artist']}\n")

def compare_songs(playlist_tracks, my_songs):
    """Compare playlist tracks with user's song list and track mismatches."""
    matches = []
    mismatches = []
    for item in playlist_tracks:
        track = item.get('track')
        if track and track.get('artists'):
            song_name = track.get('name', '').lower()
            artist_name = track['artists'][0]['name'].lower()
            found = False
            for song in my_songs:
                if song_name == song['name'].lower() and artist_name == song['artist'].lower():
                    matches.append(f"{track['name']} by {track['artists'][0]['name']}")
                    found = True
                    break
            if not found:
                mismatches.append(f"{track['name']} by {track['artists'][0]['name']}")
    return matches, mismatches

def display_matches(matches, mismatches, playlist_tracks, my_songs, playlist_id):
    """Display results with stats and save options."""
    total_matches = len(matches)
    total_mismatches = len(mismatches)
    total_playlist_songs = len(playlist_tracks)
    total_my_songs = len(my_songs)
    match_percentage = (total_matches / total_playlist_songs * 100) if total_playlist_songs > 0 else 0

    print(f"\n=== Comparison Results for Playlist ID: {playlist_id} ===")
    print(f"Playlist: {total_playlist_songs} songs | Your List: {total_my_songs} songs")
    print(f"Matches: {total_matches} ({match_percentage:.2f}%) | Non-Matches: {total_mismatches}")
    if matches:
        print("\nMatching Songs:")
        for match in matches:
            print(f"- {match}")
    if mismatches:
        print("\nSongs in Playlist Not in Your List:")
        for mismatch in mismatches:
            print(f"- {mismatch}")

    # Save to file option
    save = input("\nSave results to file? (yes/no): ").strip().lower()
    if save == 'yes':
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(RESULTS_FILE, 'w') as file:
            file.write(f"Comparison Results ({timestamp})\n")
            file.write(f"Playlist ID: {playlist_id}\n")
            file.write(f"Playlist Songs: {total_playlist_songs}\n")
            file.write(f"Your Songs: {total_my_songs}\n")
            file.write(f"Matches: {total_matches} ({match_percentage:.2f}%)\n")
            file.write("Matching Songs:\n")
            for match in matches:
                file.write(f"{match}\n")
            file.write("\nNon-Matching Songs:\n")
            for mismatch in mismatches:
                file.write(f"{mismatch}\n")
        print(f"Results saved to '{RESULTS_FILE}'.")

    # Save to history
    with open(HISTORY_FILE, 'a') as file:
        file.write(f"{timestamp},Playlist {playlist_id},{total_matches},{total_mismatches}\n")

def manage_song_list(filename):
    """Enhanced song list management with sorting and bulk add."""
    songs = read_my_songs(filename)
    while True:
        print("\n=== Manage Song List ===")
        print("1. View list")
        print("2. Add song")
        print("3. Bulk add songs")
        print("4. Remove song")
        print("5. Edit song")
        print("6. Search songs")
        print("7. Sort list")
        print("8. Back")
        choice = input("Choose an option: ").strip()

        if choice == '1':
            if songs:
                for i, song in enumerate(songs, 1):
                    print(f"{i}. {song['name']} by {song['artist']}")
            else:
                print("List is empty.")
        elif choice == '2':
            name = input("Song name: ").strip()
            artist = input("Artist name: ").strip()
            if name and artist:
                songs.append({'name': name, 'artist': artist})
                write_my_songs(filename, songs)
                print("Song added.")
            else:
                print("Name and artist required.")
        elif choice == '3':
            print("Enter songs (format: song_name,artist_name; one per line). Type 'done' to finish:")
            while True:
                line = input("> ").strip()
                if line.lower() == 'done':
                    break
                parts = line.split(',')
                if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                    songs.append({'name': parts[0].strip(), 'artist': parts[1].strip()})
                else:
                    print("Invalid format. Use: song_name,artist_name")
            write_my_songs(filename, songs)
            print("Bulk add completed.")
        elif choice == '4':
            if songs:
                for i, song in enumerate(songs, 1):
                    print(f"{i}. {song['name']} by {song['artist']}")
                try:
                    index = int(input("Number to remove: ")) - 1
                    if 0 <= index < len(songs):
                        confirm = input(f"Remove {songs[index]['name']} by {songs[index]['artist']}? (yes/no): ").strip().lower()
                        if confirm == 'yes':
                            removed = songs.pop(index)
                            write_my_songs(filename, songs)
                            print(f"Removed {removed['name']} by {removed['artist']}")
                        else:
                            print("Canceled.")
                    else:
                        print("Invalid number.")
                except ValueError:
                    print("Enter a valid number.")
            else:
                print("No songs to remove.")
        elif choice == '5':
            if songs:
                for i, song in enumerate(songs, 1):
                    print(f"{i}. {song['name']} by {song['artist']}")
                try:
                    index = int(input("Number to edit: ")) - 1
                    if 0 <= index < len(songs):
                        new_name = input(f"New name (current: {songs[index]['name']}): ").strip()
                        new_artist = input(f"New artist (current: {songs[index]['artist']}): ").strip()
                        if new_name:
                            songs[index]['name'] = new_name
                        if new_artist:
                            songs[index]['artist'] = new_artist
                        write_my_songs(filename, songs)
                        print("Song updated.")
                    else:
                        print("Invalid number.")
                except ValueError:
                    print("Enter a valid number.")
            else:
                print("No songs to edit.")
        elif choice == '6':
            if songs:
                query = input("Search by name or artist: ").strip().lower()
                found = False
                for i, song in enumerate(songs, 1):
                    if query in song['name'].lower() or query in song['artist'].lower():
                        print(f"{i}. {song['name']} by {song['artist']}")
                        found = True
                if not found:
                    print("No matches.")
            else:
                print("No songs to search.")
        elif choice == '7':
            if songs:
                sort_by = input("Sort by (name/artist): ").strip().lower()
                if sort_by in ['name', 'artist']:
                    songs.sort(key=lambda x: x[sort_by].lower())
                    write_my_songs(filename, songs)
                    print(f"Sorted by {sort_by}.")
                else:
                    print("Invalid sort option.")
            else:
                print("No songs to sort.")
        elif choice == '8':
            break
        else:
            print("Invalid choice.")

def view_history():
    """Display comparison history from file."""
    try:
        with open(HISTORY_FILE, 'r') as file:
            lines = file.readlines()
            if lines:
                print("\n=== Comparison History ===")
                for line in lines:
                    timestamp, playlist, matches, mismatches = line.strip().split(',')
                    print(f"{timestamp}: {playlist} - {matches} matches, {mismatches} non-matches")
            else:
                print("\nNo history available.")
    except FileNotFoundError:
        print("\nNo history available.")

def generate_recommendations(matches, mismatches):
    """Simple recommendation based on matches."""
    if matches:
        print("\n=== Recommendations ===")
        print("Based on your matches, you might enjoy exploring more songs by these artists!")
        artists = set()
        for match in matches:
            artist = match.split(' by ')[1]
            artists.add(artist)
        for i, artist in enumerate(artists, 1):
            print(f"{i}. {artist}")
    else:
        print("\nNo recommendations due to no matches.")

def main():
    """Main function with enhanced menu and features."""
    print("🎵 Welcome to the Spotify Playlist Comparator! 🎵")
    print("Compare playlists, manage songs, view history, and more!")
    access_token = get_access_token()

    while True:
        print("\n=== Main Menu ===")
        print("1. Compare playlist")
        print("2. Manage song list")
        print("3. View history")
        print("4. Help")
        print("5. Exit")
        choice = input("Option: ").strip()

        if choice == '1':
            playlist_link = input("Spotify playlist link: ").strip()
            match = re.search(r'open\.spotify\.com/playlist/([a-zA-Z0-9]+)', playlist_link)
            if not match:
                print("Invalid link.")
                continue
            playlist_id = match.group(1)
            playlist_tracks = get_playlist_tracks(playlist_id, access_token)
            if not playlist_tracks:
                continue
            my_songs = read_my_songs(SONG_LIST_FILE)
            if not my_songs:
                print("Add songs to 'my_songs.txt' first.")
                continue
            matches, mismatches = compare_songs(playlist_tracks, my_songs)
            display_matches(matches, mismatches, playlist_tracks, my_songs, playlist_id)
            generate_recommendations(matches, mismatches)
        elif choice == '2':
            manage_song_list(SONG_LIST_FILE)
        elif choice == '3':
            view_history()
        elif choice == '4':
            print("\n=== Help ===")
            print("1. Compare Playlist: Match a Spotify playlist with your song list.")
            print("2. Manage Song List: Add, edit, remove, search, or sort songs.")
            print("3. View History: See past comparisons.")
            print("4. Help: This menu.")
            print("5. Exit: Close the program.")
        elif choice == '5':
            print("Thanks for using Spotify Playlist Comparator! Goodbye!")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()

# Execution Steps:
#
# 2. Install Requests Library:
#    - Open terminal and run: pip install requests
#
# 3. Prepare Song List:
#    - Create 'my_songs.txt' in the same directory as this script.
#    - Format: song_name,artist_name (one per line), e.g.:
#      God's Plan,Drake
#      HUMBLE.,Kendrick Lamar
#      Love Story,Taylor Swift
#
# 4. Save and Run:
#    - Save this as 'spotify_comparator.py'.
#    - In terminal, navigate to script directory and run: python spotify_comparator.py
#
# 5. Usage:
#    - Compare Playlist: Enter a Spotify link (e.g., https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M)
#    - Manage Song List: Edit your song list with various options.
#    - View History: See past comparison stats.
#    - Help: Instructions.
#    - Exit: Close program.
#
# Guidelines:
# - Requires internet for Spotify API.
# - Results save to 'comparison_results.txt'; history to 'comparison_history.txt'.
# - Uses basic programming concepts suitable for CS32.
# - Replace CLIENT_ID and CLIENT_SECRET with your own for full functionality (get from https://developer.spotify.com/dashboard/).
