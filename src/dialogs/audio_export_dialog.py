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
    export_button = Gtk.Template.Child()
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
        self.suggested_filename = "new_beat"

        self._connect_signals()

    def _connect_signals(self):
        """Connect UI signals"""
        self.export_button.connect("clicked", self._on_export_clicked)

    def _create_file_dialog_with_format(self, selected_format):
        """Create file dialog with format-specific filter"""
        format_info = {
            0: {"ext": ".wav", "pattern": "*.wav", "name": _("WAV files")},
            1: {"ext": ".flac", "pattern": "*.flac", "name": _("FLAC files")},
            2: {"ext": ".ogg", "pattern": "*.ogg", "name": _("OGG files")},
            3: {"ext": ".mp3", "pattern": "*.mp3", "name": _("MP3 files")},
        }

        info = format_info.get(selected_format, format_info[0])
        
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
                
                # Check if file exists
                if os.path.exists(filename):
                    self._confirm_overwrite(filename)
                else:
                    self._start_export(filename)
        except GLib.Error:
            pass

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
            # Show advanced toast with Open button
            self._show_parent_toast_with_action(
                _("Audio exported to {}").format(os.path.basename(filename)), filename
            )
            self.close()
        else:
            self._show_parent_toast(
                _("Export failed - check file permissions and format support")
            )

    def _show_parent_toast(self, message):
        """Show a toast notification on the parent window"""
        self.parent_window.show_toast(message)

    def _show_parent_toast_with_action(self, message, file_path):
        """Show a toast with open action on the parent window"""
        self.parent_window.show_toast(message, open_file=True, file_path=file_path)

    def present(self, parent_window=None):
        """Present the dialog"""
        if parent_window:
            self.parent_window = parent_window
        super().present(parent_window or self.parent_window)
