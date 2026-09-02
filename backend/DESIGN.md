# Admin Design System

## Purpose

This document is the source of truth for the visual identity of the Portas Abertas
administrative interface in `static/admin/`. Read it before creating or changing any UI.

The interface should feel institutional, calm, clear, and dependable. It uses deep green to
anchor navigation, a brighter green for actions, warm off-white surfaces, and restrained
feedback colors. Prefer hierarchy, legibility, and task completion over decorative effects.

## Token model

Tokens have two layers:

- **Primitive tokens** describe the available palette and scales. Do not use them directly in
  component rules unless no semantic token describes the intended role.
- **Semantic tokens** describe purpose, such as text, surface, border, or action. Components
  should consume these tokens so the visual identity can change without rewriting selectors.

Use lowercase kebab-case names. Define global tokens on `:root` and consume them with
`var(--token-name)`. Do not duplicate a literal value merely to give it a component-specific
name.

## CSS tokens

The following block is canonical. Keep the corresponding declarations in `admin.css` aligned
with it when implementing or changing the interface.

```css
:root {
  color-scheme: light;

  /* Primitive colors */
  --green-50: #f5faf7;
  --green-100: #e5f1eb;
  --green-200: #cfe3d8;
  --green-300: #91b5a2;
  --green-500: #2c614a;
  --green-600: #16734a;
  --green-700: #173c2d;
  --green-800: #203e31;
  --neutral-0: #ffffff;
  --neutral-50: #fafbfa;
  --neutral-100: #f3f5f2;
  --neutral-200: #e1e6e3;
  --neutral-300: #d8dfdb;
  --neutral-400: #bac5bf;
  --neutral-600: #67746d;
  --neutral-800: #24312a;
  --yellow-50: #fff8d9;
  --yellow-400: #ead27b;
  --red-600: #aa2f2f;
  --overlay-green: #17251f88;

  /* Typography */
  --font-family-sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-md: 1rem;
  --font-size-lg: 1.25rem;
  --font-size-xl: 1.5rem;
  --font-size-2xl: 2rem;
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  --line-height-tight: 1.2;
  --line-height-normal: 1.5;

  /* Spacing */
  --space-0: 0;
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;

  /* Shape, borders, and elevation */
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-pill: 999px;
  --border-width: 1px;
  --shadow-dialog: 0 1rem 3rem rgb(23 60 45 / 24%);
  --shadow-card: 0 0.5rem 1.5rem rgb(23 60 45 / 8%);

  /* Motion */
  --duration-fast: 120ms;
  --duration-normal: 200ms;
  --ease-standard: ease-out;

  /* Semantic colors */
  --color-page: var(--neutral-100);
  --color-surface: var(--neutral-0);
  --color-surface-subtle: var(--neutral-50);
  --color-surface-selected: var(--green-100);
  --color-text: var(--neutral-800);
  --color-text-muted: var(--neutral-600);
  --color-text-on-dark: var(--neutral-0);
  --color-border: var(--neutral-300);
  --color-border-strong: var(--neutral-400);
  --color-action-primary: var(--green-600);
  --color-action-primary-hover: var(--green-500);
  --color-navigation: var(--green-700);
  --color-navigation-active: var(--green-500);
  --color-focus: var(--green-300);
  --color-danger: var(--red-600);
  --color-warning-surface: var(--yellow-50);
  --color-warning-border: var(--yellow-400);
  --color-backdrop: var(--overlay-green);

  /* Semantic layout */
  --sidebar-width: 13.75rem;
  --content-width: 75rem;
  --control-height: 2.5rem;
  --content-padding: var(--space-8);
  --panel-padding: var(--space-4);
  --component-gap: var(--space-3);
}
```

## Usage rules

### Components

- Semantic variants such as `.primary-action` and `.danger-action` carry their complete visual
  contract (spacing, border, radius, surface, and typography), independent of their container.

### Color

- Use `--color-navigation` only for persistent navigation or similarly strong brand anchors.
- Use `--color-action-primary` for the single primary action in a context. Secondary actions
  use a surface, text, and border token rather than another saturated fill.
- Use `--color-danger` for destructive actions and errors, never for ordinary emphasis.
- Use semantic text and surface tokens instead of primitive colors in component selectors.
- Do not communicate status through color alone; pair it with text, an icon, or both.

### Typography

- Use the system font stack; the admin must not depend on a font download to remain usable.
- Page titles use `--font-size-xl` and `--font-weight-bold`. Section titles use
  `--font-size-lg` and `--font-weight-semibold`. Body copy uses `--font-size-sm` or
  `--font-size-md` with `--line-height-normal`.
- Avoid uppercase body text. Uppercase is reserved for short labels and eyebrows.

### Spacing and layout

- Use the spacing scale instead of arbitrary pixel values. Add a primitive token only when a
  recurring need cannot be represented by the existing scale.
- Keep the main content at or below `--content-width`; allow dense tables to scroll rather than
  shrinking text below `--font-size-sm`.
- On desktop widths above 1024px, use explicit `sidebar`, `message`, and `content` grid areas. The
  content must follow the status message immediately; sidebar height must not create an implicit
  empty row above it.
- Between 750px and 1024px, keep the two-column layout but reduce the sidebar to `12rem` and the
  content padding to `--space-6`.
- At 749px and below, convert the sidebar to horizontal navigation, stack forms, and keep primary
  actions visible. Do not rely on hover for access to actions.
- Every page-level `.content-header` uses `--space-5` below it. Primary header actions belong in
  `.toolbar-actions` so schedule and catalog views share dimensions and alignment.

### Components and interaction

- Interactive controls must have a visible `:focus-visible` treatment using `--color-focus`.
- Buttons and fields must be at least `--control-height` tall. Labels remain visible; placeholders
  do not replace labels.
- Cards and panels use `--color-surface`, `--color-border`, and `--radius-lg`. Reserve shadows for
  overlays or cases where a boundary cannot be communicated with a border.
- Dialogs need a clear title, keyboard focus management, and an explicit primary action labeled
  “Salvar” in the bottom-right of the footer. “Salvar” must share the complete primary-button
  contract with other primary actions: `--control-height`, spacing tokens, border, radius, and
  semantic action colors. Do not render a “Fechar” button; the backdrop and `Esc` close the dialog.
  In activity dialogs, place “Adicionar horário” on the left of the same footer. Destructive
  actions should be visually separated from confirmation actions.
- Hide scrollbar chrome on the page and dialogs without disabling scrolling; preserve keyboard,
  wheel, and touch scrolling.
- Motion must be brief and informative. Respect `prefers-reduced-motion` for nonessential
  transitions and animations.
- Preserve the active admin view, selected schedule section, expanded groups, and scroll position
  across reloads with `sessionStorage`. Validate restored IDs against fresh API data, never persist
  unsaved form contents, and clear the view state on logout.

## Example

```css
.primary-action {
  min-height: var(--control-height);
  padding-inline: var(--space-4);
  border: var(--border-width) solid var(--color-action-primary);
  border-radius: var(--radius-md);
  background: var(--color-action-primary);
  color: var(--color-text-on-dark);
  transition: background-color var(--duration-fast) var(--ease-standard);
}

.primary-action:hover {
  background: var(--color-action-primary-hover);
}

.primary-action:focus-visible {
  outline: 3px solid var(--color-focus);
  outline-offset: 2px;
}
```

## Changing the system

Before adding a token, search for an existing token with the same visual purpose. Add a primitive
only for a reusable scale value and add a semantic token only for a stable UI role. When changing
a canonical token, update this document and the CSS declaration together, then inspect the login,
navigation, schedule editor, catalog views, dialogs, focus states, and mobile layout.

## References

- [W3C CSS Custom Properties specification](https://www.w3.org/TR/css-variables-1/)
- [Design Tokens Community Group format](https://www.designtokens.org/tr/drafts/format/)
- [MDN: Using CSS custom properties](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Cascading_variables/Using_custom_properties)
