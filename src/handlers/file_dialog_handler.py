# handlers/file_dialog_handler.py
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
gi.require_version("Gio", "2.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gio, GLib, Adw
from gettext import gettext as _
from ..config.constants import DEFAULT_PATTERNS, SUPPORTED_INPUT_AUDIO_FORMATS
from ..dialogs.audio_export_dialog import AudioExportDialog


class FileDialogHandler:
    """Handles file dialogs and pattern management"""

    def __init__(self, window):
        self.window = window
        self.filename = None

    def setup_pattern_menu(self):
        """Setup the pattern menu with default patterns"""
        menu = Gio.Menu.new()
        section = Gio.Menu.new()

        for pattern in DEFAULT_PATTERNS:
            item = Gio.MenuItem.new(pattern, "win.load-pattern")
            item.set_action_and_target_value(
                "win.load-pattern", GLib.Variant.new_string(pattern)
            )
            section.append_item(item)

        menu.append_section(_("Default Patterns"), section)

        pattern_action = Gio.SimpleAction.new("load-pattern", GLib.VariantType.new("s"))
        pattern_action.connect("activate", self.on_pattern_selected)
        self.window.add_action(pattern_action)

        self.window.file_pattern_button.set_menu_model(menu)

    def handle_open_file(self):
        """Handle opening a file with unsaved changes check"""
        if self.window.save_changes_service.has_unsaved_changes():
            self.window.save_changes_service.prompt_save_changes(
                on_save=self._save_and_open_file, on_discard=self._open_file_directly
            )
        else:
            self._open_file_directly()

    def handle_save_pattern(self):
        """Handle saving a pattern"""
        self.show_save_dialog()

    def handle_export_audio(self):
        """Handle audio export"""
        # Check if pattern has any active beats
        has_active_beats = any(
            any(beats.values())
            for beats in self.window.drum_machine_service.drum_parts_state.values()
        )

        if not has_active_beats:
            # Show error dialog
            dialog = Adw.AlertDialog.new(
                _("No Pattern"),
                _("Please create a drum pattern before exporting audio."),
            )
            dialog.add_response("ok", _("_OK"))
            dialog.set_default_response("ok")
            dialog.set_close_response("ok")
            dialog.present(self.window)
            return

        # Show export dialog
        export_dialog = AudioExportDialog(
            self.window,
            self.window.audio_export_service,
            self.window.drum_machine_service.drum_parts_state,
            self.window.drum_machine_service.bpm,
            self.filename,
        )
        export_dialog.present(self.window)

    def _save_and_open_file(self):
        self.show_save_dialog(self._open_file_directly)

    def _open_file_directly(self):
        """Show file open dialog"""
        filefilter = Gtk.FileFilter.new()
        filefilter.add_pattern("*.mid")
        filefilter.set_name(_("MIDI files"))

        filefilters = Gio.ListStore.new(Gtk.FileFilter)
        filefilters.append(filefilter)

        dialog = Gtk.FileDialog.new()
        dialog.set_title(_("Open MIDI File"))
        dialog.set_filters(filefilters)
        dialog.set_modal(True)

        dialog.open(parent=self.window, callback=self._handle_file_response)

    def _handle_file_response(self, dialog, response):
        """Handle file dialog response"""
        try:
            file = dialog.open_finish(response)
            if file:
                # Load the pattern data into the service
                self.window.drum_machine_service.load_pattern(file.get_path())
                # Update the UI to reflect the new pattern structure
                self.window.drum_machine_service.update_total_beats()
                self.window.drum_grid_builder.reset_carousel_pages()
                self.window.ui_helper.load_pattern_into_ui(
                    self.window.drum_machine_service.drum_parts_state
                )
                self.filename = self._get_filename_without_extension(file)

                self.window.save_changes_service.mark_unsaved_changes(False)
        except GLib.Error:
            return

    def on_pattern_selected(self, action, parameter):
        """Handle pattern selection from menu"""
        if self.window.save_changes_service.has_unsaved_changes():
            self.window.save_changes_service.prompt_save_changes(
                on_save=lambda: self._save_and_open_pattern(parameter),
                on_discard=lambda: self._open_pattern_directly(parameter),
            )
        else:
            self._open_pattern_directly(parameter)

    def _save_and_open_pattern(self, parameter):
        self.show_save_dialog(lambda: self._open_pattern_directly(parameter))

    def _open_pattern_directly(self, parameter):
        """Load a pattern directly"""
        pattern_name = parameter.get_string()
        pattern_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "patterns"
        )
        file_path = os.path.join(pattern_dir, f"{pattern_name}.mid")

        # Load the pattern data into the service
        self.window.drum_machine_service.load_pattern(file_path)
        # Update the UI to reflect the new pattern structure
        self.window.drum_machine_service.update_total_beats()
        self.window.drum_grid_builder.reset_carousel_pages()
        self.window.ui_helper.load_pattern_into_ui(
            self.window.drum_machine_service.drum_parts_state
        )
        self.filename = None

        self.window.save_changes_service.mark_unsaved_changes(False)

    def show_save_dialog(self, after_save_callback=None):
        """Show save file dialog"""
        filefilter = Gtk.FileFilter.new()
        filefilter.add_pattern("*.mid")
        filefilter.set_name(_("MIDI files"))

        filefilters = Gio.ListStore.new(Gtk.FileFilter)
        filefilters.append(filefilter)

        initial_name = f"{self.filename or 'new_sequence'}.mid"

        dialog = Gtk.FileDialog.new()
        dialog.set_title(_("Save Sequence"))
        dialog.set_filters(filefilters)
        dialog.set_modal(True)
        dialog.set_initial_name(initial_name)

        def save_callback(dialog, result):
            try:
                file = dialog.save_finish(result)
                if file:
                    file_path = file.get_path()
                    if not file_path.endswith(".mid"):
                        file_path += ".mid"
                    self.window.drum_machine_service.save_pattern(file_path)
                    self.window.save_changes_service.mark_unsaved_changes(False)
                    self.filename = self._get_filename_without_extension(file)
                    if after_save_callback:
                        after_save_callback()
            except GLib.Error:
                return

        dialog.save(parent=self.window, callback=save_callback)

    def handle_add_samples(self):
        """Handle adding multiple audio samples via file dialog"""
        self.open_audio_file_chooser(
            _("Add Audio Samples"),
            self._handle_samples_response_callback,
            multiple=True,
        )

    def _handle_samples_response_callback(self, files, *args):
        """Handle multiple audio files selection response"""
        if files and len(files) > 0:
            # Use existing multiple files handler
            self.window.drag_drop_handler.handle_multiple_files_drop(files, None)

    def open_audio_file_chooser(self, title, callback, *args, multiple=False):
        """Open a file chooser for audio files

        Args:
            title (str): Dialog title
            callback (callable): Function to call with selected file(s)
            *args: Additional arguments to pass to callback
            multiple (bool): Whether to allow multiple file selection
        """
        # Create file filter for supported audio formats
        audio_filter = Gtk.FileFilter.new()
        audio_filter.set_name(_("Audio files"))

        # Add supported formats
        for fmt in SUPPORTED_INPUT_AUDIO_FORMATS:
            audio_filter.add_pattern(f"*{fmt}")

        filefilters = Gio.ListStore.new(Gtk.FileFilter)
        filefilters.append(audio_filter)

        dialog = Gtk.FileDialog.new()
        dialog.set_title(title)
        dialog.set_filters(filefilters)
        dialog.set_modal(True)

        def internal_callback(dialog, result):
            try:
                if multiple:
                    files = dialog.open_multiple_finish(result)
                    if files and files.get_n_items() > 0:
                        # Convert to list of Gio.File objects
                        file_list = [
                            files.get_item(i) for i in range(files.get_n_items())
                        ]
                        callback(file_list, *args)
                else:
                    file = dialog.open_finish(result)
                    if file:
                        callback(file.get_path(), *args)
            except GLib.Error:
                return

        if multiple:
            dialog.open_multiple(parent=self.window, callback=internal_callback)
        else:
            dialog.open(parent=self.window, callback=internal_callback)

    def _get_filename_without_extension(self, file):
        """Extract filename without extension from Gio.File"""
        base_name = file.get_basename()
        return os.path.splitext(base_name)[0]
