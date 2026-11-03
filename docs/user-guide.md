# USPTO Patent Intelligence: User Guide

**For:** Malachi Hernandez
**Release:** 1.0
**Needs:** a Mac with Apple silicon (M1 or later) running macOS 15 Sequoia or later

This guide covers installing, updating, and removing the application, plus a short tour of how it works. You never need the Terminal or a configuration file (`MNT-user-guide`, `USE-zero-config`).

_Screenshots: to be added from the 1.0 build during the clean-Mac install check (`QS-fresh-mac-install`)._

---

## 1. Install

1. Open the project's **Releases** page on GitHub and download the newest file named `USPTO-Patent-Intelligence-<version>-arm64.dmg`.
2. Double-click the downloaded `.dmg`. A window opens showing the app and an **Applications** folder.
3. Drag **USPTO Patent Intelligence** onto **Applications**.
4. Eject the disk image by clicking the eject button next to it in the Finder sidebar. You can delete the `.dmg` afterward.

## 2. Open it for the first time (do this once)

The application is free and not registered with Apple, so the first time you open it, macOS asks you to confirm that you trust it. After that, it opens normally.

1. Open **Applications** and double-click **USPTO Patent Intelligence**.
2. macOS says the app "Not Opened" or "cannot be verified". Click **Done** (not "Move to Trash").
3. Open **System Settings** (Apple menu → System Settings) and choose **Privacy & Security** in the sidebar.
4. Scroll down to **Security**. You will see a line saying "USPTO Patent Intelligence" was blocked. Click **Open Anyway**.
5. Enter your Mac password or use Touch ID, then click **Open Anyway** again.

The app opens. From now on, open it like any other app, from Applications, Launchpad, or Spotlight. You can keep it in the Dock by right-clicking its Dock icon and choosing **Options → Keep in Dock**.

On macOS 15, right-clicking the app and choosing **Open** no longer skips the warning. Use System Settings as described above.

The first start can take several seconds while the app gets its chart fonts ready. Later starts are faster.

## 3. Using the application

The window has four tabs.

- **Import:** drag one or more weekly office action files from Finder onto the window. A progress bar shows each file. When it finishes, the app tells you how many records it stored and how many it rejected, and why. A file that isn't a weekly file, or is damaged or only partly downloaded, is refused, and nothing from it is stored. Importing the same file twice changes nothing. Quitting during an import is safe: import that file again next time.
- **Visualizations:** choose the imported data and the visualizations you want, then click **Create visualizations**.
- **Sources:** click **View source records** on a chart, or click one of its bars, to see the office actions behind it, with the source file and import date. Select a record to read its letter text.
- **Export:** choose the visualizations to export and click **Export…**, then pick a folder. Each one is saved as a labeled PNG image, ready for a post.

The application never uses the internet. It works with Wi-Fi turned off.

## 4. Update to a new release

1. Quit the application.
2. Download the new `.dmg` from the Releases page and drag the app onto **Applications** as in section 1. When asked, choose **Replace**.
3. Open it. If macOS shows the warning again, repeat section 2 once.

Everything you have imported is kept. Your data is not stored in the app itself (see section 5), so replacing the app does not touch it. The first start after an update may take a moment while the app updates its database.

## 5. Where your data is

Everything the application stores is in one folder:

`~/Library/Application Support/USPTO Patent Intelligence`

To open it: in Finder, choose **Go → Go to Folder…**, paste the path above, and press Return.

| What | Where in that folder |
|---|---|
| All imported records and the charted data | `patent-intelligence.duckdb` |
| The log file (counts and outcomes only, never letter text or examiner numbers) | `logs/patent-intelligence.log` |
| Temporary working files during large imports | `tmp/` |

Exported images are saved in whichever folder you picked when exporting, not here.

**Backing up:** quit the app, then copy the folder somewhere safe. Time Machine backs it up automatically.

## 6. When something goes wrong

- **The app shows an error message:** it explains what went wrong. The technical details go to the log file. Send the team (or whoever maintains the app) the file `logs/patent-intelligence.log` from the folder in section 5.
- **"The data folder could not be written to"** at start-up: check that the disk isn't full. Then quit and open the app again.
- **The app won't open after an update:** repeat section 2.

## 7. Remove the application

1. Drag **USPTO Patent Intelligence** from Applications to the Trash.
2. To also delete every imported record, delete the folder in section 5. This cannot be undone, so back it up first if you might want it again.

## 8. Changing the AI model

Release 1.0 has no AI features (`KD-no-ai-in-mvp`), so there is no model to change. This section will be written when AI is added.
