# application.py
#
# Copyright 2025 revisto
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import platform
import gi
from gettext import gettext as _

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk
from .window import DrumMachineWindow


class DrumMachineApplication(Adw.Application):
    def __init__(self, version):
        super().__init__(
            application_id="io.github.revisto.drum-machine",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.version = version
        self.create_action("about", self.on_about_action)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = DrumMachineWindow(application=self)
        win.present()

    def on_about_action(self, *_args):
        debug_info = f"Drum Machine {self.version}\n"
        debug_info += f"System: {platform.system()}\n"
        if platform.system() == "Linux":
            debug_info += f"Dist: {platform.freedesktop_os_release()['PRETTY_NAME']}\n"
        debug_info += f"Python {platform.python_version()}\n"
        debug_info += (
            f"GTK {Gtk.MAJOR_VERSION}.{Gtk.MINOR_VERSION}.{Gtk.MICRO_VERSION}\n"
        )
        debug_info += "PyGObject {}.{}.{}\n".format(*gi.version_info)
        debug_info += (
            f"Adwaita {Adw.MAJOR_VERSION}.{Adw.MINOR_VERSION}.{Adw.MICRO_VERSION}"
        )
        about = Adw.AboutDialog(
            application_name=_("Drum Machine"),
            application_icon="io.github.revisto.drum-machine",
            developer_name="Revisto",
            version=self.version,
            developers=["Revisto"],
            copyright="© 2024–2025 Revisto",
            comments=_(
                "Drum Machine is a modern and intuitive application for creating, "
                "playing, and managing drum patterns."
            ),
            debug_info=debug_info,
            license_type=Gtk.License.GPL_3_0,
            translator_credits=_("translator-credits"),
            issue_url="https://github.com/Revisto/drum-machine/issues",
            website="https://apps.gnome.org/DrumMachine/",
        )
        about.add_acknowledgement_section(
            _("Special thanks"), ["Sepehr Rasouli", "Tobias Bernard"]
        )
        about.add_legal_section(
            _("Sounds"),
            _("The drum samples used in this application are from ")
            + "<a href='https://99sounds.org/drum-samples/'>99Sounds</a>.",
            Gtk.License.UNKNOWN,
        )
        about.add_legal_section("Mido", None, Gtk.License.MIT_X11)
        about.add_legal_section("Pygame", None, Gtk.License.LGPL_2_1)
        about.present(self.props.active_window)

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)
