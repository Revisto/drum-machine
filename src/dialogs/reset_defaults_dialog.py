# dialogs/reset_defaults_dialog.py
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

from gi.repository import Adw, Gtk


@Gtk.Template(
    resource_path="/io/github/revisto/drum-machine/gtk/reset-defaults-dialog.ui"
)
class ResetDefaultsDialog(Adw.AlertDialog):
    __gtype_name__ = "ResetDefaultsDialog"

    def __init__(self, window, on_reset_callback=None):
        super().__init__()
        self._on_reset_callback = on_reset_callback
        self.present(window)

    @Gtk.Template.Callback()
    def _on_reset(self, _dialog, _response):
        if callable(self._on_reset_callback):
            self._on_reset_callback()
        self.close()

    @Gtk.Template.Callback()
    def _on_cancel(self, _dialog, _response):
        self.close()
