#Spotify media keys script by SveinT (sveint@gmail.com)
#Initial version


import dbus
from dbus.mainloop.glib import DBusGMainLoop
import gobject, gtk


class SpotifyNotify(): 
    
    def __init__(self, object, update_handler):
        self.on_update = update_handler

        self.bus = object
        self.spotifyservice = self.bus.get_object('com.spotify.qt', '/TrackList')
        self.spotifyservice.connect_to_signal('TrackChange', self.trackChange)

    def executeCommand(self, key):
        if (key):
            self.cmd = self.spotifyservice.get_dbus_method(key, 'org.freedesktop.MediaPlayer')
            self.cmd()
    
    def trackChange(self, *trackChange):
        print trackChange
        data = trackChange[0]

        if "artist" in data:
            song = {'artist': data["artist"], 'title': data["title"]}
            self.on_update(song)

class spotify(object):
    def __init__(self, update_handler):

        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
        self.bus_object = self.bus.get_object(
            'org.gnome.SettingsDaemon', '/org/gnome/SettingsDaemon/MediaKeys')

        self.bus_object.GrabMediaPlayerKeys(
            "Spotify", 0, dbus_interface='org.gnome.SettingsDaemon.MediaKeys')
        
        self.bus_object.connect_to_signal(
            'MediaPlayerKeyPressed', self.handle_mediakey)

        self.SN = SpotifyNotify(self.bus, update_handler)
        
    def handle_mediakey(self, *mmkeys):
        for key in mmkeys:
            print key
            if key == "Play":
                self.SN.executeCommand(key)
            elif key == "Stop":
                key = "Pause"
                self.SN.executeCommand(key)
            elif key == "Next":
                self.SN.executeCommand(key)
            elif key == "Previous":
                key = "Prev"
                self.SN.executeCommand(key)


    def loop(self):
        gtk.main()
