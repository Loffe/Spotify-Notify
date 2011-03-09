#!/usr/bin/env python

# Spotify-Notify
#
# By Victor Koronen <koronen@kth.se>
# Fork from Erik Eloff <erik@eloff.se>
# Original code by noalwin <lambda512@gmail.com>
#              and SveinT <sveint@gmail.com>
#

import os, time, sys, datetime, string
import pynotify
import pylast
import tempfile

API_KEY = '73f8547fa82ecbd0d0313f063c29571d' #spotify-notify's Last.fm API key
CURRENT_DIR = os.path.abspath(os.curdir).replace(';','')+"/"
TMP_DIR = tempfile.gettempdir() + "/"

class SpotifyNotify(object):
    oldsong = None
    old_id = None

    def __init__(self):
        try:
            import  spotify_notify_dbus
            self.backend = spotify_notify_dbus.spotify(self)
        except:
            import  spotify_notify_xlib
            self.backend = spotify_notify_xlib.spotify(self)
        self.backend.loop()

    """
    Clean up tmp cover image (if any)
    """
    def __del__(self):
        if self.cover_image and os.path.exists(self.cover_image):
            os.unlink(self.cover_image)

    def fetchAlbumCover(self, artist, title, album = None):
        try:
            network = pylast.get_lastfm_network(api_key = API_KEY)

            if (album is None):
                track = network.get_track(artist, title)
                album = track.get_album()
            else:
                album = network.get_album(artist, album)

            url = album.get_cover_image(size = 1) #Equals medium size (best speed/quality compromise)
            self.albumname = album.get_name()
            import urllib2
            coverfile = urllib2.urlopen(url)

            # Remove old tmp if any
            if self.cover_image and os.path.exists(self.cover_image):
                os.unlink(self.cover_image)

            output = tempfile.NamedTemporaryFile(prefix="spotifynotify_cover", suffix=".jpg",delete=False)
            output.write(coverfile.read())
            output.close()
            release_date = album.get_release_date()
            if (release_date): #Lousy check, needs to be fixed in case last.fm changes date data
                release_string = release_date.split(" ")[2]
                release_string = release_string.split(",")[0]
                release_string = " ("+release_string+")"
            else:
                release_string = ""
            self.release_string = release_string
            #self.cover_image = TMP_DIR + 'spotifynotify_cover.jpg'
            self.cover_image = output.name
        except Exception as e:
            print "Exception: ", e
            print "Couldn't find song/cover in music database, using default image..."
            self.albumname = self.release_string =  ""
            self.cover_image = None

    def on_track_change(self, song):
        if song != self.oldsong and song is not None:
            self.oldsong = song
            if 'artist' in song:
                #Getting info from Last.FM

                artist = song['artist'] if 'artist' in song else ''
                title = song['title'] if 'title' in song else ''
                album = song['album'] if 'album' in song else None
                print "Fetching info for " +artist+" - "+title+" from Last.FM"
                coverData = self.fetchAlbumCover(artist, title, album)

                if self.cover_image:
                    cover_image = self.cover_image
                else:
                    cover_image = CURRENT_DIR + 'icon_spotify.png'
                #Showing notification
                n = pynotify.Notification (artist,
                    title +'\n '+
                    self.albumname + self.release_string,
                    cover_image)

                # Save notification id to replace popups
                if (self.old_id is not None):
                    n.props.id = self.old_id

                n.show()
                self.old_id = n.props.id

if __name__ == "__main__":
    if not pynotify.init("icon-summary-body"):
        print "You need to have a working pynotify-library installed.\nIf you are using Ubuntu, try \"sudo apt-get install python-notify\""
        sys.exit(1)

    SpotifyNotify()

