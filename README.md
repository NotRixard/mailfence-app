# mailfence-app
A tiny, unofficial desktop wrapper for the Mailfence web app, built with GTK4 and WebKitGTK.

Not affiliated with or endorsed by Mailfence / ContactOffice Group. It simply displays the official web interface in its own window.

Install
Dependencies (Arch): 

```bash
sudo pacman -S python-gobject gtk4 webkitgtk-6.0
```
```bash
git clone https://github.com/NotRixard/mailfence-app
```
```bash
cd mailfence-app
```
```bash
bash install.sh
```

Run mailfence-app or launch "Mailfence" from your app menu. Set MAILFENCE_DEBUG=1 to print loaded URLs to the terminal.

Notes
Session data (including login cookies) is stored in ~/.local/share/mailfence-app/. Delete that folder to sign out.
The wrapper keeps your login by giving session cookies a 30-day expiry locally. Remove that behavior in persist_cookies() if you don't want it.
This is a web wrapper only. It does not add IMAP/SMTP, passkeys or anything else Mailfence doesn't offer.
