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
# MERCHANTABILITY or FITNESS FOR ANY PURPOSE.  See the
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
from .audio_export_progress_dialog import AudioExportProgressDialog


@Gtk.Template(
    resource_path="/io/github/revisto/drum-machine/gtk/audio-export-dialog.ui"
)
class AudioExportDialog(Adw.Dialog):
    """Dialog for exporting audio with progress tracking"""

    __gtype_name__ = "AudioExportDialog"

    # Template children
    export_button = Gtk.Template.Child()
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
        self.cover_art_path = None
        self.progress_dialog = None

        # Define format configuration
        self.format_config = {
            0: {"ext": ".ogg", "pattern": "*.ogg", "name": _("OGG files"), "display": _("OGG Vorbis"), "supports_metadata": True},
            1: {"ext": ".mp3", "pattern": "*.mp3", "name": _("MP3 files"), "display": _("MP3"), "supports_metadata": True},
            2: {"ext": ".flac", "pattern": "*.flac", "name": _("FLAC files"), "display": _("FLAC (Lossless)"), "supports_metadata": True},
            3: {"ext": ".wav", "pattern": "*.wav", "name": _("WAV files"), "display": _("WAV (Uncompressed)"), "supports_metadata": False},
        }

        self._populate_format_list()
        self._setup_defaults()
        self._connect_signals()
        self._update_metadata_sensitivity()

    def _populate_format_list(self):
        """Populate the format dropdown with available formats"""
        for index in sorted(self.format_config.keys()):
            format_info = self.format_config[index]
            self.format_list.append(format_info["display"])

    def _setup_defaults(self):
        """Set up default values for metadata fields"""
        # Set default artist name to system username
        try:
            system_username = getpass.getuser()
            self.artist_row.set_text(system_username)
        except Exception:
            pass  # Keep field empty if unable to get username

    def _connect_signals(self):
        """Connect UI signals"""
        self.export_button.connect("clicked", self._on_export_clicked)
        self.cover_button.connect("clicked", self._on_cover_button_clicked)
        self.format_row.connect("notify::selected", self._on_format_changed)

    def _create_file_dialog_with_format(self, selected_format):
        """Create file dialog with format-specific filter"""
        info = self.format_config.get(selected_format, self.format_config[0])
        
        file_filter = Gtk.FileFilter.new()
        file_filter.add_pattern(info["pattern"])
        file_filter.set_name(info["name"])

        filefilters = Gio.ListStore.new(Gtk.FileFilter)
        filefilters.append(file_filter)

        dialog = Gtk.FileDialog.new()
        dialog.set_title(_("Save Audio File"))
        dialog.set_filters(filefilters)
        dialog.set_modal(True)
        dialog.set_initial_name(self.suggested_filename + info["ext"])

        return dialog, info["ext"]

    def _format_supports_metadata(self, format_index):
        """Check if the selected format supports metadata"""
        return self.format_config.get(format_index, {}).get("supports_metadata", False)

    def _update_metadata_sensitivity(self):
        """Update metadata fields sensitivity based on selected format"""
        selected_format = self.format_row.get_selected()
        metadata_enabled = self._format_supports_metadata(selected_format)
        
        self.artist_row.set_sensitive(metadata_enabled)
        self.song_row.set_sensitive(metadata_enabled)
        self.cover_row.set_sensitive(metadata_enabled)
        self.cover_button.set_sensitive(metadata_enabled)

    def _on_format_changed(self, combo_row, pspec):
        """Handle format selection change to enable/disable metadata fields"""
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
        dialog.set_modal(True)
        
        dialog.open(parent=self.parent_window, callback=self._on_cover_selected)

    def _on_cover_selected(self, dialog, result):
        """Handle cover art file selection"""
        try:
            file = dialog.open_finish(result)
            if file:
                self.cover_art_path = file.get_path()
                filename = os.path.basename(self.cover_art_path)
                self.cover_button.set_label(filename[:20] + "..." if len(filename) > 20 else filename)
        except GLib.Error:
            pass

    def _on_export_clicked(self, button):
        """Handle export button click"""
        # Check if pattern has any active beats
        has_beats = False
        for part_state in self.drum_parts_state.values():
            if any(part_state.values()):
                has_beats = True
                break

        if not has_beats:
            self._show_parent_toast(_("Pattern is empty - nothing to export"))
            return

        # Get selected format and create file dialog with format-specific filter
        selected_format = self.format_row.get_selected()
        dialog, expected_ext = self._create_file_dialog_with_format(selected_format)
        
        dialog.save(parent=self.parent_window, callback=self._on_file_selected)

    def _on_file_selected(self, dialog, result):
        """Handle file selection from save dialog"""
        try:
            file = dialog.save_finish(result)
            if file:
                filename = file.get_path()
                
                self._start_export(filename)
        except GLib.Error:
            pass

    def _start_export(self, filename):
        """Start the export process"""
        repeat_count = int(self.repeat_row.get_value())
        
        # Get metadata from fields
        metadata = {
            "artist": self.artist_row.get_text().strip() or None,
            "title": self.song_row.get_text().strip() or None,
            "cover_art": self.cover_art_path
        }
        
        # Close export dialog
        self.close()
        
        # Create and show progress dialog
        self.progress_dialog = AudioExportProgressDialog(self.parent_window)
        self.progress_dialog.present(self.parent_window)
        
        # Start export process
        self.progress_dialog.start_export(
            self.audio_export_service,
            self.drum_parts_state,
            self.bpm,
            filename,
            repeat_count,
            metadata
        )



    def present(self, parent_window=None):
        """Present the dialog"""
        if parent_window:
            self.parent_window = parent_window
        super().present(parent_window or self.parent_window)
