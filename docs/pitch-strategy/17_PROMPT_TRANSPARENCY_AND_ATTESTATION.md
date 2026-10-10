# Mend: Open Prompt & Attestation Strategy

Captured 2026-10-10 from a strategy conversation about publishing Thimble's system prompt to earn user trust. Not yet built; this is the rationale and the shape of what to build, not finished copy.

## The problem this solves

The biggest adoption barrier for Mend is the surveillance paradox: an employee asked to drop their guard in a company-sponsored tool reasonably assumes it has a hidden agenda, stealth-scores them, or reports back to HR. Mend's actual architecture (see [03_TECHNICAL_ARCHITECTURE_AND_WATCHER.md](03_TECHNICAL_ARCHITECTURE_AND_WATCHER.md)) already has nothing to hide; publishing the prompt turns that into something a skeptical employee or HR buyer can verify instead of take on faith.

## What to publish

- The actual prompt files already at repo root (`facilitator-persona.md`, `facilitator-intake-system-prompt.md`, `facilitator-case-plan-system-prompt.md`, `facilitator-joint-session-system-prompt.md`, `facilitator-post-session-system-prompt.md`, `facilitator-manager-coaching-system-prompt.md`) and `manager-app/THIMBLE_MINDSET.md` as the "why." These are already written as clean, pasteable prompt text with rationale attached, so there is no separate "public-facing cleanup" pass needed beyond fixing anything genuinely embarrassing or half-finished before release.
- A short, human-readable summary for the trust page: neutrality rubric, turn-taking rules, what triggers the safety floor, pointing back at the real files rather than restating them in marketing language.

## Why publishing the prompt doesn't compromise safety

The Watcher (see 03, "Multi-Agent Orchestration Loop") audits every Thimble draft before it reaches the screen, independent of the facilitator prompt. Someone who memorizes Thimble's instructions can try to steer it, but they can't disable the Watcher by knowing the facilitator's wording, and the mandatory floor categories (threats, harassment, discrimination, illegal activity, immediate safety risk) are deliberately fixed and non-configurable rather than prompt-defined behavior that a clever phrasing could talk around.

## Verifying the live prompt matches what's published

The gap a technical buyer will actually probe: "you published a prompt, how do I know the running app uses that exact text and not something else." Two pieces close that gap, in order of effort:

1. **SHA-256 manifest.** A small script hashes each `facilitator-*-system-prompt.md` file and the Watcher's rubric file, checked into the repo alongside a `commit` field. Cheap, no runtime cost, and already enough to let anyone diff the published file against what a leaked or exported transcript implies the app is running.
2. **Runtime attestation endpoint.** A read-only route (e.g. `/api/v1/attestation`) that hashes the files the running server actually loaded into memory and returns them alongside the published manifest. This is the piece that actually proves the *deployed* instance matches the *published* repo, not just that the repo is internally consistent. Worth building once there's a real server deployment to attest; premature before that.

Hardware attestation (confidential-computing enclaves, signed boot quotes) is a real option for the "zero persistent storage, RAM only" claim specifically, but it's a heavier lift than the product needs at pilot stage. Revisit if an enterprise security review specifically asks for it; don't build it speculatively.

## Trust page copy direction

Short, point at the real artifact, don't oversell:

> Thimble's instructions are public. We publish the exact system prompt and the rules that trigger an HR escalation, so you can verify for yourself that nothing here is secretly scored, profiled, or reported upward. [Read the facilitator prompt →]

Avoid stacking adjectives ("radical," "zero hidden agendas") in the actual shipped copy; the strongest version of this claim is the link itself, not the framing around it.

## Open questions

- Which repo (or a mirror of just the prompt files) actually gets made public, given `origin`'s current status; a prompt-only mirror repo is the likely shape, not opening this whole working repo.
- Whether the trust-page link goes live before or after the first real pilot; publishing before any outside user has seen the product risks it reading as a transparency stunt rather than an earned claim.
