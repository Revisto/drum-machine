from typing import Callable
from .drum_machine_service import DrumMachineService
from ..dialogs.save_changes_dialog import SaveChangesDialog


class SaveChangesService:
    """
    Responsible for prompting the user about unsaved changes and
    handling the user's decision (save or discard).
    """

    def __init__(self, window, drum_machine_service: DrumMachineService) -> None:
        self.window = window
        self.drum_machine_service = drum_machine_service
        self._unsaved_changes: bool = False

    def mark_unsaved_changes(self, value: bool) -> None:
        self._unsaved_changes = value

    def has_unsaved_changes(self) -> bool:
        return self._unsaved_changes

    def prompt_save_changes(self, on_save: Callable, on_discard: Callable) -> None:
        """
        Open the dialog; if user discards, call on_discard().
        If user saves, call on_save(), then mark changes as saved.
        """
        SaveChangesDialog(
            window=self.window,
            on_save_callback=self._wrap_save_callback(on_save),
            on_discard_callback=on_discard,
        )

    def _wrap_save_callback(self, callback: Callable) -> Callable:
        """
        Wrap the user-provided callback to reset unsaved changes after saving.
        """

        def wrapper():
            callback()
            self.mark_unsaved_changes(False)

        return wrapper
