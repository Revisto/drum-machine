# window.py
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

import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from gettext import gettext as _

from .config import DRUM_PARTS, NUM_TOGGLES
from .handlers.file_dialog_handler import FileDialogHandler
from .handlers.window_actions import WindowActionHandler
from .services.drum_machine_service import DrumMachineService
from .services.save_changes_service import SaveChangesService
from .services.sound_service import SoundService
from .services.ui_helper import UIHelper
from .ui.drum_grid_builder import DrumGridBuilder


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
        self._setup_services()
        self._setup_handlers()
        self._initialize_interface()

    def _setup_services(self):
        """Initialize all services"""
        self.application = self.get_application()
        drumkit_dir = os.path.join(os.path.dirname(__file__), "..", "data", "drumkit")

        self.sound_service = SoundService(drumkit_dir)
        self.sound_service.load_sounds()

        self.ui_helper = UIHelper(self, DRUM_PARTS)
        self.drum_machine_service = DrumMachineService(
            self.sound_service, self.ui_helper
        )
        self.save_changes_service = SaveChangesService(self, self.drum_machine_service)

    def _setup_handlers(self):
        """Initialize UI handlers"""
        self.drum_grid_builder = DrumGridBuilder(self)
        self.action_handler = WindowActionHandler(self)
        self.file_dialog_handler = FileDialogHandler(self)

    def _initialize_interface(self):
        """Initialize the complete interface"""
        # Build drum grid
        drum_interface = self.drum_grid_builder.build_drum_machine_interface()
        self.drum_machine_box.append(drum_interface)

        # Setup other components
        self.file_dialog_handler.setup_preset_menu()
        self._connect_signals()
        self.action_handler.setup_actions()

    def _connect_signals(self):
        """Connect UI signals"""
        self.connect("close-request", self._on_close_request)
        self.bpm_spin_button.connect("value-changed", self.on_bpm_changed)
        self.volume_button.connect("value-changed", self.on_volume_changed)
        self.clear_button.connect("clicked", self.handle_clear)
        self.play_pause_button.connect("clicked", self.handle_play_pause)
        self.file_preset_button.connect("clicked", self._on_open_file_clicked)
        self.save_preset_button.connect("clicked", self._on_save_preset_clicked)
        self.drum_machine_box.connect(
            "notify::css-classes", self._on_breakpoint_changed
        )

    def _on_breakpoint_changed(self, box, gparam):
        """
        Called when the css-classes property of the drum_machine_box changes.
        """
        css_classes = box.get_css_classes()

        # Handle responsive layout for toggles (half-view)
        is_tiny = "half-view" in css_classes
        self.handle_layout_change(is_tiny=is_tiny)

        # Handle compact spacing for instrument list
        is_compact = "compact" in css_classes
        self.drum_grid_builder.update_drum_parts_spacing(is_compact=is_compact)

    def handle_layout_change(self, is_tiny):
        """
        Rebuilds the drum grid when the layout size changes.
        """
        focus_beat_index = 0
        old_beats_per_page = self.drum_machine_service.beats_per_page

        if is_tiny:
            # For smaller views, use half the number of toggles
            beats_per_page = NUM_TOGGLES // 2
        else:
            beats_per_page = NUM_TOGGLES

        # Avoid rebuilding if the layout hasn't actually changed
        if self.drum_machine_service.beats_per_page == beats_per_page:
            return

        # Determine the correct beat to focus on
        if self.drum_machine_service.playing:
            focus_beat_index = self.drum_machine_service.playing_beat
        else:
            current_page = self.carousel.get_position()
            focus_beat_index = current_page * old_beats_per_page

        self.drum_machine_service.beats_per_page = beats_per_page
        self.drum_machine_service.update_total_beats()

        # Rebuild the grid with the new size. The builder will handle loading the pattern.
        self.drum_grid_builder.rebuild_carousel(focus_beat_index=focus_beat_index)

    # Delegate methods to handlers
    def _on_open_file_clicked(self, button):
        self.file_dialog_handler.handle_open_file()

    def _on_save_preset_clicked(self, button):
        self.file_dialog_handler.handle_save_preset()

    def on_open_file(self, button):
        """Compatibility method"""
        self._on_open_file_clicked(button)

    def on_save_preset(self, button):
        """Compatibility method"""
        self._on_save_preset_clicked(button)

    def scroll_carousel_to_page(self, page_index):
        """Scrolls the carousel to a specific page if auto-scroll is enabled."""
        current_page = self.carousel.get_position()
        if current_page != page_index:
            self.carousel.scroll_to(self.carousel.get_nth_page(page_index), True)

    # Event handlers that need to stay in window
    def on_toggle_changed(self, toggle_button, part, index):
        state = toggle_button.get_active()

        if state:
            self.drum_machine_service.drum_parts_state[part][index] = True
        else:
            self.drum_machine_service.drum_parts_state[part].pop(index, None)

        # Tell the service to recalculate the total pattern length
        self.drum_machine_service.update_total_beats()

        # Mark as unsaved when toggles change
        self.save_changes_service.mark_unsaved_changes(True)

    def on_bpm_changed(self, spin_button):
        value = spin_button.get_value()
        self.drum_machine_service.set_bpm(value)

        # Update tooltip and accessibility with current BPM
        bpm_text = _("{} Beats per Minute (BPM)").format(int(value))
        spin_button.set_tooltip_text(bpm_text)

        # Mark as unsaved when BPM changes
        self.save_changes_service.mark_unsaved_changes(True)

    def on_volume_changed(self, button, value):
        self.drum_machine_service.set_volume(value)
        # Update button tooltip to show current volume level
        volume_text = _("{:.0f}% Volume").format(value)
        button.set_tooltip_text(volume_text)

    def handle_clear(self, button):
        self.drum_machine_service.clear_all_toggles()
        # After clearing, update the total beats which will reset active_pages to 1
        self.drum_machine_service.update_total_beats()
        # Now, reset the carousel UI to its initial state
        self.drum_grid_builder.reset_carousel_pages()
        # Mark as saved when clearing
        self.save_changes_service.mark_unsaved_changes(False)

    def handle_play_pause(self, button):
        if self.drum_machine_service.playing:
            button.set_icon_name("media-playback-start-symbolic")
            button.set_tooltip_text(_("Play"))
            self.drum_machine_service.stop()
        else:
            button.set_icon_name("media-playback-pause-symbolic")
            button.set_tooltip_text(_("Pause"))
            self.drum_machine_service.play()

    def on_drum_part_button_clicked(self, button, part):
        self.drum_machine_service.preview_drum_part(part)

    def _on_right_click_released(self, gesture_click, n_press, x, y, toggle_button):
        toggle_button.set_active(not toggle_button.props.active)
        toggle_button.emit("toggled")

    def _on_close_request(self, *args):
        self.action_handler.on_quit_action(None, None)
        return True

    def _save_and_close(self):
        self.file_dialog_handler._show_save_dialog(lambda: self.cleanup_and_destroy())

    def cleanup(self):
        """Stop playback and cleanup resources"""
        if self.drum_machine_service.playing:
            self.drum_machine_service.stop()
        self.drum_machine_service.playing = False

    def cleanup_and_destroy(self):
        self.cleanup()
        self.destroy()
