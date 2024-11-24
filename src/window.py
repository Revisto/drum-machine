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
from gi.repository import Adw, Gtk
from .services.sound_service import SoundService
from .services.drum_machine_service import DrumMachineService
from .services.ui_helper import UIHelper
from .config import DRUM_PARTS, NUM_TOGGLES, GROUP_TOGGLE_COUNT


@Gtk.Template(resource_path="/lol/revisto/DrumMachine/window.ui")
class DrumMachineWindow(Adw.ApplicationWindow):
    __gtype_name__ = "DrumMachineWindow"

    outer_box = Gtk.Template.Child()
    bpm_spin_button = Gtk.Template.Child()
    volume_scale = Gtk.Template.Child()
    clear_button = Gtk.Template.Child()
    play_pause_button = Gtk.Template.Child()
    drum_machine_box = Gtk.Template.Child()
    preset_combo_box = Gtk.Template.Child()
    load_preset_button = Gtk.Template.Child()
    save_preset_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        drumkit_dir = os.path.join(os.path.dirname(__file__), "..", "data", "drumkit")
        self.sound_service = SoundService(drumkit_dir)
        self.sound_service.load_sounds()
        self.ui_helper = UIHelper(self, DRUM_PARTS, NUM_TOGGLES)
        self.drum_machine_service = DrumMachineService(
            self.sound_service, self.ui_helper
        )
        self.create_drumkit_toggle_buttons()
        self.connect_signals()
        self.init_drum_parts()
        self.load_presets()

    def create_drumkit_toggle_buttons(self):
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        container.set_homogeneous(False)

        for part in DRUM_PARTS:
            # Create label for drum part
            label = Gtk.Label(label=f"{part.capitalize()}:", halign=Gtk.Align.START)
            label.set_size_request(100, -1)

            # Create box for toggle buttons
            toggle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)

            # Calculate the number of groups
            num_groups = (NUM_TOGGLES + GROUP_TOGGLE_COUNT - 1) // GROUP_TOGGLE_COUNT

            # Create groups of buttons
            for group in range(num_groups):
                # Create box for group of buttons
                group_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

                # Add toggle buttons to the group
                for i in range(GROUP_TOGGLE_COUNT):
                    toggle_num = group * GROUP_TOGGLE_COUNT + i + 1
                    if toggle_num > NUM_TOGGLES:
                        break
                    toggle_button = Gtk.ToggleButton()
                    toggle_button.set_size_request(30, 30)
                    toggle_button.set_name(f"{part}_toggle_{toggle_num}")
                    toggle_button.connect("toggled", self.on_toggle_changed, part, toggle_num - 1)
                    group_box.append(toggle_button)
                    # Store reference to toggle button
                    setattr(self, f"{part}_toggle_{toggle_num}", toggle_button)

                toggle_box.append(group_box)

            # Create a horizontal box for label and toggles
            part_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            part_box.append(label)
            part_box.append(toggle_box)

            # Add part_box to the container
            container.append(part_box)

        # Add the container to the drum_machine_box
        self.drum_machine_box.append(container)

    def connect_signals(self):
        self.bpm_spin_button.connect("value-changed", self.on_bpm_changed)
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        self.clear_button.connect("clicked", self.handle_clear)
        self.play_pause_button.connect("clicked", self.handle_play_pause)
        self.load_preset_button.connect("clicked", self.on_load_preset)
        self.save_preset_button.connect("clicked", self.on_save_preset)

    def init_drum_parts(self):
        self.drum_parts = {
            part: [False for _ in range(NUM_TOGGLES)] for part in DRUM_PARTS
        }

        for part in DRUM_PARTS:
            for i in range(NUM_TOGGLES):
                toggle = getattr(self, f"{part}_toggle_{i + 1}")
                self.drum_parts[part][i] = toggle.get_active()
                toggle.connect("toggled", self.on_toggle_changed, part, i)

    def on_toggle_changed(self, toggle_button, part, index):
        state = toggle_button.get_active()
        self.drum_parts[part][index] = state
        self.drum_machine_service.drum_parts[part][index] = state

    def on_bpm_changed(self, spin_button):
        self.drum_machine_service.set_bpm(spin_button.get_value())

    def on_volume_changed(self, scale):
        self.drum_machine_service.set_volume(scale.get_value())

    def handle_clear(self, button):
        self.drum_machine_service.clear_all_toggles()

    def handle_play_pause(self, button):
        if self.drum_machine_service.playing:
            button.set_label("Play")
            self.drum_machine_service.stop()
        else:
            button.set_label("Pause")
            self.drum_machine_service.play()

    def load_presets(self):
        # Load default presets and add them to the combo box
        default_presets = ["Shoot", "Maybe Rock", "Boom Boom", "Night", "Slow", "Chill"]
        for preset in default_presets:
            self.preset_combo_box.append_text(preset)
        self.preset_combo_box.append_text("Load Your File...")

        # Set the active preset to the first default preset
        self.preset_combo_box.set_active(0)

    def on_load_preset(self, button):
        selected_preset = self.preset_combo_box.get_active_text()
        if selected_preset == "Load Your File...":
            dialog = Gtk.FileChooserDialog(
                title="Please choose a file",
                parent=self,
                action=Gtk.FileChooserAction.OPEN,
            )
            dialog.add_buttons(
                "_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.OK
            )

            # Add a filter to show only .mid files
            filter_midi = Gtk.FileFilter()
            filter_midi.set_name("MIDI files")
            filter_midi.add_pattern("*.mid")
            dialog.add_filter(filter_midi)

            def on_response(dialog, response):
                if response == Gtk.ResponseType.OK:
                    file_path = dialog.get_file().get_path()
                    self.drum_machine_service.load_preset(file_path)
                dialog.close()

            dialog.connect("response", on_response)
            dialog.show()
        else:
            preset_dir = os.path.join(
                os.path.dirname(__file__), "..", "data", "presets"
            )
            file_path = os.path.join(preset_dir, f"{selected_preset}.mid")
            self.drum_machine_service.load_preset(file_path)

    def on_save_preset(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Save Preset", parent=self, action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            "_Cancel", Gtk.ResponseType.CANCEL, "_Save", Gtk.ResponseType.OK
        )

        dialog.set_current_name("new_preset.mid")

        def on_response(dialog, response):
            if response == Gtk.ResponseType.OK:
                file_path = dialog.get_file().get_path()
                if not file_path.endswith(".mid"):
                    file_path += ".mid"
                self.drum_machine_service.save_preset(file_path)
            dialog.close()

        dialog.connect("response", on_response)
        dialog.show()
