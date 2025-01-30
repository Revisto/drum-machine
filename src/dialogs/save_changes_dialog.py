from gi.repository import Adw, Gtk


@Gtk.Template(
    resource_path="/io/github/revisto/drum-machine/gtk/save_changes_dialog.ui"
)
class SaveChangesDialog(Adw.AlertDialog):
    __gtype_name__ = "SaveChangesDialog"

    def __init__(self, parent_window, on_save_callback=None, on_discard_callback=None):
        super().__init__()
        self._on_save_callback = on_save_callback
        self._on_discard_callback = on_discard_callback
        self.present(parent_window)

    @Gtk.Template.Callback()
    def _on_save(self, _dialog, _response):
        if callable(self._on_save_callback):
            self._on_save_callback()
        self.close()

    @Gtk.Template.Callback()
    def _on_discard(self, _dialog, _response):
        if callable(self._on_discard_callback):
            self._on_discard_callback()
        self.close()

    @Gtk.Template.Callback()
    def _on_cancel(self, _dialog, _response):
        self.close()
