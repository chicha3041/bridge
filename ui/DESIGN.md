---
name: Bridge Analysis System
colors:
  surface: '#051424'
  surface-dim: '#051424'
  surface-bright: '#2c3a4c'
  surface-container-lowest: '#010f1f'
  surface-container-low: '#0d1c2d'
  surface-container: '#122131'
  surface-container-high: '#1c2b3c'
  surface-container-highest: '#273647'
  on-surface: '#d4e4fa'
  on-surface-variant: '#c6c6cd'
  inverse-surface: '#d4e4fa'
  inverse-on-surface: '#233143'
  outline: '#909097'
  outline-variant: '#45464d'
  surface-tint: '#bec6e0'
  primary: '#bec6e0'
  on-primary: '#283044'
  primary-container: '#0f172a'
  on-primary-container: '#798098'
  inverse-primary: '#565e74'
  secondary: '#b9c7e0'
  on-secondary: '#233144'
  secondary-container: '#3c4a5e'
  on-secondary-container: '#abb9d2'
  tertiary: '#dec29a'
  on-tertiary: '#3e2d11'
  tertiary-container: '#231500'
  on-tertiary-container: '#957d5a'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#d5e3fd'
  secondary-fixed-dim: '#b9c7e0'
  on-secondary-fixed: '#0d1c2f'
  on-secondary-fixed-variant: '#3a485c'
  tertiary-fixed: '#fcdeb5'
  tertiary-fixed-dim: '#dec29a'
  on-tertiary-fixed: '#271901'
  on-tertiary-fixed-variant: '#574425'
  background: '#051424'
  on-background: '#d4e4fa'
  surface-variant: '#273647'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  title-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  data-mono:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
  label-xs:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 12px
---

## Brand & Style

The design system is engineered for the intellectual rigour and strategic depth of competitive bridge. It evokes a "Digital Club" atmosphere—sophisticated, authoritative, and focused. The aesthetic prioritizes **Corporate Modernism** with a heavy emphasis on **High-Density Utility**.

The visual language is characterized by:
- **Analytical Precision:** Every pixel serves a data-driven purpose. 
- **Sophisticated Professionalism:** A dark, scholarly palette that reduces eye strain during prolonged post-game analysis.
- **Structured Logic:** Clear visual hierarchies that guide the eye through complex auction sequences and hand distributions without cognitive overload.

The UI should feel like a premium analytical tool: silent, efficient, and deeply informative.

## Colors

The color palette is anchored in deep navies and slates to establish a refined environment.

- **Primary & Neutral:** The foundation uses `Navy (#0F172A)` for the deepest surfaces and `Slate (#334155)` for UI containers. This creates a low-glare, "midnight" club aesthetic.
- **Functional Accents:** 
    - **North/South (Blue):** A clear, professional blue for identifying the home pair.
    - **East/West (Green):** A distinct emerald green for identifying the opponents.
- **Semantic Status:** 
    - **Points Won:** High-contrast Emerald for positive outcomes.
    - **Points Lost:** A muted but clear Rose for negative outcomes.
- **Data Coloring:** Use suit symbols (Spades/Clubs in Slate-100, Hearts/Diamonds in Rose-400) within data tables for instant recognition.

## Typography

The design system utilizes **Inter** for its exceptional legibility in data-heavy environments and its neutral, technical tone.

**Key Typographic Rules:**
- **Tabular Figures:** For all numerical data, auction tables, and point counts, the `tnum` (tabular numbers) OpenType feature must be enabled to ensure vertical alignment across rows.
- **Visual Hierarchy:** Use `label-xs` for technical metadata (e.g., "HCP", "Vulnerability") to maximize space while maintaining readability.
- **Scalability:** On mobile devices, `display-lg` should scale down to 24px to prevent layout breaking in hand detail views.

## Layout & Spacing

This design system employs a **Structured Grid** model designed for high information density.

- **Grid System:** A 12-column fluid grid for desktop, collapsing to 4 columns on mobile. 
- **Density:** We utilize a tight 4px base unit. This allows for complex auction tables and hand diagrams to sit comfortably on a single screen without scrolling.
- **Component Padding:** Internal card padding is strictly `12px (gutter)` or `16px (md)` to ensure data feels organized but not cramped.
- **Reflow Rules:** On mobile, hand details reflow from a horizontal "Compass" view to a vertical stacked list (N, E, S, W).

## Elevation & Depth

To maintain the sophisticated "club" feel while staying modern, we use **Tonal Layering** instead of heavy shadows.

- **Surface 0 (Background):** `#0F172A` (Navy) - The primary application canvas.
- **Surface 1 (Cards/Containers):** `#1E293B` (Slate-800) - Used for primary content sections like Hand Details.
- **Surface 2 (Interactive/Overlay):** `#334155` (Slate-700) - Used for hover states, dropdowns, and modal elements.
- **Outlines:** Instead of shadows, use 1px solid borders in `#334155` to define component boundaries. This creates a crisp, architectural look suitable for analytical software.

## Shapes

The shape language is **Soft (0.25rem)**, striking a balance between the rigidity of data tables and the approachability of a modern web application.

- **Standard Elements:** Buttons, input fields, and small cards use a 4px (0.25rem) radius.
- **Data Cells:** Cells within auction tables remain square (0px) to maximize the "spreadsheet" efficiency and vertical alignment.
- **Feature Components:** Large hand-analysis cards may use `rounded-lg` (8px) to signify they are primary containers.

## Components

### Hand Detail Cards
Primary containers for card distributions. They feature a 1px border and use the color-coded suits. Layout should be fixed-width to ensure the "Spade, Heart, Diamond, Club" alignment is consistent across all hands.

### Auction Tables
The core of the analysis. These use a strict grid with `data-mono` typography. Header cells should be semi-transparent Slate to distinguish the bidding positions (N, E, S, W).

### Bidding Chips
Small, interactive elements representing a bid (e.g., 1NT, 4S). These use the `rounded-sm` radius and high-contrast text. Use the primary Blue for NS bids and Emerald for EW bids.

### Technical Progress Bars
Used for tracking "High Card Points" (HCP) or "Winning Probability." These are slim (4px-8px height) with a Slate track and colored fills based on the pair (Blue/Green).

### Input Fields
Dark-themed inputs with `#334155` backgrounds. On focus, use a 1px solid `accent_ns_hex` border.

### Status Indicators
Small circular dots or subtle background tints used in the scorecards to denote "Vulnerable" vs "Non-Vulnerable" status.