#!/usr/bin/env python
# -*- encoding: utf8 -*-
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
import urllib2
import pynotify
import tempfile
import webbrowser

sys.path.append("./lib")
import pylast

SPOTIFY_OPEN_URL = "http://open.spotify.com/track/"
LASTFM_API_KEY = '73f8547fa82ecbd0d0313f063c29571d' #spotify-notify's Last.fm API key
CURRENT_DIR = os.path.abspath(os.curdir)+'/'
TMP_DIR = tempfile.gettempdir() + '/'

class SpotifyNotify(object):
    """ constructor """
    def __init__(self):
        # initialize fields
        self.oldmeta = None
        self.old_id = None

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

    """ called on track change """
    def on_track_change(self, meta):
        # check if it really was a track change
        if meta != self.oldmeta and meta is not None:
            # old meta is now new meta
            self.oldmeta = meta

            # hack to see if there is any metadata in meta
            if 'artist' in meta:
                artist = meta['artist'] if 'artist' in meta else '(no artist)'
                title = meta['title'] if 'title' in meta else '(no title)'
                album = meta['album'] if 'album' in meta else '(no album)'
                created = meta['created'] if 'created' in meta else '0000-00-00 00:00 UTC'
                year = int(created[:4])
                track_id = meta['track_id'] if 'track_id' in meta else None
                
                #TODO: enable choise
                #coverData = self.fetchLastFmAlbumCover(artist, title, album)
                self.fetchCoverImageSpotify(track_id)

                # use cover image if available, otherwise just use the logo
                if self.cover_image:
                    cover_image = self.cover_image
                else:
                    cover_image = CURRENT_DIR + 'icon_spotify.png'

                # create notification
                n = pynotify.Notification(artist, '<i>%s</i>\n%s (%04d)' % (title, album, year), cover_image)

                # save notification id to replace popups
                if self.old_id is not None:
                    n.props.id = self.old_id

                # show the notification
                n.show()
                self.old_id = n.props.id

            # show link to lyrics on lyric wiki
            if True:
                def e(s):
                    return "_".join(map(urllib2.quote, s.title().split(" ")))

                url = "http://lyrics.wikia.com/%s:%s" % (e(artist), e(title))
                print url
                #webbrowser.open()

""" main (duh!) """
def main():
    # dependency check
    if not pynotify.init('icon-summary-body'):
        print 'You need to have a working pynotify-library installed.\nIf you are using Ubuntu, try "sudo apt-get install python-notify"'
        sys.exit(1)

    # run!
    sn = SpotifyNotify()
    sn.run()

if __name__ == '__main__':
    main()

