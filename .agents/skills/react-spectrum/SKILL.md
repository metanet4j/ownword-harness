---
name: react-spectrum
description: React Spectrum implementation rules for OwnWord frontend development.
---

# React Spectrum Implementation Skill

## Purpose

React Spectrum is the component implementation foundation for common UI interactions in OwnWord.

Before applying this skill, read:

1. `_task/system-design/spec/核心认知.md`
2. the current version design document
3. `standard/design-skill-architecture.md`

This skill implements existing OwnWord design decisions. It does not define product facts or product positioning.

## Use React Spectrum for

- Button
- Dialog
- Menu
- Form controls
- Selection components
- Accessible interaction patterns
- Common component states and interaction behavior

## Do not force React Spectrum for

- Personal homepage hero sections
- Brand identity presentation
- Custom storytelling layouts
- Unique content visualization
- Project-specific visual expressions already defined by the current design document

## Component Rules

Prefer official React Spectrum components before creating custom equivalents when they satisfy the required interaction.

Custom components should focus on OwnWord-specific experiences and visual expressions.

When the current version design document specifies React Spectrum or Spectrum S2, follow that design-system constraint for common UI components and interaction patterns.

## Design Token Rules

Use React Spectrum tokens and theme capabilities for:

- Color
- Typography
- Spacing
- Component states
- Focus and interaction states

Avoid arbitrary values when an existing token can express the requirement.

Project-specific visual tokens may be introduced only when required by the current design document and when they do not duplicate an existing Spectrum token.

## Accessibility Rules

Interactive components must support:

- Keyboard navigation
- Focus management
- Screen reader usage
- Correct semantic structure
- Required contrast and non-color state communication

## Boundary

Product facts come from `_task/system-design/spec/核心认知.md`.

Page structure, visual direction and version-specific interaction requirements come from the current version design document.

`baoyu-design` and visual design skills may improve design reasoning and expression within those constraints.

React Spectrum defines component implementation behavior, tokens, interaction consistency and accessibility. It must not override Core Cognition or the current version design document.
