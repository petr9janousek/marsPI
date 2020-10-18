#!/usr/bin/env python3

#import modules
import os, sys, logging, serial, queue, time, configparser

#setup logger
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(module)s:%(message)s")
logger = logging.getLogger("log")
logger.setLevel("DEBUG")

#import my code
import mars_serial, mars_plot

#import GTK
from gi.repository import Gtk, Gdk
import gi
gi.require_version("Gtk", "3.0")


#find directories
my_directory = os.path.dirname(os.path.realpath(__file__))
glade_file = os.path.join(my_directory, 'environment.glade')
style_file = os.path.join(my_directory, 'styles.css')
init_file = os.path.join(my_directory, 'config.ini')

class Settings():
    def __init__(self, builder):
        self.config = configparser.ConfigParser()
        self.config.read(init_file)        
        self.builder = builder
        self.lists = []
        for sec in self.config.sections():
            #fill models
            ls = Gtk.ListStore(str,str)
            ls.set_name("{}_settings_store".format(sec)) #create name for models
            for opt in self.config.items(sec):
                ls.append(opt)
            self.lists.append(ls)
            #fill treeviews with models
            try:
                treeview = self.builder.get_object("{}_treeview".format(sec)) #name used in glade
                model = next(x for x in self.lists if x.get_name() == ls.get_name())
                treeview.set_model(model)
            except: pass #no need to react
        
    def write(self, section, option, value):
        self.config.set(section, option, value)
        with open(init_file, 'w') as configfile:
            self.config.write(configfile)

    def read(self, section, key):
            return self.config.get(section, key)

    def read_bool(self, section, key):
            return self.config.getboolean(section, key)

#ADR (from), CMD (type of info), VAL VAL (short1) VAL VAL (short2) VAL VAL (short3)
class Manager():
    def __init__(self, builder):
        self.builder = builder      #for access to components
        self.data_que = queue.Queue()       #internally creates a queue in which data will be stored

    def state(self, *args):
        pass
        #print([x for x in args])

    def sensor(self, *args):
        pass

    def default(self, *args):
        pass

    #dataclass?
    actuators = {
        0: "lis_toggle_vyhazovace", 
        1: "lis_toggle_pritlak",
        2: "lis_toggle_kopyto",
        3: "lis_toggle_forma"
    }
    def actuator(self, *args):
        toggle = self.builder.get_object(actuators[args[2]])
        #block signal to not emitt the signal twice
        toggle.handler_block_by_func(self.on_genericToggle_toggled)
        toggle.set_active(args[3])
        toggle.handler_unblock_by_func(self.on_genericToggle_toggled)

    def message(self, *args):
        pass

    def other(self, *args):
        pass

    actions = { -1: default, 0: state, 1: sensor, 2: actuator, 3: message, 4: other}
    #machines = { 0: , 1, 2, 3, 4, 5}
    def call_action(self, act_key, *args):
        try:
            self.actions[act_key](self, args)
        except KeyError:
            self.actions[default]
        #return self.actions.get(act_key, lambda *_: "ERROR: Invalid action key")(*args)

    #mel by pervest datovy paket na formu kterou by byla schopna zpracovat tato trida
    def internalize(self, data):
        time_stamp = time.strftime("%H:%M:%S", time.localtime())
        self.call_action(data[1], data)
        
    #mel by primo pouzit vnitrni info k uprave panelu
    def manage_info(self):
        #machine, message, thing, val
        data = self.data_que.get()
        #self.internalize(data.split(","))
        #self.internalize(data)
        #self.show()
        #text = self.builder.get_object("info_textbox_master").get_buffer()
        #text.set_text("Prijato: %s" % (data))


class Command:
    pallete = {
        "lis_settings_temp": "2, 15, val, bit",
        "lis_settings_perm": "2, 7, 0, bit",
        "rov_settings_temp": "1, 15, val, bit",
        "rov_settings_perm": "1, 7, 0, bit",
        "pla_settings_temp": "3, 15, val, bit",
        "pla_settings_perm": "3, 7, 0, bit",
        "jer_settings_temp": "5, 15, val, bit",
        "jer_settings_perm": "5, 7, 0, bit"
    }
    
    def listed(self, name, **kwargs):
        cmd = Command.pallete.get(name).split(",")
        if kwargs.get('adr', None):
            cmd[0] = kwargs['adr']
        if kwargs.get('cmd', None):
            cmd[1] = kwargs['cmd']
        if kwargs.get('val', None):
            cmd[2] = kwargs['val']
        if kwargs.get('bit', None):
            cmd[3] = kwargs['bit']
        return  cmd

    def new(self, name, value):
        Command.pallete['name'] = str(value)
        return value.split(",")

class Handlers:
    # ----------------------------------------------------------------------INIT
    def __init__(self, builder, settings, serial):
        #self.app = caller
        self.builder = builder
        self.serial = serial
        self.settings = settings 
        self.cmd = Command()
    # ----------------------------------------------------------------------USER ACTION

    def on_port_toggle_toggled(self, toggle):
        label = self.builder.get_object("port_label")
        combo = self.builder.get_object("port_combobox")
        text = combo.get_active_text()
        if text == "Nevybráno":
            label.set_text("Status: Vyberte nejprve port")
            toggle.set_active(False)
            return
        if toggle.get_active():
            self.serial.connect(text)
            label.set_text("Status: Připojeno")
            self.serial.serialthread.resume()
        else:
            self.serial.disconnect()
            label.set_text("Status: Odpojeno")
            self.serial.serialthread.pause()

    def on_port_button_clicked(self, combo):
        combo.remove_all()
        available = self.serial.list_ports()
        for p in available:
            combo.append_text(p)  # it has be [list] or (tuple,) to work

    def on_mainWindow_show(self, window):
        combo = self.builder.get_object("port_combobox")
        auto = self.settings.read_bool("general", "auto_connect") #měl by se připojit?
        self.builder.get_object("port_checkbox").set_active(auto)  #sežeň a v každém případě změň čudlík
        if auto:
            port = self.settings.read("general", "com_port") #k jakému portu
            combo.prepend_text(port) #vytvoř položku
            combo.set_active(int(0)) #vytvoř položku
            self.builder.get_object("port_toggle").set_active(True)
        else:
            combo = self.builder.get_object("port_combobox")
            available = self.serial.list_ports()
            for p in available:
                combo.append_text(p)  # it has be [list] or (tuple,) to work
        

    def on_lis_toggle_vyhazovace_toggled(self, toggle):
        tag = toggle.get_name()
        state = toggle.get_active()
        #print(tag)

    def on_genericButton_clicked(self, button):
        tag = button.get_name()
        cmd = tag.split(',')
        #print(cmd)
        self.serial.write(cmd)

    def on_genericToggle_toggled(self, toggle):
        tag = toggle.get_name()
        state = toggle.get_active()
        cmd = tag.split(',') #get list
        cmd[3] = int(state) #1 or 0
        #print(cmd) #debug
        self.serial.write(cmd)

    def on_genericValue_clicked(self, entry):
        tag = entry.get_name()
        val = entry.get_text()
        cmd = tag.split(',') #get list
        if val == '':
            val = "0"
            entry.set_text("0")
        cmd[2] = int(val) #val
        #print(cmd) #debug
        self.serial.write(cmd)

    def on_genericCombo_changed(self, combo):
        tag = combo.get_name()
        val = combo.get_active()
        if val != 0:
            cmd = tag.split(',') #get list
            cmd[2] = int(val) - 1 #val BUT nevybrano
            #print(cmd) #debug
            self.serial.write(cmd)

    def on_genericJogPlasma_clicked(self, button):
        #self.on_question_clicked(button)
        scale_val = int(self.builder.get_object("pla_scale").get_value())
        tag = button.get_name()
        cmd = tag.split(',') #get list
        dist = int(cmd[-1])
        cmd[-1] = 5 * dist + scale_val #5 je MAX_DIST
        self.serial.write(cmd)

    def on_genericJogCrane_clicked(self, button):
        #self.on_question_clicked(button)
        scale_val = int(self.builder.get_object("jer_scale").get_value())
        tag = button.get_name()
        cmd = tag.split(',') #get list
        dist = int(cmd[-1])
        cmd[-1] = 5 * dist + scale_val #5 je MAX_DIST
        self.serial.write(cmd)

    def on_rov_button_levo_pressed(self, button):
        tag = "1,2,0,0"
        cmd = tag.split(',') #get list
        self.serial.write(cmd)

    def on_rov_button_levo_released(self, button):
        tag = "1,1,0,0"
        cmd = tag.split(',') #get list
        self.serial.write(cmd)

    def on_rov_button_pravo_pressed(self, button):
        tag = "1,3,0,0"
        cmd = tag.split(',') #get list
        self.serial.write(cmd)

    def on_rov_button_pravo_released(self, button):
        tag = "1,1,0,0"
        cmd = tag.split(',') #get list
        self.serial.write(cmd)

    def on_rovvValue_clicked(self, button):
        tag = button.get_name()
        entry = self.builder.get_object("rovv_entry")
        val = entry.get_text()
        cmd = tag.split(',') #get list
        if val == '':
            val = "0"
            entry.set_text("0")
        cmd[2] = int(val) #val
        #print(cmd) #debug
        self.serial.write(cmd)

    def on_leg_button_hotovo_clicked(self, button):
        value = self.builder.get_object("leg_updown_hotovo").get_value()
        tag = button.get_name()
        cmd = tag.split(',')
        cmd[2] = value
        self.serial.write(cmd)

    def on_leg_button_vyrob_clicked(self, button):
        take = self.builder.get_object("leg_radio_odvezeni").get_active()
        value = self.builder.get_object("leg_updown_vyrob").get_value()
        tag = button.get_name()
        cmd = tag.split(',')
        cmd[2] = value
        cmd[3] = take
        self.serial.write(cmd)
    
    def on_side_button_zacni_clicked(self, button):
        big = self.builder.get_object("side_radio_big").get_active()
        value = self.builder.get_object("side_updown_vyrob").get_value()
        tag = button.get_name()
        cmd = tag.split(',')
        cmd[2] = value
        cmd[3] = big
        self.serial.write(cmd)

    def on_side_button_vyrob_clicked(self, button):
        pass

    def on_bottom_button_vyrob_clicked(self, button):
        size1100 = self.builder.get_object("bottom_radio_1100").get_active()
        value = self.builder.get_object("bottom_updown_vyrob").get_value()
        tag = button.get_name()
        cmd = tag.split(',')
        cmd[2] = value
        cmd[3] = size1100
        self.serial.write(cmd)
    
    def on_bottom_button_zacni_clicked(self, button):
        pass

    def on_control_button_on_clicked(self, button):
        _val = self.builder.get_object("control_combo").get_active()
        _bit = self.builder.get_object("control_entry").get_text()
        _cmd = button.get_name().split(',')
        _msg = self.cmd.make_new(_cmd, val=_val, bit=_bit)
        self.serial.write(_msg)
    
    # ----------------------------------------------------------------------SETTINGS
    def on_set_checkbox_maximize_toggled(self, check):
        checked = str(check.get_active())
        self.settings.write("general", "window_startup_maximize", checked)
        #self.settings.save()

    def on_port_checkbox_toggled(self, check):
        checked = bool(check.get_active())
        self.settings.write("general", "auto_connect", str(checked))
        if checked:
            com = self.builder.get_object("port_combobox").get_active_text()
            logger.debug(com)
            self.settings.write("general", "com_port", str(com))
        #self.settings.save()

    def on_lis_selector_changed(self, selector):
        par = self.builder.get_object("lis_settings_entry_par")
        val = self.builder.get_object("lis_settings_entry_val")
        (model, pathlist) = selector.get_selected_rows()
        tree_iter = model.get_iter(pathlist[0])
        par.set_text(model.get_value(tree_iter,0))
        val.set_text(model.get_value(tree_iter,1))
    
    def on_lis_settings_button_clicked(self, selector):
        par = self.builder.get_object("lis_settings_entry_par").get_text()
        val = self.builder.get_object("lis_settings_entry_val").get_text()
        (model, pathlist) = selector.get_selected_rows()
        tree_iter = model.get_iter(pathlist[0])
        model.set(tree_iter, 0, par)
        model.set(tree_iter, 1, val)
        self.settings.write("lis", par, val)
        self.serial.write(self.cmd.listed("lis_settings_temp", val=str(val), bit=str(pathlist[0])))
        self.serial.write(self.cmd.listed("lis_settings_perm", bit=pathlist[0]))  
    
    def on_pla_selector_changed(self, selector):
        par = self.builder.get_object("pla_settings_entry_par")
        val = self.builder.get_object("pla_settings_entry_val")
        (model, pathlist) = selector.get_selected_rows()
        tree_iter = model.get_iter(pathlist[0])
        par.set_text(model.get_value(tree_iter,0))
        val.set_text(model.get_value(tree_iter,1))
    
    def on_pla_settings_button_clicked(self, selector):
        par = self.builder.get_object("pla_settings_entry_par").get_text()
        val = self.builder.get_object("pla_settings_entry_val").get_text()
        (model, pathlist) = selector.get_selected_rows()
        tree_iter = model.get_iter(pathlist[0])
        model.set(tree_iter, 0, par)
        model.set(tree_iter, 1, val)
        self.settings.write("pla", par, val)
        self.serial.write(self.cmd.listed("pla_settings_temp", val=str(val), bit=str(pathlist[0])))
        self.serial.write(self.cmd.listed("pla_settings_perm", bit=pathlist[0]))
    
    def on_rov_selector_changed(self, selector):
        par = self.builder.get_object("rov_settings_entry_par")
        val = self.builder.get_object("rov_settings_entry_val")
        (model, pathlist) = selector.get_selected_rows()
        tree_iter = model.get_iter(pathlist[0])
        par.set_text(model.get_value(tree_iter,0))
        val.set_text(model.get_value(tree_iter,1))
    
    def on_rov_settings_button_clicked(self, selector):
        par = self.builder.get_object("rov_settings_entry_par").get_text()
        val = self.builder.get_object("rov_settings_entry_val").get_text()
        (model, pathlist) = selector.get_selected_rows()
        tree_iter = model.get_iter(pathlist[0])
        model.set(tree_iter, 0, par)
        model.set(tree_iter, 1, val)
        self.settings.write("rov", par, val)
        self.serial.write(self.cmd.listed("rov_settings_temp", val=str(val), bit=str(pathlist[0])))
        self.serial.write(self.cmd.listed("rov_settings_perm", bit=pathlist[0]))
    
    def on_jer_selector_changed(self, selector):
        par = self.builder.get_object("jer_settings_entry_par")
        val = self.builder.get_object("jer_settings_entry_val")
        (model, pathlist) = selector.get_selected_rows()
        tree_iter = model.get_iter(pathlist[0])
        par.set_text(model.get_value(tree_iter,0))
        val.set_text(model.get_value(tree_iter,1))
    
    def on_jer_settings_button_clicked(self, selector):
        par = self.builder.get_object("jer_settings_entry_par").get_text()
        val = self.builder.get_object("jer_settings_entry_val").get_text()
        (model, pathlist) = selector.get_selected_rows()
        tree_iter = model.get_iter(pathlist[0])
        model.set(tree_iter, 0, par)
        model.set(tree_iter, 1, val)
        self.settings.write("jer", par, val)
        self.serial.write(self.cmd.listed("jer_settings_temp", val=str(val), bit=str(pathlist[0])))
        self.serial.write(self.cmd.listed("jer_settings_perm", bit=pathlist[0]))
    
    # ----------------------------------------------------------------------GUI SIGNAL
    def on_mainWindow_destroy(self, window):
        Gtk.main_quit()

    def on_numericEntry_changed(self, entry):
        text = entry.get_text().strip()
        entry.set_text(''.join([i for i in text if i in '0123456789']))

    def on_question_clicked(self):
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
            logger.info("QUESTION dialog closed by YES option")
        elif response == Gtk.ResponseType.NO:
            logger.info("QUESTION dialog closed by NO option")
        dialog.destroy()
        return response

class Application():
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(glade_file)

        self.settings = Settings(self.builder)
        self.manager = Manager(self.builder)
        self.serial = mars_serial.UART(self.manager)

        self.callbacks = Handlers(self.builder, self.settings, self.serial)
        self.builder.connect_signals(self.callbacks)

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
        if self.settings.read_bool("general", "window_startup_maximize"): 
            window.maximize()
        window.set_title("MARS OVLÁDÁNÍ")
        window.show_all()
        Gtk.main()
        # no commands after this line ---!

if __name__ == "__main__":
    gui = Application()
    gui.show()