# dialogs/audio_export_progress_dialog.py
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
import threading
from gi.repository import Adw, Gtk, GLib
from gettext import gettext as _


@Gtk.Template(
    resource_path="/io/github/revisto/drum-machine/gtk/audio-export-progress-dialog.ui"
)
class AudioExportProgressDialog(Adw.Dialog):
    __gtype_name__ = "AudioExportProgressDialog"

    # Template children
    status_label = Gtk.Template.Child()
    progress_bar = Gtk.Template.Child()
    detail_label = Gtk.Template.Child()

    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.export_cancelled = False
        self.export_thread = None
        
        # Connect close signal to handle cancellation
        self.connect("closed", self._on_dialog_closed)
        
    def start_export(self, audio_export_service, drum_parts_state, bpm, filename, repeat_count=1, metadata=None):
        """Start the export process"""
        self.progress_bar.set_fraction(0.0)
        self.status_label.set_label(_("Preparing export..."))
        self.detail_label.set_label(_("This may take a few moments..."))
        
        # Start export in background thread
        self.export_thread = threading.Thread(
            target=self._export_worker, 
            args=(audio_export_service, drum_parts_state, bpm, filename, repeat_count, metadata), 
            daemon=True
        )
        self.export_thread.start()

    def _export_worker(self, audio_export_service, drum_parts_state, bpm, filename, repeat_count, metadata):
        """Background worker for audio export"""
        try:
            if self.export_cancelled:
                return
                
            success = audio_export_service.export_audio(
                drum_parts_state,
                bpm,
                filename,
                repeat_count=repeat_count,
                progress_callback=self._on_progress_update,
                metadata=metadata
            )
            
            if not self.export_cancelled:
                GLib.idle_add(self._on_export_complete, success, filename)
        except Exception as e:
            print(f"Export error: {e}")
            if not self.export_cancelled:
                GLib.idle_add(self._on_export_complete, False, filename)

    def _on_progress_update(self, progress):
        """Update progress bar from main thread"""
        GLib.idle_add(self._update_progress_ui, progress)

    def _update_progress_ui(self, progress):
        """Update progress UI elements"""
        if self.export_cancelled:
            return
            
        self.progress_bar.set_fraction(progress)
        percentage = int(progress * 100)
        self.progress_bar.set_text(f"{percentage}%")

        # Update status based on progress
        if progress < 0.1:
            self.status_label.set_label(_("Preparing export..."))
            self.detail_label.set_label(_("Initializing..."))
        elif progress < 0.9:
            self.status_label.set_label(_("Rendering audio..."))
            self.detail_label.set_label(_("Processing beats..."))
        else:
            self.status_label.set_label(_("Saving file..."))
            self.detail_label.set_label(_("Writing to disk..."))

    def _on_export_complete(self, success, filename):
        """Handle export completion"""
        if success:
            self._show_parent_toast_with_action(
                _("Audio exported to {}").format(os.path.basename(filename)), filename
            )
        else:
            self._show_parent_toast(
                _("Export failed")
            )
        self.close()

    def _show_parent_toast(self, message):
        """Show a toast notification on the parent window"""
        if hasattr(self.parent_window, 'show_toast'):
            self.parent_window.show_toast(message)

    def _show_parent_toast_with_action(self, message, file_path):
        """Show a toast with open action on the parent window"""
        if hasattr(self.parent_window, 'show_toast'):
            self.parent_window.show_toast(message, open_file=True, file_path=file_path)

    def _on_dialog_closed(self, dialog):
        """Handle dialog close - cancel export if still running"""
        if not self.export_cancelled and self.export_thread and self.export_thread.is_alive():
            self.export_cancelled = True
            self._show_parent_toast(_("Export cancelled"))
