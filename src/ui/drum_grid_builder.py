import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk
from ..config import DRUM_PARTS, NUM_TOGGLES, GROUP_TOGGLE_COUNT


class DrumGridBuilder:
    """Responsible for building the drum grid UI components"""

    def __init__(self, window):
        self.window = window

    def build_drum_machine_interface(self):
        """Build the complete drum machine grid interface"""
        drum_rows_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        drum_rows_container.set_homogeneous(False)

        for drum_part in DRUM_PARTS:
            drum_row = self.create_drum_row(drum_part)
            drum_rows_container.append(drum_row)

        return drum_rows_container

    def create_drum_row(self, drum_part):
        """Create a complete row for a drum part"""
        instrument_container = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=10
        )
        num_beat_groups = (NUM_TOGGLES + GROUP_TOGGLE_COUNT - 1) // GROUP_TOGGLE_COUNT

        instrument_button = self.create_instrument_button(drum_part)
        instrument_container.append(instrument_button)

        for group_index in range(num_beat_groups):
            beat_group = self.create_beat_toggle_group(drum_part, group_index)
            instrument_container.append(beat_group)

            if group_index != num_beat_groups - 1:
                beat_group.set_margin_end(20)

        return instrument_container

    def create_instrument_button(self, drum_part):
        """Create the instrument preview button"""
        button_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_container.set_spacing(5)

        instrument_button = Gtk.Button(
            label=f"{drum_part.capitalize().replace('-', ' ')}"
        )
        instrument_button.set_halign(Gtk.Align.START)
        instrument_button.connect(
            "clicked", self.window.on_drum_part_button_clicked, drum_part
        )
        instrument_button.add_css_class("drum-part-button")
        instrument_button.add_css_class("flat")
        instrument_button.set_tooltip_text(
            f"Click to Preview {drum_part.capitalize().replace('-', ' ')}"
        )
        instrument_button.set_has_tooltip(True)

        button_container.append(instrument_button)
        spacer = Gtk.Label()
        spacer.set_hexpand(True)
        button_container.append(spacer)

        return button_container

    def create_beat_toggle_group(self, drum_part, group_index):
        """Create a group of beat toggles"""
        beat_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        for position in range(GROUP_TOGGLE_COUNT):
            beat_number = group_index * GROUP_TOGGLE_COUNT + position + 1
            if beat_number > NUM_TOGGLES:
                break
            beat_toggle = self.create_single_beat_toggle(drum_part, beat_number)
            beat_group.append(beat_toggle)

        return beat_group

    def create_single_beat_toggle(self, drum_part, beat_number):
        """Create a single beat toggle button"""
        beat_toggle = Gtk.ToggleButton()
        beat_toggle.set_size_request(20, 20)
        beat_toggle.set_name(f"{drum_part}_toggle_{beat_number}")
        beat_toggle.set_valign(Gtk.Align.CENTER)
        beat_toggle.add_css_class("drum-toggle")
        beat_toggle.connect(
            "toggled", self.window.on_toggle_changed, drum_part, beat_number - 1
        )

        right_click_gesture = Gtk.GestureClick.new()
        right_click_gesture.set_button(Gdk.BUTTON_SECONDARY)
        right_click_gesture.connect(
            "released", self.window._on_right_click_released, beat_toggle
        )
        beat_toggle.add_controller(right_click_gesture)

        setattr(self.window, f"{drum_part}_toggle_{beat_number}", beat_toggle)
        return beat_toggle
