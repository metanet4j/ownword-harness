---
name: react-spectrum
description: Spectrum S2 implementation rules for OwnWord frontend development.
---

# Spectrum S2 Implementation Skill

## Purpose

Spectrum S2 is the fixed and only primary design system for OwnWord.

This skill is the implementation guardrail for applying Spectrum S2 to OwnWord frontend work. It does not choose a design system and does not define product facts or product positioning.

Before applying this skill, read:

1. `_task/system-design/spec/核心认知.md`
2. the current version design document
3. `standard/design-skill-architecture.md`

## Binding Rule

Always use Spectrum S2 as the primary design system.

Do not replace or parallel it with another primary system such as Material, Fluent, Carbon, shadcn/ui, or Radix Themes.

Visual specialist skills may influence composition, density, typography, or motion only where their rules remain compatible with Spectrum S2 and the current version design document.

## Use Spectrum S2 for

- Button
- Dialog
- Menu
- Form controls
- Selection components
- Common navigation and action patterns
- Common component states
- Accessible interaction patterns
- Design Tokens
- Focus and interaction behavior

## Custom OwnWord UI

Custom layouts and components are allowed for OwnWord-specific expression, including:

- Personal homepage Hero
- Identity presentation
- Content Showcase
- Artifact presentation
- Custom storytelling layouts
- Unique content visualization

Custom UI must:

- prefer Spectrum S2 tokens where applicable;
- reuse Spectrum S2 components for standard interactions;
- follow Spectrum S2 state and interaction conventions;
- preserve Spectrum S2 accessibility requirements;
- avoid creating a parallel generic component system.

## Component Rules

Prefer official Spectrum S2 components before creating custom equivalents when they satisfy the required interaction.

Create custom components when the requirement is OwnWord-specific or cannot be expressed coherently with an existing Spectrum S2 component.

Do not restyle a standard interaction into a separate visual language merely to satisfy a visual specialist skill.

## Design Token Rules

Use Spectrum S2 tokens and theme capabilities for:

- Color
- Typography
- Spacing
- Component states
- Focus and interaction states

Avoid arbitrary values when an existing Spectrum S2 token can express the requirement.

Project-specific visual tokens may be introduced only when required by the current version design document and when they do not duplicate an existing Spectrum S2 token or create a parallel token system.

## Accessibility Rules

Interactive components must support:

- Keyboard navigation
- Focus management
- Screen reader usage
- Correct semantic structure
- Required contrast
- Non-color state communication
- Reduced-motion behavior where applicable

## Boundary

Product facts come from `_task/system-design/spec/核心认知.md`.

Page structure, visual direction and version-specific interaction requirements come from the current version design document.

Spectrum S2 defines the fixed design-system foundation.

`baoyu-design` organizes the design workflow. `design-taste-frontend` and `high-end-visual-design` may improve visual execution only inside the Spectrum S2 boundary.

This skill checks Spectrum S2 implementation behavior, tokens, interaction consistency and accessibility. It must not override Core Cognition or the current version design document.
