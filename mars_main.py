#import modules
import os, sys, logging, serial, queue, time

#setup logger
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(module)s:%(message)s")
logger = logging.getLogger("log")
logger.setLevel("DEBUG")

#import my code
import mars_serial, mars_plot, mars_thread

#import GTK
from gi.repository import Gtk, Gdk, GLib
import gi
gi.require_version("Gtk", "3.0")

#find directories
my_directory = os.path.dirname(os.path.realpath(__file__))
glade_file = os.path.join(my_directory, 'environment.glade')
style_file = os.path.join(my_directory, 'styles.css')


class DataManager():
    def __init(self, app):
        self.app = app

    #mel by pervest datovy paket na formu kterou by byla schopna zpracovat tato trida
    def internalize(self, item):
        #item should be string loaded from queue
        pass
    #mel by primo pouzit vnitrni info k uprave panelu
    def manage_info(self):
        pass

class Handlers:
    # ----------------------------------------------------------------------INIT
    def __init__(self, caller):
        self.app = caller
    # ----------------------------------------------------------------------USER ACTION

    def on_port_toggle_toggled(self, toggle):
        label = self.app.builder.get_object("port_label")
        combo = self.app.builder.get_object("port_combobox")
        text = combo.get_active_text()
        if text == "Nevybráno":
            label.set_text("Vyberte port")
            toggle.set_active(False)
            return
        if toggle.get_active():
            self.app.serial.connect(text)
            label.set_text("Status: Připojeno")
            self.app.serialthread.resume()
        else:
            self.app.serial.disconnect()
            label.set_text("Status: Odpojeno")
            self.app.serialthread.pause()

    def on_port_button_clicked(self, combo):
        combo.remove_all()
        available = self.app.serial.list_ports()
        for p in available:
            combo.append_text(p)  # it has be [list] or (tuple,) to work

    def on_mainWindow_show(self, window):
        combo = self.app.builder.get_object("port_combobox")
        available = self.app.serial.list_ports()
        for p in available:
            combo.append_text(p)  # it has be [list] or (tuple,) to work
        check = self.app.builder.get_object("port_checkbox")
        if check.get_active:
            combo.set_active(1)
            #toggle = self.app.builder.get_object("port_toggle")
            #toggle.set_active(True)

    def on_lis_toggle_vyhazovace_toggled(self, toggle):
        tag = toggle.get_name()
        state = toggle.get_active()
        #print(tag)

    def on_genericButton_clicked(self, button):
        tag = button.get_name()
        cmd = tag.split(',')
        #print(cmd)
        self.app.serial.write(cmd)

    def on_genericToggle_toggled(self, toggle):
        tag = toggle.get_name()
        state = toggle.get_active()
        cmd = tag.split(',') #get list
        cmd[3] = int(state) #1 or 0
        #print(cmd) #debug
        self.app.serial.write(cmd)

    def on_genericValue_clicked(self, entry):
        tag = entry.get_name()
        val = entry.get_text()
        cmd = tag.split(',') #get list
        if val == '':
            val = "0"
            entry.set_text("0")
        cmd[2] = int(val) #val
        #print(cmd) #debug
        self.app.serial.write(cmd)

    def on_genericCombo_changed(self, combo):
        tag = combo.get_name()
        val = combo.get_active()
        if val != 0:
            cmd = tag.split(',') #get list
            cmd[2] = int(val) - 1 #val BUT nevybrano
            #print(cmd) #debug
            self.app.serial.write(cmd)

    def on_genericJogPlasma_clicked(self, button):
        #self.on_question_clicked(button)
        scale_val = int(self.app.builder.get_object("pla_scale").get_value())
        tag = button.get_name()
        cmd = tag.split(',') #get list
        dist = int(cmd[-1])
        cmd[-1] = 5 * dist + scale_val #5 je MAX_DIST
        self.app.serial.write(cmd)

    def on_genericJogCrane_clicked(self, button):
        #self.on_question_clicked(button)
        scale_val = int(self.app.builder.get_object("jer_scale").get_value())
        tag = button.get_name()
        cmd = tag.split(',') #get list
        dist = int(cmd[-1])
        cmd[-1] = 5 * dist + scale_val #5 je MAX_DIST
        self.app.serial.write(cmd)

    def on_rov_button_levo_pressed(self, button):
        tag = "1,2,0,0"
        cmd = tag.split(',') #get list
        self.app.serial.write(cmd)

    def on_rov_button_levo_released(self, button):
        tag = "1,1,0,0"
        cmd = tag.split(',') #get list
        self.app.serial.write(cmd)

    def on_rov_button_pravo_pressed(self, button):
        tag = "1,3,0,0"
        cmd = tag.split(',') #get list
        self.app.serial.write(cmd)

    def on_rov_button_pravo_released(self, button):
        tag = "1,1,0,0"
        cmd = tag.split(',') #get list
        self.app.serial.write(cmd)

    def on_rovvValue_clicked(self, button):
        tag = button.get_name()
        entry = self.app.builder.get_object("rovv_entry")
        val = entry.get_text()
        cmd = tag.split(',') #get list
        if val == '':
            val = "0"
            entry.set_text("0")
        cmd[2] = int(val) #val
        #print(cmd) #debug
        self.app.serial.write(cmd)

    def on_leg_button_zacni_clicked(self, button):
        pass
    def on_leg_button_vyrob_clicked(self, button):
        pass
    # ----------------------------------------------------------------------GUI SIGNAL
    def on_mainWindow_destroy(self, window):
        Gtk.main_quit()
        
    def on_numericEntry_changed(self, entry):
        text = entry.get_text().strip()
        entry.set_text(''.join([i for i in text if i in '0123456789']))
    
    def on_question_clicked(self, widget):
        dialog = Gtk.MessageDialog(
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="This is an QUESTION MessageDialog",
        )
        dialog.format_secondary_text(
            "And this is the secondary text that explains things."
        )
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            print("QUESTION dialog closed by clicking YES button")
        elif response == Gtk.ResponseType.NO:
            print("QUESTION dialog closed by clicking NO button")

        dialog.destroy()

class Application():
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(glade_file)

        self.que = queue.Queue()

        self.serial = mars_serial.UART()
        self.serialthread = mars_thread.Job(target=self.read_thread, args=(self.serial, self.que), daemon=True)
        self.serialthread.start()

        self.callbacks = Handlers(self)
        self.builder.connect_signals(self.callbacks)

    def manage_info(self, que):
        data = que.get()
        text = self.builder.get_object("info_textbox_master").textBuffer()
        text.set_text("Prijato: %s" % data)

    def read_thread(self, stream, que):
        stream.read_queue(que)
        if not que.empty():
            GLib.idle_add(self.manage_info, que)

    def show(self):
        # for CSS styling create
        provider = Gtk.CssProvider()
        screen = Gdk.Screen.get_default()
        context = Gtk.StyleContext()
        # apply styles from file
        provider.load_from_path(style_file)
        context.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        # get Window up and running
        window = self.builder.get_object("mainWindow")
        window.maximize()
        window.set_title("MARS OVLÁDÁNÍ")
        window.show_all()
        Gtk.main()
        # no commands after this line ---!

if __name__ == "__main__":
    gui = Application()
    gui.show()
    