import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gio


class WindowActionHandler:
    """Handles window-level actions and keyboard shortcuts"""

    def __init__(self, window):
        self.window = window

    def setup_actions(self):
        """Setup all window actions and keyboard shortcuts"""
        actions = [
            ("open_menu", self.on_open_menu_action, ["F10"]),
            ("show-help-overlay", self.on_show_help_overlay, ["<primary>question"]),
            ("play_pause", self.handle_play_pause_action, ["space"]),
            ("clear_toggles", self.handle_clear_action, ["<primary>Delete"]),
            ("increase_bpm", self.increase_bpm_action, ["plus", "equal"]),
            ("decrease_bpm", self.decrease_bpm_action, ["minus"]),
            ("increase_volume", self.increase_volume_action, ["<primary>Up"]),
            ("decrease_volume", self.decrease_volume_action, ["<primary>Down"]),
            ("load_preset", self.on_open_file_action, ["<primary>o"]),
            ("save_preset", self.on_save_preset_action, ["<primary>s"]),
            ("quit", self.on_quit_action, ["<primary>q"]),
            ("close_window", self.on_quit_action, ["<primary>w"]),
        ]

        for action_name, callback, shortcuts in actions:
            self._create_action(action_name, callback, shortcuts)

    def _create_action(self, name, callback, shortcuts=None):
        """Create and register an action with optional keyboard shortcuts"""
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.window.add_action(action)
        if shortcuts:
            self.window.application.set_accels_for_action(f"win.{name}", shortcuts)

    # Action handlers
    def on_open_menu_action(self, action, param):
        self.window.menu_button.activate()

    def on_show_help_overlay(self, action, param):
        self.window.get_help_overlay().present()

    def handle_play_pause_action(self, action, param):
        self.window.handle_play_pause(self.window.play_pause_button)

    def handle_clear_action(self, action, param):
        self.window.handle_clear(self.window.clear_button)

    def increase_bpm_action(self, action, param):
        current_bpm = self.window.bpm_spin_button.get_value()
        self.window.bpm_spin_button.set_value(current_bpm + 1)

    def decrease_bpm_action(self, action, param):
        current_bpm = self.window.bpm_spin_button.get_value()
        self.window.bpm_spin_button.set_value(current_bpm - 1)

    def increase_volume_action(self, action, param):
        current_volume = self.window.volume_button.get_value()
        self.window.volume_button.set_value(min(current_volume + 5, 100))

    def decrease_volume_action(self, action, param):
        current_volume = self.window.volume_button.get_value()
        self.window.volume_button.set_value(max(current_volume - 5, 0))

    def on_open_file_action(self, action, param):
        self.window.on_open_file(self.window.file_preset_button)

    def on_save_preset_action(self, action, param):
        self.window.on_save_preset(self.window.save_preset_button)

    def on_quit_action(self, action, param):
        if self.window.save_changes_service.has_unsaved_changes():
            self.window.save_changes_service.prompt_save_changes(
                on_save=self.window._save_and_close,
                on_discard=self.window.cleanup_and_destroy,
            )
        else:
            self.window.cleanup_and_destroy()
