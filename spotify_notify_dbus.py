#Spotify media keys script by SveinT (sveint@gmail.com)
#Initial version

import dbus
from dbus.mainloop.glib import DBusGMainLoop
import gobject, gtk

class spotify(object):
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
            self.connect()
            self.cmd = self.spotifyservice.get_dbus_method(key, 'org.mpris.MediaPlayer2.Player')
            self.cmd()
        
    def handle_mediakey(self, *mmkeys):
        for key in mmkeys:
            #print key
            if key == "Play":
                self.executeCommand(key)
            elif key == "Stop":
                key = "Pause"
                self.executeCommand(key)
            elif key == "Next":
                self.executeCommand(key)
            elif key == "Previous":
                key = "Prev"
                self.executeCommand(key)

    def trackChange2(self, *trackChange):
        self.spotifyservice = self.bus.get_object('com.spotify.qt', '/')
        self.cmd = self.spotifyservice.get_dbus_method('GetMetadata', 'org.freedesktop.MediaPlayer2')
        self.new  = self.cmd()
        self.trackChange(self.new)

    def trackChange(self, *trackChange):
        data = trackChange[0]
        print data
        if "xesam:artist" in data:
            song = {
                    'artist': data["xesam:artist"].encode("latin-1"),
                    'title': data["xesam:title"].encode("latin-1"),
                    'album': data["xesam:album"].encode("latin-1")}
            self.listener.on_track_change(song)

    def loop(self):
        gtk.main()

