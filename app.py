from flask import Flask, request, redirect
import webbrowser
import requests
from urllib.parse import urlencode
import base64
import time
import threading

# ATTENTION
# in clientvals.txt add in the following order: 
# client id
# client secret
# playlist id
# always 3 rows in the file, even if no playlist id yet

app = Flask(__name__)
f = open("clientvals.txt", "r")
client_id = f.readline()[:-1]
client_secret = f.readline()[:-1]
playlist_url = f.readline()
f.close()

scopes = 'playlist-modify-public user-read-email user-top-read'

@app.route("/")
def index():
    return "<p>Hello, World!</p>"

@app.route("/callback")
def callback():
    code = request.args.get('code')
    encoded_credentials = base64.b64encode(client_id.encode() + b':' + client_secret.encode()).decode("utf-8")
    token_headers = {
        "Authorization": "Basic " + encoded_credentials,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://localhost:7777/callback"
    }

    r = requests.post("https://accounts.spotify.com/api/token", data=token_data, headers=token_headers)
    print(r.json())
    token = r.json()["access_token"]

    user_headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
    }

    # get / create playlist if needed.
    active_playlist = playlist_url
    if not active_playlist: 
        print("creating playlist.")
        playlist_body = {
            "name": "test playlist",
            "description": "My favorite songs over the past month",
            "public":True
        }
        r = requests.post("https://api.spotify.com/v1/me/playlists", json=playlist_body, headers=user_headers)
        active_playlist = r.json()['id']
        print(f'Using newly created playlist: {active_playlist}')
        print(f'\n###########################################\n\tPlease put this url at the bottom of \"clientvals.txt\": {active_playlist}\n###########################################')
    else: 
        print(f'using found playlist url: {active_playlist}')

    # get songs
    r = requests.get("https://api.spotify.com/v1/me/top/tracks?time_range=short_term&limit=30", headers=user_headers)

    song_list_json = r.json()
    song_uris = []
    for song in song_list_json['items']:
        song_uris.append(song['uri'])

    song_put_json = {'uris': song_uris}
    r = requests.put(f'https://api.spotify.com/v1/playlists/{active_playlist}/tracks', headers=user_headers, json=song_put_json)
    print(r)

    return redirect(f'https://open.spotify.com/playlist/{active_playlist}')

def open_app():
    time.sleep(3)
    auth_headers = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": "http://localhost:7777/callback",
        "scope": scopes
    }

    webbrowser.open("https://accounts.spotify.com/authorize?" + urlencode(auth_headers))
    

if __name__ == "__main__":
    app_thread = threading.Thread(target=open_app, args=())
    app_thread.start()
    app.run(debug=False, port=7777)
    


