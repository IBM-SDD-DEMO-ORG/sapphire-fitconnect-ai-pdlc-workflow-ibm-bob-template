# Implementation Queue — SDDSDLC-223

Generated: 2025-07-17

> Each entry is one `speckit.implement` invocation. Entries are processed in order.
> Tick `[x]` only when the corresponding invocation produces a `## Phase Complete` report.
> Entries within the same dependency tier can be run in parallel (marked `[P]`).

---

## Queue

### Tier 1 — Branch Setup (all repos, parallel)

- [ ] Q01 sapphire-charting-api / Phase 1 — Setup
- [ ] Q02 [P] sapphire-bff-api / Phase 1 — Setup
- [ ] Q03 [P] Sapphire / Phase 1 — Setup

### Tier 2 — Foundational (charting-api first; bff-api contract test runs in parallel)

- [ ] Q04 sapphire-charting-api / Phase 2 — Foundational
- [ ] Q05 [P] sapphire-bff-api / Phase 2 — Foundational

### Tier 3 — US1: Ingestion (charting-api only; bff-api and Sapphire unblock after Q04)

- [ ] Q06 sapphire-charting-api / Phase 3 — [US1] Ingest and Store Temperature Readings (P1)

### Tier 4 — US2: Trends + GraphQL + Chart (charting-api backend → bff-api → Sapphire)

- [ ] Q07 sapphire-charting-api / Phase 4 — [US2] View Temperature History and Trends (P2)
- [ ] Q08 sapphire-bff-api / Phase 4 — [US2] View Temperature History and Trends (P2)
- [ ] Q09 [P] Sapphire / Phase 4 — [US2] View Temperature History and Trends (P2)

### Tier 5 — US3: Export + Dashboard (all three repos, charting-api → bff-api + Sapphire parallel)

- [ ] Q10 sapphire-charting-api / Phase 5 — [US3] Export and Analytics Dashboard Inclusion (P3)
- [ ] Q11 [P] sapphire-bff-api / Phase 5 — [US3] Export and Analytics Dashboard Inclusion (P3)
- [ ] Q12 [P] Sapphire / Phase 5 — [US3] Export and Analytics Dashboard Inclusion (P3)

### Tier 6 — Polish & Cross-Cutting (all repos, parallel)

- [ ] Q13 sapphire-charting-api / Phase 6 — Polish & Cross-Cutting Concerns
- [ ] Q14 [P] sapphire-bff-api / Phase 6 — Polish & Cross-Cutting Concerns

---

## Dependency Order

```
Q01, Q02, Q03 (branch setup — all parallel)
  └─► Q04 (charting-api foundational: enum, migration, DTOs, config)
  └─► Q05 (bff-api foundational: SDL contract test — parallel with Q04)
        └─► Q06 (charting-api US1: ingestion service, controller, tests)
              └─► Q07 (charting-api US2: trend service + endpoint)
              └─► Q08 (bff-api US2: typeDefs, resolver, datasource, tests)
                    └─► Q09 (Sapphire US2: GraphQL queries + chart component — parallel with Q08 completion)
              └─► Q10 (charting-api US3: export + dashboard)
              └─► Q11 (bff-api US3: dashboard BFF extension — parallel with Q10)
              └─► Q12 (Sapphire US3: metrics list — parallel with Q10)
Q13, Q14 (polish — parallel, after all story phases)
```

---

## Invocation Template

For each entry above, invoke:

```
/speckit.implement STORY_ID=SDDSDLC-223 REPO=<repo-name> PHASE=<exact phase label>
```

### Full invocation list (copy-paste ready)

```
/speckit.implement STORY_ID=SDDSDLC-223 REPO=sapphire-charting-api PHASE="Phase 1 — Setup"
/speckit.implement STORY_ID=SDDSDLC-223 REPO=sapphire-bff-api PHASE="Phase 1 — Setup"
/speckit.implement STORY_ID=SDDSDLC-223 REPO=Sapphire PHASE="Phase 1 — Setup"
/speckit.implement STORY_ID=SDDSDLC-223 REPO=sapphire-charting-api PHASE="Phase 2 — Foundational"
/speckit.implement STORY_ID=SDDSDLC-223 REPO=sapphire-bff-api PHASE="Phase 2 — Foundational"
/speckit.implement STORY_ID=SDDSDLC-223 REPO=sapphire-charting-api PHASE="Phase 3 — [US1] Ingest and Store Temperature Readings (P1)"
/speckit.implement STORY_ID=SDDSDLC-223 REPO=sapphire-charting-api PHASE="Phase 4 — [US2] View Temperature History and Trends (P2)"
/speckit.implement STORY_ID=SDDSDLC-223 REPO=sapphire-bff-api PHASE="Phase 4 — [US2] View Temperature History and Trends (P2)"
/speckit.implement STORY_ID=SDDSDLC-223 REPO=Sapphire PHASE="Phase 4 — [US2] View Temperature History and Trends (P2)"
/speckit.implement STORY_ID=SDDSDLC-223 REPO=sapphire-charting-api PHASE="Phase 5 — [US3] Export and Analytics Dashboard Inclusion (P3)"
/speckit.implement STORY_ID=SDDSDLC-223 REPO=sapphire-bff-api PHASE="Phase 5 — [US3] Export and Analytics Dashboard Inclusion (P3)"
/speckit.implement STORY_ID=SDDSDLC-223 REPO=Sapphire PHASE="Phase 5 — [US3] Export and Analytics Dashboard Inclusion (P3)"
/speckit.implement STORY_ID=SDDSDLC-223 REPO=sapphire-charting-api PHASE="Phase 6 — Polish & Cross-Cutting Concerns"
/speckit.implement STORY_ID=SDDSDLC-223 REPO=sapphire-bff-api PHASE="Phase 6 — Polish & Cross-Cutting Concerns"
```

---

## Total Invocations: 14

| # | Repo | Phase | Tier |
|---|------|-------|------|
| Q01 | `sapphire-charting-api` | Phase 1 — Setup | 1 |
| Q02 | `sapphire-bff-api` | Phase 1 — Setup | 1 |
| Q03 | `Sapphire` | Phase 1 — Setup | 1 |
| Q04 | `sapphire-charting-api` | Phase 2 — Foundational | 2 |
| Q05 | `sapphire-bff-api` | Phase 2 — Foundational | 2 |
| Q06 | `sapphire-charting-api` | Phase 3 — [US1] Ingest and Store (P1) | 3 |
| Q07 | `sapphire-charting-api` | Phase 4 — [US2] Trends (P2) | 4 |
| Q08 | `sapphire-bff-api` | Phase 4 — [US2] Trends (P2) | 4 |
| Q09 | `Sapphire` | Phase 4 — [US2] Trends (P2) | 4 |
| Q10 | `sapphire-charting-api` | Phase 5 — [US3] Export/Dashboard (P3) | 5 |
| Q11 | `sapphire-bff-api` | Phase 5 — [US3] Export/Dashboard (P3) | 5 |
| Q12 | `Sapphire` | Phase 5 — [US3] Export/Dashboard (P3) | 5 |
| Q13 | `sapphire-charting-api` | Phase 6 — Polish & Cross-Cutting | 6 |
| Q14 | `sapphire-bff-api` | Phase 6 — Polish & Cross-Cutting | 6 |

---

> When all implementations are done, raise PRs with:
> `/speckit.ship STORY_ID=SDDSDLC-223`
