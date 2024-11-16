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
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk, Gdk, Gio
from .services.sound_service import SoundService
from .services.drum_machine_service import DrumMachineService
from .services.ui_helper import UIHelper


@Gtk.Template(resource_path="/lol/revisto/DrumMachine/window.ui")
class DrumMachineWindow(Adw.ApplicationWindow):
    __gtype_name__ = "DrumMachineWindow"

    header_label = Gtk.Template.Child()
    outer_box = Gtk.Template.Child()
    main_controls_box = Gtk.Template.Child()
    header_bar = Gtk.Template.Child()
    bpm_spin_button = Gtk.Template.Child()
    volume_scale = Gtk.Template.Child()
    play_pause_button = Gtk.Template.Child()
    drum_machine_box = Gtk.Template.Child()

    TOGGLE_PARTS = ["kick", "snare", "hihat"]
    NUM_TOGGLES = 16

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        drumkit_dir = os.path.join(os.path.dirname(__file__), "..", "data", "drumkit")
        self.sound_service = SoundService(drumkit_dir)
        self.sound_service.load_sounds()
        self.ui_helper = UIHelper(self, self.TOGGLE_PARTS, self.NUM_TOGGLES)
        self.drum_machine_service = DrumMachineService(
            self.sound_service, self.ui_helper
        )
        self.init_css()
        self.create_drumkit_toggle_buttons()
        self.apply_css_classes()
        self.connect_signals()
        self.init_drum_parts()

    def create_drumkit_toggle_buttons(self):
        # Create containers for labels and toggle buttons
        self.label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        self.toggle_button_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=10
        )

        # Add labels for each drum part
        for part in self.TOGGLE_PARTS:
            label = Gtk.Label(label=f"{part.capitalize()}:")
            label.set_halign(Gtk.Align.END)
            self.label_box.append(label)

            # Create horizontal box for the part's toggle groups
            part_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)

            # Create 4 groups of 4 buttons each
            for group in range(4):
                # Create box for group of 4 buttons
                group_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

                # Add 4 toggle buttons to the group
                for i in range(4):
                    toggle_num = group * 4 + i + 1
                    toggle_button = Gtk.ToggleButton()
                    toggle_button.set_name(f"{part}_toggle_{toggle_num}")
                    toggle_button.connect(
                        "toggled", self.on_toggle_changed, part, toggle_num - 1
                    )
                    setattr(self, f"{part}_toggle_{toggle_num}", toggle_button)
                    group_box.append(toggle_button)

                part_box.append(group_box)

            self.toggle_button_box.append(part_box)

        # Add label_box and toggle_button_box to the UI
        self.drum_machine_box.append(self.label_box)
        self.drum_machine_box.append(self.toggle_button_box)

    def init_css(self):
        path = os.path.join(os.path.dirname(__file__), "style.css")
        css_provider = Gtk.CssProvider()
        css_provider.load_from_file(Gio.File.new_for_path(path))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
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

    def connect_signals(self):
        self.bpm_spin_button.connect("value-changed", self.on_bpm_changed)
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        self.play_pause_button.connect("clicked", self.handle_play_pause)

    def init_drum_parts(self):
        self.drum_parts = {
            part: [False for _ in range(self.NUM_TOGGLES)] for part in self.TOGGLE_PARTS
        }

        for part in self.TOGGLE_PARTS:
            for i in range(self.NUM_TOGGLES):
                toggle = getattr(self, f"{part}_toggle_{i + 1}")
                self.drum_parts[part][i] = toggle.get_active()
                toggle.connect("toggled", self.on_toggle_changed, part, i)

    def on_toggle_changed(self, toggle_button, part, index):
        state = toggle_button.get_active()
        self.drum_parts[part][index] = state
        self.drum_machine_service.drum_parts[part][index] = state

    def on_bpm_changed(self, spin_button):
        self.drum_machine_service.set_bpm(spin_button.get_value())
        print(f"BPM changed to: {self.drum_machine_service.bpm}")

    def on_volume_changed(self, scale):
        self.drum_machine_service.set_volume(scale.get_value())
        print(f"Volume changed to: {self.drum_machine_service.volume}")

    def handle_play_pause(self, button):
        if self.drum_machine_service.playing:
            button.set_label("Play")
            self.drum_machine_service.stop()
            print("Paused.")
        else:
            button.set_label("Pause")
            self.drum_machine_service.play()
            print("Playing...")
