# window.py
#
# Copyright 2024 revisto
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
import time
import threading
import pygame
from gi.repository import Adw, Gtk, Gdk, Gio

@Gtk.Template(resource_path='/lol/revisto/DrumMachine/window.ui')
class DrumMachineWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'DrumMachineWindow'

    header_label = Gtk.Template.Child()
    outer_box = Gtk.Template.Child()
    main_controls_box = Gtk.Template.Child()
    header_bar = Gtk.Template.Child()
    bpm_spin_button = Gtk.Template.Child()
    volume_scale = Gtk.Template.Child()
    play_pause_button = Gtk.Template.Child()
    drum_machine_box = Gtk.Template.Child()
    label_box = Gtk.Template.Child()

    TOGGLE_PARTS = ['kick', 'snare', 'hihat']
    NUM_TOGGLES = 16

    # Dynamically creating toggle children
    for part in TOGGLE_PARTS:
        for i in range(1, NUM_TOGGLES + 1):
            locals()[f"{part}_toggle_{i}"] = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pygame.init()
        self.playing = False  # Initialize playing state
        self.bpm = 120  # Initialize BPM
        self.volume = 0.8  # Initialize volume
        self.play_thread = None  # Thread for playing drum sequence
        self.stop_event = threading.Event()
        self.init_css()
        self.apply_css_classes()
        self.connect_signals()
        self.init_drum_parts()
        self.load_drum_sounds()

    def init_css(self):
        path = os.path.join(os.path.dirname(__file__), "style.css")
        css_provider = Gtk.CssProvider()
        css_provider.load_from_file(Gio.File.new_for_path(path))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    def apply_css_classes(self):
        self.header_label.get_style_context().add_class("header_label")
        self.outer_box.get_style_context().add_class("outer_box")
        self.main_controls_box.get_style_context().add_class("main_controls_box")
        self.header_bar.get_style_context().add_class("header_bar")
        self.bpm_spin_button.get_style_context().add_class("spinbutton-button")
        self.play_pause_button.get_style_context().add_class("play-button")
        self.drum_machine_box.get_style_context().add_class("drum-machine-box")
        self.label_box.get_style_context().add_class("center-align")

    def connect_signals(self):
        self.bpm_spin_button.connect("value-changed", self.on_bpm_changed)
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        self.play_pause_button.connect("clicked", self.handle_play_pause)  # Connect play/pause button

    def init_drum_parts(self):
        self.drum_parts = {part: [False for _ in range(self.NUM_TOGGLES)] for part in self.TOGGLE_PARTS}

        for part in self.TOGGLE_PARTS:
            for i in range(self.NUM_TOGGLES):
                toggle = getattr(self, f"{part}_toggle_{i + 1}")
                self.drum_parts[part][i] = toggle.get_active()
                toggle.connect("toggled", self.on_toggle_changed, part, i)

    def load_drum_sounds(self):
        base_path = os.path.join(os.path.dirname(__file__))
        self.sounds = {
            'kick': pygame.mixer.Sound(os.path.join(base_path, "KICK.wav")),
            'snare': pygame.mixer.Sound(os.path.join(base_path, "SNARE.wav")),
            'hihat': pygame.mixer.Sound(os.path.join(base_path, "CLOSED-HAT.wav")),
        }

    def on_toggle_changed(self, toggle_button, part, index):
        state = toggle_button.get_active()
        self.drum_parts[part][index] = state

    def on_bpm_changed(self, spin_button):
        self.bpm = spin_button.get_value()
        print(f"BPM changed to: {self.bpm}")

    def on_volume_changed(self, scale):
        self.volume = scale.get_value()
        for sound in self.sounds.values():
            sound.set_volume(self.volume / 100)
        print(f"Volume changed to: {self.volume}")

    def handle_play_pause(self, button):
        self.playing = not self.playing  # Toggle playing state
        if self.playing:
            button.set_label("Pause")
            print("Playing...")
            self.start_playback()
        else:
            button.set_label("Play")
            print("Paused.")
            self.stop_playback()

    def start_playback(self):
        self.stop_event.clear()  # Clear the stop event before starting playback
        self.play_thread = threading.Thread(target=self.play_drum_sequence)
        self.play_thread.start()

    def stop_playback(self):
        self.playing = False
        print("Stopping playback...")
        self.stop_event.set()  # Signal the thread to stop
        if self.play_thread is not None:
            self.play_thread.join()
            self.play_thread = None
        print("Playback stopped.")

    def play_sound(self, sound_name):
        print(f"Playing {sound_name}")
        self.sounds[sound_name].play()

    def update_toggle_ui(self, index, add_class=True):
        for part in self.TOGGLE_PARTS:
            toggle = getattr(self, f"{part}_toggle_{index + 1}")
            if add_class:
                toggle.get_style_context().add_class("toggle-active")
            else:
                toggle.get_style_context().remove_class("toggle-active")
                
    def calculate_beat_interval(self):
        return 60 / self.bpm

    def play_drum_sequence(self):
        def play_sounds():
            for i in range(self.NUM_TOGGLES):
                if self.stop_event.is_set():  # Check if stop event is set
                    return
                if self.drum_parts['kick'][i]:
                    self.play_sound('kick')
                if self.drum_parts['snare'][i]:
                    self.play_sound('snare')
                if self.drum_parts['hihat'][i]:
                    self.play_sound('hihat')
                
                self.update_toggle_ui(i, add_class=True)
                
                # Calculate the total sleep time for each beat
                total_sleep_time = self.calculate_beat_interval()
                sleep_interval = 0.01  # Smaller sleep interval
                elapsed_time = 0
                
                while elapsed_time < total_sleep_time:
                    if self.stop_event.is_set():
                        self.update_toggle_ui(i, add_class=False)
                        return
                    time.sleep(sleep_interval)
                    elapsed_time += sleep_interval
                
                self.update_toggle_ui(i, add_class=False)

        while self.playing and not self.stop_event.is_set():
            play_sounds()