# handlers/window_actions.py
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

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")
gi.require_version("Adw", "1")
from gi.repository import Gio


class WindowActionHandler:
    """Handles window-level actions and keyboard shortcuts"""

    def __init__(self, window):
        self.window = window

    def setup_actions(self):
        """Setup all window actions and keyboard shortcuts"""
        actions = [
            ("open_menu", self.on_open_menu_action, ["F10"]),
            ("show-help-overlay", self.on_show_help_overlay, ["<primary>question"]),
            ("play_pause", self.handle_play_pause_action, ["space"]),
            ("clear_toggles", self.handle_clear_action, ["<primary>Delete"]),
            ("random_beats", self.on_random_beats_action, ["<primary>r"]),
            ("increase_bpm", self.increase_bpm_action, ["plus", "equal"]),
            ("decrease_bpm", self.decrease_bpm_action, ["minus"]),
            ("increase_volume", self.increase_volume_action, ["<primary>Up"]),
            ("decrease_volume", self.decrease_volume_action, ["<primary>Down"]),
            ("load_preset", self.on_open_file_action, ["<primary>o"]),
            ("save_preset", self.on_save_preset_action, ["<primary>s"]),
            ("export_audio", self.on_export_audio_action, ["<primary>e"]),
            ("quit", self.on_quit_action, ["<primary>q"]),
            ("close_window", self.on_quit_action, ["<primary>w"]),
            ("go_to_instrument", self.handle_go_to_instrument_action, ["<primary>i"]),
            ("previous_page", self.handle_previous_page_action, ["Page_Up"]),
            ("next_page", self.handle_next_page_action, ["Page_Down"]),
            ("mute", self.handle_mute, ["<primary>m"]),
        ]

        for action_name, callback, shortcuts in actions:
            self._create_action(action_name, callback, shortcuts)

    def _create_action(self, name, callback, shortcuts=None):
        """Create and register an action with optional keyboard shortcuts"""
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.window.add_action(action)
        if shortcuts:
            self.window.application.set_accels_for_action(f"win.{name}", shortcuts)

    # Action handlers
    def on_open_menu_action(self, action, param):
        self.window.menu_button.activate()

    def on_show_help_overlay(self, action, param):
        self.window.get_help_overlay().present()

    def handle_play_pause_action(self, action, param):
        self.window.handle_play_pause(self.window.play_pause_button)

    def handle_clear_action(self, action, param):
        self.window.handle_clear(self.window.clear_button)

    def increase_bpm_action(self, action, param):
        current_bpm = self.window.bpm_spin_button.get_value()
        self.window.bpm_spin_button.set_value(current_bpm + 1)

    def decrease_bpm_action(self, action, param):
        current_bpm = self.window.bpm_spin_button.get_value()
        self.window.bpm_spin_button.set_value(current_bpm - 1)

    def increase_volume_action(self, action, param):
        current_volume = self.window.volume_button.get_value()
        self.window.volume_button.set_value(min(current_volume + 5, 100))

    def decrease_volume_action(self, action, param):
        current_volume = self.window.volume_button.get_value()
        self.window.volume_button.set_value(max(current_volume - 5, 0))

    def on_open_file_action(self, action, param):
        self.window.on_open_file(self.window.file_preset_button)

    def on_save_preset_action(self, action, param):
        self.window.on_save_preset()

    def on_export_audio_action(self, action, param):
        self.window._on_export_audio_clicked(self.window.export_audio_button)

    def on_random_beats_action(self, action, param):
        from ..dialogs.random_beats_dialog import RandomBeatsDialog
        dialog = RandomBeatsDialog(self.window)
        dialog.present(self.window)

    def on_quit_action(self, action, param):
        if self.window.save_changes_service.has_unsaved_changes():
            self.window.save_changes_service.prompt_save_changes(
                on_save=self.window._save_and_close,
                on_discard=self.window.cleanup_and_destroy,
            )
        else:
            self.window.cleanup_and_destroy()

    def handle_go_to_instrument_action(self, action, param):
        """Go to the currently focused instrument button."""
        if hasattr(self.window, "carousel"):
            # Find which drum part is currently focused
            focused_widget = self.window.get_focus()
            if focused_widget:
                widget_name = focused_widget.get_name()
                if widget_name and "_toggle_" in widget_name:
                    drum_part = widget_name.split("_toggle_")[0]
                    try:
                        instrument_button = getattr(
                            self.window, f"{drum_part}_instrument_button"
                        )
                        instrument_button.grab_focus()
                    except AttributeError:
                        pass

    def handle_previous_page_action(self, action, param):
        """Go to the previous page."""
        if hasattr(self.window, "carousel"):
            carousel = self.window.carousel
            current_page = carousel.get_position()
            if current_page > 0:
                carousel.scroll_to(carousel.get_nth_page(current_page - 1), True)

    def handle_next_page_action(self, action, param):
        """Go to the next page."""
        if hasattr(self.window, "carousel"):
            carousel = self.window.carousel
            current_page = carousel.get_position()
            n_pages = carousel.get_n_pages()
            if current_page < n_pages - 1:
                carousel.scroll_to(carousel.get_nth_page(current_page + 1), True)

    def handle_mute(self, action, param):
        current_volume = self.window.volume_button.get_value()
        last_volume = self.window.drum_machine_service.last_volume
        if current_volume == 0:
            self.window.volume_button.set_value(last_volume)
        else:
            self.window.volume_button.set_value(0)
