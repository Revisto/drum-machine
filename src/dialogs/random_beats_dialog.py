# dialogs/random_beats_dialog.py
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
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk
from gettext import gettext as _


@Gtk.Template(
    resource_path="/io/github/revisto/drum-machine/gtk/random-beats-dialog.ui"
)
class RandomBeatsDialog(Adw.Dialog):
    """Dialog for generating random beats based on a density percentage."""

    __gtype_name__ = "RandomBeatsDialog"

    # Template children
    density_scale = Gtk.Template.Child()
    density_value_label = Gtk.Template.Child()
    generate_button = Gtk.Template.Child()
    cancel_button = Gtk.Template.Child()

    def __init__(self, parent_window):
        super().__init__()

        self.parent_window = parent_window

        self._connect_signals()
        self._sync_density_label()

    def _connect_signals(self):
        self.density_scale.connect("value-changed", self._on_density_changed)
        self.generate_button.connect("clicked", self._on_generate_clicked)
        self.cancel_button.connect("clicked", self._on_cancel_clicked)

    def _sync_density_label(self):
        value = int(self.density_scale.get_value())
        self.density_value_label.set_text(f"{value}%")

    def _on_density_changed(self, scale):
        self._sync_density_label()

    def _on_generate_clicked(self, _button):
        density_percent = int(self.density_scale.get_value())

        # Generate random pattern via service
        service = self.parent_window.drum_machine_service
        service.randomize_pattern(density_percent)

        # Update UI to reflect new pattern length and toggles
        service.update_total_beats()
        self.parent_window.drum_grid_builder.reset_carousel_pages()
        # Clear all toggles first, then apply
        self.parent_window.ui_helper.deactivate_all_toggles_in_ui()
        self.parent_window.ui_helper.load_pattern_into_ui(service.drum_parts_state)

        # Mark as unsaved
        self.parent_window.save_changes_service.mark_unsaved_changes(True)

        # Give user feedback and close
        self.parent_window.show_toast(
            _("Generated random beats at {}% density").format(density_percent)
        )
        self.close()

    def _on_cancel_clicked(self, _button):
        self.close()
