# AMP privacy

AMP processes your media locally and does not upload your files or collect playback
analytics. It has no account system, advertising, media-library database or background
media scan. Artwork, tags, matching subtitle files and lyrics are read from the selected
files and their companion files. Linked artwork URLs are ignored.

## Connections you choose

Manual update checks contact GitHub for public release metadata. Automatic checks are
off by default and require confirmation; when enabled, successful checks are spaced at
least 24 hours apart. Requests include AMP's version in the User-Agent, but no media
paths, media contents or playback history. GitHub receives ordinary connection information
such as your public IP address. AMP does not download or install updates.

Opening a network share accesses its file server. Files in cloud-backed folders may
involve their sync provider. Those are properties of the location you select; selecting
a file does not cause AMP to upload it to an AMP service. Website and GitHub links in
About open your browser only when selected.

## Operating-system boundary

Windows playback uses system media components through Media Foundation. Windows
diagnostics, error reporting, installed codecs, security software and other operating-system
activity are governed by your Windows settings and are outside AMP's control. AMP cannot
guarantee that Windows or other installed software never communicates with its providers.
Linux playback similarly uses the distribution's libmpv and system components.

## Local storage

Preferences are stored in `%LOCALAPPDATA%/AMP/AMP/preferences.ini` on Windows and
`${XDG_CONFIG_HOME:-~/.config}/AMP/AMP/preferences.ini` on Linux. AMP does not store media
paths or playback history there. Screenshots are saved only when requested. Ordinary
playback does not write an AMP diagnostic log. Explicit developer self-tests and the
optional network-capture tool write local evidence to the chosen output folder.

## Verification and limits

A Windows network trace on 21 October 2026 covered startup, music, video, an invalid-media
phase and shutdown using the installed 0.8b development build. No internet connection or
DNS request attributable to AMP was identified. SMB reads confirmed that part of the
music test used a network share. The trace decoder reported zero lost events.

Windows diagnostic and error-reporting services were stopped in the before/after snapshots.
The test therefore does not establish their behaviour with diagnostics enabled, after a
crash, or on another Windows configuration. Other applications and Windows processes had
network connections. A short observation cannot establish that no delayed communication
will ever occur. The trace applies to the tested build, not automatically to later binaries.

Raw system-wide captures contain private local identifiers and unrelated traffic. They
remain local and are not included in AMP's repository or distribution.
