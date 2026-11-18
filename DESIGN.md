---
name: Cement Dispatch Control
description: Multi-enterprise agentic decision support, drawn as a dispatch manifest that agents fill and a person stamps.
colors:
  navy-ink: "#0b1b33"
  slate-ink: "#3b4a63"
  muted-ink: "#5c6b82"
  cool-ground: "#f3f5f8"
  form-stock: "#ffffff"
  hairline-rule: "#c9d2de"
  faint-rule: "#e3e8ef"
  idle-grey: "#9aa8bb"
  action-blue: "#1d4ed8"
  live-cyan: "#0891b2"
  live-cyan-text: "#0e7490"
  alarm-red: "#b91c1c"
  wait-amber: "#b45309"
  approval-violet: "#5b21b6"
  distribution-umber: "#92400e"
  change-lamp: "#fff4d6"
  wait-notice-tint: "#fffaf0"
  critical-notice-tint: "#fff5f5"
  docket-label: "#9fb2cf"
  docket-running: "#bfe9f5"
  sidebar-active: "#1d3a66"
  sidebar-panel: "#132a4d"
  sidebar-seam: "#24406b"
  sidebar-section: "#8ea3c4"
  sidebar-caption: "#a9bbd6"
  sidebar-text: "#e4ebf5"
typography:
  display:
    fontFamily: "Archivo, sans-serif"
    fontSize: "1.95rem"
    fontWeight: 750
    letterSpacing: "-0.03em"
    fontVariation: "'wdth' 92"
  headline:
    fontFamily: "Archivo, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 750
    lineHeight: 1.1
    letterSpacing: "-0.01em"
  figure:
    fontFamily: "Archivo, sans-serif"
    fontSize: "1.35rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.02em"
    fontFeature: "'tnum' 1"
  title:
    fontFamily: "Archivo, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
    letterSpacing: "-0.005em"
  box-title:
    fontFamily: "Archivo, sans-serif"
    fontSize: "0.92rem"
    fontWeight: 700
    lineHeight: 1.2
  body:
    fontFamily: "Archivo, sans-serif"
    fontSize: "0.82rem"
    fontWeight: 400
    lineHeight: 1.45
    fontFeature: "'tnum' 1"
  label:
    fontFamily: "Archivo, sans-serif"
    fontSize: "0.68rem"
    fontWeight: 650
    letterSpacing: "0.08em"
    fontVariation: "'wdth' 88"
  code:
    fontFamily: "Archivo, sans-serif"
    fontSize: "0.66rem"
    fontWeight: 700
    lineHeight: 1.5
    letterSpacing: "0.1em"
rounded:
  form: "0px"
  control: "2px"
spacing:
  hair: "2px"
  xs: "4px"
  sm: "6px"
  md: "10px"
  lg: "14px"
  section: "18px"
components:
  button-primary:
    backgroundColor: "{colors.action-blue}"
    textColor: "{colors.form-stock}"
    rounded: "{rounded.control}"
  button-secondary:
    backgroundColor: "{colors.form-stock}"
    textColor: "{colors.navy-ink}"
    rounded: "{rounded.control}"
  ledger-field:
    backgroundColor: "{colors.form-stock}"
    textColor: "{colors.navy-ink}"
    typography: "{typography.figure}"
    rounded: "{rounded.form}"
    padding: "6px 12px"
  docket-head:
    backgroundColor: "{colors.navy-ink}"
    textColor: "{colors.form-stock}"
    typography: "{typography.headline}"
    rounded: "{rounded.form}"
    padding: "10px 14px"
  docket-box:
    backgroundColor: "{colors.form-stock}"
    textColor: "{colors.slate-ink}"
    typography: "{typography.body}"
    rounded: "{rounded.form}"
    padding: "9px 11px 8px"
  code-chip:
    textColor: "{colors.action-blue}"
    typography: "{typography.code}"
    rounded: "{rounded.form}"
    padding: "0 5px"
  notice-warning:
    backgroundColor: "{colors.wait-notice-tint}"
    textColor: "{colors.navy-ink}"
    rounded: "{rounded.form}"
    padding: "7px 10px"
  notice-critical:
    backgroundColor: "{colors.critical-notice-tint}"
    textColor: "{colors.navy-ink}"
    rounded: "{rounded.form}"
    padding: "7px 10px"
  stamp-approved:
    textColor: "{colors.action-blue}"
    rounded: "{rounded.form}"
    padding: "2px 10px"
  stamp-rejected:
    textColor: "{colors.alarm-red}"
    rounded: "{rounded.form}"
    padding: "2px 10px"
---

# Design System: Cement Dispatch Control

## Overview

**Creative North Star: "The Dispatch Manifest"**

Every screen is a printed shipping form: bills of lading, cargo manifests, dispatch dockets. White form stock sits on a cool grey ground, ruled with navy and blue-grey hairlines, and filled in navy ink with tabular figures. An orchestration run is a numbered docket. Each agent fills and signs its own box, the planner writes the plan into a ruled table, the narrator adds remarks, and a person stamps the authorisation box. The form is the interface; there are no floating cards, no pills and no gradients.

Density is high and deliberate, because the same sheet serves a projector audience and a working planner. Hierarchy comes from scale and weight contrast inside one variable family (Archivo), not from colour. Colour is reserved for meaning: blue for action, cyan for what is running now, violet for what waits on a human, amber for waiting and warning, red only for failure, rejection, stock-out and lateness. Motion is limited to three functional events: the running mark blinks, the filling box lifts while the others dim, and an authorisation stamp lands.

**Key Characteristics:**
- Ruled form stock: 1px hairline seams, navy frame rules, zero radius on every form surface.
- Field labels as small uppercase condensed caps above tabular-figure values.
- States as printed square marks plus an uppercase word, never as rounded badges.
- Enterprise identity by a 1px-ruled three-letter code chip in the enterprise colour.
- Human authority as a double-ruled, rotated stamp.

## Colors

A navy ink and grey-paper world in which saturated colour appears only as a signal.

### Primary
- **Dispatch Blue** (action-blue): primary buttons, links, focus rings, the Approved stamp, the MFG code chip and the theme primary. It marks what a person can do.

### Secondary
- **Live Cyan** (live-cyan): the running mark fill, the live box outline, the parallel group's dashed frame. **Deep Cyan** (live-cyan-text) is its text-weight partner for running state words, the parallel tag and the docket note, and the SHP chip.
- **Approval Violet** (approval-violet): "Requires human approval" marks, words and ledger figures, and the SUP chip.

### Tertiary
- **Wait Amber** (wait-amber): waiting and degraded states, warning ledger figures, warning notice borders, the EVT chip.
- **Alarm Red** (alarm-red): failure, rejection, stock-out, late arrival, critical notices. Nothing else.
- **Distribution Umber** (distribution-umber): the DST enterprise chip only.

### Neutral
- **Navy Ink** (navy-ink): all primary text, the completed mark, frame rules, the docket head bar, the sidebar, chart axes and hover labels.
- **Slate Ink** (slate-ink) and **Muted Ink** (muted-ink): secondary text, then field labels, captions, timestamps and signatures.
- **Cool Ground** (cool-ground): the page behind the forms. **Form Stock** (form-stock): every form surface.
- **Hairline Rule** (hairline-rule): seams between fields, boxes and slips. **Faint Rule** (faint-rule): table row rules, box header rules, chart gridlines.
- **Idle Grey** (idle-grey): idle mark borders, scrollbar thumb, idle chart series.
- **Change Lamp** (change-lamp): background of plan rows that changed and are not yet acknowledged.
- Sidebar set (sidebar-panel, sidebar-active, sidebar-seam, sidebar-section, sidebar-caption, sidebar-text) and docket-head set (docket-label, docket-running): the same palette read on navy.

### Named Rules
**The Ink Not Green Rule.** Completed is a filled navy square. Green is not a state colour in this system; success is the absence of alarm.

**The Red Is Refusal Rule.** Alarm red appears only for failure, rejection, stock-out, late arrival and critical notices. If nothing is wrong, the screen holds no red.

**The Lamp Until Acknowledged Rule.** A changed plan row stays lit in change lamp, with the superseded value struck through, until a person acknowledges it.

## Typography

**Display Font:** Archivo (variable, wdth 62 to 125, wght 300 to 800), with sans-serif fallback
**Body Font:** Archivo
**Label/Mono Font:** Archivo at reduced width; tabular figures are on for the whole app.

**Character:** One grotesque used across its width and weight axes, condensed for labels and headings, regular for prose, so the sheet reads like typeset form stock. Base size 15px.

### Hierarchy
- **Display** (750, 1.95rem, -0.03em, width 92%): the page title in the page head only.
- **Headline** (750, 1.5rem, 1.1): the docket number and run title on the navy head bar.
- **Figure** (700, 1.35rem, 1.2, -0.02em, tabular): ledger field values.
- **Title** (700, 1rem): section rule titles and h3.
- **Box title** (700, 0.92rem, 1.2): docket box, authorisation and enterprise slip titles.
- **Body** (400, 0.82rem, 1.45): box contents, tables, notices, the manifest log (0.8rem).
- **Label** (650, 0.68rem, 0.08em, uppercase, width 88%): field labels, table headers (0.66rem), state words (0.72rem, 0.06em), the synthetic-data flag.
- **Code** (700, 0.66rem, 0.1em): box numbers ("BOX 3") and enterprise chips.

### Named Rules
**The Scale Contrast Rule.** Hierarchy is carried by size, weight and width, never by colouring a heading.

**The Field Label Rule.** A label sits above its value in small condensed uppercase muted ink; the value is the loud element.

## Layout

A wide single sheet (max 1600px container, 2.3rem top padding) laid out as ruled rows rather than a card grid. The page head is a flex row closed by a 2px navy rule. Sections open with a 1px navy rule carrying a title on the left and a muted caption on the right (18px above, 10px below). The ledger strip is one bordered grid row of equal fields separated by hairline seams. The docket is a navy head bar, then one ruled row of equal-height boxes (event box slightly wider at 1.05fr), then a two-column row (plan 2.05 : remarks and authorisation 1). Registry slips tile at a 230px minimum with shared hairline seams. The route slip runs horizontally with 14px navy connectors and scrolls sideways when it overflows.

Spacing is tight and small-step (2, 4, 6, 10, 14, 18px). Below 640px the ledger becomes a two-column grid with top seams, the page head stacks, and docket rows collapse to one column with top seams instead of side seams.

## Elevation & Depth

Flat. Depth comes from rules and the ground/stock contrast, not shadows. The one shadow is functional: the box an agent is filling right now lifts while its siblings dim to 50% opacity, with a 0.3s ease-out transition.

### Shadow Vocabulary
- **Filling lift** (`box-shadow: 0 3px 14px rgba(11,27,51,.16)`): the live docket box only, together with a cyan outline.
- **Approval ring** (`box-shadow: inset 0 0 0 2px #fff, inset 0 0 0 5px #5b21b6`): draws the concentric approval mark; a print device, not elevation.

### Named Rules
**The Lift Only While Filling Rule.** Surfaces are flat at rest. Only the box currently being filled lifts, and only while it is running.

## Shapes

Square. Every form surface, container, expander, alert, tab group and sidebar link has 0 radius; buttons and page links get 2px so they read as pressable controls. Borders are the form language: 1px hairline seams inside, 1px navy for frames and section rules, 2px navy under the page head, dashed hairline above signatures, dashed cyan around the parallel agent group, and a 3px double rule around stamps. State marks are 9px squares with a 1.5px border.

### Named Rules
**The Zero Radius Rule.** Forms are cut paper: 0 radius. Only controls take 2px.

## Components

### Buttons
Plain, firm, labelled controls.
- **Shape:** near-square (2px), weight 650.
- **Primary:** dispatch blue fill and border, white text. Used for Run and Approve.
- **Secondary:** form stock with a 1px navy border and navy text. Used for Reject and Acknowledge.
- **Focus:** 2px dispatch blue outline, 2px offset.
- **Isolated Reject:** in the authorisation box Approve sits left, Reject right, separated by a spacer column (1 : 0.35 : 1) so the two never sit edge to edge.

### State Marks
- **Style:** a 9px square mark followed by an uppercase state word (0.72rem, 650, 0.06em).
- **States:** completed is a filled navy square; running is a filled cyan square blinking in two steps (1.2s); waiting is an amber outline; approval is a violet concentric square; failed is a filled red square; idle is a grey outline. Superseded and idle share the idle mark.

### Chips
- **Enterprise code chip:** three letters (MFG, SHP, DST, SUP, GLB, MGT, EVT) in the enterprise colour with a 1px border in currentColor, no fill, full name in the hover title.
- **Tag:** uppercase slate word with a hairline border on form stock, for labels such as "extension".

### Ledger Strip
One navy-framed row of fields replacing KPI cards. Each field: label, figure, a muted sub-line. Tone variants recolour only the figure: alarm red, wait amber, approval violet.

### Dispatch Docket (signature component)
A navy head bar carries the run id and title in headline type, with labelled meta (status, opened, elapsed, parallel agents, cycle) in docket-label caps. Below it, numbered boxes ("BOX 1" in code type) each hold a title, an enterprise chip, a state mark, two or three bulleted facts and a dashed-rule signature line ("Signed 13:45:33 · 630 ms" or "Awaiting signature"). Empty boxes drop their body text to muted grey. The plan box holds a ruled table; the authorisation box has a navy frame and closes with buttons or a stamp.

### Stamps
Uppercase, 800 weight, 0.16em tracking, 3px double border in currentColor, rotated -4deg. Approved is dispatch blue, rejected alarm red, superseded muted ink. It lands from 1.6x scale over 0.45s on `cubic-bezier(.16,1,.3,1)`; reduced motion removes both the landing and the blink.

### Ruled Tables
Uppercase condensed headers over a 1px navy rule, rows divided by faint rules, numeric columns right aligned, late arrivals in alarm red at 650.

### Manifest Log
A navy-ruled list; each line is a 58px timestamp column and a route line (chip, sender, arrow, chip, receiver, type) above the message. Negotiation messages go semibold; error messages go red.

### Registry and Route Slips
Registry slips tile agents as ruled paper slips with chip, state, name, role and last run. The route slip lays the pipeline left to right as small ruled steps joined by navy connectors, with parallel workers stacked inside a dashed cyan frame labelled "parallel".

### Notices
Bordered tinted strips: amber border on warm tint for warnings, red border on red tint for critical, hairline border on stock for info. Bold title, then body, then muted source.

### Navigation
A navy sidebar. Section headers in sidebar-section caps (0.68rem, 700, 0.12em). Links are square; the current page fills with sidebar-active. The brand block uses 800 weight, 0.04em tracking, width 90%, closed by a sidebar-seam rule.

### Charts
Plotly template "manifest": Archivo 12px, white paper, navy x-axis line with outside ticks, faint horizontal gridlines only, no zero lines, navy hover label, horizontal legend top right. Series order: navy, live cyan, dispatch blue, amber, violet, muted ink, then extras. Status colours match the state marks.

## Do's and Don'ts

### Do:
- **Do** draw every surface as ruled form stock: white fill, 1px hairline seams, 0 radius.
- **Do** put a small uppercase condensed label above every figure, and set figures in tabular numerals.
- **Do** express state with a square mark and an uppercase word, using the mark colours above.
- **Do** identify an enterprise with its three-letter code chip wherever an agent or message appears.
- **Do** keep changed plan rows lit in change lamp, with the old value struck through, until acknowledged.
- **Do** keep Reject separated from Approve and secondary in weight.
- **Do** honour reduced motion: no blink, no stamp landing.

### Don't:
- **Don't** build KPI card grids; use a ledger strip of ruled fields.
- **Don't** round form surfaces or use pill badges for state.
- **Don't** use green for success or red for anything except failure, rejection, stock-out, lateness and critical notices.
- **Don't** add shadows to resting surfaces; only the box being filled lifts.
- **Don't** use gradients or decorative animation.
- **Don't** colour headings to create hierarchy; use size, weight and width.
