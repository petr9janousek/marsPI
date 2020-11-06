import can
from gi.repository import GLib

class GuiReader(can.Listener):
    """
    Listener child class for calling GLib async GUI refresh with new can data.
    Notifier class read in thread and notify this class.
    """

    def __init__(self, manager):
        self.manager = manager
        #super(GuiReader, self).__init__()
        #self.is_paused = False

    def on_message_received(self, msg):
        #print(msg)
        self.manager.data_que.put(msg)
        GLib.idle_add(self.manager.add_info)

    #def pause(self):
    #    self.is_paused = True