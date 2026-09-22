<img src="assets/header.svg" alt="Martin Bouvet — Builder × Business × AI" width="100%" />

## Business student who ships AI-powered products

I study at emlyon and I build. I learned LLMs, generative and agentic AI at Oxford, and I work with AI agents the way a founder works with a small team: I own the problem, the product decisions and the trade-offs, and the agents compress the distance between a decision and a shipped feature.

Still a student — and already shipping seriously. That order matters.

**[Portfolio: five case studies →](https://martinbouvet2000-tech.github.io/)**

---

## Selected work

<a href="https://github.com/martinbouvet2000-tech/nightshift"><img src="assets/covers/nightshift.svg" alt="nightshift — a second brain that works while you sleep" width="100%" /></a>

**The problem.** I saved hundreds of videos and remembered almost none of them. Saving is not learning.  
**What I built.** A pipeline that turns saved videos into scored Markdown notes, and a Claude Code agent that consolidates the vault overnight inside hard limits: a time window, a lock, a timeout, one retry, and a proof line it must print before the run counts as done. Its file access never leaves the vault, because a transcript from the internet is untrusted input.  
**Proof.** 89 tests · CI on Linux and Windows · a demo that runs offline, with no API key, in under a minute.

[Repository](https://github.com/martinbouvet2000-tech/nightshift) · [Case study](https://martinbouvet2000-tech.github.io/work/ai-os.html)

<a href="https://github.com/martinbouvet2000-tech/nous-deux"><img src="assets/covers/nous-deux.svg" alt="Nous Deux — warm product, paranoid backend" width="100%" /></a>

**The problem.** Two people living apart juggle time zones, two timetables and a dozen apps to share small daily moments — with data as private as data gets.  
**What I built.** One shared space: dual clocks, an opt-in live map with 48-hour retention, a calendar that imports a whole school timetable from a PDF, and time capsules the database keeps sealed until their date. Notifications say *who* did something, never *what*.  
**Proof.** Security lives in row-level policies, not in the client: 24 migrations, sign-ups capped at two accounts, 374 test cases, CI on every push.

[Repository](https://github.com/martinbouvet2000-tech/nous-deux) · [Live app](https://martinbouvet2000-tech.github.io/nous-deux/) · [Case study](https://martinbouvet2000-tech.github.io/work/nous-deux.html)

<a href="https://martinbouvet2000-tech.github.io/work/cortex.html"><img src="assets/covers/cortex.svg" alt="Cortex — course handout in, study system out" width="100%" /></a>

**The problem.** First-year medicine and law students rewrite their handouts by hand, then revise without structure. Flashcard apps don't know their course; chatbots answer from the whole internet.  
**What I built.** Drop in a PDF, get a study sheet, ten questions, a spaced-repetition plan and a tutor that answers only from that course. Freemium with Stripe, and an admin panel that runs the public site from a phone.  
**Proof.** Live in production in demo mode, 33 tests, and a security pass: rate limits, CSRF checks, per-user data scoping, server-side grading. The code is private.

[Live site](https://cortex-revisions.vercel.app) · [Case study](https://martinbouvet2000-tech.github.io/work/cortex.html)

<sub>Also built: <a href="https://github.com/martinbouvet2000-tech/business-idea-radar">Business Idea Radar</a> · <a href="https://martinbouvet2000-tech.github.io/Diabete/">Diavie</a> · <a href="https://martinbouvet2000-tech.github.io/code-examen/">Code Examen</a> · <a href="https://martinbouvet2000-tech.github.io/aurelia-masque/">Aurélia</a></sub>

---

## How I build

```text
   me                          agents                        me
   ──                          ──────                        ──
   problem  ──►  spec  ──►  build  ──►  tests  ──►  review  ──►  ship
      ▲                                                            │
      └────── the night agent consolidates what I learned ◄────────┘
              (00:30, every day, inside hard limits)
```

I own the decisions: what the problem is, who it is for, what gets cut, what "done" means. Agents own execution speed. Every run ends with a verification pass, and nothing ships on trust alone — that is why the numbers above are test counts, not adjectives.

My second brain feeds the loop: it is versioned on GitHub, indexed so agents can search it, and consolidated every night. The reusable core is open source as [nightshift](https://github.com/martinbouvet2000-tech/nightshift).

---

## Stack

**Build** — TypeScript · React · Next.js · Python · Node  
**AI &amp; agents** — Claude Code · Anthropic API · MCP · Obsidian  
**Ship &amp; run** — Supabase · PostgreSQL · Vercel · GitHub Actions · Stripe

---

## Currently building

**nightshift v0.2** — more capture sources, and real-run coverage for the night agent.  
**E-invoicing audit** — a fixed-price readiness audit for small businesses, before France's September 2026 deadline.  
**Cortex** — a first student cohort, then switching real generation on.

---

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/pulse-dark.svg" />
    <img src="assets/pulse-light.svg" alt="Languages I write and my weekly contribution pulse over the last 12 months" width="100%" />
  </picture>
</p>

<sub>This card is generated from the GitHub API by <a href="scripts/build_card.py">a script in this repo</a> and rebuilt every morning by a GitHub Action — the profile maintains itself. <a href="scripts/build_covers.py">The project covers</a> are generated the same way.</sub>

**Contact** — [portfolio](https://martinbouvet2000-tech.github.io/) · [discussions](https://github.com/martinbouvet2000-tech/martinbouvet2000-tech/discussions) · [issues on nightshift](https://github.com/martinbouvet2000-tech/nightshift/issues)
