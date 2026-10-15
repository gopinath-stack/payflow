# Working rules (enterprise workflow)
1. One ticket = one branch: `git checkout -b PF-<n>-<short-name>`
2. Commit message: `PF-<n>: <what changed>`
3. Open a PR to `main`, fill the PR template, self-review against it, then merge.
4. Never commit secrets. Passwords go in Kubernetes Secrets / AWS Secrets Manager.
5. Every incident gets an RCA in `docs/rca/` within 24 hours.
6. AWS: create with Terraform only, destroy after each session.
