# dialogs/midi_mapping_dialog.py
#
# Copyright 2025 revisto
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
from gettext import gettext as _

# Common GM Percussion Map (General MIDI Level 1)
GM_PERCUSSION_MAP = {
    35: _("Acoustic Bass Drum"),
    36: _("Bass Drum 1"),
    37: _("Side Stick"),
    38: _("Acoustic Snare"),
    39: _("Hand Clap"),
    40: _("Electric Snare"),
    41: _("Low Floor Tom"),
    42: _("Closed Hi Hat"),
    43: _("High Floor Tom"),
    44: _("Pedal Hi Hat"),
    45: _("Low Tom"),
    46: _("Open Hi Hat"),
    47: _("Low-Mid Tom"),
    48: _("Hi-Mid Tom"),
    49: _("Crash Cymbal 1"),
    50: _("High Tom"),
    51: _("Ride Cymbal 1"),
    52: _("Chinese Cymbal"),
    53: _("Ride Bell"),
    54: _("Tambourine"),
    55: _("Splash Cymbal"),
    56: _("Cowbell"),
    57: _("Crash Cymbal 2"),
    58: _("Vibraslap"),
    59: _("Ride Cymbal 2"),
    60: _("Hi Bongo"),
    61: _("Low Bongo"),
    62: _("Mute Hi Conga"),
    63: _("Open Hi Conga"),
    64: _("Low Conga"),
    65: _("High Timbale"),
    66: _("Low Timbale"),
    67: _("High Agogo"),
    68: _("Low Agogo"),
    69: _("Cabasa"),
    70: _("Maracas"),
    71: _("Short Whistle"),
    72: _("Long Whistle"),
    73: _("Short Guiro"),
    74: _("Long Guiro"),
    75: _("Claves"),
    76: _("Hi Wood Block"),
    77: _("Low Wood Block"),
    78: _("Mute Cuica"),
    79: _("Open Cuica"),
    80: _("Mute Triangle"),
    81: _("Open Triangle"),
}


class MidiMappingDialog(Adw.Dialog):
    def __init__(self, parent, drum_part, on_save_callback):
        super().__init__()
        self.drum_part = drum_part
        self.on_save_callback = on_save_callback

        self.set_title(_("MIDI Mapping"))
        self.set_content_width(450)

        # Toolbar View to hold HeaderBar + Content
        toolbar_view = Adw.ToolbarView()
        self.set_child(toolbar_view)

        # Header Bar
        header_bar = Adw.HeaderBar()
        header_bar.set_show_title(True)

        toolbar_view.add_top_bar(header_bar)

        # Content Area - Match export dialog structure with margins
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_propagate_natural_height(True)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)

        scrolled.set_child(content_box)
        toolbar_view.set_content(scrolled)

        # Use PreferencesPage for nice grouping
        page = Adw.PreferencesPage()
        content_box.append(page)

        # Group 1: Note Assignment
        note_group = Adw.PreferencesGroup(title=_("Note Assignment"))
        note_group.set_description(
            _(
                "Assign a MIDI note for '{}'. "
                "This ensures correct playback when exporting."
            ).format(drum_part.name)
        )
        page.add(note_group)

        # Action Row for Note
        self.note_row = Adw.ActionRow(title=_("MIDI Note"))
        self.note_row.set_subtitle(_("The note number to trigger"))

        # Spin Button for Note Number
        adjustment = Gtk.Adjustment(
            value=drum_part.midi_note_id or 36,
            lower=0,
            upper=127,
            step_increment=1,
            page_increment=12,
        )
        self.spin_button = Gtk.SpinButton(adjustment=adjustment)
        self.spin_button.set_valign(Gtk.Align.CENTER)
        self.spin_button.connect("value-changed", self._on_value_changed)

        self.note_row.add_suffix(self.spin_button)
        note_group.add(self.note_row)

        # Group 2: Standard Instruments
        preset_group = Adw.PreferencesGroup(title=_("Standard Instruments"))
        preset_group.set_description(
            _("Select a General MIDI instrument to automatically set the note.")
        )
        page.add(preset_group)

        preset_row = Adw.ActionRow(title=_("Instrument Preset"))

        # Dropdown for presets
        model = Gtk.StringList()
        self.note_map = []  # List of (note, string_item)

        # Sort by note number
        sorted_map = sorted(GM_PERCUSSION_MAP.items())

        current_note = int(adjustment.get_value())
        selected_idx = -1

        idx = 0
        for note, name in sorted_map:
            display_str = f"{note} - {name}"
            model.append(display_str)
            self.note_map.append(note)
            if note == current_note:
                selected_idx = idx
            idx += 1

        self.dropdown = Gtk.DropDown(model=model)
        self.dropdown.set_enable_search(True)
        self.dropdown.set_valign(Gtk.Align.CENTER)

        self.dropdown.connect("notify::selected", self._on_preset_selected)

        if selected_idx != -1:
            self.dropdown.set_selected(selected_idx)
        else:
            self.dropdown.set_selected(Gtk.INVALID_LIST_POSITION)

        preset_row.add_suffix(self.dropdown)
        preset_group.add(preset_row)

        # Update subtitle of note row to match initial state
        self._update_gm_subtitle(int(adjustment.get_value()))

        # Bottom Bar for actions - single pill button (matching export dialog style)
        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_bottom(32)

        save_btn = Gtk.Button(label=_("Save"))
        save_btn.add_css_class("pill")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save_clicked)
        button_box.append(save_btn)

        toolbar_view.add_bottom_bar(button_box)

    def _on_value_changed(self, button):
        val = int(button.get_value())
        self._update_gm_subtitle(val)

        # Update dropdown if matches
        found = False
        try:
            if val in self.note_map:
                idx = self.note_map.index(val)
                if self.dropdown.get_selected() != idx:
                    self.dropdown.set_selected(idx)
                found = True
        except ValueError:
            # ValueError is expected if val is not in self.note_map;
            # ignore and handle as 'not found'
            pass

        if not found:
            self.dropdown.set_selected(Gtk.INVALID_LIST_POSITION)

    def _on_preset_selected(self, dropdown, pspec):
        selected_idx = dropdown.get_selected()
        if selected_idx != Gtk.INVALID_LIST_POSITION and selected_idx < len(
            self.note_map
        ):
            note = self.note_map[selected_idx]
            if int(self.spin_button.get_value()) != note:
                self.spin_button.set_value(note)

    def _update_gm_subtitle(self, note):
        name = GM_PERCUSSION_MAP.get(note)
        if name:
            self.note_row.set_subtitle(name)
        else:
            self.note_row.set_subtitle(_("Custom Note"))

    def _on_save_clicked(self, button):
        note = int(self.spin_button.get_value())
        self.on_save_callback(self.drum_part.id, note)
        self.close()
