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

    def __init__(self, parent_window):
        super().__init__()

        self.parent_window = parent_window

        self._part_controls = {}
        self._connect_signals()
        self._build_per_part_controls()
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

    def _build_per_part_controls(self):
        """Create per-instrument override sliders inside the preferences group."""
        global_default = int(self.density_scale.get_value())
        for part in DRUM_PARTS:
            nice_name = part.capitalize().replace('-', ' ')

            row = Adw.ActionRow(title=nice_name)

            # Override switch
            override_switch = Gtk.Switch()
            override_switch.set_valign(Gtk.Align.CENTER)
            row.add_suffix(override_switch)
            row.set_activatable_widget(override_switch)

            # Value label
            value_label = Gtk.Label(label=f"{global_default}%")
            value_label.add_css_class("dim-label")
            value_label.set_valign(Gtk.Align.CENTER)

            # Slider
            adjustment = Gtk.Adjustment(lower=0, upper=100, step_increment=1, page_increment=10, value=global_default)
            scale = Gtk.Scale(adjustment=adjustment)
            scale.set_valign(Gtk.Align.CENTER)
            scale.set_hexpand(True)
            scale.set_draw_value(False)
            scale.set_width_request(260)

            # Keep label in sync
            def on_value_changed(scale, _pl=value_label):
                _pl.set_text(f"{int(scale.get_value())}%")
            scale.connect("value-changed", on_value_changed)

            # Enable/disable slider based on switch
            def on_override_toggled(switch, _scale=scale):
                _scale.set_sensitive(switch.get_active())
            override_switch.connect("notify::active", on_override_toggled)
            scale.set_sensitive(False)

            # Place slider and label as suffix widgets
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            box.append(scale)
            box.append(value_label)
            row.add_suffix(box)

            self.per_part_group.add(row)

            # Store controls
            self._part_controls[part] = (override_switch, scale, value_label)
