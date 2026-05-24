# Design

## Visual Direction

Use a restrained, editorial-technical look with a dark neutral surface, one strong accent, and dense but highly legible information blocks.

## Color

- Base: tinted charcoal and slate neutrals
- Accent: muted electric cyan
- Support: warm paper tint for receipts and evidence panels

## Typography

- Headings: serif display with character
- Body: modern sans for dense reading
- Numeric or protocol labels: monospace

## Layout

- Full-width hero band with a left-aligned explanation and right-side live protocol comparison
- Two-column comparison below, raw chat on one side, structured receipt on the other
- Compact evidence rail for receipts, status, next owner, and human decision

## Components

- Segmented toggle for "Without SACP" and "With SACP"
- Receipt cards with status, next owner, and evidence chips
- Timeline strip for handoff -> attempt -> receipt -> next owner
- Evidence chips and status badges

## Motion

- Subtle entrance and crossfade when switching between states
- No decorative motion
- Motion should support the comparison, not distract from it

## Responsiveness

- Stack the comparison on small screens
- Keep the receipt state visible before the evidence rail collapses
- Preserve readable line lengths on all viewports
