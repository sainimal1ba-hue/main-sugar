# Copyright (C) 2026 Sugar Labs
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gettext import gettext as _

from gi.repository import GObject
from gi.repository import Gtk

from sugar3.graphics.palette import Palette
from sugar3.graphics.palettemenu import PaletteMenuBox
from sugar3.graphics.palettemenu import PaletteMenuItem

from jarabe.frame.frameinvoker import FrameWidgetInvoker
from jarabe.frame.notification import NotificationIcon
import jarabe.frame

def request_install_confirmation(bundle, on_confirm, on_decline):
    _PendingInstall(bundle, on_confirm, on_decline)

class _PendingInstall(GObject.GObject):
    """Owns one notification icon + palette for a single pending install."""

    def __init__(self, bundle, on_confirm, on_decline):
        GObject.GObject.__init__(self)
        self._bundle = bundle
        self._on_confirm = on_confirm
        self._on_decline = on_decline
        self._resolved = False
        self._notif_icon = NotificationIcon()
        self._notif_icon.props.icon_name = 'emblem-warning'
        icon_path = bundle.get_icon() if bundle is not None else None
        if icon_path:
            self._notif_icon.props.icon_filename = icon_path
        self._notif_icon.connect('button-release-event',
                                 self.__button_release_event_cb)
        palette = _InstallConfirmationPalette(bundle)
        palette.props.invoker = FrameWidgetInvoker(self._notif_icon)
        palette.set_group_id('frame')
        palette.connect('confirm', self.__confirm_cb)
        palette.connect('decline', self.__decline_cb)
        self._palette = palette
        frame = jarabe.frame.get_view()
        frame.add_notification(self._notif_icon, Gtk.CornerType.TOP_LEFT)
        self._palette.popup(immediate=True)

    def __button_release_event_cb(self, icon, event):
        self._palette.popup(immediate=True)

    def __confirm_cb(self, palette):
        self._resolve(self._on_confirm)

    def __decline_cb(self, palette):
        self._resolve(self._on_decline)

    def _resolve(self, callback):
        if self._resolved:
            return
        self._resolved = True
        frame = jarabe.frame.get_view()
        frame.remove_notification(self._notif_icon)
        callback()

class _InstallConfirmationPalette(Palette):
    __gsignals__ = {
        'confirm': (GObject.SignalFlags.RUN_FIRST, None, ([])),
        'decline': (GObject.SignalFlags.RUN_FIRST, None, ([])),
    }

    def __init__(self, bundle):
        Palette.__init__(self, '')
        self.menu_box = PaletteMenuBox()
        self.set_content(self.menu_box)
        self.menu_box.show()
        menu_item = PaletteMenuItem(_('Install'), icon_name='dialog-ok')
        menu_item.connect('activate', self.__install_activate_cb)
        self.menu_box.append_item(menu_item)
        menu_item.show()
        menu_item = PaletteMenuItem(_('Decline'), icon_name='dialog-cancel')
        menu_item.connect('activate', self.__decline_activate_cb)
        self.menu_box.append_item(menu_item)
        menu_item.show()
        name = bundle.get_name() if bundle is not None else _('activity')
        self.set_primary_text(name)
        self.set_secondary_text(
            _('Only install activities you trust.'))

    def __install_activate_cb(self, menu_item):
        self.emit('confirm')

    def __decline_activate_cb(self, menu_item):
        self.emit('decline')
