#!/usr/bin/python -OO
# Spotify-notify
# By Erik Eloff (erik@eloff.se)
# Original code by noalwin (lambda512@gmail.com)
#                  SveinT (sveint@gmail.com)
# Based on pypanel code
print "Spotify-notify v0.1"
import os, time, sys, datetime, string
import pynotify
import pylast
from spotify_notify_xlib import spotify

API_KEY = '73f8547fa82ecbd0d0313f063c29571d' #spotify-notify's Last.fm API key
CURRENT_DIR = os.path.abspath(os.curdir).replace(';','')+"/"

oldsong = None
def update_handler():
    song = s.get_song()
    global oldsong
    #song['artist'] = "Midlake"
    #song['title'] = "Roscoe"
    if song != oldsong:
        oldsong = song

        if song is not None:
            if 'artist' in song:
                #Getting info from Last.FM

                artist = song['artist'] if 'artist' in song else ''
                title = song['title'] if 'title' in song else ''
                print "Fetching info for " +artist+" - "+title+" from Last.FM"
                try:
                    network = pylast.get_lastfm_network(api_key = API_KEY)
                    track = network.get_track(artist, title)
                    album = track.get_album()
                    url = album.get_cover_image(size = 1) #Equals medium size (best speed/quality compromise)
                    albumname = album.get_name()
                    import urllib2
                    coverfile = urllib2.urlopen(url)
                    output = open(CURRENT_DIR + 'spotifynotify_cover.jpg','wb')
                    output.write(coverfile.read())
                    output.close()
                    release_date = album.get_release_date()
                    if (release_date): #Lousy check, needs to be fixed in case last.fm changes date data
                        release_string = release_date.split(" ")[2]
                        release_string = release_string.split(",")[0]
                        release_string = " ("+release_string+")"
                    else:
                        release_string = ""
                    cover_image = CURRENT_DIR + 'spotifynotify_cover.jpg'
                except Exception as e:
                    print "Exception: ", e
                    print "Couldn't find song/cover in music database, using default image..."
                    albumname = release_string =  ""
                    cover_image = CURRENT_DIR + 'icon_spotify.png'
                #Showing notification
                n = pynotify.Notification (artist,
                    title +'\n '+
                    albumname +release_string,
                    cover_image)
                n.show ()


if __name__ == "__main__":
    if not pynotify.init ("icon-summary-body"):
        print "You need to have a working pynotify-library installed.\nIf you are using Ubuntu, try \"sudo apt-get install python-notify\""
        sys.exit (1)

    s = spotify(update_handler)
    s.loop()

