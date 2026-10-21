# Little Bird Trading installers CI

Builds and tests the Little Bird Trading desktop app on Windows and Linux. The app's source stays in a private
repository; these workflows check it out with a read-only deploy key, build, test and upload the results as
workflow artifacts. Nothing here is published anywhere.

- `tests.yml`: the shared rules and the desktop app's tests on Linux and Windows (with screenshots).
- `windows.yml`: builds the MSI and EXE (website and Microsoft Store builds), installs the MSI, runs it and photographs it.
- `linux.yml`: builds the AppImage and the Snap, runs the AppImage on a virtual screen and photographs it.

`mock/` is a stand-in for the website's app API with made-up times and levels, so the screenshots never depend on
the live site. The fixture contains only Index Levels (US, four symbols) and Active Traders (AT, 24 symbols).
US is free/open; AT is locked and carries no levels. One startup clock supplies all schedule timestamps.
Unknown lists return404. Payloads are not logged, and the server binds only to127.0.0.1.
Run `python3 -m unittest discover -s mock -p test_server.py` for offline fixture checks.
Installer captures include both level screens. Synthetic captures are diagnostic evidence, not approved
store artwork or proof of production data, transactions, sign-in or notification delivery.
