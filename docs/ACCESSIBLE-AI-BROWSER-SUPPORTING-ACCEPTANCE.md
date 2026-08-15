# Accessible AI Browser Supporting Acceptance v0.1

Status: **F-06 IN PROGRESS — automated browser evidence, not WCAG conformance**

This tranche closes part of the gap left deliberately open by the existing axe-based supporting workflow. Axe can identify many machine-detectable issues, but it does not prove that a person can traverse the actual interface with a keyboard or that content reflows acceptably when the available CSS viewport becomes narrow.

## Search-before-build

This uses established browser-testing and accessibility guidance rather than creating another browser automation framework.

- W3C/WAI's Reflow guidance explains that a width of **320 CSS pixels** corresponds to the horizontal geometry of a 1280-CSS-pixel viewport at 400% zoom for reflow evaluation.
- WAI keyboard guidance requires functionality to be operable through a keyboard interface where applicable.
- Playwright/Selenium-style browser automation can exercise focus and viewport behavior, but browser automation and role/focus assertions do not replace accessibility audits or WCAG conformance evaluation.
- The existing pinned axe workflow remains a separate automated-rule evidence source.

The repository uses Selenium here because the GitHub-hosted runner already exposes pinned Chrome/ChromeDriver in the current acceptance environment. The public renderer itself gains no Selenium runtime dependency.

## Exact artifact under test

CI generates the same sanitized semantic System Doctor report in English and Spanish using:

```text
system_doctor.collect()
        ↓
accessible_report.render_html()
        ↓
loopback-only HTTP server
        ↓
headless Chrome
```

The artifact hash is retained in the supporting evidence record.

## Automated keyboard path

For each generated artifact, the browser performs this narrow interaction sequence:

```text
Tab
  ↓
visible Skip-to-report link
  ↓
Tab
  ↓
Engineering details <summary>
  ↓
Enter
  ↓
details opens
  ↓
Tab
  ↓
focusable engineering <pre>
```

The test verifies that the initially off-screen skip link becomes visibly exposed when focused.

A PASS means this **specific automated focus path** worked in the tested Chrome environment. It does not prove that every future interface feature is keyboard usable or that a keyboard-only user found the experience usable.

## 320-CSS-pixel reflow proxy

Chrome DevTools emulation sets a 320 CSS-pixel viewport. The probe then requires both document and body scroll widths to remain within the viewport width (allowing one pixel of rounding tolerance).

This is retained under the existing `zoom_reflow_400` evidence field because the geometry is relevant to WAI Reflow evaluation. The evidence notes explicitly state that this is an automated 320-CSS-pixel **proxy**, not a manual 400%-zoom user-agent acceptance session.

## Reduced motion and language

The browser emulates `prefers-reduced-motion: reduce` and requires the media query to be observable by the page. It also verifies exact `html[lang]` values for English and Spanish artifacts.

These checks support the existing design contract but do not prove every future animated component or translation is accessible.

## Deliberately NOT tested here

- screen reader behavior;
- speech input/control;
- switch control;
- magnifier usability beyond the reflow proxy;
- cognitive accessibility/usability;
- disability-inclusive real-user acceptance;
- complete WCAG 2.2 A/AA conformance;
- production deployment.

The evidence schema therefore continues to require hard-false claims:

```text
wcag_conformance = false
all_accessibility_issues_found = false
real_user_acceptance = false
production_ready = false
```

## Privacy

The generated System Doctor record must retain its existing read-only/no-private-content guarantees. The loopback server binds only to `127.0.0.1`, and the uploaded artifact contains generated public/sanitized acceptance data rather than participant or credential information.

## F-06 progression

F-06 now has complementary hosted supporting evidence for:

- semantic English/Spanish rendering;
- pinned axe automated-rule checks;
- document-language semantics;
- an automated keyboard focus/activation path;
- a 320-CSS-pixel horizontal reflow proxy;
- reduced-motion preference detection.

F-06 remains **IN PROGRESS**. Manual assistive-technology sessions, disability-inclusive usability, broader language review, production interface acceptance, dedicated distribution/release and the rest of the canonical completion contract remain outstanding.
