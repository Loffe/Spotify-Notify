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
import logging

""" DBus interface """
class SpotifyDBus(object):
    """ constructor """
    def __init__(self, listener):
        logging.info('Using DBus backend')
        self.listener = listener

        # open bus
        DBusGMainLoop(set_as_default = True)
        self.dbus_bus = dbus.Bus(dbus.Bus.TYPE_SESSION)

        # connect to service
        logging.debug('Connecting to Spotify DBus service')
        self.dbus_spotify_service = self.dbus_bus.get_object('com.spotify.qt', '/org/mpris/MediaPlayer2')

        # listen for track changes
        logging.debug('Connecting to track change signal')
        self.dbus_spotify_service.connect_to_signal('TrackChange', self.on_track_change)
        self.dbus_spotify_service.connect_to_signal('PropertiesChanged', self.on_property_change)

        # listen for media key presses
        logging.debug('Connecting to media keys signal')
        bus_object = self.dbus_bus.get_object('org.gnome.SettingsDaemon', '/org/gnome/SettingsDaemon/MediaKeys')
        bus_object.GrabMediaPlayerKeys('Spotify', 0, dbus_interface='org.gnome.SettingsDaemon.MediaKeys')
        bus_object.connect_to_signal('MediaPlayerKeyPressed', self.on_media_key_pressed)

    """ calls a given method over DBus """
    def call_method(self, method):
        if (method):
            logging.debug('Calling DBus method {0}'.format(method))
            self.dbus_spotify_service = self.dbus_bus.get_object('com.spotify.qt', '/org/mpris/MediaPlayer2')
            dbus_method = self.dbus_spotify_service.get_dbus_method(method, 'org.mpris.MediaPlayer2.Player')
            dbus_method()

    """
    media key handler

    sends the corresponding command to Spotify
    """
    def on_media_key_pressed(self, *mmkeys):
        logging.debug('Media key pressed')
        for key in mmkeys:
            if key == 'Play':
                self.call_method('PlayPause')
            elif key == 'Stop':
                self.call_method('Pause')
            elif key == 'Next':
                self.call_method('Next')
            elif key == 'Previous':
                self.call_method('Previous')

    """
    property change handler

    this method will also run on track change
    """
    def on_property_change(self, *data):
        logging.debug('Property change event triggered')
        self.dbus_spotify_service = self.dbus_bus.get_object('com.spotify.qt', '/')
        dbus_method = self.dbus_spotify_service.get_dbus_method('GetMetadata', 'org.freedesktop.MediaPlayer2')
        self.on_track_change(dbus_method())

    """
    track change handler
    """
    def on_track_change(self, *info_hash):
        logging.debug('Track change event triggered')
        data = info_hash[0]
        if 'xesam:artist' in data:
            song = {
                'artist': data['xesam:artist'][0].encode('latin-1'),
                'title': data['xesam:title'].encode('latin-1'),
                'album': data['xesam:album'].encode('latin-1'),
                'created': data['xesam:contentCreated'].encode('latin-1'),
                'track_id': data['mpris:trackid'].split(':', 3)[2].encode('latin-1')
            }
            self.listener.on_track_change(song)

    """ backend loop """
    def loop(self):
        gtk.main()

