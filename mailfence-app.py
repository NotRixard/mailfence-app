#!/usr/bin/env python3
"""Tiny native wrapper around the Mailfence web app (GTK4 + WebKitGTK 6)."""
import os
from urllib.parse import urlparse

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("WebKit", "6.0")
from gi.repository import Gio, GLib, Gtk, WebKit

URL = "https://mailfence.com"
APP_ID = "dev.local.Mailfence"
ALLOWED_HOSTS = ("mailfence.com",)
COOKIE_DAYS = 30

DATA = os.path.join(GLib.get_user_data_dir(), "mailfence-app")
CACHE = os.path.join(GLib.get_user_cache_dir(), "mailfence-app")


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.view = None
        self._tried_autologin = False

    def do_activate(self):
        win = self.props.active_window
        if win:
            win.present()
            return

        session = WebKit.NetworkSession.new(DATA, CACHE)
        session.get_cookie_manager().set_persistent_storage(
            os.path.join(DATA, "cookies.sqlite"),
            WebKit.CookiePersistentStorage.SQLITE,
        )

        view = WebKit.WebView(network_session=session)
        view.connect("permission-request", self.on_permission)
        view.connect("show-notification", self.on_notification)
        view.connect("decide-policy", self.on_policy)
        view.connect("load-changed", self.on_load)
        view.load_uri(URL)
        self.view = view

        win = Gtk.ApplicationWindow(application=self, title="Mailfence")
        win.set_default_size(1200, 800)
        win.set_child(view)
        win.connect("close-request", self.on_close)
        win.present()

        # Periodically persist session cookies (survives crashes too)
        GLib.timeout_add_seconds(30, self.on_tick)

    # --- skip the landing page ------------------------------------------
    CLICK_LOGIN_JS = """
    (function () {
      const els = [...document.querySelectorAll('a, button')];
      const el = els.find(e => /^\\s*log\\s*in\\s*$/i.test(e.textContent));
      if (el) el.click();
    })();
    """

    def on_load(self, view, event):
        if event != WebKit.LoadEvent.FINISHED:
            return
        if os.environ.get("MAILFENCE_DEBUG"):
            print("loaded:", view.get_uri(), flush=True)
        if not self._tried_autologin:
            self._tried_autologin = True

            def click():
                view.evaluate_javascript(
                    self.CLICK_LOGIN_JS, len(self.CLICK_LOGIN_JS), None, None, None, None
                )
                return False

            GLib.timeout_add(800, click)

    # --- keep login across restarts -------------------------------------
    def persist_cookies(self, then=None):
        """Give session cookies an expiry so WebKit saves them to disk."""
        cm = self.view.get_network_session().get_cookie_manager()
        uris = {URL, self.view.get_uri() or URL}
        pending = [len(uris)]

        def done():
            pending[0] -= 1
            if pending[0] == 0 and then:
                then()

        for uri in uris:
            def got(cm_, res):
                try:
                    cookies = cm_.get_cookies_finish(res)
                except GLib.Error:
                    cookies = []
                todo = [c for c in cookies if c.get_expires() is None]
                if not todo:
                    done()
                    return
                left = [len(todo)]
                for c in todo:
                    c.set_expires(GLib.DateTime.new_now_utc().add_days(COOKIE_DAYS))

                    def added(cm2, r2):
                        try:
                            cm2.add_cookie_finish(r2)
                        except GLib.Error:
                            pass
                        left[0] -= 1
                        if left[0] == 0:
                            done()

                    cm.add_cookie(c, None, added)

            cm.get_cookies(uri, None, got)

    def on_tick(self):
        if self.view:
            self.persist_cookies()
        return True

    def on_close(self, win):
        if getattr(win, "_closing", False):
            return False
        win._closing = True

        def finish():
            if getattr(win, "_closed", False):
                return False
            win._closed = True
            win.destroy()
            return False

        self.persist_cookies(then=finish)
        GLib.timeout_add_seconds(3, finish)  # failsafe
        return True
    # --------------------------------------------------------------------

    def on_permission(self, view, request):
        if isinstance(request, WebKit.NotificationPermissionRequest):
            request.allow()
            return True
        return False

    def on_notification(self, view, notification):
        n = Gio.Notification.new(notification.get_title() or "Mailfence")
        n.set_body(notification.get_body() or "")
        self.send_notification(None, n)
        return True

    def on_policy(self, view, decision, decision_type):
        if decision_type == WebKit.PolicyDecisionType.NAVIGATION_ACTION:
            uri = decision.get_navigation_action().get_request().get_uri()
            host = urlparse(uri).hostname or ""
            if not any(host == h or host.endswith("." + h) for h in ALLOWED_HOSTS):
                if urlparse(uri).scheme in ("http", "https"):
                    Gtk.show_uri(self.props.active_window, uri, 0)
                    decision.ignore()
                    return True
        return False


if __name__ == "__main__":
    App().run()
