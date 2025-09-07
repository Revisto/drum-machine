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
from ..config.constants import DRUM_PARTS


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
    per_part_group = Gtk.Template.Child()
    # Per-part widgets from UI
    kick_override_switch = Gtk.Template.Child()
    kick_scale = Gtk.Template.Child()
    kick_value_label = Gtk.Template.Child()
    kick_2_override_switch = Gtk.Template.Child()
    kick_2_scale = Gtk.Template.Child()
    kick_2_value_label = Gtk.Template.Child()
    kick_3_override_switch = Gtk.Template.Child()
    kick_3_scale = Gtk.Template.Child()
    kick_3_value_label = Gtk.Template.Child()
    snare_override_switch = Gtk.Template.Child()
    snare_scale = Gtk.Template.Child()
    snare_value_label = Gtk.Template.Child()
    snare_2_override_switch = Gtk.Template.Child()
    snare_2_scale = Gtk.Template.Child()
    snare_2_value_label = Gtk.Template.Child()
    hihat_override_switch = Gtk.Template.Child()
    hihat_scale = Gtk.Template.Child()
    hihat_value_label = Gtk.Template.Child()
    hihat_2_override_switch = Gtk.Template.Child()
    hihat_2_scale = Gtk.Template.Child()
    hihat_2_value_label = Gtk.Template.Child()
    clap_override_switch = Gtk.Template.Child()
    clap_scale = Gtk.Template.Child()
    clap_value_label = Gtk.Template.Child()
    tom_override_switch = Gtk.Template.Child()
    tom_scale = Gtk.Template.Child()
    tom_value_label = Gtk.Template.Child()
    crash_override_switch = Gtk.Template.Child()
    crash_scale = Gtk.Template.Child()
    crash_value_label = Gtk.Template.Child()

    def __init__(self, parent_window):
        super().__init__()

        self.parent_window = parent_window

        self._part_controls = {}
        self._connect_signals()
        self._wire_per_part_controls_from_ui()
        self._sync_density_label()

    def _connect_signals(self):
        self.density_scale.connect("value-changed", self._on_density_changed)
        self.generate_button.connect("clicked", self._on_generate_clicked)
        self.cancel_button.connect("clicked", self._on_cancel_clicked)

    def _sync_density_label(self):
        value = int(self.density_scale.get_value())
        self.density_value_label.set_text(f"{value}%")

        # When global density changes, update any disabled part sliders to match
        for part, controls in self._part_controls.items():
            override_switch, scale, value_label = controls
            if not override_switch.get_active():
                scale.set_value(value)
                value_label.set_text(f"{int(scale.get_value())}%")

    def _on_density_changed(self, scale):
        self._sync_density_label()

    def _on_generate_clicked(self, _button):
        density_percent = int(self.density_scale.get_value())

        # Generate random pattern via service
        service = self.parent_window.drum_machine_service
        per_part_density = {}
        for part, controls in self._part_controls.items():
            override_switch, scale, _label = controls
            if override_switch.get_active():
                per_part_density[part] = int(scale.get_value())
        service.randomize_pattern(density_percent, per_part_density if per_part_density else None)

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

    def _wire_per_part_controls_from_ui(self):
        """Hook up per-instrument widgets defined in the .ui and wire events."""
        mapping = {
            "kick": (self.kick_override_switch, self.kick_scale, self.kick_value_label),
            "kick-2": (self.kick_2_override_switch, self.kick_2_scale, self.kick_2_value_label),
            "kick-3": (self.kick_3_override_switch, self.kick_3_scale, self.kick_3_value_label),
            "snare": (self.snare_override_switch, self.snare_scale, self.snare_value_label),
            "snare-2": (self.snare_2_override_switch, self.snare_2_scale, self.snare_2_value_label),
            "hihat": (self.hihat_override_switch, self.hihat_scale, self.hihat_value_label),
            "hihat-2": (self.hihat_2_override_switch, self.hihat_2_scale, self.hihat_2_value_label),
            "clap": (self.clap_override_switch, self.clap_scale, self.clap_value_label),
            "tom": (self.tom_override_switch, self.tom_scale, self.tom_value_label),
            "crash": (self.crash_override_switch, self.crash_scale, self.crash_value_label),
        }

        for part, (override_switch, scale, value_label) in mapping.items():
            # Initial label text
            value_label.set_text(f"{int(scale.get_value())}%")
            # Keep label in sync with slider
            def on_value_changed(scale, _pl=value_label):
                _pl.set_text(f"{int(scale.get_value())}%")
            scale.connect("value-changed", on_value_changed)
            # Enable/disable slider based on switch
            def on_override_toggled(switch, _scale=scale):
                _scale.set_sensitive(switch.get_active())
            override_switch.connect("notify::active", on_override_toggled)
            # Ensure disabled by default matches UI
            scale.set_sensitive(override_switch.get_active())
            # Store
            self._part_controls[part] = (override_switch, scale, value_label)
