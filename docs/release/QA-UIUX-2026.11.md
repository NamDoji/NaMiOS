# NaMiOS 2026.11 "Đông Sơn" — UI/UX QA Audit (role: independent UI/UX QA)

> **Scope:** does the system look/feel like a polished Windows 11 experience, and is it
> visually CONSISTENT + accessible? **READ-ONLY audit** — no code/config was changed to
> produce this document. `verified_on_host: NO` for every item unless marked otherwise —
> this is a static source audit from inside a headless container; nothing here was seen
> rendered on a real KDE Plasma session. Where a finding can only be confirmed by booting,
> it is tagged **NEEDS-BOOT-TEST**; where the defect is provable from source alone
> (wrong hex, missing property, dead code path, contradictory doc), it is tagged
> **CODE-FIXABLE-NOW**.
>
> **Method:** read `docs/design/{WINDOWS11-PARITY,NAMI-DESIGN-TOKENS,NAMI-UI-KIT,
> NAMI-GLOSSARY-VI,DESIGN-SYSTEM,CONSISTENCY-AUDIT,HIG-ADOPTION-VERDICT,P0-UI-AUDIT,
> MODERN-FUTURE-UX}.md` + `nami-tokens.json`; the shell config
> (`appletsrc`/`kwinrc`/`kdeglobals`); `usr/share/color-schemes/*.colors`;
> `usr/share/plasma/desktoptheme/NaMiOS-Sen/**`; `usr/share/aurorae/themes/NaMiOSLotus/**`;
> all 7 PySide6 app `ui.py`/`branding.py`/`_i18n.py`; all 14 QML files under
> SDDM/Calamares/Plasma look-and-feel/plasmoids/`usr/share/namios/qml/`; `.desktop` files;
> `design/tokens.json`; `design/wallpaper-manifest.json`. Every file:line below was either
> read directly or spot-verified with a follow-up grep/read before inclusion.

---

## 0. Verdict (read this first)

**The repo is mid-migration, not broken, and not finished.** As of commit `93f200a`
(today, 2026-11-11), the OS shipped a genuine "Đông Sơn v3" rebrand wave: taskbar
centered (Win11-style), window buttons moved to the right (`min/max/close`), a real
semantic color-token layer with measured WCAG contrast, and most of the
chrome-critical surfaces (NaMiOS.colors, desktoptheme, SDDM theme.conf, Calamares
branding.desc) were correctly repainted to v3. **But the migration stopped at the
"shell chrome" layer and did not reach the "app content" layer**: every one of the 7
PySide6 apps and 5 of 14 QML surfaces still carry stale v2 hex, invented off-palette
grays, or fully independent, un-synced copies of "what navy/ivory/gold is." The
project's own top-level "single source of truth" doc (`DESIGN-SYSTEM.md`) is itself
stale — it still asserts the *previous* v2 palette as canonical, written the same day
as (but before) the newer `nami-tokens.json`/`NAMI-DESIGN-TOKENS.md` v3 spec that
supersedes it. That doc-level contradiction is very likely *why* downstream apps/QML
still show v2 colors — anyone following "the" design system doc today gets the wrong
palette.

**Win11 parity:** real and verifiable at the shell level (centered taskbar, buttons
right, Kickoff start menu, Dolphin address bar, desktop icons, Meta+E/Meta+I
shortcuts). Falls apart at: the Aurorae window-border theme (explicitly macOS-styled,
currently disabled but one `kwinrc` uncomment away from regressing silently), the SDDM
login screen (capsule/pill inputs read iOS, not Win11; zero hover feedback on
clickable power actions; zero accessibility API usage anywhere on the login screen),
and the Settings hub (a `kdialog` list of 8 buttons, not a searchable Windows-11-style
Settings app).

**Accessibility:** the written spec (`NAMI-UI-KIT.md`, `nami-tokens.json`) is
genuinely rigorous (35/36 WCAG pairs measured and passing, documented focus-ring/
error-structure/5-part rules). Implementation is **far behind the spec**: zero
`setAccessibleName`/`setAccessibleDescription` calls across all 7 PySide6 apps; the
SDDM login screen has zero `Accessible.*` properties on any interactive control; a
shipped high-contrast color scheme (`NaMi-HighContrast.colors`) exists but is wired
into no settings UI anywhere, so a real user has no discoverable way to turn it on.

---

## 1. Win11-parity scorecard

| Area | Verdict | Evidence |
|---|---|---|
| Taskbar centered | **DONE** (static, low risk) | `etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc:60` `AppletOrder=6;2;3;7;4;5` + 2 `org.kde.plasma.panelspacer expanding=true` applets (`[Applets][6]`/`[7]`) |
| Panel floating + rounded | **DONE** | `appletsrc:64` `floating=1`; `NaMiOS-Sen/widgets/panel-background.svg` 28px radius |
| Window buttons on right, Win order | **DONE** (Breeze decoration) | `etc/skel/.config/kwinrc:95-97` `[org.kde.kdecoration2] ButtonsOnLeft=` / `ButtonsOnRight=IAX` (live, not commented) |
| Custom window-border theme (Aurorae `NaMiOSLotus`) | **OFF, by design — but a landmine** | `kwinrc:63-65` Aurorae `library=`/`theme=` lines are **commented out** (safe — login-hang history `dfbbf3c`). But `NaMiOSLotus/metadata.desktop` literally says *"3 nút tròn san hô/vàng/đỏ-son kiểu macOS"* — if anyone uncomments those 2 lines to "finish the job" without first redrawing the buttons, the OS silently reverts to a macOS-styled window border. No guard/comment-linked warning prevents this. |
| Start menu (Kickoff) | **DONE**, close to Win11 | search-on-top + pinned grid + Apps tab + power row — `WINDOWS11-PARITY.md §2` |
| Start menu "workgroups" app-group tile (Office/Thuế/Kế toán…) | **SHIPPED BUT BROKEN** | see §2.1 — `org.namios.workgroups/main.qml` uses stale v2 + generic Tailwind-style colors unrelated to any brand token |
| File manager (Dolphin) feel | **DONE** | editable address bar, Quick Access, space info confirmed in `dolphinrc` |
| Settings hub ("Cài đặt") | **PARTIAL** | `namios-control-panel` is a `kdialog` 8-item list, not a searchable native app; no accessibility-contrast entry point (see §2.5) |
| Quick Settings / Action Center (Win+A) | **NOT ATTEMPTED** | systray used as-is; no "Cài đặt nhanh" grouping yet (`WINDOWS11-PARITY.md §7`) |
| Snap / Task View (Win+Tab) | **DONE** | Quick Tile + Overview (`Meta+W`/`Meta+Tab`) confirmed in `kglobalshortcutsrc` |
| Login screen (SDDM) Win11-adjacent feel | **PARTIAL, undermined by implementation gaps** | centered-bottom login block + top chrome is structurally Win11-ish, but capsule/pill-shaped inputs (`radius: height/2`) read iOS/Material, not Fluent; zero hover feedback on Sleep/Restart/Shut Down; zero accessibility |
| Installer (Calamares) "Windows 11 Setup" feel | **PARTIAL** | intentional Win11-Setup layout grammar (dark sidebar, top accent bar, slide dots) confirmed in `show.qml`, but introduces 2 more undocumented off-palette colors (`#274664`, `#B2B9BA`) |
| Desktop icons ("Máy tính của tôi"/"Tài liệu của tôi"/"Thùng rác") | **DONE**, nice touch | bilingual `Name`/`Name[en]` = "This PC"/"My Documents"/"Trash" |
| Keyboard habits (Meta+E Explorer, Meta+I Settings) | **DONE** | `kglobalshortcutsrc:103` `Meta+E` → Dolphin; Meta+I → systemsettings (line ~214+) |
| Mica/Acrylic materials | **Correctly deferred** | `blurEnabled`/`contrastEnabled=true` configured but gated behind `namios-auto-compositing.sh` GPU detection — correct trade-off for low-end hardware, not a bug |

---

## 2. Ranked findings

### 2.1 BLOCKER

**B1. `SenVietPalette.qml` — the shared QML palette singleton itself carries one stray v2 hex, inherited everywhere.**
`distro/live-build/config/includes.chroot/usr/share/namios/qml/SenVietPalette.qml:38`
```qml
readonly property color textSecondary: dark ? "#C9D3D6" : "#52646B"
```
`#52646B` is the retired v2 "Sen Việt" `text-secondary` value, not derived from the v3
Đông Sơn table. It fans out through `pal.textSecondary` into every consumer:
`ErrorCard.qml:150,162,213`, `AIPlanCard.qml:100,153,194`, `ConnectionStepper.qml:137,163`,
`UpdateCenterPL19.qml` (17+ call sites), `Gallery.qml:71` (hand-copied). Note: `nami-tokens.json`
§2.1 actually *also* lists `#52646B` as the current v3 `text-secondary` value (it's one of the
"functional, not brand" colors that didn't change between v2→v3), so the hex itself may be
correct by coincidence — but nothing in `SenVietPalette.qml` traces this back to
`nami-tokens.json`, so it reads as a drift risk regardless of whether today's value happens
to be right. **Fix:** add a comment anchoring this line to `nami-tokens.json §2.1 text-secondary`
so a future "purge all old hex" pass doesn't break it by "fixing" a non-bug.
CODE-FIXABLE-NOW.

**B2. `org.namios.workgroups` Start-menu widget — the one feature `WINDOWS11-PARITY.md` names as the next priority ships with stale v2 AND generic non-brand colors.**
`distro/live-build/config/includes.chroot/usr/share/plasma/plasmoids/org.namios.workgroups/contents/ui/main.qml:42-47`
```qml
{ label: "Văn phòng",  badge: "VP", c1: "#e2776b", c2: "#d64c3e", ink: false },
{ label: "Thuế",       badge: "%",  c1: "#ff8b6c", c2: "#d94d43", ink: false },
{ label: "Kế toán",    badge: "KT", c1: "#ffe1a1", c2: "#e5a53e", ink: true  },
{ label: "Bảo hiểm",   badge: "BH", c1: "#3b82f6", c2: "#1d4ed8", ink: false },
{ label: "Giáo dục",   badge: "GD", c1: "#22c55e", c2: "#15803d", ink: false },
{ label: "Hành chính", badge: "HC", c1: "#c084fc", c2: "#7c3aed", ink: false }
```
"Thuế"/"Kế toán" use the retired v2 coral/gold family (`#D94D43`/`#E5A53E`/`#FFE1A1`);
"Bảo hiểm"/"Giáo dục"/"Hành chính" use **generic Tailwind-CSS blue/green/purple that
appear nowhere in any NaMiOS palette, v2 or v3**. Also `main.qml:65,123` `color: "#f7f6f1"`
and `:156` `color: "#b7c4cf"` are v2 near-duplicate grays, and `:116` `"#172c3d"` is an
off-by-a-few-RGB-units v2 text color, not v3 navy `#092D4F`. Since this widget is the
flagship deliverable of `WINDOWS11-PARITY.md` backlog item #5 ("landing Start nhóm
việc"), shipping it with 3 random generic colors undermines the one-brand-identity goal
most visibly of anything in the repo. CODE-FIXABLE-NOW (pure hex-literal edit, 6 lines).

**B3. `org.namios.smartai` plasmoid — same class of bug, plus it's non-interactive despite being the "Ask SmartAI" entry point.**
`distro/live-build/config/includes.chroot/usr/share/plasma/plasmoids/org.namios.smartai/contents/ui/main.qml:40-41` live v2 coral gradient `"#ff8b6c"→"#d94d43"`; `:57` `color: "#f7f6f1"` (v2 ivory, should be `#FFF9EF`); `:63` `color: "#b7c4cf"` (v2 gray). Separately — **zero `MouseArea` anywhere in the file**: the widget whose entire stated purpose (per its own header comment) is to be a clickable "Hỏi SmartAI" entry point has no click handler at all. It is presently a static, unclickable pill. CODE-FIXABLE-NOW for both the colors and the missing interactivity (the latter is a functional gap, not just cosmetic).

**B4. Design-system documentation points to the wrong palette.** `docs/design/DESIGN-SYSTEM.md` (dated 2026-11-11, explicitly self-titled "hợp nhất một nguồn sự thật" / "the consolidated single source of truth") declares the *previous* **Sen Việt v2** palette as canonical and currently-shipping: `son #C93643`, `muc_dem #122A3A`, `vang_tam #F2C66D`, `action.primary teal #006E72` (§1.1–1.2). This is dated the **same day as**, but chronologically **before**, `docs/design/nami-tokens.json` / `NAMI-DESIGN-TOKENS.md` / `WINDOWS11-PARITY.md`, which establish **Đông Sơn v3** (`navy #092D4F`, `gold #DEA93E`, `vermilion #D64C3E`, `teal #278F8D`) as authoritative and explicitly supersede v2. Commit `93f200a` (later the same day) then migrated the live shipped assets (`NaMiOS.colors`, `theme.conf`, `branding.desc`) to v3 — but nobody went back and updated `DESIGN-SYSTEM.md`. **A contributor who opens "the" design system doc today — which is exactly what it's named to encourage — will build against the wrong, now-retired palette.** This is very likely the root cause of findings B2/B3 and the per-app `branding.py` drift in §2.2: those files look like they were built by someone correctly following `DESIGN-SYSTEM.md` before the v3 wave landed. **Fix:** update `DESIGN-SYSTEM.md` §1 (or add a one-line banner matching the style already used in `CONSISTENCY-AUDIT.md`/`NAMI-DESIGN-TOKENS.md` headers) pointing to `nami-tokens.json` as the new authority, superseding this file's own §1. CODE-FIXABLE-NOW, and arguably the single highest-leverage fix in this whole report — it's a documentation change that prevents the next 10 regressions of this exact kind.

**B5. `namios_welcome` first-run wizard silently swallows every error with zero user-facing feedback.**
`src/namios_welcome/ui.py` (byte-identical to `opt/namios/namios_welcome-src/ui.py`):
- `:204-207` `WelcomeDoneMarker.mark_done()` `OSError` → `pass`
- `:235-244` `FirstRunValidationError`/`OSError` from applying IME/font/default-app choices → `return`, no dialog — user's choices silently did not save
- `:246-252` `apply_runtime_desktop_settings` wrapped in bare `except Exception: pass`
- `:256-264` Windows-data-migration failure (`WindowsVolumeUnsafeError`/`OSError`, e.g. BitLocker-locked or hibernated source drive) → `pass`, no dialog

This is not "missing the 5-part error pattern" (§2.2) — it's the absence of *any* error UI
at all, on the very first screen a new user sees. A user who points the migration step at
an unreadable Windows volume will be told nothing went wrong and nothing will have been
migrated. CODE-FIXABLE-NOW (each site needs one `QMessageBox`/system-notification call;
no new infrastructure required since `namios_i18n` is already wired into this file).

**B6. `namios_lich` (Calendar) has no exception handling around any user-triggered action — real crash risk, not just a missing dialog.**
`distro/live-build/config/includes.chroot/opt/namios/namios_lich-src/ui.py`. The file's
**only** `try/except` guards the brand-color loader (`:109-116`); none of
`_on_add_reminder`, `_on_manage_reminders`, `_refresh_month_grid`, `_refresh_upcoming`
wrap the calls into `holidays.py`/`lunar.py`/the file-backed reminders store. A corrupted
reminders file or a full disk produces an unhandled Python traceback, not a dialog —
worse than every other app in the suite (which at minimum swallow silently). Also:
`namios_lich` has **zero `namios_i18n` import** (confirmed via grep) — it is 100%
hardcoded Vietnamese with no English fallback at all, unlike 4 of its 6 siblings.
CODE-FIXABLE-NOW for the exception handling (wrap the 4 handlers); the i18n gap is a
larger, separate piece of work.

**B7. Status/semantic colors in `namios_dichvu` and `namios_antoan` are invented independently per app and match no v3 token.**
`opt/namios/namios_dichvu-src/branding.py:43-46`:
```python
STATUS_WORKS_WEB = "#2E7D32"      # green, not v3 success #127A52
STATUS_WORKS_NATIVE = "#1B5E8A"   # blue — no blue exists anywhere in v3
STATUS_WINE_CANDIDATE = "#B8860B" # not v3 warning #965300
STATUS_BLOCKED = "#C62828"        # not v3 danger #A02E22
```
`opt/namios/namios_antoan-src/branding.py:44-47` declares a **second, independently-named**
set (`STATUS_OK`, `STATUS_ATTENTION`, `STATUS_OFF`, `STATUS_UNKNOWN`) that numerically
*happens* to match 3 of the 4 dichvu values — by coincidence, not by shared code (verified:
these are two separate literal dicts, not an import of one shared module). v3 already
defines exactly the tokens this needs (`success #127A52/#59C798`, `warning #965300/#F6BB68`,
`danger #A02E22/#E48A81`) — neither app uses them. CODE-FIXABLE-NOW: point both at the v3
tokens and delete one of the two duplicate definitions.

**B8. The mandated 5-part error structure (NAMI-UI-KIT.md §3) is implemented nowhere end-to-end, including in the app the design doc names as "closest to compliant."**
`NAMI-UI-KIT.md` itself documents parts (2)/(3) as present in `namios_assistant`'s offline-KB
answers, but reading `opt/namios/namios_assistant-src/ui.py:315-317` shows the actual
generic-failure path (`_on_ask_failed`) renders one sentence with **no error code, no
correlation_id, no Retry/Help buttons** — just prose "Hãy thử lại" (try again), not a button.
`ErrorCard.qml` (the QML equivalent, used in `UpdateCenterPL19.qml`) gets parts (1)(2)(4)
right but fails part (5): `ErrorCard.qml:157-166` renders the error code/correlation_id as
plain `Text` with no `textInteractionFlags: Qt.TextSelectableByMouse` — Qt's default is
**not selectable**, so a user literally cannot copy the string by mouse-drag, let alone via
a dedicated Copy button. Every PySide6 app's own error dialogs (`QMessageBox.information`/
`.warning` in lich/dichvu/antoan/manchieu) are plain one-liners with zero parts of the
5-part structure. CODE-FIXABLE-NOW for the QML copy-affordance (one property) and the
assistant wiring (doc already names the exact plumbing: `namios_core/errors.py`/
`envelope.py`); the PySide6-wide rollout is bigger (see MAJOR M1 below).

### 2.2 MAJOR

**M1. No shared button/dialog/error widget across the 7 PySide6 apps — 4 independent copies of the same fallback-color dict, and each app invents its own non-brand gray palette for 90% of its chrome.**
`branding.py` exists in 4 apps (dichvu/antoan/manchieu/assistant) plus an inline 5th
reimplementation in `namios_lich/ui.py:102-118` — all with an identical literal
`_FALLBACK_COLORS` dict (confirmed byte-for-byte equal keys/values), none importing a
shared module. Separately, every `branding.py`'s actual QSS stylesheet uses generic,
non-token grays for backgrounds/borders/hover states instead of v3 `ivory`/`ivory-subtle`/
derived-hover tokens — e.g. `namios_assistant-src/branding.py:69,91,102,104,110,123,
136,148,149,152` (`#FFFFFF`, `#FAFAFA`, `#F1F1F1`, `#DDDDDD`, `#777777`, `#CCCCCC`,
`#FBEAEA`, `#888888`, `#999999`); the identical pattern repeats in `dichvu-src/branding.py`
(`#F4F4F4`/`#CCCCCC`/`#DDDDDD`/`#666666`/`#555555`/`#888888`/`#AAAAAA`/`#FBEAEA`),
`antoan-src/branding.py`, and `manchieu-src/branding.py`. The net effect: every PySide6
app window looks like a generic light-gray Qt app, not the warm navy/ivory/gold NaMiOS
identity that the desktop shell, SDDM, and Calamares all correctly share. `teal` (#278F8D),
the officially-designated secondary accent, is used in **none** of the 5 apps that have
custom QSS. `NAMI-UI-KIT.md §7` already names this exact gap ("Tạo 1 thư viện widget dùng
chung... thay vì mỗi app tự QSS") — this audit confirms it is the single largest
consistency gap in the whole product. CODE-FIXABLE-NOW as a find-and-replace against the
ivory/ivory-subtle/vermilion-light tokens; architecturally better as one shared QSS module.

**M2. i18n architecture is split down the middle — half the apps are bilingual, half are Vietnamese-only, with no indication to the user which is which.**
`namios_welcome`, `namios_dichvu`, `namios_antoan`, `namios_assistant` route every string
through `namios_i18n.t()` with full VI/EN catalogs. `namios_lich` and `namios_manchieu`
have **zero `namios_i18n` import** — confirmed via grep — meaning `NAMIOS_LANG=en` silently
has no effect on 2 of the 6 custom apps. A user who sets the system to English will get a
product that is English in 4 apps and Vietnamese-only in the other 2, with no way to tell
in advance which is which. CODE-FIXABLE-NOW to detect/flag; fixing it properly (adding
i18n to lich/manchieu) is new work, not a one-line patch.

**M3. Hardcoded strings bypass the i18n layer in otherwise fully-translated files, and one string mixes English mid-sentence into Vietnamese.**
`opt/namios/namios_antoan-src/ui.py:262-266` (`_on_probe_failed`): headline string is a
raw Python literal, not routed through `t()`, inside a class where every other string is.
`opt/namios/namios_assistant-src/ui.py:264-268`: same pattern on a clipboard-OCR failure
message. `opt/namios/namios_manchieu-src/ui.py:129-133`: a single footer sentence says
*"mở Cài đặt Hiển thị KDE... mở **System Settings** → Hiển thị"* — the same UI referred to
once correctly in Vietnamese, once left as untranslated English, in the same sentence.
CODE-FIXABLE-NOW (each is a 1-2 line string fix).

**M4. Zero accessibility API usage across all 7 PySide6 apps, confirmed by repo-wide grep.** No
`setAccessibleName`/`setAccessibleDescription`/`setTabOrder` calls anywhere in
`opt/namios/*-src/ui.py` or `src/namios_welcome/ui.py`. Concretely harmful instances:
`namios_antoan-src/ui.py` — 5 colored status dots (Update/Firewall/AppArmor/Antivirus/
Backup) with no accessible name distinguishing them for a screen reader, despite
`NAMI-UI-KIT.md §4` explicitly requiring "Icon có `accessibleName`" for exactly this
pattern; `ui.py:196` the dot itself is `setFixedSize(14, 14)`, under both the 32×32 and
44×44 minimums (low practical risk since it's non-interactive, but it is also
unlabeled, compounding the issue). `namios_assistant-src/ui.py:162`
`self._transcript.setFocusPolicy(Qt.FocusPolicy.NoFocus)` removes keyboard
focusability from the chat transcript — a keyboard/screen-reader user cannot Tab into
the conversation history at all. CODE-FIXABLE-NOW (the `NoFocus` flag flip is a
one-line fix; adding accessible names is mechanical but touches every app).

**M5. SDDM login screen: zero `Accessible.*` properties on any control, and zero hover/press feedback on any of the 3 power actions.**
`distro/live-build/config/includes.chroot/usr/share/sddm/themes/namios/Main.qml` — the
username field, password field, avatar picker, login button, session selector, and the
3 footer actions (Sleep/Restart/Shut Down, lines ~439-462) have no `Accessible.name`/
`role` anywhere in the file. The 3 footer actions are plain `Text` + `MouseArea
anchors.fill: parent` with **no `hoverEnabled`, no visual state change on hover or
press** — contradicted directly by Win11's own login screen, where the equivalent
power/network/accessibility icons highlight on hover. Click targets for these 3 actions
are also effectively just the text glyph bounds (~16-20px tall), under both the 32px
desktop and 44px touch minimums the rest of the design system enforces via
`SenVietButton`'s 40px `implicitHeight`. CODE-FIXABLE-NOW for all three (add
`hoverEnabled`+ color-swap state, add `Accessible.name`, wrap in a min-height
container) — none require a boot to identify, though the lived experience needs
boot-test to confirm with Orca.

**M6. SDDM login inputs and button use full capsule/pill radii (`radius: height/2`), breaking the 8/12/16px radius scale used everywhere else and reading as iOS/Material rather than Win11 Fluent.**
`Main.qml:297` (username), `:326` (password), `:362` (login button) — all
`radius: height/2`. `DESIGN-SYSTEM.md §3.1` and the newer `nami-tokens.json §5`
("radius: sm 8 · md 12 · lg 16 · pill 999 only for chips") both establish that only
pill-shaped *chips/status badges* should use a full radius; text inputs and primary
buttons should use 8-16px. Win11 Fluent text inputs/buttons use small discrete corner
radii, not capsules — the current SDDM greeter reads closer to an iOS/Android login
sheet than Windows 11. `Splash.qml:356,364` (progress track/fill) repeats the same
capsule pattern. CODE-FIXABLE-NOW — static numeric values in source.

**M7. At least 5 independently-maintained "what is navy/gray" literals exist outside `SenVietPalette.qml`, with no single source of truth or build-time check.** `theme.conf:55`/
`Main.qml:101`/`Clock.qml:55`/`Splash.qml:265,314` all hardcode the retired v2 gray
`#B7C4CF` as "dim text on navy," each independently commenting that the contrast math
checks out (true — 7.87:1 on navy — but it's still the wrong, retired literal, not a v3
derivative). Separately, `show.qml:201` (`#274664`), `Splash.qml:193` (`#0E3A63`), and
`org.namios.smartai/main.qml:25` (`Qt.rgba(0.06,0.13,0.18,0.72)` ≈ `#0F212E`) are **three
different, undocumented "lighter navy" inventions** across three files that architecturally
cannot import the shared `SenVietPalette.qml` (SDDM greeter, Calamares, and a Plasma
look-and-feel splash all run in isolated Qt/QML contexts) — yet no lint/CI step cross-checks
these against each other or against `nami-tokens.json`. `show.qml:312,356,401,473` also use
`#B2B9BA` for every installer slide's secondary text, matching neither v2 nor v3
`text-secondary`. `Main.qml:406` uses an ad hoc `#F08A8F` for the login-failed/Caps-Lock
notice, matching neither v2 `#E56365` nor v3 `vermilion-light #E48A81`. Root cause is
architectural (no shared-palette import path across package boundaries), so the practical
fix is a documented "cross-package navy/gray palette" reference table (even just a comment
block duplicated into each isolated file) rather than a single import. CODE-FIXABLE-NOW to
reconcile the values; the governance (how to stop the next drift) needs a small CI grep
step, which doesn't exist today (confirmed: no CI workflow references "contrast" or
"accessib" at all).

**M8. `UpdateCenterPL19.qml` has 5 `QQC2.Switch` controls with no accessible name and no `text:` property — a screen reader announces "switch," not what it does.**
`distro/live-build/config/includes.chroot/usr/share/namios/qml/UpdateCenterPL19.qml:197`
(`darkSwitch`), `:202` (`motionSwitch`), `:454` (pause switch), `:473` (`meteredLimit`),
`:480` (`chargeOnly`) — each paired only with a visually-adjacent `Text` label with no
programmatic association. CODE-FIXABLE-NOW (add `Accessible.name` to each, or set
`text:` directly on the Switch).

**M9. No automatic Vietnamese translation of standard Qt dialog/wizard button labels — "Back/Next/Finish/Cancel/OK" risk shipping in English on every PySide6 dialog.**
`QWizard`'s standard navigation buttons and `QMessageBox`/`QDialogButtonBox`'s standard
buttons (OK/Cancel/Yes/No/Retry) get their text from Qt's own base translation catalogs
(`qtbase_<locale>.qm`), not from `namios_i18n`. No package list under
`distro/live-build/config/package-lists/*.list.chroot` installs a Qt6 translations
package (grepped for "qt"/"translat"/"l10n" — zero hits). If this package is indeed
missing from the image, every `namios_welcome` wizard page, every `QMessageBox` in
lich/dichvu/antoan/manchieu, and every standard Qt dialog across the OS will render its
navigation buttons in English regardless of how carefully each app's own strings were
translated — a systemic, repo-wide inconsistency that is easy to miss because it's
invisible in source (the English text is Qt's, not this repo's). **Needs verification**
that Debian trixie's actual Qt6 translation package name is added if missing (I could not
confirm the exact package name without network access to the Debian archive — recommend
the owning team verify against `apt-cache search qt6 | grep -i l10n` on a real build host
and add it to `0100-desktop-kde.list.chroot` or a dedicated l10n list if absent).
CODE-FIXABLE-NOW once the package name is confirmed; otherwise NEEDS-BOOT-TEST to see
actual button text.

**M10. `design/tokens.json` (PL12) still hardcodes the dead ruby/navy palette and is not clearly marked unsafe-to-copy-from at the point someone would open it.** `design/tokens.json`
`$meta.title: "NaMiOS — Design tokens v1 (PL12)"`, `brand_note` (lines ~111) literally
says *"BẮT BUỘC = ruby NaMiOS đã chốt... #a21f46... KHÔNG đổi giá trị brand ở file này"*
(mandatory, do not change) — directly contradicting the fact that this palette was
retired twice over (first by Sen Việt v2, then by Đông Sơn v3). Confirmed **not currently
loaded by any runtime code** (`src/namios_ux/tokens.py` is a generic WCAG-math utility, it
does not read this JSON file) — so the live risk is copy-paste by a future contributor,
not a runtime bug today. Separately, this exact file's `light.surface: "#f4f6fb"` value
is the one used verbatim in `distro/live-build/config/includes.chroot/usr/share/namios/
huong-dan-nhanh.html:21` (`background: #f4f6fb`) — a shipped, user-facing HTML page — which
confirms the "it gets copied" risk is not hypothetical. CODE-FIXABLE-NOW: add a bold
"RETIRED — do not use, see nami-tokens.json" banner at the top of `design/tokens.json`
(the file's own `brand_note` currently says the opposite) and fix the one confirmed leak
in `huong-dan-nhanh.html` to use `#FFF9EF` (v3 ivory).

**M11. The shipped `NaMi-HighContrast.colors` scheme is invisible to the product's own Settings surface — no Accessibility entry point exists anywhere.** Confirmed: no
`kaccessrc` shipped in `etc/skel/.config`, and `usr/local/bin/namios-control-panel`
(the custom "Cài đặt" hub, 8 kdialog buttons) has no "Tương phản cao"/Accessibility
entry at all (grepped for "Accessibility"/"tuong phan"/"Tương phản" — zero hits). A user
can only reach the color scheme by independently knowing to open System Settings →
Colors and finding it in KDE's auto-discovered list — there is no product-level
affordance, despite Windows 11's own Settings app giving Contrast Themes a prominent,
named entry. CODE-FIXABLE-NOW: add a 9th button to `namios-control-panel` mapping to
`kcmshell6 kcm_colors` (or equivalent), matching the existing 8-button pattern exactly.

### 2.3 MINOR

- **`design/tokens.json` typography/radius/motion scales also diverge** (h1:24 vs the
  current h1:28; radius 6/10/16 vs the current A/B two-scale system) — already correctly
  flagged as stale in `CONSISTENCY-AUDIT.md §8` and `DESIGN-SYSTEM.md §3.1`; no new
  finding, just confirming the prior audit is still accurate.
- **4 `branding.py` docstrings still literally say `"Sen Việt" v2.0`** in their module
  header even though their `_FALLBACK_COLORS` dict values were already updated to v3 hex
  (`dichvu-src/branding.py:1`, `antoan-src/branding.py:1`, `manchieu-src/branding.py:1`).
  Purely a stale-comment issue, but it's exactly the kind of doc that misleads the next
  person touching the file. CODE-FIXABLE-NOW.
- **`namios_welcome`'s IME/scale combo boxes show raw technical values to the end user**:
  `src/namios_welcome/ui.py:84` `self.ime_combo.addItems(["telex", "vni"])` (lowercase,
  untranslated) and `:86` `self.scale_combo.addItems(["100", "125", "150"])` (no "%"
  suffix) — small polish gap in an otherwise clean, zero-hardcoded-color file.
  CODE-FIXABLE-NOW.
- **`huong-dan-nhanh.html`** uses `border-radius: 6px` (`usr/share/namios/huong-dan-nhanh.html:50,54`), off the 8/12/16 scale used everywhere else. CODE-FIXABLE-NOW.
- **`Gallery.qml` hand-copies palette values instead of importing `SenVietPalette.qml`**,
  by its own admission in a comment (lines 5-10) — currently in sync, but it is the
  project's own component-preview tool, ironic that it's the one file most likely to
  silently drift at the next rebrand. CODE-FIXABLE-NOW to switch to an import.
- **`ErrorCard.qml` has no dedicated "what you can do" text slot** distinct from
  `messageVi` — part (3) of the 5-part structure is implied, not schema-enforced. Minor
  schema gap, not a rendering bug.
- **SDDM `Main.qml` margins (20/28/64) don't align to the documented 4/8/12/16/24/32dp
  spacing scale** — the Kirigami-card QML files (`UpdateCenterPL19.qml`, etc.) do align
  (16/24/28/32). SDDM-specific drift.
- **`theme.conf:57` `showClock=true` is dead config** — `Main.qml` never reads
  `config.showClock`; the clock is unconditionally shown. Harmless today (clock is wanted),
  but a config key a future admin might reasonably expect to toggle does nothing.
- **Glossary D2/D3/D5/D7 from `NAMI-GLOSSARY-VI.md` remain open, confirmed still live
  in this session:** `namios-go-cai-dat.desktop` id still reads "go-cai-dat" (ambiguous,
  D2); `namios-smartai.desktop` ("Hỏi AI") vs `namios-assistant.desktop` ("Trợ lý") are
  still two differently-named AI entry points with no in-product explanation of the
  difference (D3); `nConnect`'s `GenericName[vi]` still says "máy quét" where the glossary
  prefers "Quét tài liệu" for the action verb (D5, though this one is arguably about the
  *device* not the *action*, so may be a false positive — flagging for the owning team to
  re-confirm); Dolphin is not yet relabeled "Tệp" in Kickoff/Desktop (D7). **D1 (Control
  Panel → "Cài đặt") and D4 (nWine honesty) are both confirmed FIXED** in this session
  (`namios-control-panel.desktop:4` now reads `Name[vi]=Cài đặt`; `namios-windows-app.desktop`'s
  `Comment[vi]` now explicitly says "KHÔNG hoạt động dù cửa sổ mở lên được" for
  accounting/signing software) — good, no further action needed on those two.

---

## 3. Cross-screen consistency verdict

Boot → login → splash → desktop → apps does **not yet** feel like one product end to end:

- Boot (GRUB/Plymouth) and the desktop shell (panel/desktoptheme/color-scheme) are
  correctly v3 and internally consistent — this part is genuinely solid.
- SDDM login and the Calamares installer are *mostly* v3 but each introduces 1-3 of its
  own undocumented off-palette colors (§2.2 M7) and a different corner-radius language
  (capsules vs. the 8/12/16 scale, §2.2 M6) — close, not identical.
- The moment a user opens any of the 6 custom PySide6 apps, the experience changes
  completely: generic light-gray Qt chrome (§2.2 M1) instead of the warm ivory/navy/gold
  identity seen one screen earlier on the desktop shell. This is the single biggest
  break in the "feels like one product" chain.
- The Start-menu "workgroups" tile (§2.1 B2) and SmartAI widget (§2.1 B3) — the two
  most Win11-signature, most-visible desktop-shell surfaces after the taskbar itself —
  are the worst-offending files in the entire audit for off-brand color.

---

## 4. CODE-FIXABLE-NOW list (verbatim, for direct hand-off)

1. `usr/share/plasma/plasmoids/org.namios.workgroups/contents/ui/main.qml:42-47,65,116,123,156` — replace 6 badge-gradient color pairs + 3 text colors with v3 tokens (no more Tailwind blue/green/purple).
2. `usr/share/plasma/plasmoids/org.namios.smartai/contents/ui/main.qml:40-41,57,63` — replace stray v2 hex with v3 equivalents; add a `MouseArea`/click handler so the widget is actually clickable.
3. `docs/design/DESIGN-SYSTEM.md §1` — add a banner pointing to `nami-tokens.json`/`NAMI-DESIGN-TOKENS.md` as the superseding authority (same pattern already used in `CONSISTENCY-AUDIT.md`'s own header).
4. `src/namios_welcome/ui.py:204-207,235-244,246-252,256-264` — surface a user-visible message (toast/dialog) on every currently-silent exception path.
5. `opt/namios/namios_lich-src/ui.py` — wrap `_on_add_reminder`/`_on_manage_reminders`/`_refresh_month_grid`/`_refresh_upcoming` in try/except with a user-visible error, instead of zero exception handling.
6. `opt/namios/namios_dichvu-src/branding.py:43-46` and `opt/namios/namios_antoan-src/branding.py:44-47` — delete both independent status-color dicts, use v3 `success`/`warning`/`danger` tokens instead.
7. `usr/share/namios/qml/ErrorCard.qml:157-166` — add `textFormat`/`textInteractionFlags: Qt.TextSelectableByMouse` (or a Copy button) so the error code/correlation_id is actually copyable.
8. `opt/namios/namios_assistant-src/ui.py:162` — remove `setFocusPolicy(Qt.FocusPolicy.NoFocus)` on the chat transcript so keyboard users can Tab into message history.
9. `usr/share/namios/qml/UpdateCenterPL19.qml:197,202,454,473,480` — add `Accessible.name` (or `text:`) to the 5 unlabeled `QQC2.Switch` controls.
10. `usr/share/sddm/themes/namios/Main.qml:439-462` — add `hoverEnabled`+visual state to the 3 power-action `MouseArea`s; wrap in a min-40px-tall container; add `Accessible.name`/`role` to every interactive control in this file (password/username fields, avatar, login button, session selector, power actions).
11. `usr/share/sddm/themes/namios/Main.qml:297,326,362` and `Splash.qml:356,364` — change `radius: height/2` capsules to 8-16px per the documented radius scale.
12. `usr/local/bin/namios-control-panel` + its `.desktop` — add a 9th entry mapping to the high-contrast/accessibility KCM so `NaMi-HighContrast.colors` is actually discoverable from the product's own Settings hub.
13. `distro/live-build/config/includes.chroot/usr/share/namios/huong-dan-nhanh.html:21,50,54` — replace `#f4f6fb` with v3 ivory `#FFF9EF`; fix `border-radius: 6px` to 8px.
14. `design/tokens.json` — flip the `brand_note` from "mandatory, do not change" to a clear "RETIRED, see nami-tokens.json" banner.
15. `opt/namios/namios_antoan-src/ui.py:262-266` and `opt/namios/namios_assistant-src/ui.py:264-268` — route the two hardcoded literal strings through `t()`.
16. `opt/namios/namios_manchieu-src/ui.py:129-133` — fix the single sentence that says both "Cài đặt Hiển thị KDE" and "System Settings" for the same app; pick one Vietnamese term.
17. `distro/live-build/config/includes.chroot/opt/namios/namios_*-src/branding.py` (dichvu/antoan/manchieu) module docstrings — drop the stale `"Sen Việt" v2.0` self-label, since the fallback values are already v3.
18. `src/namios_welcome/ui.py:84,86` — capitalize/translate `["telex","vni"]` combo items and append "%" to the scale options.
19. Verify (and if missing, add to a package-lists file) a Qt6 translations package so standard `QWizard`/`QMessageBox` button labels render in Vietnamese, not English, system-wide.

## 5. NEEDS-BOOT-TEST list (cannot be settled from source)

- Actual on-screen contrast of every pre-computed WCAG pair under real KWin compositing/blur.
- Screen-reader/AT-SPI announce behavior for every `Accessible.*` property in this repo (none are `verified_on_host: YES` anywhere).
- Whether Aurorae `NaMiOSLotus` + desktoptheme together still hang the login screen under QEMU/TCG (`dfbbf3c`) — blocks ever safely enabling the custom window-border theme.
- SDDM login-block layout on short/laptop-aspect screens (`Main.qml`'s own header already flags this as unverified).
- Spinner/`RotationAnimation` smoothness in `Splash.qml` under `QT_QUICK_BACKEND=software` (no-GPU path).
- Real rendered button/control heights where only QSS padding (not an explicit minimum size) is set — `namios_dichvu`/`namios_antoan` buttons in particular (~30px estimated vs. the 40dp token target).
- Whether `favorites=` `.desktop` IDs in `appletsrc` actually resolve to installed packages on a built ISO (package names are confirmed present in `package-lists/`, but the `.desktop` file's real on-disk presence is unverified).
