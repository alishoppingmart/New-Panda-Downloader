# Panda Pro Downloader

A clean, free video & audio downloader — **no license key, no account, no activation**.
Anyone can run it. Built on [yt-dlp](https://github.com/yt-dlp/yt-dlp), so it works with
YouTube, TikTok, Instagram, Facebook, Douyin, and 1000+ other sites. Handles single
videos, audio-only MP3, full playlists, and several downloads at once.

## Features

- Modern sidebar interface (Dashboard / Download / Activity Log / Settings)
- Paste many links at once — playlists supported automatically
- Quality presets: Best (up to 4K) / 1080p / 720p / 480p / Audio-only MP3
- Concurrent downloads (1-5 at a time)
- Live progress, counters, and an activity log
- Light / Dark theme toggle
- Green panda branding, packaged as a single standalone .exe with ffmpeg bundled inside

---

## How to run it — the easy way (just use the .exe)

If you already have PandaProDownloader.exe (from the GitHub build below or shared to you):

1. Double-click PandaProDownloader.exe. No install, no key, nothing to set up.
2. Paste one or more links into the big box (one per line).
3. Pick a Quality and how many Concurrent downloads you want.
4. Click Choose Folder to set where files save.
5. Click START DOWNLOAD. Watch progress; check Activity Log for details.

That's it.

---

## How to run from source (for testing on your own PC)

You need Python 3.10+ installed.

    pip install -r requirements.txt
    python make_logo.py        # creates the green panda logo + icon
    python panda_pro_downloader.py

Running from source needs ffmpeg on your PATH for MP3 conversion and high-res merging.
The packaged .exe already includes ffmpeg, so end users never have to.

---

## How to build the standalone .exe (GitHub Actions — no setup on your PC)

1. Create a new GitHub repo and push every file, keeping the folder layout
   (especially .github/workflows/build-exe.yml).
2. Open the repo's Actions tab. The build runs on push, or click Run workflow.
3. When it finishes, open the run and download the PandaProDownloader-Windows
   artifact. Inside is PandaProDownloader.exe — one file you can share with anyone.

The workflow auto-generates the logo, downloads ffmpeg, bundles everything, and sets the
green panda as the app icon.

---

## Notes

- Please download only content you own or have the right to download, and respect each
  platform's terms of service.
- When a site eventually changes and stops working, bump the yt-dlp version in
  requirements.txt and rebuild — that fixes it the vast majority of the time.
