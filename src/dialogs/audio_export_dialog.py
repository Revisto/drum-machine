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
import threading
from gi.repository import Adw, Gtk, GLib, Gio
from gettext import gettext as _


@Gtk.Template(
    resource_path="/io/github/revisto/drum-machine/gtk/audio-export-dialog.ui"
)
class AudioExportDialog(Adw.Dialog):
    """Dialog for exporting audio with progress tracking"""

    __gtype_name__ = "AudioExportDialog"

    # Template children
    toast_overlay = Gtk.Template.Child()
    export_button = Gtk.Template.Child()
    file_entry = Gtk.Template.Child()
    browse_button = Gtk.Template.Child()
    format_row = Gtk.Template.Child()
    repeat_row = Gtk.Template.Child()
    progress_group = Gtk.Template.Child()
    progress_label = Gtk.Template.Child()
    progress_bar = Gtk.Template.Child()
    progress_spinner = Gtk.Template.Child()
    progress_phase_label = Gtk.Template.Child()
    progress_status_label = Gtk.Template.Child()

    def __init__(self, parent_window, audio_export_service, drum_parts_state, bpm):
        super().__init__()

        self.parent_window = parent_window
        self.audio_export_service = audio_export_service
        self.drum_parts_state = drum_parts_state
        self.bpm = bpm
        self.export_thread = None
        self.export_success = False
        self.suggested_filename = "drum_pattern"

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the user interface"""
        # Set default filename based on format
        self._update_filename_extension()

    def _connect_signals(self):
        """Connect UI signals"""
        self.export_button.connect("clicked", self._on_export_clicked)
        self.browse_button.connect("clicked", self._on_browse_clicked)
        self.format_row.connect("notify::selected", self._on_format_changed)

    def _on_format_changed(self, combo_row, pspec):
        """Handle format selection change"""
        self._update_filename_extension()

    def _update_filename_extension(self):
        """Update filename extension based on selected format"""
        current_text = self.file_entry.get_text()
        base_name = os.path.splitext(current_text)[0] or self.suggested_filename

        format_extensions = {
            0: ".wav",  # WAV (Uncompressed)
            1: ".flac",  # FLAC (Lossless)
            2: ".ogg",  # OGG Vorbis
            3: ".mp3",  # MP3
        }

        selected = self.format_row.get_selected()
        extension = format_extensions.get(selected, ".wav")
        new_filename = base_name + extension

        self.file_entry.set_text(new_filename)

    def _on_browse_clicked(self, button):
        """Handle browse button click"""
        # Create file filters
        wav_filter = Gtk.FileFilter.new()
        wav_filter.add_pattern("*.wav")
        wav_filter.set_name(_("WAV files"))

        flac_filter = Gtk.FileFilter.new()
        flac_filter.add_pattern("*.flac")
        flac_filter.set_name(_("FLAC files"))

        ogg_filter = Gtk.FileFilter.new()
        ogg_filter.add_pattern("*.ogg")
        ogg_filter.set_name(_("OGG files"))

        mp3_filter = Gtk.FileFilter.new()
        mp3_filter.add_pattern("*.mp3")
        mp3_filter.set_name(_("MP3 files"))

        all_audio_filter = Gtk.FileFilter.new()
        all_audio_filter.add_pattern("*.wav")
        all_audio_filter.add_pattern("*.flac")
        all_audio_filter.add_pattern("*.ogg")
        all_audio_filter.add_pattern("*.mp3")
        all_audio_filter.set_name(_("All audio files"))

        filefilters = Gio.ListStore.new(Gtk.FileFilter)
        filefilters.append(all_audio_filter)
        filefilters.append(wav_filter)
        filefilters.append(flac_filter)
        filefilters.append(ogg_filter)
        filefilters.append(mp3_filter)

        dialog = Gtk.FileDialog.new()
        dialog.set_title(_("Save Audio File"))
        dialog.set_filters(filefilters)
        dialog.set_modal(True)
        dialog.set_initial_name(self.file_entry.get_text())

        dialog.save(parent=self, callback=self._on_file_selected)

    def _on_file_selected(self, dialog, result):
        """Handle file selection"""
        try:
            file = dialog.save_finish(result)
            if file:
                file_path = file.get_path()
                self.file_entry.set_text(file_path)
        except GLib.Error:
            pass

    def _on_export_clicked(self, button):
        """Handle export button click"""
        filename = self.file_entry.get_text().strip()

        if not filename:
            self._show_toast(_("Please enter a filename"))
            return

        # Check if pattern has any active beats
        has_beats = False
        for part_state in self.drum_parts_state.values():
            if any(part_state.values()):
                has_beats = True
                break

        if not has_beats:
            self._show_toast(_("Pattern is empty - nothing to export"))
            return

        # Ensure file has correct extension
        selected_format = self.format_row.get_selected()
        format_extensions = [".wav", ".flac", ".ogg", ".mp3"]
        expected_ext = format_extensions[selected_format]

        if not filename.lower().endswith(expected_ext):
            filename += expected_ext
            self.file_entry.set_text(filename)

        # Check if file exists
        if os.path.exists(filename):
            self._confirm_overwrite(filename)
        else:
            self._start_export(filename)

    def _confirm_overwrite(self, filename):
        """Show confirmation dialog for file overwrite"""
        dialog = Adw.MessageDialog(
            heading=_("File Already Exists"),
            body=_("The file already exists. Do you want to replace it?"),
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("replace", _("Replace"))
        dialog.set_response_appearance("replace", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")

        dialog.connect(
            "response", lambda d, r: self._on_overwrite_response(d, r, filename)
        )
        dialog.set_transient_for(self.parent_window)
        dialog.present()

    def _on_overwrite_response(self, dialog, response, filename):
        """Handle overwrite confirmation response"""
        if response == "replace":
            self._start_export(filename)
        dialog.destroy()

    def _start_export(self, filename):
        """Start the export process"""
        # Show progress UI
        self.progress_group.set_visible(True)
        self.export_button.set_sensitive(False)
        self.progress_bar.set_fraction(0.0)
        self.progress_label.set_text("0%")
        self.progress_phase_label.set_text(_("Preparing export..."))
        self.progress_status_label.set_text(_("Initializing..."))
        self.progress_spinner.set_spinning(True)

        # Start export in background thread
        self.export_thread = threading.Thread(
            target=self._export_worker, args=(filename,), daemon=True
        )
        self.export_thread.start()

    def _export_worker(self, filename):
        """Background worker for audio export"""
        try:
            repeat_count = int(self.repeat_row.get_value())
            success = self.audio_export_service.export_audio(
                self.drum_parts_state,
                self.bpm,
                filename,
                repeat_count=repeat_count,
                progress_callback=self._on_progress_update,
            )

            GLib.idle_add(self._on_export_complete, success, filename)

        except Exception as e:
            print(f"Export error: {e}")
            GLib.idle_add(self._on_export_complete, False, filename)

    def _on_progress_update(self, progress):
        """Update progress bar"""
        self.progress_bar.set_fraction(progress)
        percentage = int(progress * 100)
        self.progress_label.set_text(f"{percentage}%")

        # Update phase label and status based on progress
        if progress < 0.1:
            self.progress_phase_label.set_text(_("Preparing export..."))
            self.progress_status_label.set_text(_("Initializing..."))
        elif progress < 0.9:
            self.progress_phase_label.set_text(_("Rendering audio..."))
            self.progress_status_label.set_text(_("Processing beats..."))
        else:
            self.progress_phase_label.set_text(_("Saving file..."))
            self.progress_status_label.set_text(_("Writing to disk..."))

    def _on_export_complete(self, success, filename):
        """Handle export completion"""
        self.progress_spinner.set_spinning(False)
        self.progress_group.set_visible(False)
        self.export_button.set_sensitive(True)

        if success:
            self._show_toast(_("Audio exported successfully"))
            self.close()
        else:
            self._show_toast(_("Export failed"))

    def _show_toast(self, message):
        """Show a toast notification"""
        toast = Adw.Toast(title=message, timeout=3)
        self.toast_overlay.add_toast(toast)

    def present(self, parent_window=None):
        """Present the dialog"""
        if parent_window:
            self.parent_window = parent_window
        super().present(parent_window or self.parent_window)
