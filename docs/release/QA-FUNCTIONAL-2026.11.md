# NaMiOS 2026.11 — Functional QA (screen-by-screen, flow-by-flow)

Role: senior QA, read-only. Goal: zero bugs at release. This document ranks
findings only — it does NOT fix anything. Every item has `file:line`, a
concrete failure scenario (inputs → wrong result), and a one-line fix, split
into **CODE-FIXABLE-NOW** (change text/logic in the repo, no hardware) vs
**NEEDS-BOOT-TEST** (only confirmable on a real KDE Plasma 6 / Debian 13 ISO).

Method: read every user-facing Python app + bash launcher + installer surface;
ran the real test suite and compile/lint; reproduced the two most serious
launcher defects on a stock Debian toolchain.

## Current-state evidence (ran, not assumed)

- `python3 -m pytest -q` → **2593 passed, 5 skipped** in ~13s (clean).
- `py_compile` over all `/opt/namios/**.py` app sources → rc 0 (all compile).
- `bash -n` over all 12 `/usr/local/bin/namios-*` launchers → all pass.
- i18n key resolution: every `t("...")` literal key in dichvu/antoan/assistant
  `ui.py` resolves in **both** vi and en; base catalog `vi.json`/`en.json` =
  114 keys each at full parity, no empty values; merged per-app catalogs
  (dichvu 167 / antoan 198 / assistant 230) at full vi↔en parity.
- Fail-safe entrypoints (ran with PySide6 absent, as on the headless build):
  `namios_dichvu.main()`→rc 0 (quiet), `namios_antoan.main()`/`namios_manchieu.main()`→rc 1
  with a clear stderr line — matches the documented per-app policy.
- **Reproduced BLOCKER-1** (mawk interval regex) and confirmed MAJOR-1
  (bwrap exit-code) by reading `bwrap` semantics.

## VERDICT

**NOT yet zero-bug-shippable, but very close.** One **BLOCKER** produces exactly
the fake "success" the owner forbids, and it reproduces on Debian's default
`awk`. The Python app layer (the 4 Vietnamese apps' real logic + i18n + first-run
+ Windows-data migration) is **exceptionally clean, fail-safe, and honest** —
no blocker there. The remaining risk is concentrated in a few bash launchers,
the installer's destructive-default, and a brand-asset regression trap. Fix the
1 BLOCKER + 4 MAJORs and the release clears the honesty bar; the rest are MINOR
polish. Two flagship apps (nServices, nSecurity) ship with **zero automated
tests** — the clean verdict for them rests on manual review, not a regression net.

---

## BLOCKER

### B1 — `namios-chan-doan` prints a FABRICATED "[OK] all PCI devices have drivers" on Debian's default awk (mawk)
- File: `distro/live-build/config/includes.chroot/usr/local/bin/namios-chan-doan:150-164`
- The driverless-device scan uses ERE interval quantifiers:
  `/^[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]/`. Debian's default `awk` is
  **mawk** (confirmed `mawk 1.3.4 20200120` here), which does not honor `{2}`
  intervals by default → the device-header line never matches → `missing=""`.
- Reproduced: fed a two-device `lspci -k` sample where `03:00.0` genuinely has
  no `Kernel driver in use`. The script's verbatim awk block printed **nothing**
  (so the tool would say `[OK] Mọi thiết bị PCI đều có driver đang gắn`); the
  no-interval variant correctly printed `03:00.0`.
- Failure scenario: a laptop whose Wi-Fi / fingerprint device truly has no
  kernel driver → user opens "Phần cứng & driver" → sees a green "all devices
  have drivers", and the exported support log (`export_log`→`hw_report`) records
  the same false all-clear. This is the exact fake-success the owner forbids and
  it defeats the tool's core purpose.
- One-line fix: remove the intervals — `/^[0-9a-fA-F][0-9a-fA-F]:[0-9a-fA-F][0-9a-fA-F]\.[0-9a-fA-F]/` — (or force `gawk`); add a driverless fixture test.
- **CODE-FIXABLE-NOW** (reproduced on this toolchain).

---

## MAJOR

### M1 — `namios-wine-capsule` reports "sandbox failed — app NOT run" for any app that exits non-zero (false failure; propagates to `namios-windows-app`)
- File: `.../usr/local/bin/namios-wine-capsule:429-432` (and consumer
  `.../usr/local/bin/namios-windows-app:184,413-416,466-468`).
- `bwrap "${bargs[@]}" -- wine "$exe_abs" ...` returns the **child's** exit code.
  Many Windows installers/apps return non-zero on a perfectly normal close/cancel.
  The script maps any non-zero to `log_err "bwrap báo lỗi khi dựng sandbox — DỪNG,
  KHÔNG chạy ứng dụng ngoài sandbox"` — a statement that the app did **not** run,
  when in fact it ran inside the sandbox and merely exited non-zero. `namios-windows-app`
  then greps `^\[LỖI\]` and shows "Có vấn đề khi chạy" after a successful run.
  (The non-bwrap path `run_without_bwrap:435-439` ignores wine's exit code entirely
  — the two isolation modes disagree about success.)
- Failure scenario: user installs/runs a Windows app that exits 1 on close →
  told the sandbox failed and nothing ran → confusion / repeated reinstalls.
- One-line fix: separate bwrap setup failure from child exit (e.g. `--info-fd`
  sentinel or a setup probe), and report the wine exit code neutrally instead of
  treating child-nonzero as "sandbox not built".
- **CODE-FIXABLE-NOW** for the logic; full validation is NEEDS-BOOT-TEST (real wine+bwrap).

### M2 — Redaction `|| cat` fallback can write UNREDACTED secrets while the UI claims "đã che bí mật"
- Files: `.../usr/local/bin/namios-chan-doan:384` (`sed ... "$src" >> "$dst" 2>/dev/null || cat "$src" >> "$dst"`) and `.../usr/local/bin/namios-smartai-policy.sh:103` (same `|| cat`).
- If `sed` exits non-zero for any reason, the fallback dumps the **raw** source
  (passwords/tokens/OTP/IP/email) into the exported file, yet `export_log` still
  prints "Mật khẩu/token/OTP/email/IP… đã được che tự động" (`namios-chan-doan:414`)
  and the file header claims redaction. The regex works on GNU sed (low probability),
  but a security control that silently fails open while asserting it succeeded is
  exactly what the honesty bar rejects.
- Failure scenario: a transient `sed` error on export → support bundle contains
  live credentials while telling the user they were scrubbed.
- One-line fix: on `sed` failure write a `[REDACTION-FAILED]` marker / abort the
  export — never `|| cat` the raw file.
- **CODE-FIXABLE-NOW.**

### M3 — Stale Calamares asset generator silently regresses the brand v3→v2
- File: `branding/calamares/make-calamares-assets.py:1-13,30-31,38-39,44-79`.
- The generator still copies the **v2 "Sen Việt"** red-lotus icon to `logo.png`
  and renders a `"NaMiOS"` wordmark in v2 colors (`INK #182E3B` / `SON #C93643`).
  The shipped `logo.png` is **v3 "Đông Sơn"** (165,782 B bronze-drum); the generator
  would emit a 61,979 B copy of the v2 icon. `branding.desc`/`show.qml` are already
  v3 (navy `#092D4F` / gold `#DEA93E`); there is no v3 generator for the Calamares logo/welcome.
- Failure scenario: anyone running the file's own documented reproduce command
  (`python3 branding/calamares/make-calamares-assets.py:20`) overwrites the v3
  installer art with v2 red-lotus art + v2 colors — a silent brand regression that
  clashes with the navy/gold installer chrome.
- One-line fix: repoint the generator at the v3 Đông Sơn kit (or delete it and add
  a v3 variant) so the documented reproduce step cannot revert the brand.
- **CODE-FIXABLE-NOW.**

### M4 — Installer defaults to "Erase disk" (destructive) as the pre-selected partitioning choice
- File: `.../etc/calamares/modules/partition.conf:114` — `initialPartitioningChoice: erase`.
- Deliberately overrides Calamares' upstream `none` (which exists to force a
  conscious pick of the destructive option). Documented as intentional (lines 94-113);
  the Choice-screen disk selector + Summary page remain as friction.
- Failure scenario: a user with a second data disk bulk-clicking Next lands on a
  Choice page with "Erase disk" already checked; if they miss the target-disk
  selector they can wipe the wrong disk. Highest-consequence item for sign-off.
- One-line fix: keep `erase` only after a real-VM confirmation that Choice+Summary
  friction is sufficient; otherwise set `initialPartitioningChoice: none`.
- **NEEDS-BOOT-TEST** (product/safety decision; confirm friction on a real VM).

### M5 — Two flagship apps (nServices/dichvu, nSecurity/antoan) ship with ZERO automated tests
- Evidence: no `test_*.py` anywhere imports `namios_dichvu` or `namios_antoan`
  (lich=2, manchieu=1, welcome=3 test files; dichvu=0, antoan=0). The "2593 passed"
  headline therefore never exercises catalog loading, status coercion, diacritic
  search, envcheck, the PKCS#11 probe, the security probes, or the pkexec actions.
- Failure scenario: a future refactor silently breaks `_coerce_entry`'s
  "unknown→blocked" coercion or `fold_vi`, and CI stays green — a regression ships.
- One-line fix: add unit tests for `catalog`/`envcheck` (dichvu) and `probes`/`actions`
  (antoan), mirroring the lich/manchieu/welcome conftest-register pattern.
- **CODE-FIXABLE-NOW** (test-coverage gap; the code itself reviewed clean).

---

## MINOR

### MN1 — i18n catalog drift: `src/namios_i18n/locale/*.json` vs the shipped chroot copy differ; tests pin the untested copy
- Files: `src/namios_i18n/locale/{vi,en}.json` vs `distro/.../opt/namios/namios_i18n/locale/{vi,en}.json`.
- `translator.py` is byte-identical across the two trees, but ~14 `vi.json` values
  differ (chroot is the polished "tệp"/"phân vùng"/"đã gắn (mount)"; src still says
  "file"/"volume"/"mount"). The ~800 string-assertion tests run against `src/`, but
  the ISO ships `distro/.../`. Each copy is internally valid (114 keys, full parity) —
  no crash, no raw-key leak; pure drift.
- One-line fix: single source of truth + a CI check asserting the two `locale/` dirs are identical.
- **CODE-FIXABLE-NOW.**

### MN2 — `translator._load_locale_file` has no guard → a missing/corrupt base JSON would crash every Python app at import
- File: `distro/.../opt/namios/namios_i18n/translator.py:134-137` (opened with no try/except), via `Translator.__init__:189-192` at module-import singleton `:263`.
- Both files are currently present and parse (validated), so this is latent. If
  `vi.json`/`en.json` were ever absent/malformed in the image, `import namios_i18n`
  raises → cascades to crash nSecurity/nAssistant/nServices/nWelcome at startup.
- One-line fix: wrap `_load_locale_file` in try/except and fall back to an empty
  catalog (degrade to raw-key display, not a dead app).
- **CODE-FIXABLE-NOW.**

### MN3 — nCalendar (lich) and nProjector (manchieu) are Vietnamese-only but their `.desktop` advertises English
- Files: `.../opt/namios/namios_lich-src/ui.py:87-98` (hardcoded VI) and
  `.../namios_manchieu-src/ui.py:73,129-133` (hardcoded VI) — neither imports
  `namios_i18n`; vs `namios-lich.desktop` / `namios-manchieu.desktop:3-9` which carry
  English `Name[en]`/GenericName/Comment.
- Failure scenario: `LANG=en_US` user opens nCalendar/nProjector → entirely
  Vietnamese UI, unlike nSecurity/nServices which do switch to English — breaks the
  bilingual contract the `.desktop` implies.
- One-line fix: add `lich.ui.*`/`manchieu.ui.*` catalogs (as antoan/dichvu do), OR
  drop the English `Name[en]`/GenericName/Comment to stop advertising EN.
- **CODE-FIXABLE-NOW.**

### MN4 — Web-shortcut launchers have a half-Vietnamese fallback `Name`
- Files: `namios-facebook.desktop:3`, `namios-tiktok.desktop:3`, `namios-youtube.desktop:3`, `namios-zalo-web.desktop:3` — `Name=Facebook (Dịch vụ web)` with `Name[vi]` but no `Name[en]`.
- Failure scenario: English locale falls back to the bare `Name`, already Vietnamese → mixed-language menu entry. Cosmetic.
- One-line fix: add `Name[en]=Facebook (Web service)` and make bare `Name=Facebook`.
- **CODE-FIXABLE-NOW.**

### MN5 — nSecurity (antoan) error-path strings are hardcoded Vietnamese (bypass i18n)
- File: `.../opt/namios/namios_antoan-src/ui.py:265` (`"Có lỗi không lường được khi kiểm tra trạng thái."`), `:160` (`"[... xem đầy đủ ở 'Show Details' ...]"`), `:163` (`"(không có nội dung)"`).
- Failure scenario: an EN-locale user hitting the rare probe-failure path sees
  Vietnamese while the rest of the window is English. Edge-path cosmetic.
- One-line fix: route these through `t()` with seeded `antoan.ui.*` keys.
- **CODE-FIXABLE-NOW.**

### MN6 — `namios-smartai` overclaims an "advanced assistant" that is never invoked
- File: `.../usr/local/bin/namios-smartai:162-178` (`backend_mode_line`).
- If `OPENAI_API_KEY`/`ANTHROPIC_API_KEY`/`NAMIOS_SMARTAI_*` is set (or a `namios`
  binary exists), the header says "có trợ lý nâng cao khả dụng", but routing is 100%
  rule-based (`route_free_text`) — no LLM is ever called. Mild capability overclaim.
- One-line fix: say "backend phát hiện nhưng chưa dùng cho phiên này", or gate the claim on an actually-wired call.
- **CODE-FIXABLE-NOW.**

### MN7 — `namios-smartai` Wine remediation opens `winecfg` on the wrong prefix
- File: `.../usr/local/bin/namios-smartai:560-564` — launches bare `winecfg` (edits `~/.wine`), but user apps run in per-app capsules with their own `WINEPREFIX`, so the change can't affect the app being troubleshot.
- One-line fix: route Wine-app help to `namios-windows-app`/capsule management, or set `WINEPREFIX` to the relevant capsule.
- **CODE-FIXABLE-NOW.**

### MN8 — `namios-wine-capsule` silently disables hash-retest when python3 is absent
- File: `.../usr/local/bin/namios-wine-capsule:189-191` (`_py_state_record_exe`) consumed at `:636-648`.
- With no python3, the "app hash changed → RETEST REQUIRED" promise (U13-10) is silently off and `capsule.json` exe-history isn't updated — no warning (unlike the sha256 branch at `:647`).
- One-line fix: warn once when python3 is missing that retest-tracking is disabled.
- **CODE-FIXABLE-NOW.**

### MN9 — `namios-compat-assessor` JSON escaper misses control characters
- File: `.../usr/local/bin/namios-compat-assessor:233` (`esc()`), used at `:247-248`.
- Escapes only `\` and `"`. A `file -b` description or TARGET containing a tab/newline would emit invalid JSON, breaking the CLI-003 envelope claim. Low probability from `file`.
- One-line fix: also escape control characters (or build JSON via python3, as sibling scripts do).
- **CODE-FIXABLE-NOW.**

### MN10 — "NaMi" vs "NaMiOS" product name inconsistency on the Welcome screen
- Files: `.../etc/calamares/branding/namios/branding.desc:72-78` (`productName: NaMi`), `show.qml:285` (`"Welcome to NaMi"`) vs the `welcome.png` wordmark which renders "NaMiOS".
- Failure scenario: first installer screen says "Welcome to the NaMi installer" beside a logo reading "NaMiOS". Cosmetic but front-and-center.
- One-line fix: standardize strings on "NaMiOS" (or regenerate `welcome.png` to "NaMi").
- **CODE-FIXABLE-NOW** for the strings; the asset regen is bundled with M3.

### MN11 — Installer launchers lack `TryExec` (no auto-hide if binary absent)
- Files: `.../usr/share/applications/calamares-install-debian.desktop:19`, `namios-go-cai-dat.desktop:10`.
- Without `TryExec`, the entry always shows and fails on click if the binary is missing, instead of hiding. (`plasma-discover --mode installed` is a valid mode; Exec/Icon/Categories otherwise valid.)
- One-line fix: add `TryExec=calamares-install-debian` / `TryExec=plasma-discover`.
- **CODE-FIXABLE-NOW.**

### MN12 — welcome autostart `Icon=namios-welcome` is a placeholder name
- File: `.../etc/skel/.config/autostart/namios-welcome.desktop` (`Icon=namios-welcome`).
- Placeholder icon not yet installed; Plasma falls back to a generic icon (no crash). Cosmetic.
- One-line fix: ship the icon or point `Icon=` at an existing themed name.
- **CODE-FIXABLE-NOW** (ship asset).

### MN13 — "Đang mở …" shown before fire-and-forget launch (soft overclaim)
- Files: `.../usr/local/bin/namios-control-panel` `open_kcm:97-110` + `do_*`, same pattern in `namios-ket-noi-thiet-bi` (do_bluetooth/do_wifi) and `namios-smartai` `confirm_and_launch`.
- `show_text "Đang mở …"` prints first, then `launch_bg <kcm> ` backgrounds (output discarded) and returns 0 immediately. If a KCM module id is wrong/absent on the built image, nothing opens and the user sees only the "opening" claim.
- One-line fix: soften wording to "Đang thử mở…" and/or a short post-launch liveness check.
- **Split**: wording change CODE-FIXABLE-NOW; verifying the KCM module ids is NEEDS-BOOT-TEST.

### MN14 — `namios-add-widgets.sh` assumes NaMiOS plasmoids are packaged
- File: `.../usr/local/bin/namios-add-widgets.sh:12-17,28` — `addWidget("org.namios.smartai"/"org.namios.workgroups")`; `evaluateScript` returns success even if the plasmoid isn't installed, then the script deletes its own autostart and never retries → desktop silently has no widget.
- One-line fix: verify plasmoid ids exist before claiming done / before self-removing the autostart.
- **NEEDS-BOOT-TEST.**

### MN15 — `namios-demo-first-login.sh` hardcodes fcitx5 engine id + X11-only deps
- File: `.../usr/local/bin/namios-demo-first-login.sh:56` (`fcitx5-remote -s unikey`), `:59` (xdotool typing), `:67` (demo PDF path).
- If the installed VN engine id differs, the Telex demo types garbled ASCII; depends on `xdotool` (X11-only) and a demo PDF asset. Demo-only.
- One-line fix: read the engine id from fcitx5 config; guard on xdotool/asset presence.
- **NEEDS-BOOT-TEST.**

### MN16 — `namios-auto-compositing.sh` treats "not a VM" as "has a working GPU"
- File: `.../usr/local/bin/namios-auto-compositing.sh:50-65` — on bare metal it sets `Compositing Enabled=true` + `OpenGLIsUnsafe=false`. On a bare-metal box with a broken/llvmpipe-only GPU this can black-screen KWin on next login, overriding the deliberately-safe default.
- One-line fix: also probe for a usable GL renderer before clearing `OpenGLIsUnsafe`.
- **NEEDS-BOOT-TEST.**

### MN17 — `locale.conf` pins timezone but sets no explicit installed-system `LANG=vi_VN` floor
- File: `.../etc/calamares/modules/locale.conf:28-29` (region/zone fixed to Asia/Ho_Chi_Minh, correct).
- No key forces the installed system `LANG=vi_VN`; the Vietnamese default relies on the installer UI language propagating. If a user flips the Welcome-page language to English, the installed locale follows. Expected Calamares behavior, worth a conscious note.
- One-line fix: document/confirm the intended installed-locale floor on a real run.
- **NEEDS-BOOT-TEST.**

### MN18 — `show.qml` Slide 3 icon row can overflow on short slideshow areas
- File: `.../etc/calamares/branding/namios/show.qml:412-433` (self-flagged `:92-98`).
- On a short area the NaMiOffice icon row can collide with the bottom slide-dots. Non-blocking (QML errors don't halt the install phase).
- One-line fix: anchor/clip the icon row above the reserved dot band.
- **NEEDS-BOOT-TEST** (visual).

### MN19 — `tai-lieu-cua-toi.desktop` (Type=Application) may trigger KDE "untrusted .desktop" prompt
- File: `.../etc/skel/Desktop/tai-lieu-cua-toi.desktop` (Exec=sh -c … dolphin). File is executable; the `$HOME/Tài liệu`→`Documents`→`$HOME` fallback chain is correct.
- Plasma 6 may show an "untrusted program" prompt for Type=Application on the desktop. The Type=Link shortcuts (computer:/, trash:/) don't have this.
- One-line fix: confirm first-login trust behavior on a real desktop; consider a `.directory`/pinned-folder approach if prompted.
- **NEEDS-BOOT-TEST.**

### MN20 — Windows-data migration imports only one user profile
- File: `.../opt/namios/namios_welcome-src/migrate.py:201-239` (`_profile_candidates`/`discover_folders`).
- `discover_folders` returns the first candidate (`source_root`, then sorted `Users/*`) that has any known folder. A partition with `Users/Alice` + `Users/Bob` migrates only Alice's folders. Documented single-profile limitation, not a safety bug.
- One-line fix: if desired, let the wizard choose among discovered profiles.
- **CODE-FIXABLE-NOW** (feature; current behavior is safe and documented).

---

## Explicitly CLEAN (reviewed, no material findings)

Python app logic (the real business flows):
- `namios_lich/lunar.py` — faithful port of the published Hồ Ngọc Đức algorithm;
  `_int=floor`, correct JD, new-moon/leap-month, Can-Chi; module self-verifies
  Tết 2020–2028, Giỗ Tổ 2024, 2023 leap month, 2000-day round-trip. UTC+7 fixed.
- `namios_lich/holidays.py` — fail-safe load (bad JSON → empty, no crash), correct
  lunar→solar per-year resolution, day-30→29 fallback for 29-day months (fixes the
  Giao thừa off-by-one), idempotent reminder store.
- `namios_lich/ui.py` — no KeyError (fallback colors always present), correct
  month navigation + today panel + reminder dialogs.
- `namios_dichvu/catalog.py` — absolute fail-safe load, unknown `realistic_status`
  coerced to **"blocked"** (never guesses "good"), NFD+casefold diacritic fold.
- `namios_dichvu/envcheck.py` — read-only (`shutil.which`/`datetime` only), PKCS#11
  probe is fixed-argv/shell=False/timeout and honestly reports "unknown" on any
  failure, never "works"; manual-check items are explicitly not auto-concluded.
- `namios_dichvu/ui.py` — honest: open-web disabled when no URL, scheme-checked,
  no fake "opened" claim; URLs are plausible real gov/vendor domains (not fabricated).
- `namios_antoan/probes.py` — fail-safe (missing tool → "not installed" + install
  hint, never a fake green tick), `ok` tri-state, honest "đang bật ≠ an toàn tuyệt đối".
- `namios_antoan/actions.py` — privileged work via `pkexec` only (never silent sudo),
  rc 126 → "you declined polkit", rc≠0 → honest error; `clamscan` detect/update honest.
- `namios_antoan/ui.py` — correct QThread pattern (moveToThread, quit/deleteLater,
  double-click guard, closeEvent cleanup), results shown verbatim.
- `namios_manchieu/display.py` — well-sourced `kscreen-doctor` parse (ANSI strip
  mandatory, numeric-ID tokens, atomic single call), correct internal/external
  classification order (EDP before DP).
- `namios_manchieu/backend.py` — success only on rc 0; fail-safe, never raises.
- `namios_manchieu/ui.py` — guarded concurrency, confirm-before-apply, honest result box.
- `namios_welcome/firstrun.py` — atomic writes + `.bak`/revert + idempotent done-marker;
  per-aspect try/except that never raises; `skipped` refuses to point defaults at
  non-existent apps/printers (`_find_desktop_file`, `lpstat -p` precheck).
- `namios_welcome/migrate.py` — copy-only (never move/delete source), never overwrites
  (`"xb"` + conflict-rename), TOCTOU-safe `open_within`, hibernation refusal,
  BitLocker-key skip, no file content logged.
- `namios_i18n/translator.py` — bulletproof `t()` (effective→VI→EN→raw-key, never
  KeyError/None), safe `format_map` (missing param → "", no injection), `DEFAULT_LANG=VI`,
  full vi↔en parity across all app catalogs.
- branding modules (`*/branding.py`) — fail-safe fallback colors, no KeyError if
  `brand.json` is missing/corrupt.

Launchers / installer / docs:
- `namios-ket-noi-thiet-bi` — honest device probing (`scanimage -L`/`lsusb`/`mtp-detect`
  with timeouts), never claims "connected", degrades to CUPS web UI / konsole with clear guidance.
- `namios-panel-polish.sh` — correct marker/idempotency, qdbus fallback, honest in-file notes.
- `namios-smartai-policy.sh` — sound policy/audit/catalog library (except the shared M2 `|| cat`).
- `namios-compat-assessor` — static-only, every route labeled a suggestion with
  `final_verdict: REQUIRES_REAL_RUN` + device/token disclaimer (except MN9).
- Calamares `settings.conf` / `branding.desc` / `show.qml` / hook `0710` — schema-valid,
  fail-soft, `quit-at-end:false` (no fake auto-complete), all referenced images exist,
  hook is verify-only + idempotent + no `curl|bash`/`eval`.
- `GO-CAI-DAT.md`, `CONTROL-PANEL.md` — honest docs (no fabricated URLs, no overclaim;
  "uninstall" is explicitly only a shortcut into Discover's Installed tab, not a fake stub).
- Desktop shortcuts (`may-tinh-cua-toi`/`thung-rac` Type=Link `computer:/`/`trash:/`;
  `tai-lieu-cua-toi` Documents fallback chain) — targets valid.
- All 25 `.desktop` Exec/Icon targets resolve; the 6 wrapper-creating hooks
  (`0305/0307/0308/0309/0311` + `0300`) correctly rename `*-src`→package, set
  `PYTHONPATH=/opt/namios`, preflight PySide6, and `exec python3 -m <pkg>`.

---

## CODE-FIXABLE-NOW — full list (fix these without hardware)

1. **B1** `namios-chan-doan:150-164` — remove `{2}` interval regex (use `[0-9a-fA-F][0-9a-fA-F]…`) or force `gawk`; add a driverless-fixture test. (Fabricated driver "[OK]" on default mawk — reproduced.)
2. **M1** `namios-wine-capsule:429-432` (+ consumer `namios-windows-app:184,413-416`) — stop mapping child non-zero exit to "sandbox failed / app NOT run"; report the wine exit code neutrally.
3. **M2** `namios-chan-doan:384` and `namios-smartai-policy.sh:103` — replace `|| cat "$src"` with a `[REDACTION-FAILED]` marker / abort; never dump raw source while claiming it was redacted.
4. **M3** `branding/calamares/make-calamares-assets.py:30-79` — repoint at the v3 "Đông Sơn" kit (or remove) so the documented reproduce step can't revert `logo.png`/`welcome.png` to v2.
5. **M5** add unit tests for `namios_dichvu` (`catalog`, `envcheck`) and `namios_antoan` (`probes`, `actions`), using the lich/manchieu conftest-register pattern.
6. **MN1** `src/namios_i18n/locale/*` vs `distro/.../namios_i18n/locale/*` — make one the source of truth; add a CI check that the two `locale/` dirs are identical (tests currently pin the copy the ISO doesn't ship).
7. **MN2** `namios_i18n/translator.py:134-137` — wrap `_load_locale_file` in try/except → empty-catalog fallback (missing base JSON must not crash every app).
8. **MN3** `namios_lich-src/ui.py` + `namios_manchieu-src/ui.py` — either add `_i18n.py` catalogs or drop the English `Name[en]`/GenericName/Comment from `namios-lich.desktop`/`namios-manchieu.desktop`.
9. **MN4** `namios-facebook/tiktok/youtube/zalo-web.desktop:3` — add `Name[en]=…` and make bare `Name=` language-neutral.
10. **MN5** `namios_antoan-src/ui.py:160,163,265` — route the three hardcoded Vietnamese error-path strings through `t()`.
11. **MN6** `namios-smartai:162-178` — stop claiming "trợ lý nâng cao khả dụng"; say "backend phát hiện nhưng chưa dùng".
12. **MN7** `namios-smartai:560-564` — route Wine help to `namios-windows-app`/capsule (or set the capsule `WINEPREFIX`), not bare `winecfg` on `~/.wine`.
13. **MN8** `namios-wine-capsule:189-191` — warn once when python3 is absent that hash-retest tracking (U13-10) is disabled.
14. **MN9** `namios-compat-assessor:233` `esc()` — also escape control characters (or build JSON via python3).
15. **MN10** `branding.desc:72-78` + `show.qml:285` — standardize product name on "NaMiOS" (string side).
16. **MN11** `calamares-install-debian.desktop:19` + `namios-go-cai-dat.desktop:10` — add `TryExec=`.
17. **MN12** `etc/skel/.config/autostart/namios-welcome.desktop` — ship the `namios-welcome` icon or point `Icon=` at an existing themed name.
18. **MN13 (partial)** `namios-control-panel`/`namios-ket-noi-thiet-bi`/`namios-smartai` — soften "Đang mở…" to "Đang thử mở…" (KCM-id verification is boot-test).
19. **MN20 (optional)** `migrate.py` — multi-profile selection (current single-profile is safe/documented).

## NEEDS-BOOT-TEST — must confirm on a real ISO/VM
- **M4** `partition.conf:114` `initialPartitioningChoice: erase` — confirm Choice+Summary friction is enough, else revert to `none`.
- **M1 validation** — exercise wine-capsule success/non-zero-exit on real wine+bwrap.
- **MN13 (part)** verify the KCM module ids (`kcm_updates`, etc.) open on the built image.
- **MN14** `namios-add-widgets.sh` — confirm `org.namios.*` plasmoids are packaged.
- **MN15** `namios-demo-first-login.sh` — confirm the fcitx5 engine id + xdotool/PDF deps.
- **MN16** `namios-auto-compositing.sh` — confirm GL renderer is usable before enabling compositing on bare metal.
- **MN17** `locale.conf` — confirm installed-system `LANG=vi_VN` floor on a real run.
- **MN18** `show.qml:412-433` — confirm slide-3 icon row doesn't overlap the dots.
- **MN19** `tai-lieu-cua-toi.desktop` — confirm no "untrusted .desktop" prompt on first login.
