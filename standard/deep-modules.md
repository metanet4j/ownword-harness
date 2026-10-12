```
# Deep Modules and AI-First Design

This reference defines the design target for every transformation in the refactor-code
skill: **deep modules** — simple interfaces hiding substantial functionality — organized
around **domain boundaries** and documented with **CONTEXT.md** files. It exists because
the default gravity of "clean code" refactoring pulls the other way, toward shallow
modules, and that direction is expensive in AI-maintained codebases.

## Shallow vs. Deep

A module's value is the functionality it provides minus the cost of its interface
(John Ousterhout, *A Philosophy of Software Design*).

```
        SHALLOW (avoid)                       DEEP (target)
┌──────────────────────────────┐             ┌───────────┐
│          interface           │             │ interface │
├──────────────────────────────┤             ├───────────┤
│        functionality         │             │           │
└──────────────────────────────┘             │ substan-  │
                                             │ tial      │
                                             │ function- │
                                             │ ality     │
                                             └───────────┘
```

- **Shallow module:** the interface is nearly as complex as the implementation. Examples:
  a class whose methods each relay one call to another class; an interface with a single
  implementation; a "utils" function extracted from its only call site; a service layer
  that adds no behavior between controller and repository.
- **Deep module:** callers see a few simple operations; the complexity (edge cases, state,
  protocol details) lives inside. Examples: a file system API (`open`/`read`/`write`/`close`
  hiding caching, buffering, and permissions), a `parseDocument()` that hides an entire
  grammar.

Classic clean-code heuristics — keep functions tiny, one class per responsibility, add a
layer for testability — applied mechanically produce shallow modules: more files, more
indirection, the same total complexity smeared across layers.

## Why This Matters More with AI

The human cost of shallow modules is real but tolerable. The AI cost is structural:

| Cost | Effect |
|---|---|
| Context tokens | Every layer is another file loaded into the model's context window |
| Navigation | Agents follow call chains hop by hop; each pass-through layer is another tool call and another chance to lose the thread |
| Latency and price | More files per task → more tokens → slower, more expensive agent runs |
| Cognitive load | Same as for humans: understanding one behavior requires assembling N partial views |

A deep module inverts all four: an agent reads one CONTEXT.md plus one implementation
file and has the whole story.

## The Depth Test

Before extracting a function, splitting a file, introducing an interface, or adding a
layer, all three must hold:

1. **Reuse or real complexity.** The logic is duplicated in 2+ call sites, or it is
   genuinely complex enough that a simple interface hides meaningful detail. Single-use,
   straightforward logic stays inline.
2. **The interface hides something.** If the new function/class mostly relays parameters
   to another function/class (pass-through), it adds a hop without hiding complexity.
   Don't create it.
3. **Fewer files to understand a behavior.** After the change, tracing one user-visible
   behavior should touch the same number of files or fewer. If the count goes up, the
   refactor made the codebase shallower — reconsider.

The same test applies to design patterns: a pattern that passes is a tool; a pattern
that fails is ceremony. See the design-patterns skill's "Evaluate Fit" step.

## Shallow-Module Smells (Refactor Candidates)

These are as much technical debt as god classes — flag them in Phase 1 and collapse
them in Phase 3:

| Smell | Fix |
|---|---|
| Pass-through methods or classes (only relay calls) | Inline the layer |
| Interface with one implementation and no test seam | Delete the interface, keep the implementation |
| Single-use helper extracted "for cleanliness" | Inline into the caller |
| Layer-per-technical-concern (controller → service → manager → repository, each a few lines) | Merge into one deep module per domain capability |
| Wrapper classes that only hold another object | Use the object directly |
| Deep import chains (A → B → C → D to find one behavior) | Flatten |

## Domain Boundaries (DDD-lite)

Deep modules need good boundaries, and the best boundaries are domain capabilities, not
technical layers:

- **Group by capability:** `billing/`, `ingestion/`, `notifications/` — not
  `controllers/`, `services/`, `helpers/`.
- **Ubiquitous language:** name modules, types, and functions with the words the domain
  experts use. An agent that reads `invoice.settle()` needs no extra context;
  `dataManager.process()` needs a paragraph.
- **Explicit boundaries:** each module exposes a small public surface; everything else is
  internal. Cross-module imports go through the public surface only.

You don't need full tactical DDD (aggregates, repositories, domain events) to get the
benefit — boundaries plus language plus a CONTEXT.md per module captures most of the
value at a fraction of the structure.

## CONTEXT.md: Persistent Context per Module

Every significant module directory gets a `CONTEXT.md`. It is the agent-facing (and
human-facing) summary that survives between sessions, so nobody has to re-derive the
module from source every time.

Template:

```markdown
# <module name>

## Purpose
One paragraph: what capability this module provides and for whom.

## Domain language
| Term | Meaning |
|---|---|
| ... | Definition as the domain experts use it |

## Boundaries
- Public surface: <the few entry points other modules may use>
- Depends on: <modules this one imports from>
- Used by: <modules that import this one>

## Invariants
- Rules that must always hold (e.g., "an invoice is immutable after settlement")
- Intentional quirks that must NOT be "fixed" during refactoring

## Key flows
- 2-4 bullet walkthroughs of the main behaviors and which files implement them
```

Rules:

- Keep it under ~80 lines — it is a map, not a mirror of the code.
- Phase 1 (analyze-codebase) reads existing CONTEXT.md files first and flags stale ones.
- Phase 3 (refactor-code, Pass 3) writes or refreshes CONTEXT.md for every module touched.
- Treat a wrong CONTEXT.md as a bug: agents will trust it.

## Optimize for Now, Not for Hypothetical Futures

Speculative flexibility — "wrap it in an interface in case we swap providers someday" —
is the single biggest generator of shallow layers. Two facts make it a bad trade:

1. **You pay the indirection cost on every task from day one**, in tokens, hops, and
   review effort.
2. **The cost of restructuring later keeps falling.** Models and methodology improve
   every quarter; refactors that once justified months of defensive abstraction are now
   executed in days behind a test safety net — which is this framework's whole premise.

Build the simplest deep structure that serves today's requirements. When a real
requirement arrives, run the four phases and restructure with evidence instead of
guesses.
```