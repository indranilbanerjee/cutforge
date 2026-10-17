# Eval suite

Run with a Claude Code version that ships `claude plugin eval`. Every eval run is a real model call and counts against
your plan or API bill.

```bash
# skill-routing check (cheap graders, one arm):
claude plugin eval . --tag trigger --ablation none --runs 1 --threshold 0.8
```

`triggers/` holds one case per skill, phrased the way a user would ask without naming the skill, plus two unrelated
requests that must NOT invoke the plugin. A failing trigger case means that skill's `description` no longer routes
natural requests to it: fix the description (60-150 characters, the decisive words first), not the case. Results land in
`evals/results/` (gitignored).

Every case sets `max_turns: 1`: the graders only check that the first action is the right skill.
