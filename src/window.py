# window.py
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

import os
from gi.repository import Adw
from gi.repository import Gtk, Gdk, Gio

@Gtk.Template(resource_path='/lol/revisto/DrumMachine/window.ui')
class DrumMachineWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'DrumMachineWindow'

    header_label = Gtk.Template.Child()
    outer_box = Gtk.Template.Child()
    main_controls_box = Gtk.Template.Child()
    header_bar = Gtk.Template.Child()
    bpm_spin_button = Gtk.Template.Child()
    volume_scale = Gtk.Template.Child()
    play_pause_button = Gtk.Template.Child()
    drum_machine_box = Gtk.Template.Child()
    label_box = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_css()
        self.apply_css_classes()

    def init_css(self):
        path = os.path.join(os.path.dirname(__file__), "style.css")
        css_provider = Gtk.CssProvider()
        css_provider.load_from_file(Gio.File.new_for_path(path))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    def apply_css_classes(self):
        self.header_label.get_style_context().add_class("header_label")
        self.outer_box.get_style_context().add_class("outer_box")
        self.main_controls_box.get_style_context().add_class("main_controls_box")
        self.header_bar.get_style_context().add_class("header_bar")
        self.bpm_spin_button.get_style_context().add_class("spinbutton-button")
        self.play_pause_button.get_style_context().add_class("play-button")
        self.drum_machine_box.get_style_context().add_class("drum-machine-box")
        self.label_box.get_style_context().add_class("center-align")