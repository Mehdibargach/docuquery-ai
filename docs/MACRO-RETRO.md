# Macro Retro — DocuQuery AI

> From The Builder PM Method — POST-SHIP
> Fill this AFTER shipping. This is the bridge between V(n) and V(n+1).
> If you skip this, the macro-loop is broken — V2 decisions happen in your head instead of on paper.

---

**Project:** DocuQuery AI
**Version shipped:** V1
**Eval Gate decision:** CONDITIONAL GO
**Date:** 2026-03-02

---

## 1. Harvest — What came out of the Eval Gate?

> Copy the conditions and signals from the Eval Report. Don't rewrite — transplant.

### Conditions (from CONDITIONAL GO)

| # | Condition | Level | Impact |
|---|-----------|-------|--------|
| 1 | Latency 8.5s median (17% < 5s seulement). Cause = temps de generation LLM, pas le pipeline RAG (embed + cosine < 1s). Dependance externe. | SIGNAL | UX degradee sur les questions complexes (E5 a 91.8s = outlier probable retry API). Pas de levier code — c'est l'API LLM qui domine. |
| 2 | Bug rendu LaTeX ($) dans Streamlit — les montants en dollars s'affichent mal ($175,000,withannual... au lieu de $175,000, with annual...). | SIGNAL | Affichage uniquement. Corrige de facto par le passage a Lovable (React) en Scope 3 — Streamlit n'est plus le frontend. |

### Build Learnings (from Build Log)

> 2-3 learnings that affect the PRODUCT, not just the process.

- **ChromaDB → numpy (simplicite gagne).** ChromaDB a crash a cause de SQLite sur iCloud. Remplace par ~50 lignes de cosine similarity numpy. Meme API surface, zero dependance externe, zero bug. Le produit est plus stable PARCE QU'il est plus simple.
- **Paragraph markers = display layer, pas data layer.** Les marqueurs `[P1]`, `[P2]` sont injectes au moment de la generation, pas dans les chunks stockes. Ca preserve la qualite des embeddings. Decision architecturale qui affecte directement la precision des citations (G3 = 75%).
- **TOP_K est le levier #1 de la qualite factuelle.** TOP_K 5→10 a fixe une regression Scope 1. TOP_K 10→15 a fixe le BLOCKING fail G2 (E3 TPS). 1 ligne de code, 2 fois. Le retrieval domine la qualite — pas le prompt, pas le modele.
- **Input validation > processing optimization.** Le premier utilisateur externe a uploade un livre 200+ pages → OOM sur Render 512 MB. Quatre fixes (limite 10 MB, batching embeddings, pre-calcul positions, list+join). Proteger les frontieres du systeme = priorite #1.

### User/PM Signals (from wild tests, demos, feedback)

> What did real eyes see that the golden dataset missed?

- **Le golden dataset ne teste pas les limites de taille.** Le crash OOM (livre 200+ pages) a ete trouve par un utilisateur reel, pas par l'eval. Les 12 questions E1-E12 utilisent un PDF de 59 pages — confortable pour 512 MB RAM.
- **Le switch Claude Sonnet → GPT-4o-mini post-SHIP n'a pas ete re-evalue.** Les metriques (87.5% accuracy, 0 hallucination, 75% citations) sont mesurees avec Claude Sonnet. GPT-4o-mini est ~20x moins cher mais la qualite n'est pas validee formellement. Acceptable pour un produit demo, pas pour de la production.

---

## 2. Decision — What do we do next?

| Decision | When to use |
|----------|-------------|
| **ITERATE (V+1)** | At least one condition is worth fixing AND the product has more value to unlock |
| **STOP** | Product is good enough for its purpose. Conditions are minor or not worth the investment. |
| **PIVOT** | Fundamental assumption was wrong. The product works technically but solves the wrong problem. |

**Decision:** STOP

**Why (data-driven):**

Le produit remplit son objectif. Les donnees :

1. **Le produit fonctionne.** 87.5% accuracy, 0 hallucination, 100% factual accuracy (post micro-loop), 75% citations. La Riskiest Assumption ("RAG can provide precisely cited answers from 50+ page docs") est validee.

2. **Les conditions sont mineures et hors controle.**
   - Latency (SIGNAL) = dependance API LLM. Aucun fix code possible — le pipeline RAG (embed + search) prend < 1s. Le reste c'est l'API.
   - Bug LaTeX = resolve de facto par le passage Streamlit → Lovable en Scope 3.

3. **Les observations V2 sont des optimisations, pas de la nouvelle valeur.**
   - Router factual→Haiku / synthesis→Sonnet = optimisation latency.
   - Few-shot examples = optimisation priorisation.
   - TOP_K=15 a deja ete applique.
   - Aucune de ces ameliorations ne change ce que le produit FAIT — elles ameliorent comment il le fait.

4. **Zero utilisateurs en production.** C'est un side project portfolio. Son objectif = demontrer la typologie RAG/Knowledge System et la maitrise du pipeline (chunk → embed → retrieve → generate → cite). Cet objectif est atteint. Deploye, demo-ready, About page = case study PM.

5. **La vraie valeur de DocuQuery est methodologique, pas produit.** C'est le premier projet Builder PM. Il a genere : les Build Rules (4 regles nees ici), le DOR/DOD par slice, le framework Eval Gate (BLOCKING/QUALITY/SIGNAL), le micro-loop BUILD→EVALUATE, le pattern "schema coverage > LLM intelligence". Ce materiel alimente le livre et les projets suivants. Un V2 n'ajouterait pas de nouveau materiel methodologique.

6. **Cout d'opportunite.** 4 side projects restants dans le plan (BriefBuilder, FeedbackSort, EvalKit + un 5eme). Chaque heure sur DocuQuery V2 = une heure en moins sur un nouveau projet qui couvre une nouvelle typologie AI et genere de nouveaux apprentissages.

---

## 3. Bridge — Input for the next FRAME

N/A — decision is STOP.

Pas de V2. Les observations (router LLM, few-shot, re-eval GPT-4o-mini) sont documentees dans l'Eval Report pour reference future si le contexte change.

---

## Completion

- [x] Eval Report reviewed
- [x] Decision documented with justification
- [ ] ~~Bridge section filled~~ (N/A — STOP)
- [ ] Project Dossier updated with Macro Retro decision
- [ ] CLAUDE.md updated
