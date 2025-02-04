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
from gi.repository import Adw, Gtk, Gio, GLib
from gettext import gettext as _
from .services.sound_service import SoundService
from .services.drum_machine_service import DrumMachineService
from .services.ui_helper import UIHelper
from .services.save_changes_service import SaveChangesService
from .config import DRUM_PARTS, NUM_TOGGLES, GROUP_TOGGLE_COUNT, DEFAULT_PRESETS


@Gtk.Template(resource_path="/io/github/revisto/drum-machine/window.ui")
class DrumMachineWindow(Adw.ApplicationWindow):
    __gtype_name__ = "DrumMachineWindow"

    menu_button = Gtk.Template.Child()
    outer_box = Gtk.Template.Child()
    bpm_spin_button = Gtk.Template.Child()
    volume_button = Gtk.Template.Child()
    clear_button = Gtk.Template.Child()
    play_pause_button = Gtk.Template.Child()
    drum_machine_box = Gtk.Template.Child()
    file_preset_button = Gtk.Template.Child()
    save_preset_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.application = self.get_application()
        drumkit_dir = os.path.join(os.path.dirname(__file__), "..", "data", "drumkit")
        self.sound_service = SoundService(drumkit_dir)
        self.sound_service.load_sounds()
        self.ui_helper = UIHelper(self, DRUM_PARTS, NUM_TOGGLES)
        self.drum_machine_service = DrumMachineService(
            self.sound_service, self.ui_helper
        )
        self.save_changes_service = SaveChangesService(self, self.drum_machine_service)
        self.initialize_drum_machine_interface()
        self.setup_preset_menu()
        self.connect_signals()
        self.init_drum_parts()
        self.create_actions()

    def create_actions(self):
        self._create_action("open_menu", self.on_open_menu_action, ["F10"])
        self._create_action(
            "show-help-overlay", self.on_show_help_overlay, ["<primary>question"]
        )
        self._create_action("play_pause", self.handle_play_pause_action, ["space"])
        self._create_action(
            "clear_toggles", self.handle_clear_action, ["<primary>Delete"]
        )
        self._create_action("increase_bpm", self.increase_bpm_action, ["plus", "equal"])
        self._create_action("decrease_bpm", self.decrease_bpm_action, ["minus"])
        self._create_action(
            "increase_volume", self.increase_volume_action, ["<primary>Up"]
        )
        self._create_action(
            "decrease_volume", self.decrease_volume_action, ["<primary>Down"]
        )
        self._create_action("load_preset", self.on_open_file_action, ["<primary>o"])
        self._create_action("save_preset", self.on_save_preset_action, ["<primary>s"])
        self._create_action("quit", self.on_quit_action, ["<primary>q"])
        self._create_action("close_window", self.on_quit_action, ["<primary>w"])

    def _create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.application.set_accels_for_action(f"win.{name}", shortcuts)

    def cleanup(self):
        """Stop playback and cleanup resources"""
        if self.drum_machine_service.playing:
            self.drum_machine_service.stop()
        # Ensure thread is stopped
        self.drum_machine_service.playing = False

    def cleanup_and_destroy(self):
        self.cleanup()
        self.destroy()

    def on_open_menu_action(self, action, param):
        self.menu_button.activate()

    def on_show_help_overlay(self, action, param):
        self.get_help_overlay().present()

    def handle_play_pause_action(self, action, param):
        self.handle_play_pause(self.play_pause_button)

    def handle_clear_action(self, action, param):
        self.handle_clear(self.clear_button)

    def increase_bpm_action(self, action, param):
        current_bpm = self.bpm_spin_button.get_value()
        self.bpm_spin_button.set_value(current_bpm + 1)

    def decrease_bpm_action(self, action, param):
        current_bpm = self.bpm_spin_button.get_value()
        self.bpm_spin_button.set_value(current_bpm - 1)

    def increase_volume_action(self, action, param):
        current_volume = self.volume_button.get_value()
        self.volume_button.set_value(min(current_volume + 5, 100))

    def decrease_volume_action(self, action, param):
        current_volume = self.volume_button.get_value()
        self.volume_button.set_value(max(current_volume - 5, 0))

    def on_open_file_action(self, action, param):
        self.on_open_file(self.file_preset_button)

    def on_save_preset_action(self, action, param):
        self.on_save_preset(self.save_preset_button)

    def _on_close_request(self, *args):
        self.on_quit_action(None, None)
        return True

    def on_quit_action(self, action, param):
        if self.save_changes_service.has_unsaved_changes():
            self.save_changes_service.prompt_save_changes(
                on_save=self._save_and_close, on_discard=self.cleanup_and_destroy
            )
        else:
            self.cleanup_and_destroy()

    def _save_and_close(self):
        self._show_save_dialog(lambda: self.cleanup_and_destroy())

    def initialize_drum_machine_interface(self):
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        container.set_homogeneous(False)

        for part in DRUM_PARTS:
            part_box = self.create_part_container(part)
            container.append(part_box)

        self.drum_machine_box.append(container)

    def create_part_container(self, part):
        part_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        drum_part_button = self.create_drum_part_button(part)
        toggle_box = self.create_toggle_box(part)

        part_box.append(drum_part_button)
        part_box.append(toggle_box)
        return part_box

    def create_drum_part_button(self, part):
        # Create container box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_spacing(5)

        # Create button that fits text
        button = Gtk.Button(label=f"{part.capitalize().replace('-', ' ')}")
        button.set_halign(Gtk.Align.START)
        button.connect("clicked", self.on_drum_part_button_clicked, part)
        button.add_css_class("drum-part-button")
        button.add_css_class("flat")
        button.set_tooltip_text(
            f"Click to preview {part.capitalize().replace('-', ' ')}"
        )
        button.set_has_tooltip(True)

        # Add button and flexible spacer to box
        button_box.append(button)
        spacer = Gtk.Label()
        spacer.set_hexpand(True)
        button_box.append(spacer)

        return button_box

    def create_toggle_box(self, part):
        toggle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        num_groups = (NUM_TOGGLES + GROUP_TOGGLE_COUNT - 1) // GROUP_TOGGLE_COUNT

        for group in range(num_groups):
            group_box = self.create_toggle_button_group(part, group)
            toggle_box.append(group_box)

        return toggle_box

    def create_toggle_button_group(self, part, group):
        group_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        for i in range(GROUP_TOGGLE_COUNT):
            toggle_num = group * GROUP_TOGGLE_COUNT + i + 1
            if toggle_num > NUM_TOGGLES:
                break
            toggle_button = self.create_single_toggle_button(part, toggle_num)
            group_box.append(toggle_button)

        return group_box

    def create_single_toggle_button(self, part, toggle_num):
        toggle_button = Gtk.ToggleButton()
        toggle_button.set_size_request(20, 20)
        toggle_button.set_name(f"{part}_toggle_{toggle_num}")
        toggle_button.set_valign(Gtk.Align.CENTER)
        toggle_button.add_css_class("drum-toggle")
        toggle_button.connect("toggled", self.on_toggle_changed, part, toggle_num - 1)
        setattr(self, f"{part}_toggle_{toggle_num}", toggle_button)
        return toggle_button

    def on_drum_part_button_clicked(self, button, part):
        self.drum_machine_service.preview_drum_part(part)

    def connect_signals(self):
        self.connect("close-request", self._on_close_request)
        self.bpm_spin_button.connect("value-changed", self.on_bpm_changed)
        self.volume_button.connect("value-changed", self.on_volume_changed)
        self.clear_button.connect("clicked", self.handle_clear)
        self.play_pause_button.connect("clicked", self.handle_play_pause)
        self.file_preset_button.connect("clicked", self.on_open_file)
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
        # Mark as unsaved when toggles change
        self.save_changes_service.mark_unsaved_changes(True)

    def on_bpm_changed(self, spin_button):
        self.drum_machine_service.set_bpm(spin_button.get_value())
        # Mark as unsaved when BPM changes
        self.save_changes_service.mark_unsaved_changes(True)

    def on_volume_changed(self, button, value):
        self.drum_machine_service.set_volume(value)
        # Update button tooltip to show current volume level
        volume_text = _("{:.0f}% volume").format(value)
        button.set_tooltip_text(volume_text)

    def handle_clear(self, button):
        self.drum_machine_service.clear_all_toggles()
        # Mark as unsaved when clearing
        self.save_changes_service.mark_unsaved_changes(True)

    def handle_play_pause(self, button):
        if self.drum_machine_service.playing:
            button.set_icon_name("media-playback-start-symbolic")
            self.drum_machine_service.stop()
        else:
            button.set_icon_name("media-playback-pause-symbolic")
            self.drum_machine_service.play()

    def setup_preset_menu(self):
        menu = Gio.Menu.new()
        section = Gio.Menu.new()

        # Add presets section
        for preset in DEFAULT_PRESETS:
            item = Gio.MenuItem.new(preset, "win.load-preset")
            item.set_action_and_target_value(
                "win.load-preset", GLib.Variant.new_string(preset)
            )
            section.append_item(item)

        menu.append_section(_("Default Presets"), section)

        # Create the action without state
        preset_action = Gio.SimpleAction.new("load-preset", GLib.VariantType.new("s"))
        preset_action.connect("activate", self.on_preset_selected)
        self.add_action(preset_action)

        self.file_preset_button.set_menu_model(menu)

    def on_open_file(self, button):
        # If unsaved changes exist, prompt the user first
        if self.save_changes_service.has_unsaved_changes():
            self.save_changes_service.prompt_save_changes(
                on_save=self._save_and_open_file, on_discard=self._open_file_directly
            )
        else:
            self._open_file_directly()

    def _save_and_open_file(self):
        self._show_save_dialog(self._open_file_directly)

    def _save_and_open_preset(self, parameter):
        self._show_save_dialog(lambda: self._open_preset_directly(parameter))

    def _open_file_directly(self):
        filefilter = Gtk.FileFilter.new()
        filefilter.add_pattern("*.mid")
        filefilter.set_name(_("MIDI files"))

        filefilters = Gio.ListStore.new(Gtk.FileFilter)
        filefilters.append(filefilter)

        dialog = Gtk.FileDialog.new()
        dialog.set_title(_("Open MIDI File"))
        dialog.set_filters(filefilters)
        dialog.set_modal(True)

        dialog.open(parent=self, callback=self._handle_file_response)

    def _handle_file_response(self, dialog, response):
        try:
            file = dialog.open_finish(response)
            if file:
                self.drum_machine_service.load_preset(file.get_path())
                # Reset unsaved changes after loading
                self.save_changes_service.mark_unsaved_changes(False)
        except GLib.Error:
            return

    def on_preset_selected(self, action, parameter):
        if self.save_changes_service.has_unsaved_changes():
            self.save_changes_service.prompt_save_changes(
                on_save=lambda: self._save_and_open_preset(parameter),
                on_discard=lambda: self._open_preset_directly(parameter),
            )
        else:
            self._open_preset_directly(parameter)

    def _open_preset_directly(self, parameter):
        preset_name = parameter.get_string()
        preset_dir = os.path.join(os.path.dirname(__file__), "..", "data", "presets")
        file_path = os.path.join(preset_dir, f"{preset_name}.mid")
        self.drum_machine_service.load_preset(file_path)
        # Reset unsaved changes after loading preset
        self.save_changes_service.mark_unsaved_changes(False)

    def _show_save_dialog(self, after_save_callback=None):
        filefilter = Gtk.FileFilter.new()
        filefilter.add_pattern("*.mid")
        filefilter.set_name("MIDI files")

        filefilters = Gio.ListStore.new(Gtk.FileFilter)
        filefilters.append(filefilter)

        dialog = Gtk.FileDialog.new()
        dialog.set_title("Save Preset")
        dialog.set_filters(filefilters)
        dialog.set_modal(True)
        dialog.set_initial_name("new_preset.mid")

        def save_callback(dialog, result):
            try:
                file = dialog.save_finish(result)
                if file:
                    file_path = file.get_path()
                    if not file_path.endswith(".mid"):
                        file_path += ".mid"
                    self.drum_machine_service.save_preset(file_path)
                    self.save_changes_service.mark_unsaved_changes(False)
                    if after_save_callback:
                        after_save_callback()
            except GLib.Error:
                return

        dialog.save(parent=self, callback=save_callback)

    def on_save_preset(self, button):
        self._show_save_dialog()
