# dialogs/audio_export_dialog.py
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
import getpass
from gi.repository import Adw, Gtk, GLib, Gio
from gettext import gettext as _

from ..utils.export_progress import ExportProgressHandler, ExportTask


@Gtk.Template(
    resource_path="/io/github/revisto/drum-machine/gtk/audio-export-dialog.ui"
)
class AudioExportDialog(Adw.Dialog):
    """Dialog for exporting audio with progress tracking"""

    __gtype_name__ = "AudioExportDialog"

    # Template children
    progress_bar = Gtk.Template.Child()
    status_overlay = Gtk.Template.Child()
    status_label = Gtk.Template.Child()
    detail_label = Gtk.Template.Child()
    export_button = Gtk.Template.Child()
    cancel_button = Gtk.Template.Child()
    format_row = Gtk.Template.Child()
    format_list = Gtk.Template.Child()
    repeat_row = Gtk.Template.Child()
    artist_row = Gtk.Template.Child()
    song_row = Gtk.Template.Child()
    cover_row = Gtk.Template.Child()
    cover_button = Gtk.Template.Child()

    def __init__(self, parent_window, audio_export_service, drum_parts_state, bpm):
        super().__init__()

        self.parent_window = parent_window
        self.audio_export_service = audio_export_service
        self.drum_parts_state = drum_parts_state
        self.bpm = bpm
        self.suggested_filename = "new_beat"

        # Initialize components
        self.metadata_manager = ExportMetadata(
            self.artist_row, self.song_row, self.cover_row, self.cover_button
        )
        self.progress_handler = ExportProgressHandler(
            self.progress_bar, self.status_overlay, self.status_label, self.detail_label
        )
        self.export_task = ExportTask(audio_export_service, self.progress_handler)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Initialize the UI components"""
        self._populate_format_list()
        self._update_metadata_sensitivity()

    def _populate_format_list(self):
        """Populate the format dropdown with available formats"""
        formats = self.audio_export_service.format_registry.get_all_formats()
        for format_id in sorted(formats.keys()):
            format_info = formats[format_id]
            self.format_list.append(format_info.display)

    def _connect_signals(self):
        """Connect UI signals"""
        self.export_button.connect("clicked", self._on_export_clicked)
        self.cancel_button.connect("clicked", self._on_cancel_clicked)
        self.cover_button.connect("clicked", self._on_cover_button_clicked)
        self.format_row.connect("notify::selected", self._on_format_changed)
        self.connect("closed", self._on_dialog_closed)

    def _create_file_dialog_with_format(self, selected_format):
        """Create file dialog with format-specific filter"""
        info = self.audio_export_service.format_registry.get_format(selected_format)

        file_filter = Gtk.FileFilter.new()
        file_filter.add_pattern(info.pattern)
        file_filter.set_name(info.name)

        filefilters = Gio.ListStore.new(Gtk.FileFilter)
        filefilters.append(file_filter)

        dialog = Gtk.FileDialog.new()
        dialog.set_title(_("Save Audio File"))
        dialog.set_filters(filefilters)
        dialog.set_initial_name(self.suggested_filename + info.ext)

        return dialog

    def _update_metadata_sensitivity(self):
        """Update metadata fields sensitivity based on selected format"""
        selected_format = self.format_row.get_selected()
        format_info = self.audio_export_service.format_registry.get_format(
            selected_format
        )
        self.metadata_manager.set_sensitivity(format_info.supports_metadata)

    def _on_format_changed(self, combo_row, pspec):
        """Handle format selection change"""
        self._update_metadata_sensitivity()

    def _on_cover_button_clicked(self, button):
        """Handle cover art file selection"""
        image_filter = Gtk.FileFilter.new()
        image_filter.add_pattern("*.png")
        image_filter.add_pattern("*.jpg")
        image_filter.add_pattern("*.jpeg")
        image_filter.set_name(_("Image files"))

        filefilters = Gio.ListStore.new(Gtk.FileFilter)
        filefilters.append(image_filter)

        dialog = Gtk.FileDialog.new()
        dialog.set_title(_("Select Cover Art"))
        dialog.set_filters(filefilters)

        dialog.open(parent=self.parent_window, callback=self._on_cover_selected)

    def _on_cover_selected(self, dialog, result):
        """Handle cover art file selection result"""
        try:
            file = dialog.open_finish(result)
            if file:
                self.metadata_manager.set_cover_art(file.get_path())
        except GLib.Error:
            pass

    def _on_export_clicked(self, button):
        """Handle export button click"""
        selected_format = self.format_row.get_selected()
        dialog = self._create_file_dialog_with_format(selected_format)
        dialog.save(parent=self.parent_window, callback=self._on_file_selected)

    def _on_file_selected(self, dialog, result):
        """Handle file selection from save dialog"""
        try:
            file = dialog.save_finish(result)
            if file:
                self._start_export(file.get_path())
        except GLib.Error:
            pass

    def _start_export(self, filename):
        """Start the export process"""
        repeat_count = int(self.repeat_row.get_value())
        metadata = self.metadata_manager.get_metadata()

        self._disable_export_controls()

        self.export_task.start_export(
            self.drum_parts_state,
            self.bpm,
            filename,
            repeat_count,
            metadata,
            self._on_export_complete,
        )

    def _disable_export_controls(self):
        """Disable export controls during export"""
        self.format_row.set_sensitive(False)
        self.repeat_row.set_sensitive(False)
        self.metadata_manager.set_sensitivity(False)
        self.export_button.set_visible(False)
        self.cancel_button.set_visible(True)

    def _on_export_complete(self, success, filename):
        """Handle export completion"""
        if success:
            self.parent_window.show_toast(
                _("Audio exported to {}").format(os.path.basename(filename)),
                open_file=True,
                file_path=filename,
            )
        else:
            self.parent_window.show_toast(_("Export failed"))

        self.close()

    def _on_cancel_clicked(self, button):
        """Handle cancel button click"""
        self.export_task.cancel_export()
        self.parent_window.show_toast(_("Export cancelled successfully"))
        self.close()

    def _on_dialog_closed(self, dialog):
        """Handle dialog close - cancel export if still running"""
        self.export_task.cancel_export()
        self.progress_handler.stop_progress_tracking()


class ExportMetadata:
    """Manages export metadata fields"""

    def __init__(self, artist_row, song_row, cover_row, cover_button):
        self.artist_row = artist_row
        self.song_row = song_row
        self.cover_row = cover_row
        self.cover_button = cover_button
        self.cover_art_path = None

        self._setup_defaults()

    def _setup_defaults(self):
        """Set up default values for metadata fields"""
        try:
            system_username = getpass.getuser()
            self.artist_row.set_text(system_username)
        except Exception:
            pass

    def get_metadata(self):
        """Get the current metadata as a dictionary"""
        return {
            "artist": self.artist_row.get_text().strip() or None,
            "title": self.song_row.get_text().strip() or None,
            "cover_art": self.cover_art_path,
        }

    def set_cover_art(self, file_path):
        """Set the cover art path and update UI"""
        self.cover_art_path = file_path
        if file_path:
            filename = os.path.basename(file_path)
            display_name = filename[:20] + "..." if len(filename) > 20 else filename
            self.cover_button.set_label(display_name)

    def set_sensitivity(self, sensitive: bool):
        """Enable or disable metadata fields"""
        self.artist_row.set_sensitive(sensitive)
        self.song_row.set_sensitive(sensitive)
        self.cover_row.set_sensitive(sensitive)
        self.cover_button.set_sensitive(sensitive)
