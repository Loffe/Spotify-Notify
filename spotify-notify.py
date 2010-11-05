#!/usr/bin/python -OO
# Spotify-notify
# by SveinT (sveint@gmail.com)
# Original code by noalwin (lambda512@gmail.com)
# Based on pypanel code
print "Spotify-notify v0.1"
import os, time, sys, datetime, string
try:
	from Xlib import X, display, error, Xatom
	import Xlib.protocol.event
except:
	print "You need the xlib-library. If you are using Ubuntu, try running\n\"sudo apt-get install python-xlib\""
	sys.exit(1)
import pynotify
import pylast

API_KEY = '73f8547fa82ecbd0d0313f063c29571d' #spotify-notify's Last.fm API key
CURRENT_DIR = os.path.abspath(os.curdir).replace(';','')+"/"

class spotify(object):
    def __init__(self):
        self._dsp = display.Display()
        self._screen  = self._dsp.screen()
        self._root    = self._screen.root
    #   self.error   = error.CatchError()
        self._root.change_attributes(event_mask=(X.PropertyChangeMask))
        self._dsp.flush()
        
    
        self._spotify_task = None
        self._spotify_obj = None
        self._spotify_title = None # Spotify's window title
        
        
        self._init_spotify_data()
    
    def _init_spotify_data(self):
        """Search the spotify window and initialize the data"""
        tasks = self._root.get_full_property(
                        self._dsp.intern_atom("_NET_CLIENT_LIST"),
                        Xatom.WINDOW
                ).value
        
        is_running = False
        
        for task in tasks:
            obj  = self._dsp.create_resource_object("window", task)
            name = ( obj.get_full_property(self._dsp.intern_atom("_NET_WM_NAME"), 0) or
                     obj.get_full_property(Xatom.WM_NAME, 0) )
            title = getattr(name,'value','')
            if title is not '' and title.startswith('Spotify'):
                obj.change_attributes(event_mask=(
                    X.PropertyChangeMask|X.StructureNotifyMask))
                is_running = True
                self._spotify_task = task
                self._spotify_obj = obj
                self._spotify_title = title
                break
                
        if not is_running and self._spotify_task is not None:
            self._delete_spotify_data()
        
    
    def _update_spotify_title(self):
        """Update the song data"""
        name = ( self._spotify_obj.get_full_property(self._dsp.intern_atom("_NET_WM_NAME"), 0) or
                 self._spotify_obj.get_full_property(Xatom.WM_NAME, 0) )
        title = getattr(name,'value','')
        if title is not '' and title.startswith('Spotify'):
            self._spotify_title = title
    
    def _delete_spotify_data(self):
        self._spotify_task = None
        self._spotify_obj = None
        self._spotify_title = None
    
    
    def _update(self):
        while self._dsp.pending_events():
            e = self._dsp.next_event()
            #print e
            
            if e.type == X.DestroyNotify:
                if e.window.id == self._spotify_task:
                    self._delete_spotify_data()
                    #print "Spotify has been closed"
            elif e.type == X.PropertyNotify:
                if e.atom == self._dsp.intern_atom("_NET_CLIENT_LIST"):
                    #print '_NET_CLIENT_LIST'
                    if self._spotify_task is not None:
                        #if hasattr(e, "window") and self._spotify_task == e.window.id:
                            #print 'Spotify seems to have changed'
                        pass
                    else:
                        # print 'Spotify has been started'
                        self._init_spotify_data()
                elif self._spotify_task is not None and e.window.id == self._spotify_task:
                    if e.atom in [Xatom.WM_NAME, self._dsp.intern_atom("_NET_WM_NAME")]:
                        try:
                            self._update_spotify_title()
                            #print 'Spotify has changed the name %s' % self._spotify_title
                        except Xlib.error.BadWindow:
                            #print "BADWINDOW!"
                            pass
    
    def get_song(self):
        self._update()
        # self._spotify_title -> "Spotify \xe2\x80\x93 Title - Artist"
        
        if self._spotify_title is None or self._spotify_title == 'Spotify':
            # Closed or stopped
            return None
        
        data = self._spotify_title[10:].split(' \xe2\x80\x93 ')
        
        if len(data) == 2:
            return {'artist': data[0], 'title': data[1]}
        else:
            #Unexpected format
            return {'title': self._spotify_title[10:]}
    

if __name__ == "__main__":
    if not pynotify.init ("icon-summary-body"):
        print "You need to have a working pynotify-library installed.\nIf you are using Ubuntu, try \"sudo apt-get install python-notify\""
        sys.exit (1)
    s = spotify()
    oldsong = None
    while 1:
        song = s.get_song()
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
        time.sleep(1)

