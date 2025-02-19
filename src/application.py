# application.py
#
# Copyright 2024 revisto
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

import gi

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

    def on_about_action(self, widget, _):
        about = Adw.AboutWindow(
            transient_for=self.props.active_window,
            application_name="Drum Machine",
            application_icon="io.github.revisto.drum-machine",
            developer_name="Revisto",
            version=self.version,
            developers=["Revisto"],
            copyright="© 2024–2025 Revisto",
            license_type=Gtk.License.GPL_3_0,
            issue_url="https://github.com/Revisto/drum-machine/issues",
            website="https://apps.gnome.org/DrumMachine/",
        )
        about.present()

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)
