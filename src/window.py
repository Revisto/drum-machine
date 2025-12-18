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
import logging
from typing import Optional

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk, GLib, Gio

from gettext import gettext as _

from .config.constants import NUM_TOGGLES, DEFAULT_BPM, DEFAULT_VOLUME
from .handlers.file_dialog_handler import FileDialogHandler
from .handlers.window_actions import WindowActionHandler
from .handlers.drag_drop_handler import DragDropHandler
from .services.drum_machine_service import DrumMachineService
from .services.save_changes_service import SaveChangesService
from .services.sound_service import SoundService
from .services.audio_export_service import AudioExportService
from .services.ui_helper import UIHelper
from .ui.drum_grid_builder import DrumGridBuilder


@Gtk.Template(resource_path="/io/github/revisto/drum-machine/window.ui")
class DrumMachineWindow(Adw.ApplicationWindow):
    __gtype_name__ = "DrumMachineWindow"

    menu_button = Gtk.Template.Child()
    outer_box = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    bpm_spin_button = Gtk.Template.Child()
    volume_button = Gtk.Template.Child()
    clear_button = Gtk.Template.Child()
    play_pause_button = Gtk.Template.Child()
    drum_machine_box = Gtk.Template.Child()
    file_pattern_button = Gtk.Template.Child()
    export_audio_button = Gtk.Template.Child()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._setup_services()
        self._setup_handlers()
        self._initialize_interface()

    def _setup_services(self) -> None:
        """Initialize all services"""
        self.application = self.get_application()
        # Bundled sounds from app install location (read-only in snaps)
        bundled_sounds_dir = os.path.join(
            os.path.dirname(__file__), "..", "data", "drumkit"
        )
        # User data directory (writable) - uses SNAP_USER_DATA in snaps,
        # or XDG_DATA_HOME otherwise
        user_data_dir = os.path.join(
            GLib.get_user_data_dir(), "drum-machine", "drumkit"
        )

        try:
            self.sound_service = SoundService(user_data_dir, bundled_sounds_dir)
            self.sound_service.load_sounds()
        except Exception as e:
            logging.critical(f"Failed to initialize sound service: {e}")
            raise

        self.audio_export_service = AudioExportService(self)

        self.ui_helper = UIHelper(self)
        self.drum_machine_service = DrumMachineService(
            self, self.sound_service, self.ui_helper
        )
        self.save_changes_service = SaveChangesService(self, self.drum_machine_service)

    def _setup_handlers(self) -> None:
        """Initialize UI handlers"""
        self.drum_grid_builder = DrumGridBuilder(self)
        self.action_handler = WindowActionHandler(self)
        self.file_dialog_handler = FileDialogHandler(self)
        self.drag_drop_handler = DragDropHandler(self)

    def _initialize_interface(self) -> None:
        """Initialize the complete interface"""
        # Build drum grid
        drum_interface = self.drum_grid_builder.build_drum_machine_interface()
        self.drum_machine_box.append(drum_interface)

        # Setup other components
        self.file_dialog_handler.setup_pattern_menu()
        self._connect_signals()
        self.action_handler.setup_actions()

        # Setup drag and drop
        self.drag_drop_handler.setup_drag_drop()

        # Initialize export button state
        self.update_export_button_sensitivity()

    def update_export_button_sensitivity(self) -> None:
        """Update the sensitivity of export and clear buttons based on pattern state"""
        has_active_beats = any(
            any(beats.values())
            for beats in self.drum_machine_service.drum_parts_state.values()
        )
        self.export_audio_button.set_sensitive(has_active_beats)
        self.clear_button.set_sensitive(has_active_beats)

    def _connect_signals(self) -> None:
        """Connect UI signals"""
        self.connect("close-request", self._on_close_request)
        self.bpm_spin_button.connect("value-changed", self.on_bpm_changed)
        self.volume_button.connect("value-changed", self.on_volume_changed)
        self.clear_button.connect("clicked", self.handle_clear)
        self.play_pause_button.connect("clicked", self.handle_play_pause)
        self.file_pattern_button.connect("clicked", self._on_open_file_clicked)
        self.export_audio_button.connect("clicked", self._on_export_audio_clicked)
        self.drum_machine_box.connect(
            "notify::css-classes", self._on_breakpoint_changed
        )

    def _on_breakpoint_changed(self, box: Gtk.Box, gparam: object) -> None:
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

    def handle_layout_change(self, is_tiny: bool) -> None:
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

        # Rebuild the grid with the new size. The builder will handle loading
        # the pattern.
        self.drum_grid_builder.rebuild_carousel(focus_beat_index=focus_beat_index)

    # Delegate methods to handlers
    def _on_open_file_clicked(self, button: Gtk.Button) -> None:
        self.file_dialog_handler.handle_open_file()

    def _on_save_pattern_clicked(self) -> None:
        self.file_dialog_handler.handle_save_pattern()

    def _on_export_audio_clicked(self, button: Gtk.Button) -> None:
        """Handle export audio button click"""
        self.file_dialog_handler.handle_export_audio()

    def scroll_carousel_to_page(self, page_index: int) -> None:
        """Scrolls the carousel to a specific page if auto-scroll is enabled."""
        current_page = self.carousel.get_position()
        if current_page != page_index:
            self.carousel.scroll_to(self.carousel.get_nth_page(page_index), True)

    # Event handlers that need to stay in window
    def on_toggle_changed(
        self, toggle_button: Gtk.ToggleButton, part: str, index: int
    ) -> None:
        state = toggle_button.get_active()

        if state:
            self.drum_machine_service.drum_parts_state[part][index] = True
        else:
            self.drum_machine_service.drum_parts_state[part].pop(index, None)

        # Tell the service to recalculate the total pattern length
        self.drum_machine_service.update_total_beats()

        # Update export button sensitivity
        self.update_export_button_sensitivity()

        # Mark as unsaved when toggles change
        self.save_changes_service.mark_unsaved_changes(True)

    def on_bpm_changed(self, spin_button: Gtk.SpinButton) -> None:
        value = spin_button.get_value()
        self.drum_machine_service.set_bpm(value)

        # Update tooltip and accessibility with current BPM
        bpm_text = _("{} Beats per Minute (BPM)").format(int(value))
        spin_button.set_tooltip_text(bpm_text)

        # Mark as unsaved when BPM changes
        self.save_changes_service.mark_unsaved_changes(True)

    def on_volume_changed(self, button: Gtk.VolumeButton, value: float) -> None:
        self.drum_machine_service.set_volume(value)
        # Update button tooltip to show current volume level
        volume_text = _("{:.0f}% Volume").format(value)
        button.set_tooltip_text(volume_text)

    def handle_clear(self, button: Gtk.Button) -> None:
        """Clear the pattern but keep samples"""
        self.drum_machine_service.clear_all_toggles()
        self.drum_machine_service.update_total_beats()
        self.drum_grid_builder.reset_carousel_pages()
        self.update_export_button_sensitivity()
        self.save_changes_service.mark_unsaved_changes(False)

    def reset_to_defaults(self) -> None:
        """Clear pattern and restore default samples, BPM, and volume"""
        self.drum_machine_service.clear_all_toggles()
        self.sound_service.drum_part_manager.reset_to_defaults()
        self.sound_service.reload_sounds()
        self.drum_machine_service.drum_parts_state = (
            self.drum_machine_service.create_empty_drum_parts_state()
        )
        self.drum_grid_builder.rebuild_drum_parts_column()
        self.drum_grid_builder.rebuild_carousel()
        self.drum_machine_service.update_total_beats()
        self.drum_grid_builder.reset_carousel_pages()
        self.bpm_spin_button.set_value(DEFAULT_BPM)
        self.volume_button.set_value(DEFAULT_VOLUME)
        self.update_export_button_sensitivity()
        self.save_changes_service.mark_unsaved_changes(False)

    def handle_play_pause(self, button: Gtk.Button) -> None:
        if self.drum_machine_service.playing:
            button.set_icon_name("media-playback-start-symbolic")
            button.set_tooltip_text(_("Play"))
            self.drum_machine_service.stop()
        else:
            button.set_icon_name("media-playback-pause-symbolic")
            button.set_tooltip_text(_("Pause"))
            self.drum_machine_service.play()

    def on_drum_part_button_clicked(self, button: Gtk.Button, part: str) -> None:
        self.drum_machine_service.preview_drum_part(part)

    def _on_right_click_released(
        self,
        gesture_click: Gtk.GestureClick,
        n_press: int,
        x: float,
        y: float,
        toggle_button: Gtk.ToggleButton,
    ) -> None:
        toggle_button.set_active(not toggle_button.props.active)
        toggle_button.emit("toggled")

    def _on_close_request(self, *args) -> bool:
        self.action_handler.on_quit_action(None, None)
        return True

    def _save_and_close(self) -> None:
        self.file_dialog_handler.show_save_dialog(self.cleanup_and_destroy)

    def cleanup(self) -> None:
        """Stop playback and cleanup resources"""
        if self.drum_machine_service.playing:
            self.drum_machine_service.stop()
        self.drum_machine_service.playing = False

    def cleanup_and_destroy(self) -> None:
        self.cleanup()
        self.destroy()

    def show_toast(
        self, message: str, open_file: bool = False, file_path: Optional[str] = None
    ) -> None:
        """Show a toast notification with optional action button"""
        toast = Adw.Toast(title=message, timeout=5)

        if open_file and file_path:
            # Setup action if not already done
            self._setup_toast_actions()

            # Set action
            toast.set_action_name("win.open-file")
            toast.set_action_target_value(GLib.Variant.new_string(file_path))
            toast.set_button_label(_("Open"))

        self.toast_overlay.add_toast(toast)

    def _setup_toast_actions(self) -> None:
        """Setup toast action handlers"""
        if not hasattr(self, "_open_action"):
            action = Gio.SimpleAction.new("open-file", GLib.VariantType.new("s"))
            action.connect("activate", self._open_file)
            self.add_action(action)
            self._open_action = action

    def _open_file(self, action: Gio.SimpleAction, parameter: GLib.Variant) -> None:
        """Open file with default app"""
        file_path = parameter.get_string()
        Gio.AppInfo.launch_default_for_uri(f"file://{file_path}", None)

    def show_added_toast(self, name: str) -> None:
        self.show_toast(_("Added: {}").format(name))

    def add_new_drum_part(
        self, file_path: str, name: str, show_success_toast: bool = True
    ) -> bool:
        """Add a new drum part"""
        result = self.drum_machine_service.add_new_drum_part(file_path, name)
        if result:
            if show_success_toast:
                self.show_added_toast(name)
            self.save_changes_service.mark_unsaved_changes(True)
            logging.info(f"Added custom drum part: {name}")
            return True
        else:
            logging.error(f"Failed to add custom drum part: {name} from {file_path}")
            self.show_toast(_("Failed to add custom sound"))
            return False

    def replace_drum_part(self, drum_id: str, file_path: str, name: str) -> bool:
        """Replace an existing drum part"""
        result = self.drum_machine_service.replace_drum_part(drum_id, file_path, name)
        if result:
            self.show_toast(_("Replaced drum with: {}").format(name))
            # Update button state to reflect new file availability
            self.drum_grid_builder.update_drum_button(drum_id)
            self.save_changes_service.mark_unsaved_changes(True)
            logging.info(f"Replaced drum part {drum_id} with: {name}")
            return True
        else:
            logging.error(f"Failed to replace drum part {drum_id} with {file_path}")
            self.show_toast(_("Failed to replace drum sound"))
            return False
