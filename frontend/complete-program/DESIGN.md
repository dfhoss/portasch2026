---
version: alpha
name: "Portas Abertas Complete Program Schedule"
description: "Design tokens and comprehensive visual specifications for the academic event schedule component, featuring dual view modes (Shift/Knowledge Axis), accessible accordions, and high-contrast support."
colors:
  # Light / Standard Theme (Default)
  light:
    page: "#fffff6"
    surface: "#ffffff"
    content_surface: "#fffff6"
    primary: "#015a83"
    brand_blue: "#4748d9"
    accent: "#caff00"
    accent_rose: "#ed54ce"
    alert: "#ec2642"
    text: "#304254"
    content_text: "#015a83"
    border: "#015a83"
    soft_border: "#ed54ce"
    control_background: "#caff00"
    control_border: "#caff00"
    focus: "#393ce4"
    focus_on_brand: "#caff00"
    finalized_surface: "#e7eaec"
    finalized_text: "#34404b"
    finalized_border: "#5f6b75"
    finalized_badge: "#34404b"
    finalized_badge_text: "#ffffff"
  # High-Contrast / Dark Accessibility Theme
  high_contrast:
    page: "#25265a"
    surface: "#f1f2f2"
    content_surface: "#25265a"
    primary: "#004aad"
    brand_blue: "#353359"
    accent: "#ed54ce"
    accent_rose: "#ed54ce"
    alert: "#ec2642"
    text: "#f1f2f2"
    content_text: "#f1f2f2"
    border: "#f1f2f2"
    soft_border: "#ed54ce"
    control_background: "#25265a"
    control_border: "#ed54ce"
    focus: "#caff00"
    finalized_surface: "#25265a"
    finalized_text: "#f1f2f2"
    finalized_border: "#ed54ce"
    finalized_badge: "#004aad"
    finalized_badge_text: "#f1f2f2"
typography:
  families:
    heading: '"Disket Mono", "Space Mono", "Courier New", monospace'
    supporting: '"Garet", "Montserrat", "Segoe UI", Arial, sans-serif'
    body: '"Open Sans", Arial, Helvetica, system-ui, sans-serif'
  sizes:
    section_title: "clamp(1.85rem, 4vw, 3.25rem)"
    group_title: "clamp(1.1rem, 2vw, 1.45rem)"
    course_title: "clamp(1rem, 1.8vw, 1.25rem)"
    card_title: "1.05rem"
    description: "clamp(0.95rem, 1.4vw, 1.15rem)"
    body: "0.9rem"
    course_badge: "0.8rem"
    count_badge: "0.85rem"
    status_badge: "0.72rem"
  weights:
    regular: 400
    semibold: 600
    bold: 700
  line_heights:
    tight: 1.1
    heading: 1.25
    body: 1.5
spacing:
  container_max_width: "72rem" # 1152px
  section_padding_y: "clamp(3rem, 6vw, 5rem)"
  group_gap: "1rem"
  card_grid_gap: "1rem"
  card_padding: "1.15rem"
  summary_padding: "0.9rem 1.25rem"
  selector_padding: "0.35rem"
rounded:
  sm: "0.75rem" # 12px (cards, accordions)
  md: "1.25rem" # 20px
  pill: "999px"  # badges, view selector buttons
borders:
  width: "2px"
  style: "solid"
  color: "{colors.light.border}"
components:
  view_selector:
    background: "{colors.light.surface}"
    border: "2px solid {colors.light.border}"
    radius: "{rounded.pill}"
    active_background: "{colors.light.primary}"
    active_color: "{colors.light.surface}"
  accordion:
    background: "{colors.light.surface}"
    border: "2px solid {colors.light.border}"
    radius: "{rounded.sm}"
    indicator_size: "2.15rem"
    indicator_radius: "50%"
  schedule_card:
    background: "{colors.light.surface}"
    border: "2px solid {colors.light.border}"
    radius: "{rounded.sm}"
    min_width: "17rem"
  finalized_badge:
    background: "{colors.light.finalized_badge}"
    color: "{colors.light.finalized_badge_text}"
    radius: "{rounded.pill}"
---

# Complete Program Schedule — Design System Specification

## 1. Overview & Visual Identity

The **Complete Program Schedule** (`#complete-program`) is an event scheduling interface built with an **Academic Neo-Brutalist** aesthetic. It combines robust structural borders, high-contrast typography, playful pill-shaped controls, and accessible expandable accordions to present dozens of academic sessions cleanly without overwhelming the user.

### Key Visual Principles
1. **Bold Structural Framing**: All cards, accordions, and selectors use prominent `2px solid` borders.
2. **Dual Typographic Tone**: Monospace font (`Disket Mono` / `Space Mono`) provides a technical, authoritative look for titles and icons, paired with geometric sans (`Garet` / `Montserrat`) and human-readable body copy (`Open Sans`).
3. **Dual View Dimensionality**:
   - **Turno (Shift)**: Temporal view (Manhã, Tarde, Noite). Prioritizes attendees currently on campus.
   - **Eixo (Knowledge Axis)**: Curricular view based on official Inep/Cine Brasil academic areas.
4. **Uncompromising Accessibility**: WCAG 2.1 AA and AAA compliance with native high-contrast theming, complete keyboard navigation, and explicit ARIA semantics.

---

## 2. Color Palette & Semantic Tokens

### Standard Theme (Light)
| Token | Value | Semantic Purpose |
| :--- | :--- | :--- |
| `--color-page` | `#fffff6` | Background of the page (warm off-white) |
| `--color-surface` | `#ffffff` | Card surfaces, container backgrounds |
| `--color-content-surface` | `#fffff6` | Section background container |
| `--color-primary` | `#015a83` | Deep petroleum blue: headings, active tabs, main borders |
| `--color-brand-blue` | `#4748d9` | Vibrant cobalt: primary brand identity |
| `--color-accent` | `#caff00` | High-visibility neon lime: buttons, highlights |
| `--color-accent-rose` | `#ed54ce` | Magenta: soft dividers and decorative accents |
| `--color-text` | `#304254` | Slate gray: primary body copy, locations |
| `--color-content-text` | `#015a83` | Headers, labels, course tags |
| `--color-border` | `#015a83` | Heavy 2px borders for cards and accordions |
| `--color-focus` | `#393ce4` | High-visibility keyboard focus outline |
| `--color-finalized-surface` | `#e7eaec` | Muted cool gray for past event cards |
| `--color-finalized-text` | `#34404b` | Dimmed text for finished sessions |
| `--color-finalized-badge` | `#34404b` | Pill badge background for completed sessions |

### High-Contrast / Dark Theme (`[data-theme="high-contrast"]`)
| Token | Value | Semantic Purpose |
| :--- | :--- | :--- |
| `--color-page` | `#25265a` | Deep indigo dark background |
| `--color-surface` | `#1c1d42` | Dark card surface |
| `--color-text` | `#f1f2f2` | Crisp off-white text for high readability |
| `--color-border` | `#f1f2f2` | High contrast off-white borders |
| `--color-accent` | `#ed54ce` | Vibrant magenta for active states & highlights |
| `--color-focus` | `#caff00` | Ultra-bright neon lime focus rings |

---

## 3. Typography System

### Font Hierarchy
```
Heading (Monospace)
  └── Section Title (h2): clamp(1.85rem, 4vw, 3.25rem) / Bold / Uppercase
  └── Shift/Axis Title (h3): clamp(1.1rem, 2vw, 1.45rem) / Bold / Uppercase
  └── Course Title (h4): clamp(1rem, 1.8vw, 1.25rem) / Bold / Uppercase

Supporting (Geometric Sans)
  └── Subtitle / Interval: clamp(0.95rem, 1.4vw, 1.15rem) / Regular
  └── View Selector Option: 0.95rem / Bold
  └── Course Tag: 0.8rem / Bold / Uppercase
  └── Activity Card Title (h5): 1.05rem / Bold
  └── Counter Badge: 0.85rem / Bold

Body (Humanist Sans)
  └── Description & Sessions: 0.9rem / Regular / Line-height 1.5
  └── Time Tags: 0.9rem / Bold (emphasized in primary color)
```

---

## 4. Component Anatomy & Behaviors

### 4.1. View Selector (`.schedule-view-selector`)
- **Semantic HTML**: `<div role="radiogroup" aria-label="Visualizar por">`
- **Options**: `<button role="radio" data-schedule-view="shift|knowledge-axis">`
- **Active State**:
  - `aria-checked="true"`
  - `tabindex="0"` (only active item is in tab order)
  - Color fills with `--color-primary`
- **Inactive State**:
  - `aria-checked="false"`
  - `tabindex="-1"`
  - Transparent background, subtle hover effect
- **Keyboard Navigation**:
  - `ArrowRight` / `ArrowDown`: Moves focus to next option and triggers view change.
  - `ArrowLeft` / `ArrowUp`: Moves focus to previous option.
  - `Home` / `End`: Jump to first or last option.

### 4.2. Expandable Accordion (`.schedule-view-group`)
- Built using native HTML `<details>` and `<summary>` elements.
- **Icon Indicator**: Pseudo-element `::after` formatted as a circle `2.15rem` with `+` in closed state and `−` in open state.
- **Title Lockup**: Flexbox with title on the left and activity count on the right (`Manhã 35 atividades`).
- **Dividing Border**: `1px solid var(--color-border)` between summary and expanded content.

### 4.3. Activity Card Grid (`.schedule-list` & `.schedule-item`)
- **Grid Layout**: Responsive auto-fit CSS Grid:
  ```css
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
  gap: 1rem;
  ```
- **Card Hierarchy**:
  1. Status Badge (if finalized: `FINALIZADO`)
  2. Course / Department Category (`ADMINISTRAÇÃO`, `AGRONOMIA`, etc.)
  3. Activity Title (`h5`)
  4. Activity Description (`p`)
  5. Schedule Session (`time` + location `span`)
  6. Action link (`Mais informações` if URL exists)
- **Hover Micro-interaction**: Subtle elevation `-2px` transform with shadow `0 4px 12px rgba(1, 90, 131, 0.08)`.

### 4.4. Finalized Session Treatment
- Applied when session time has elapsed on the event date (`2026-10-26`).
- Class: `.schedule-item--finalized`
- Card background shifts to `--color-finalized-surface` (`#e7eaec`).
- Opacity reduced to `0.78` to visually de-emphasize concluded activities while keeping information fully accessible.

---

## 5. How to Reproduce in Another Repository

### Option A: Vanilla HTML / CSS / JS
1. Copy the `complete-program/` folder to your project.
2. In your HTML:
   ```html
   <link rel="stylesheet" href="./complete-program/styles.css">
   <!-- Include the markup from complete-program/component.html -->
   <script type="module" src="./complete-program/script.js"></script>
   ```

### Option B: React / Next.js Component
```tsx
import React, { useState } from "react";
import "./styles.css";
import scheduleData from "./schedule-data.json";

export function CompleteProgramSchedule() {
  const [viewMode, setViewMode] = useState<"shift" | "knowledge-axis">("shift");

  return (
    <section id="complete-program" className="is-visible">
      <article className="schedule-section schedule-section--complete-program">
        <h2 className="schedule-section__title">Programação completa</h2>
        <p className="schedule-section__description">
          Intervalos: manhã, das 12h às 13h; tarde, das 17h30 às 19h.
        </p>

        <div className="schedule-view-selector" role="radiogroup" aria-label="Visualizar por">
          <span className="schedule-view-selector__label">Visualizar por</span>
          <button
            type="button"
            className="schedule-view-selector__option"
            role="radio"
            aria-checked={viewMode === "shift"}
            tabIndex={viewMode === "shift" ? 0 : -1}
            onClick={() => setViewMode("shift")}
          >
            Turno
          </button>
          <button
            type="button"
            className="schedule-view-selector__option"
            role="radio"
            aria-checked={viewMode === "knowledge-axis"}
            tabIndex={viewMode === "knowledge-axis" ? 0 : -1}
            onClick={() => setViewMode("knowledge-axis")}
          >
            Eixo
          </button>
        </div>

        {/* Render Accordion Groups dynamically using scheduleData */}
      </article>
    </section>
  );
}
```

### Option C: Tailwind CSS Configuration
If integrating into a Tailwind project, map the DESIGN.md tokens in `tailwind.config.js`:
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        schedule: {
          page: "var(--color-page, #fffff6)",
          surface: "var(--color-surface, #ffffff)",
          primary: "var(--color-primary, #015a83)",
          accent: "var(--color-accent, #caff00)",
          text: "var(--color-text, #304254)",
          border: "var(--color-border, #015a83)",
          finalized: {
            surface: "var(--color-finalized-surface, #e7eaec)",
            badge: "var(--color-finalized-badge, #34404b)",
          }
        }
      },
      fontFamily: {
        heading: ["Disket Mono", "Space Mono", "monospace"],
        supporting: ["Garet", "Montserrat", "sans-serif"],
        body: ["Open Sans", "sans-serif"],
      },
      borderRadius: {
        small: "0.75rem",
        pill: "999px"
      }
    }
  }
};
```

---

## 6. Do's and Don'ts

### Do
- **Do** maintain the `2px solid` border width across cards, selectors, and summary buttons to preserve the architectural brutalist aesthetic.
- **Do** keep `<time datetime="...">` tags formatted with machine-readable standard ISO or 24-hour time for screen readers and assistants.
- **Do** preserve the Arrow Key keyboard navigation on the view selector radiogroup.
- **Do** allow multiple `<details>` accordions to remain open simultaneously so attendees can compare morning, afternoon, and evening activities.

### Don't
- **Don't** use generic light gray borders (e.g. `#e2e8f0`); use `--color-border` (`#015a83`) to avoid visual degradation.
- **Don't** replace native `<details>` with non-semantic `div`s unless equivalent WAI-ARIA accordion attributes are rigorously maintained.
- **Don't** remove finished activities from the schedule; apply the `.schedule-item--finalized` state and badge instead.
