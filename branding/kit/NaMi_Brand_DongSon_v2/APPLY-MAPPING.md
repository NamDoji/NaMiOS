# NaMiOS brand-mark swap — v2 "Đông Sơn đương đại" → shipped ISO surfaces

**Date:** 2026-11-12
**Kit (source of truth):** `branding/kit/NaMi_Brand_DongSon_v2/assets/`
**Scope:** brand MARK only, under `distro/live-build/config/includes.chroot/` and `distro/live-build/config/bootloaders/`.
**Method note:** no SVG rasterizer in the build sandbox → SVG targets are kit-SVG copies; PNG targets are kit-PNG copies at matching pixel size; composites built with Pillow 12.3.0 + numpy.
**verified_on_host: NO** (working-tree only; not built into an ISO, not rendered on a real NaMiOS boot/login/desktop).
**Not committed / not pushed / no build triggered.**

## Variant rules applied
- light bg → color symbol (`namios-symbol*`); navy/dark bg → `namios-symbol-dark*` (ivory ring); mono → `namios-symbol-mono*`.
- ≤32 px → simplified 8-ray `namios-symbol-small-{16,24,32}`; ≥48 px → full 12-ray `namios-symbol-{48..512}`.
- No distortion / no recolor; kit assets carry their own ~15% safe area.

## A) `usr/share/namios-branding/logo/`
| Target | Kit asset | Variant | Size | Method |
|---|---|---|---|---|
| NaMiOS_Symbol_Color.svg | namios-symbol.svg | color | vector | copy |
| NaMiOS_Symbol_White.svg | namios-symbol-dark.svg | dark/ivory-ring | vector | copy |
| NaMiOS_Symbol_DarkBackground.svg | namios-symbol-dark.svg | dark/ivory-ring | vector | copy |
| NaMiOS_Symbol_Black.svg | namios-symbol-mono.svg | mono | vector | copy |
| NaMiOS_Symbol_Small.svg | namios-symbol-small.svg | simplified | vector | copy |
| NaMiOS_App_Icon_Master.svg | namios-app-icon.svg | app-tile | vector | copy |
| NaMiOS_Logo_Master_Outlined.svg | namios-lockup.svg | lockup | vector | copy |
| NaMiOS_Logo_Master_Outlined_Dark.svg | namios-lockup.svg | lockup (no dark lockup in kit) | vector | copy |
| NaMiOS_Logo_Master_Stacked.svg | namios-lockup.svg | lockup | vector | copy |
| NaMiOS_Symbol_Transparent_1024.png | namios-symbol-1024.png | color | 1024² | copy |
| NaMiOS_App_Icon_1024.png | namios-app-icon-512.png | app-tile (nearest size) | 512² | copy |
| NaMiOS_Logo_Light_2400.png | namios-lockup.png | lockup | 1640×440 | copy |
| NaMiOS_Logo_Dark_2400.png | namios-lockup.png | lockup | 1640×440 | copy |
| NaMiOS_Favicon.ico | small-16 + small-24 + small-32 + symbol-48 | simplified+color | [16,24,32,48] | composite (manual multi-size .ico, PNG entries) |

## B) `usr/share/plasma/look-and-feel/org.namios.sen/contents/images/` (Plasma splash = navy)
| Target | Kit asset | Variant | Method |
|---|---|---|---|
| NaMiOS_Symbol_Color.svg | namios-symbol-dark.svg | dark/ivory-ring | copy |
| trongdong.svg | namios-symbol-dark.svg | dark/ivory-ring | copy |

## C) `usr/share/sddm/themes/namios/` (login bg = navy)
| Target | Kit asset | Variant | Method |
|---|---|---|---|
| namios-symbol-badge.svg | namios-symbol-dark.svg | dark/ivory-ring | copy |

## D) Start-here (app-menu / panel brand icon) — both icon trees
RULE: 16←small-16, 32←small-32 (simplified); 48←symbol-48, 64←symbol-64, 128←symbol-128, 256←symbol-256, 512←symbol-512 (color). Method: copy kit PNG of matching pixel size.
- `usr/share/icons/NaMiOS-Lotus/{48,64,128,256,512}/apps/start-here-namios.png` ← symbol-{48..512}
- Siblings `start-here.png` + `start-here-kde.png` (Kickoff fallbacks) set to the SAME image at 48/64/128/256; **512 siblings newly created** (did not exist before) for consistency.
- `usr/share/icons/hicolor/{16,32,48,64,128,256,512}/apps/start-here-namios.png` ← small-16/small-32/symbol-{48..512}. (hicolor has no 24×24 dir; none created.)
- Total start-here files written: **22** (Lotus 5×3 + hicolor 7). Old tiles had an ivory squircle base; new per RULE are the bare symbol on transparent.

## E) `usr/share/plymouth/themes/namios/` (boot bg = navy)
| Target | Kit asset | Variant | Size | Method |
|---|---|---|---|---|
| watermark.png | namios-symbol-dark-256.png | dark | 256² | copy — **see FLAG 1** |
| lock.png | namios-symbol-dark-256.png | dark | 128² | composite (LANCZOS resize onto 128² transparent) — old lock.png bore the OLD symbol |
| background.png | — | — | 1920×1080 | **left untouched** (plain navy wave, no symbol) |

## F) `etc/calamares/branding/namios/`
| Target | Kit asset | Variant | Size | Method |
|---|---|---|---|---|
| logo.png | namios-symbol-512.png | color | 512² (was 1024²) | copy |

## G) `usr/share/namios/avatars/namios-default-avatar.png` (+ `etc/skel/.face.icon`)
- REGENERATED 256² PNG: navy disc #092D4F + subtle top highlight + thin gold rim + `namios-symbol-dark-256.png` composited centered at ~62% diameter.
- Generator rewritten: `branding/dongson-v3-render/make_default_avatar_v3.py` now composites the kit dark symbol (no longer draws the old trống đồng). It writes BOTH `.face.icon` and the avatar PNG (kept in sync).

## H) Bootloader splashes (boot-menu bg = navy)
| Target | Res | Method |
|---|---|---|
| `distro/live-build/config/bootloaders/grub-pc/splash.png` | 800×600 | composite |
| `distro/live-build/config/bootloaders/isolinux/splash.png` | 640×480 | composite |
- Layout CONFIDENTLY PRESERVED: reused `dongson_shapes.draw_navy_wave_background(w,h)` (reproduces the exact shipped navy + teal/gold wave), then composited a lockup = `namios-symbol-dark-256` (resized to the original 8–32% band) + "NaMiOS" wordmark in ivory (DejaVuSans-Bold), centered in the same band as the prior generator. Old symbol fully replaced; wave + text-region spacing unchanged.

## I) About backgrounds
| Target | Res | Method |
|---|---|---|
| `usr/share/namios-branding/about-background.png` | 1920×1080 | composite — old symbol band (y 157–462, centered x≈961) overpainted with flat navy #092D4F (+14 px pad), new `namios-symbol-dark-256` composited at same center/diameter (307 px). "NaMi / Về NaMi / tagline" text and bottom wave preserved. |
| `usr/share/namios/office-brand/about.png` | 640×400 | **left untouched — see FLAG 2** |

---

## REMAINING / FLAGGED
1. **Plymouth `watermark.png` dropped the wordmark.** Per the explicit mapping it was replaced with the bare `namios-symbol-dark-256` (256²). However the old asset was a 480×158 **lockup** (symbol + "NaMiOS"), and `namios.plymouth` (lines ~25–28, `WatermarkHorizontalAlignment=.5`, `VerticalAlignment=.44`) describes the watermark as "biểu tượng trống đồng + chữ NaMiOS (ivory)". The two-step module renders watermark.png at native size and does not scale it. For consistency with the grub/isolinux splashes (which I built as symbol+"NaMiOS" lockups), consider regenerating watermark.png as a **dark lockup** instead of the bare symbol. Easy to switch — say the word and I'll regenerate it to match.
2. **`usr/share/namios/office-brand/about.png` left as-is.** It bears the **nOffice RED LOTUS** product brand (+ "nOffice — dựa trên LibreOffice"), NOT the NaMiOS trống-đồng mark. That is a separate product identity, so per the "leave + flag if it doesn't bear the OLD symbol / layout is a different brand" rule I did not touch it. Decide whether nOffice should keep its own lotus or adopt the NaMiOS symbol.
3. **`NaMiOS_Logo_Master_Outlined_Dark.svg` uses the same lockup as the light one** — the kit has no dedicated dark lockup SVG. The kit wordmark text is dark-on-light; on a dark surface it may need a light-text lockup variant exported from the kit.
4. **App-tile base removed from start-here icons.** Per the RULE the Kickoff/panel icon is now the bare symbol (color ≥48, simplified ≤32) on transparent, dropping the old ivory squircle tile. If a tiled launcher is preferred, map 48–512 to `namios-app-icon-{64..512}` instead.
5. **Pixel-size changes** (filename kept): `NaMiOS_App_Icon_1024.png`→512², `calamares/logo.png`→512² (was 1024²), `watermark.png`→256² (was 480×158). Downstream code that hard-codes old dimensions should be spot-checked.
6. **No render verification.** All composites were visually inspected as flat PNGs here, but nothing was built into an ISO or seen on a real boot/login/HiDPI screen. 16/24 px legibility and on-device contrast still need the QA pass the kit README requires. `verified_on_host: NO`.
