# Little Bird Trading installers CI

Builds and tests the Little Bird Trading desktop app on Windows and Linux. The app's source stays in a private
repository; these workflows check it out with a read-only deploy key, build, test and upload the results as
workflow artifacts. Nothing here is published anywhere.

- `tests.yml`: the shared rules and the desktop app's tests on Linux and Windows (with screenshots).
- `windows.yml`: builds the MSI and EXE (website and Microsoft Store builds), installs the MSI, runs it and photographs it.
- `linux.yml`: builds the AppImage and the Snap, runs the AppImage on a virtual screen and photographs it.

`mock/` is a stand-in for the website's app API with made-up times and levels, so the screenshots never depend on
the live site.
