<img src="assets/header.svg" alt="Martin Bouvet — Builder × Business × AI" width="100%" />

## Business student who ships AI-powered products

I study at emlyon and I build. I learned LLMs, generative and agentic AI at Oxford, and I work with AI agents the way a founder works with a small team: I own the problem, the product decisions and the trade-offs, and the agents compress the distance between a decision and a shipped feature.

**[→ Portfolio: five case studies, with architecture, decisions and honest numbers](https://martinbouvet2000-tech.github.io/)**

### About

- First year of the **Global BBA at emlyon**, Gerland campus, Lyon.
- I ship in public: 2 open-source products, 8 live demos, and a system of agents that runs on a schedule every day.
- The question I answer before writing any code: **what does this create, for whom, and is it worth paying for?**
- Currently selling an e-invoicing readiness audit to small businesses, ahead of France's 2026 deadline.

## Selected work

### [nightshift](https://github.com/martinbouvet2000-tech/nightshift) — a second brain that works while you sleep

The open-source core of the system I run daily. Saved videos become scored Markdown notes, then a Claude Code agent consolidates the vault overnight inside hard limits: a time window, a lock, a timeout, one retry, and a proof line it must print before the run counts. Offline demo, no API key, under a minute.

`Python` · `Node` · `Claude Code` · `89 tests` · `CI on Linux + Windows` · **[case study](https://martinbouvet2000-tech.github.io/work/ai-os.html)**

### [Nous Deux](https://github.com/martinbouvet2000-tech/nous-deux) — warm product, paranoid backend

A private space for two people living apart: dual time zones, a real-time shared map, a shared calendar that imports a whole school timetable from a PDF, and time capsules the database keeps sealed until their date. Security lives in row-level policies, not in the client.

`React 19` · `TypeScript` · `Supabase` · `374 tests` · **[live](https://martinbouvet2000-tech.github.io/nous-deux/)** · **[case study](https://martinbouvet2000-tech.github.io/work/nous-deux.html)**

### [Cortex](https://cortex-revisions.vercel.app) — course handout in, study system out

A revision platform for French university students: drop in a PDF, get a study sheet, quizzes, a spaced-repetition plan and a tutor that answers only from that course. Freemium with Stripe, and an admin panel that runs the public site from a phone. Live MVP in demo mode; the code is private.

`Next.js 16` · `Prisma` · `Postgres` · `Claude` · `Stripe` · **[case study](https://martinbouvet2000-tech.github.io/work/cortex.html)**

<sub>Also built: <a href="https://github.com/martinbouvet2000-tech/business-idea-radar">Business Idea Radar</a> · <a href="https://martinbouvet2000-tech.github.io/Diabete/">Diavie</a> · <a href="https://martinbouvet2000-tech.github.io/code-examen/">Code Examen</a> · <a href="https://martinbouvet2000-tech.github.io/aurelia-masque/">Aurélia</a> — all on the <a href="https://martinbouvet2000-tech.github.io/#more">portfolio</a>.</sub>

## How I build

```text
idea ──► second brain ──► spec ──► agents build ──► tests ──► ship
           (Obsidian)             (Claude Code)                 │
              ▲                                                 │
              └──── the night agent consolidates what I learned ◄┘
```

- **I own the decisions, the agents own the execution.** Planning, parallel subagents, code review, and a verification pass before anything is called done.
- **A second brain that works overnight.** My vault is versioned on GitHub, indexed so agents can search it, and consolidated every night at 00:30 by a scheduled agent.
- **Capture pipelines.** The videos I save are transcribed, scored and filed as structured notes automatically — that core is [nightshift](https://github.com/martinbouvet2000-tech/nightshift).

## Stack

**Build**
<p>
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB" alt="React" />
  <img src="https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=nextdotjs&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Node.js-5FA04E?style=flat-square&logo=nodedotjs&logoColor=white" alt="Node.js" />
</p>

**Agents &amp; AI**
<p>
  <img src="https://img.shields.io/badge/Claude_Code-D97757?style=flat-square&logo=anthropic&logoColor=white" alt="Claude Code" />
  <img src="https://img.shields.io/badge/Anthropic_API-D97757?style=flat-square&logo=anthropic&logoColor=white" alt="Anthropic API" />
  <img src="https://img.shields.io/badge/MCP-000000?style=flat-square&logo=modelcontextprotocol&logoColor=white" alt="Model Context Protocol" />
  <img src="https://img.shields.io/badge/Obsidian-7C3AED?style=flat-square&logo=obsidian&logoColor=white" alt="Obsidian" />
</p>

**Ship &amp; run**
<p>
  <img src="https://img.shields.io/badge/Supabase-3FCF8E?style=flat-square&logo=supabase&logoColor=white" alt="Supabase" />
  <img src="https://img.shields.io/badge/Postgres-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white" alt="Vercel" />
  <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white" alt="GitHub Actions" />
  <img src="https://img.shields.io/badge/Stripe-635BFF?style=flat-square&logo=stripe&logoColor=white" alt="Stripe" />
</p>

## Signals

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/card-dark.svg" />
    <img src="assets/card-light.svg" alt="Profile card: business student at emlyon, AI-native builder, with live GitHub counters" width="100%" />
  </picture>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/pulse-dark.svg" />
    <img src="assets/pulse-light.svg" alt="Languages I write and my weekly contribution pulse over the last 12 months" width="100%" />
  </picture>
</p>

<sub>Both cards are generated from the GitHub API by <a href="scripts/build_card.py">a script in this repo</a> and rebuilt every morning by a GitHub Action. No third-party stats service, nothing that breaks silently.</sub>

## Currently building

- **nightshift v0.2** — more capture sources (podcasts, RSS, read-later) and real-run coverage for the night agent.
- **The e-invoicing audit** for small businesses in Lyon, before receiving becomes mandatory in September 2026.
- **Cortex with a first cohort** of students, then switching real generation on for them.

## Contact

Open an [issue on nightshift](https://github.com/martinbouvet2000-tech/nightshift/issues), start a [discussion](https://github.com/martinbouvet2000-tech/martinbouvet2000-tech/discussions), or read the [portfolio](https://martinbouvet2000-tech.github.io/) first — it explains how I work better than a résumé would.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/martinbouvet2000-tech/martinbouvet2000-tech/output/snake-dark.svg" />
  <img src="https://raw.githubusercontent.com/martinbouvet2000-tech/martinbouvet2000-tech/output/snake-light.svg" alt="My contribution graph being eaten by a snake" width="100%" />
</picture>
