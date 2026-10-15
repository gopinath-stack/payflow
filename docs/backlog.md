# PayFlow Platform Backlog

Environments: **dev** = laptop Kubernetes (Docker Desktop) · **prod** = AWS EKS (ap-south-1, Mumbai)
Every ticket: own branch → PR → review checklist → merge to `main`.

## EPIC 1: Containerise (dev)
| Ticket | Task | Acceptance criteria |
|---|---|---|
| PF-1 | Smoke test handover | `/health` returns ok for accounts and payments |
| PF-2 | Dockerfile per service | Image < 200 MB, runs as non-root, `/health` ok via `docker run` |
| PF-3 | `compose.yaml` with Postgres + Redis | `docker compose up` → payment works end-to-end, data survives restart |

## EPIC 2: Kubernetes (dev)
| PF-4 | Namespace, Deployments, Services, ConfigMap, Secret, PVC | All pods `Running`, payment works via port-forward |
| PF-5 | Ingress, probes, requests/limits, HPA | `payflow.local` opens UI; killing a pod causes no outage |
| PF-6 | Helm chart, `values-dev.yaml` / `values-prod.yaml` | `helm install` deploys whole stack in one command |

## EPIC 3: Delivery
| PF-7 | GitHub Actions CI: test → build → Trivy scan → push | Failing test or HIGH CVE blocks the merge |
| PF-8 | Argo CD GitOps | Merge to `main` auto-syncs dev; prod needs manual sync |

## EPIC 4: Operate
| PF-9 | Prometheus, Grafana, Loki, alerts | Dashboard shows request rate/errors; alert fires when accounts is down |
| PF-10 | RBAC, Pod Security, NetworkPolicies | Only payments can call accounts; pods non-root |
| PF-12 | Incident drills | 3 drills, each with an RCA in `docs/rca/` |

## EPIC 5: AWS prod
| PF-13 | AWS account hardening: IAM user, MFA, budget alarm | Budget email alert at ₹500 |
| PF-14 | Terraform: remote state (S3 + DynamoDB), VPC, EKS | `terraform apply` builds cluster; `terraform destroy` removes all |
| PF-15 | ECR repos; CI pushes images to ECR | Images tagged with git SHA |
| PF-16 | RDS Postgres + ElastiCache Redis via Terraform; secrets in AWS Secrets Manager | Apps connect without plain-text passwords |
| PF-17 | AWS Load Balancer Controller + Ingress, CloudWatch logs | Public URL works; logs visible in CloudWatch |
| PF-18 | Prod release via Argo CD to EKS; teardown runbook | Release + rollback documented in `docs/runbooks/` |
| PF-11 | Ansible: bootstrap a jump host | Playbook is idempotent (2nd run = no changes) |
