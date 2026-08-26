# Hacker Terminal Design Framework

This document outlines the design system and CSS framework used to achieve the "Hacker Terminal" aesthetic. Use this as a reference guide to replicate this exact style for your future projects and web applications.

## 1. Core Philosophy
- **Utilitarian & Angular**: Sharp edges only. No `border-radius`, no `box-shadow`, no soft gradients.
- **Monochromatic Data**: Pure black backgrounds with stark white/gray data to maximize contrast. 
- **Typewriter Feel**: Global monospace fonts to mimic command-line interfaces.
- **Subtle Interactivity**: Active states and hovers rely on stark background inversions or thin accent-colored borders (e.g., `#9d4edd` subtle purple).

---

## 2. Global Design Tokens (CSS Variables)
Include these at the root of your stylesheet.

```css
:root {
    /* Backgrounds */
    --bg-main: #000000;          /* Deepest black for main body */
    --bg-sidebar: #0a0a0a;       /* Slightly elevated background */
    --bg-card: #080808;          /* Panel background */
    --bg-card-hover: #121212;    /* Interactive panel hover */
    
    /* Borders */
    --border-color: #333333;     /* Standard thin wireframe border */
    --border-hover: #9d4edd;     /* Accent color on hover */
    
    /* Typography */
    --text-primary: #f0f0f0;     /* High contrast text */
    --text-secondary: #888888;   /* Muted text for labels/subtitles */
    
    /* Accents */
    --accent-primary: #9d4edd;   /* Primary interaction color (Subtle Purple) */
}
```

---

## 3. The "Hacker" CSS Reset
This reset enforces the monospace font and strips all modern web aesthetics (roundness and shadows) globally.

```html
<!-- Include Google Font -->
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&display=swap" rel="stylesheet">
```

```css
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    
    /* Force Angularity & Flatness */
    border-radius: 0 !important;
    box-shadow: none !important;
    
    /* Global Monospace */
    font-family: 'Fira Code', 'Courier New', monospace !important;
}

body {
    background-color: var(--bg-main);
    color: var(--text-primary);
    line-height: 1.5;
}
```

---

## 4. Component Patterns

### Typography
- **Headers**: Uppercase, tracked out (letter-spacing), solid primary text color.
- **Labels/Subtitles**: Uppercase, smaller font size (`0.8rem`), secondary text color.

```css
.text-heading {
    font-size: 1.2rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-primary);
}

.text-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    color: var(--text-secondary);
}
```

### Cards & Panels
Used to containerize content. Very simple wireframe borders.

```css
.panel {
    background-color: transparent;
    border: 1px solid var(--border-color);
    padding: 24px;
}
```

### Interactive Buttons & Selects
Transparent backgrounds with wireframe borders. Hover states change the border color to the accent. Active states change the text color and add a slight background tint.

```css
.btn {
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    padding: 10px 16px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
    outline: none;
}

.btn:hover {
    color: var(--accent-primary);
    border-color: var(--accent-primary);
}

.btn.active {
    color: var(--accent-primary);
    border-color: var(--accent-primary);
    background-color: rgba(157, 78, 221, 0.05); /* 5% opacity of accent */
}
```

### Form Inputs & Search Bars
```css
.input-text {
    background-color: transparent;
    border: 1px solid var(--border-color);
    padding: 10px 12px;
    color: var(--text-primary);
    outline: none;
    transition: border-color 0.2s ease;
}

.input-text:focus {
    border-color: var(--accent-primary);
}
```

### Data Tables
Tables are stripped back. Headers have a slightly different background, and borders separate the cells vertically and horizontally to look like terminal grids.

```css
.data-table {
    width: 100%;
    border-collapse: collapse;
}

.data-table th, .data-table td {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-color);
    border-right: 1px solid var(--border-color);
}

.data-table th {
    background-color: var(--bg-sidebar);
    color: var(--text-secondary);
    text-transform: uppercase;
    font-weight: normal;
}

.data-table tr:hover td {
    background-color: rgba(255, 255, 255, 0.05);
}
```

---

## 5. Custom Scrollbars
To complete the look, standard operating system scrollbars should be overwritten to match the dark blocky theme.

```css
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: var(--bg-main);
    border-left: 1px solid var(--border-color);
}
::-webkit-scrollbar-thumb {
    background: var(--border-color);
}
::-webkit-scrollbar-thumb:hover {
    background: var(--border-hover);
}
```

## Summary Checklist for New Projects
1. Copy the CSS `:root` variables.
2. Import `Fira Code` (or another monospace font) and apply the `*` universal reset to strip borders and shadows.
3. Build layouts using CSS Grid or Flexbox, applying `1px solid var(--border-color)` to separate visual zones.
4. Keep all backgrounds `transparent` or `#000`/`#0a0a0a`.
5. Map hover effects exclusively to `border-color` and `color` changes, avoiding background fills unless the opacity is extremely low (`~0.05`).
