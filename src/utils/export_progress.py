# utils/export_progress.py
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

import threading
import time
from enum import Enum
from gi.repository import GLib
from gettext import gettext as _
from ..config.constants import PULSE_INTERVAL_SECONDS


class ExportPhase(Enum):
    PREPARING = "preparing"
    RENDERING = "rendering"
    SAVING = "saving"


class ExportProgressHandler:
    """Handles export progress updates and UI thread coordination"""

    def __init__(self, progress_bar, status_overlay, status_label, detail_label):
        self.progress_bar = progress_bar
        self.status_overlay = status_overlay
        self.status_label = status_label
        self.detail_label = detail_label

        self.pulse_thread = None
        self.pulse_stop_event = None
        self.is_active = False

    def start_progress_tracking(self):
        """Start showing progress UI and pulse updates"""
        self.is_active = True
        self.progress_bar.set_visible(True)
        self.status_overlay.set_visible(True)
        self._start_pulse_thread()

    def stop_progress_tracking(self):
        """Stop progress tracking and hide UI"""
        self.is_active = False
        self.progress_bar.set_visible(False)
        self.status_overlay.set_visible(False)
        self._stop_pulse_thread()

    def update_phase(self, phase: ExportPhase):
        """Update the progress UI for the current export phase"""

        def update_ui():
            self.progress_bar.pulse()

            if phase == ExportPhase.PREPARING:
                self.status_label.set_label(_("Preparing..."))
                self.detail_label.set_label(_("Initializing..."))
            elif phase == ExportPhase.RENDERING:
                self.status_label.set_label(_("Rendering audio..."))
                self.detail_label.set_label(_("Processing beats..."))
            elif phase == ExportPhase.SAVING:
                self.status_label.set_label(_("Saving file..."))
                self.detail_label.set_label(_("Writing to disk..."))
            else:
                self.status_label.set_label(_("Exporting..."))
                self.detail_label.set_label(_("Processing..."))

        GLib.idle_add(update_ui)

    def _start_pulse_thread(self):
        """Start background thread for progress bar pulsing"""
        if self.pulse_thread and self.pulse_thread.is_alive():
            return

        self.pulse_stop_event = threading.Event()

        def pulse_worker():
            while not self.pulse_stop_event.is_set() and self.is_active:
                GLib.idle_add(self.progress_bar.pulse)
                time.sleep(PULSE_INTERVAL_SECONDS)

        self.pulse_thread = threading.Thread(target=pulse_worker, daemon=True)
        self.pulse_thread.start()

    def _stop_pulse_thread(self):
        """Stop the pulse thread"""
        if self.pulse_stop_event:
            self.pulse_stop_event.set()
        if self.pulse_thread and self.pulse_thread.is_alive():
            self.pulse_thread.join(timeout=1.1)


class ExportTask:
    """Manages the background export operation"""

    def __init__(self, audio_export_service, progress_handler: ExportProgressHandler):
        self.audio_export_service = audio_export_service
        self.progress_handler = progress_handler
        self.export_thread = None
        self.is_cancelled = False
        self.current_process = None

    def start_export(
        self,
        drum_parts_state,
        bpm,
        filename,
        repeat_count,
        metadata,
        completion_callback,
    ):
        """Start the export process in a background thread"""
        if self.export_thread and self.export_thread.is_alive():
            return False

        self.is_cancelled = False
        self.progress_handler.start_progress_tracking()

        self.export_thread = threading.Thread(
            target=self._export_worker,
            args=(
                drum_parts_state,
                bpm,
                filename,
                repeat_count,
                metadata,
                completion_callback,
            ),
            daemon=True,
        )
        self.export_thread.start()
        return True

    def cancel_export(self):
        """Cancel the ongoing export"""
        self.is_cancelled = True

        # Kill running process immediately
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.kill()
            except Exception:
                pass

        self.progress_handler.stop_progress_tracking()

    def _export_worker(
        self,
        drum_parts_state,
        bpm,
        filename,
        repeat_count,
        metadata,
        completion_callback,
    ):
        """Background worker for the export process"""
        try:
            if self.is_cancelled:
                return

            success = self.audio_export_service.export_audio(
                drum_parts_state,
                bpm,
                filename,
                progress_callback=self.progress_handler.update_phase,
                repeat_count=repeat_count,
                metadata=metadata,
                export_task=self,
            )

            if not self.is_cancelled:
                GLib.idle_add(completion_callback, success, filename)
        except Exception as e:
            print(f"Export error: {e}")
            if not self.is_cancelled:
                GLib.idle_add(completion_callback, False, filename)
        finally:
            self.progress_handler.stop_progress_tracking()
