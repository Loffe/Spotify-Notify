#!/usr/bin/env python
#
# Spotify-Notify - Notifications and media keys support for Spotify
# Copyright (C) 2011 Victor Koronen and contributors
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

import os, time, sys, datetime, string, re
import pynotify
import tempfile

sys.path.append("./lib")
import pylast

SPOTIFY_OPEN_URL = "http://open.spotify.com/track/"
LASTFM_API_KEY = '73f8547fa82ecbd0d0313f063c29571d' #spotify-notify's Last.fm API key
CURRENT_DIR = os.path.abspath(os.curdir).replace(';','')+"/"
TMP_DIR = tempfile.gettempdir() + "/"

class SpotifyNotify(object):
    oldsong = None
    old_id = None

    """ constructor """
    def __init__(self):
        # choose backend
        try:
            import spotify_notify_dbus
            self.backend = spotify_notify_dbus.SpotifyDBus(self)
        except:
            import spotify_notify_xlib
            self.backend = spotify_notify_xlib.SpotifyXLib(self)

    """ runs the main (backend) loop """
    def run(self):
        self.backend.loop()

    """
    Clean up tmp cover image (if any)
    """
    def __del__(self):
        if self.cover_image and os.path.exists(self.cover_image):
            os.unlink(self.cover_image)

    def fetchLastFmAlbumCover(self, artist, title, album = None):
        try:
            print "Fetching info for " +artist+" - "+title+" from Last.FM"
            network = pylast.get_lastfm_network(api_key = LASTFM_API_KEY)

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

    def fetchCoverImageSpotify(self, trackid):
        try:
            import urllib2
            url = SPOTIFY_OPEN_URL + trackid
            tracksite = urllib2.urlopen(url).read()
            matchobject = re.search('/image/(.*)" alt', tracksite)
            imageurl = "http://open.spotify.com/image/" + matchobject.group(1)
            if not (imageurl):
                print "No cover available"
                raise()
            coverfile = urllib2.urlopen(imageurl)
            (fd, self.tmpfilename) = tempfile.mkstemp()
            self.tmpfile = os.fdopen(fd, 'wb')
            data = coverfile.read()
            self.tmpfile.write(data)
            self.tmpfile.close()
            self.cover_image = self.tmpfilename
            return 1
        except Exception, e:
            print "Couldn't fetch cover image"
            print e
            self.cover_image = None
            return 0 

    def on_track_change(self, song):
        if song != self.oldsong and song is not None:
            self.oldsong = song
            if 'artist' in song:
                artist = song['artist'] if 'artist' in song else ''
                title = song['title'] if 'title' in song else ''
                album = song['album'] if 'album' in song else None
                track_id = song['track_id'] if 'track_id' in song else None
                
                #TODO: enable choise
                #coverData = self.fetchLastFmAlbumCover(artist, title, album)
                self.fetchCoverImageSpotify(track_id)

                if self.cover_image:
                    cover_image = self.cover_image
                else:
                    cover_image = CURRENT_DIR + 'icon_spotify.png'
                #Showing notification
                n = pynotify.Notification(artist, '<i>'+title +'</i>\n '+ album, cover_image)

                # Save notification id to replace popups
                if (self.old_id is not None):
                    n.props.id = self.old_id

                n.show()
                self.old_id = n.props.id

""" main (duh!) """
def main():
    if not pynotify.init("icon-summary-body"):
        print "You need to have a working pynotify-library installed.\nIf you are using Ubuntu, try \"sudo apt-get install python-notify\""
        sys.exit(1)

    sn = SpotifyNotify()
    sn.run()

if __name__ == "__main__":
    main()

