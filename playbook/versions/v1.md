# Customer Onboarding Kickoff Playbook

Version: v1

## Purpose

When Sales hands a new customer to Customer Success, decide the right next step for the kickoff meeting.

## Decisions you can make

Only use the decisions listed here.

- `schedule_kickoff`: book a kickoff call with the customer within 5 business days of the handoff.
- `escalate_to_csm_lead`: send the account to the CSM team lead because the deal is not ready for onboarding.

## Rules

1. If the contract is countersigned and the customer has a named champion, choose `schedule_kickoff`.
2. If the contract is not yet countersigned, choose `escalate_to_csm_lead`.
3. If the customer has no named champion, choose `escalate_to_csm_lead`.

## When you are not sure

If the handoff contains something these rules do not address, and it could change the right next step, do not guess. Escalate to a human operator and explain what is missing from the playbook.
