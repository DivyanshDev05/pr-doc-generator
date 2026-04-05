## 📌 PR Summary
<!-- One liner: What does this PR do? (feature / bug fix / refactor / hotfix) -->

---

## 🔍 Scope of This PR
<!-- What is in scope and explicitly what is OUT of scope -->
- **In Scope:**
- **Out of Scope:**

---

## 🧩 What Problem Does This Solve?
<!-- Link to Jira/ticket. Describe the bug or feature in plain language -->
- **Ticket:** [PROJ-XXX](link)
- **Context:**

---

## 🗄️ Database Changes
<!-- CRITICAL for QA/OPS during deployment without dev availability -->
- :cross_mark: No DB changes
- :cross_mark: Migration script included (path: `db/migrations/xxx`)
- :cross_mark: Schema changes (tables/columns added/modified/dropped):
- :cross_mark: Index changes:
- :cross_mark: Seed data / reference data changes:

- **Rollback SQL (if applicable):**
```sql
  -- paste rollback query here
```

---

## 🚀 Post-Deployment Steps
<!-- Step-by-step actions needed AFTER deployment — for QA or OPS to follow independently -->
1. Run migration: `...`
2. Clear cache: `...`
3. Update config/env variable: `...`
4. Restart service (if needed): `...`
5. Notify downstream team (if applicable): `...`

---

## 🧪 How to Test
<!-- QA should be able to follow this without dev help -->
