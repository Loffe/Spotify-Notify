# This file is part of Spotify-Notify.
#
# Spotify-Notify is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Spotify-Notify is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Spotify-Notify. If not, see <http://www.gnu.org/licenses/>.
#

import dbus
from dbus.mainloop.glib import DBusGMainLoop
import gobject, gtk

class SpotifyDBus(object):
    def __init__(self, listener):
        DBusGMainLoop(set_as_default=True)
        self.listener = listener
        self.bus = dbus.Bus(dbus.Bus.TYPE_SESSION)

        #self.spotifyservice = self.bus.get_object('com.spotify.qt', '/TrackList')
        self.spotifyservice = self.bus.get_object('com.spotify.qt', '/org/mpris/MediaPlayer2')
        self.spotifyservice.connect_to_signal('TrackChange', self.trackChange)
        self.spotifyservice.connect_to_signal('PropertiesChanged', self.trackChange2)
        self.bus_object = self.bus.get_object(
            'org.gnome.SettingsDaemon', '/org/gnome/SettingsDaemon/MediaKeys')

        self.bus_object.GrabMediaPlayerKeys(
            "Spotify", 0, dbus_interface='org.gnome.SettingsDaemon.MediaKeys')
        
        self.bus_object.connect_to_signal(
            'MediaPlayerKeyPressed', self.handle_mediakey)

    def executeCommand(self, key):
        if (key):
            #self.connect()
            self.spotifyservice = self.bus.get_object('com.spotify.qt', '/org/mpris/MediaPlayer2')
            self.cmd = self.spotifyservice.get_dbus_method(key, 'org.mpris.MediaPlayer2.Player')
            self.cmd()
        
    def handle_mediakey(self, *mmkeys):
        for key in mmkeys:
            #print key
            if key == "Play":
                key = "PlayPause"
                self.executeCommand(key)
            elif key == "Stop":
                key = "Pause"
                self.executeCommand(key)
            elif key == "Next":
                self.executeCommand(key)
            elif key == "Previous":
                self.executeCommand(key)

    def trackChange2(self, *trackChange):
        self.spotifyservice = self.bus.get_object('com.spotify.qt', '/')
        self.cmd = self.spotifyservice.get_dbus_method('GetMetadata', 'org.freedesktop.MediaPlayer2')
        self.new  = self.cmd()
        self.trackChange(self.new)

    def trackChange(self, *trackChange):
        data = trackChange[0]
        #print data
#dbus.Dictionary({dbus.String(u'xesam:album'): dbus.String(u'Worms 2 - Original Game Soundtrack', variant_level=1), dbus.String(u'xesam:title'): dbus.String(u'Pink Bravery', variant_level=1), dbus.String(u'xesam:trackNumber'): dbus.Int32(7, variant_level=1), dbus.String(u'xesam:artist'): dbus.String(u'Bj\xc3\xb8rn Lynne', variant_level=1), dbus.String(u'xesam:discNumber'): dbus.Int32(0, variant_level=1), dbus.String(u'mpris:trackid'): dbus.String(u'spotify:track:2VgL21XC3E7FTydxysLRe3', variant_level=1), dbus.String(u'mpris:length'): dbus.UInt64(263000000L, variant_level=1), dbus.String(u'xesam:autoRating'): dbus.Double(0.19, variant_level=1), dbus.String(u'xesam:contentCreated'): dbus.String(u'1998-01-01T00:00:00', variant_level=1), dbus.String(u'xesam:url'): dbus.String(u'spotify:track:2VgL21XC3E7FTydxysLRe3', variant_level=1)}, signature=dbus.Signature('sv'))
        if "xesam:artist" in data:
            song = {
                'artist': data["xesam:artist"].encode("latin-1"),
                'title': data["xesam:title"].encode("latin-1"),
                'album': data["xesam:album"].encode("latin-1"),
                'track_id': data["mpris:trackid"].split(":", 3)[2].encode("latin-1")
            }
            self.listener.on_track_change(song)

    def loop(self):
        gtk.main()

