import os
import re
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib


class DBusObject:
    def __init__(self, bus, service, path, interface):
        self.bus = bus
        self.service = service
        self.path = path
        self.interface = interface

    def get_obj(self):
        return self.bus.get_object(self.service, self.path)

    def get_prop(self, prop):
        return self.get_obj().Get(self.interface, prop, dbus_interface=dbus.PROPERTIES_IFACE)

    def call(self, method_name, *args):
        iface = dbus.Interface(self.get_obj(), self.interface)
        method = getattr(iface, method_name)
        return method(*args)


class i3ifiedesk:
    def __init__(self):
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        self.bus.add_signal_receiver(
            self.on_shortcut_pressed,
            dbus_interface="org.kde.kglobalaccel.Component",
            signal_name="globalShortcutPressed"
        )
        self.bus.add_signal_receiver(
            self.on_desktop_change,
            dbus_interface="org.kde.KWin.VirtualDesktopManager",
            signal_name="currentChanged"
        )
        self.desktop_manager = DBusObject(
            self.bus, 'org.kde.KWin', '/VirtualDesktopManager', 'org.kde.KWin.VirtualDesktopManager')
        self.kwin_manager = DBusObject(
            self.bus, 'org.kde.KWin', '/KWin', 'org.kde.KWin')
        self.kwin_script_manager = DBusObject(
            self.bus, 'org.kde.KWin', '/Scripting', 'org.kde.kwin.Scripting')
        self.shortcuts_manager = DBusObject(
            self.bus, 'org.kde.kglobalaccel', '/component/kwin', 'org.kde.kglobalaccel.Component')
        # self.activity_manager = DBusObject(self.bus, 'org.kde.ActivityManager', '/Activities', 'org.kde.ActivityManager.Activities')

        self.script_name = "rm_desk"
        script_path = os.path.dirname(os.path.realpath(
            __file__)) + '/'+self.script_name+'.js'
        self.script_id = self.kwin_script_manager.call(
            'loadScript', script_path)
        self.script_manager = DBusObject(
            self.bus, 'org.kde.KWin', f'/Scripting/Script{self.script_id}', 'org.kde.kwin.Script')
        self.kwin_manager.call('reconfigure')

        self.loop = GLib.MainLoop()
        try:
            self.loop.run()
        except KeyboardInterrupt:
            self.kwin_script_manager.call("unloadScript", self.script_name)
            self.script_manager.call("stop")
            self.loop.quit()

    def handle_desktop_switch(self, action):
        pattern = r"Switch to Desktop (\d+)"
        match = re.search(pattern, str(action))
        if match:
            target = int(match.group(1))
            desktop_count = self.desktop_manager.get_prop('count')
            if target > desktop_count:
                self.desktop_manager.call(
                    "createDesktop", target, f"Desktop {target}")
                self.kwin_manager.call("setCurrentDesktop", target)

    def handle_window_move(self, action):
        pattern = r"Window to Desktop (\d+)"
        match = re.search(pattern, str(action))
        if match:
            target = int(match.group(1))
            desktop_count = self.desktop_manager.get_prop('count')
            if target > desktop_count:
                self.desktop_manager.call(
                    "createDesktop", target, f"Desktop {target}")
                self.shortcuts_manager.call('invokeShortcut', action)

    def on_shortcut_pressed(self, component, action, shortcuts):
        self.handle_desktop_switch(action)
        self.handle_window_move(action)

        self.shortcuts_manager.call('invokeShortcut', 'Close Empty Desktops')

    def on_desktop_change(self, current):
        self.shortcuts_manager.call('invokeShortcut', 'Close Empty Desktops')


if __name__ == "__main__":
    i3ifiedesk()
