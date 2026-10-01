# operator-loop

**Operators need a way to teach AI agents how their business actually runs.**

Today that work falls to forward deployed engineers. LangSmith and LangGraph already have the building blocks: tracing, datasets, annotation queues, Prompt Hub, and experiments. This project is a lightweight layer that connects them into one loop an operator can run:

```
escalation -> operator judgment -> proposed rule with evidence -> operator approval -> versioned playbook -> re-test -> measure executable coverage
```

The idea of "ContextOps" comes from Eugen Alpeza's article ["The FDE boom is a product gap"](https://www.linkedin.com/pulse/fde-boom-product-gap-eugen-alpeza-bbfhc/) (Edra). This repo is an independent, scrappy take on that idea, built on LangSmith. It is not affiliated with Edra.

> **Status:** a working reference implementation, not a finished product. It is meant to show the shape of the loop end to end on a small, synthetic example.

## The use case

A **customer onboarding agent**. Given a sales-to-Customer-Success handoff record, it decides the right next step for kickoff by following a written playbook. The possible decisions are:

| Decision | Meaning |
|---|---|
| `schedule_kickoff` | Book the kickoff call |
| `skip_kickoff_customer_pmo` | The customer's own PMO runs the kickoff, so we skip ours |
| `hold_for_dpa` | Wait for a signed Data Processing Agreement first |
| `hold_for_baa` | Wait for a signed Business Associate Agreement first |
| `escalate_to_csm_lead` | The deal is not ready, so send it to the CSM team lead |

The agent must escalate to a human when the playbook does not clearly cover a situation, instead of guessing.

## Executable coverage

A case is **covered** when the agent did not escalate and its decision matches the expected decision.

```
executable coverage = covered cases / total cases
```

This measures how much of the real work the agent can do on its own, correctly, using only what the playbook says.

## The data (synthetic)

[`data/handoffs.json`](data/handoffs.json) holds 20 **synthetic** handoff cases. Every company and person is invented. Three patterns are planted that the starting playbook ([`playbook/playbook.md`](playbook/playbook.md), v1) does **not** cover:

1. EU customers need a signed DPA before kickoff.
2. Healthcare customers need a signed BAA before kickoff.
3. Enterprise customers with their own PMO skip our kickoff.

The dataset also contains look-alike cases (an EU customer whose DPA is already signed, an Enterprise customer with no PMO) to check that new rules are precise and not overly broad.

| Expected decision | Cases |
|---|---|
| `schedule_kickoff` | 11 |
| `hold_for_dpa` | 3 |
| `hold_for_baa` | 2 |
| `skip_kickoff_customer_pmo` | 2 |
| `escalate_to_csm_lead` | 2 |

## How an operator judges a case

During review, each escalated or wrong case gets one label:

| Label | Meaning | What happens |
|---|---|---|
| **legit exception** | A real pattern the agent should be able to handle (for example, EU customers needing a DPA). The note says what the rule should be. | Becomes a proposed rule |
| **agent mistake** | The playbook already covered it, but the agent got it wrong. | Logged. If the note suggests clarifying the playbook, that becomes a proposal too |
| **one-off** | Genuinely needs a human every time. | No rule |
| **skip** | Not reviewing this one now. | Nothing |

## Results

Baseline coverage with playbook v1: _coming in Phase 2._

## Commands

One command with subcommands (coming in Phases 2 and 3):

| Command | What it does |
|---|---|
| `operator-loop run` | Run the agent on every case as a LangSmith experiment and report coverage |
| `operator-loop review` | Send escalations and wrong answers to a LangSmith annotation queue, then judge them in the terminal |
| `operator-loop propose` | Group your notes and draft proposed rules with evidence |
| `operator-loop approve` | Approve or reject a proposal; on approval, version the playbook, push it to Prompt Hub, and re-test |
| `operator-loop rollback` | Restore an earlier playbook version |
| `operator-loop report` | Show the current version, coverage history, and open proposals |

## Setup

You need Python 3.12+, [uv](https://docs.astral.sh/uv/), an [Anthropic API key](https://console.anthropic.com), and a [LangSmith API key](https://smith.langchain.com).

```bash
git clone https://github.com/yashb0780/operator-loop.git
cd operator-loop
cp .env.example .env    # then open .env and paste in your keys
uv sync                 # installs the dependencies
```

## What's next

- **A web review screen for operators.** The terminal review works, but operators should be able to judge cases and approve rules in a simple browser UI.
- **Connect it to a real agent's traces.** Point the loop at production traces in LangSmith instead of a synthetic dataset.

## License

MIT
