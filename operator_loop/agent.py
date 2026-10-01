"""The onboarding agent: a one-step LangGraph graph that asks Claude to apply the playbook.

Input: the playbook text and one handoff case.
Output: {"decision": ..., "reason": ..., "escalate": true/false}

When LANGSMITH_TRACING=true (set in .env), every call is traced in LangSmith
automatically. No extra code is needed for that.
"""

import json
from typing import TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from operator_loop.config import MODEL

# What the agent writes back when it hands a case to a human operator.
NEEDS_OPERATOR = "needs_operator"

# Instructions for Claude. {playbook} is filled in with the live playbook.
SYSTEM_TEMPLATE = """You are a customer onboarding agent. After Sales hands a new customer to Customer Success, you decide the next step for the kickoff, following the playbook below.

How to work:
- Use only the decisions listed in the playbook.
- Follow the playbook as written. Do not apply company policies, legal requirements, or best practices that the playbook does not state.
- If the handoff contains something the playbook does not address, and it could change the right next step, do not guess. Set escalate to true, set decision to "needs_operator", and use reason to say what the playbook is missing.
- Choosing escalate_to_csm_lead is a normal playbook decision, so escalate stays false when you choose it.
- Keep reason to one or two plain sentences.

<playbook>
{playbook}
</playbook>"""


class AgentOutput(BaseModel):
    """The JSON shape Claude must return."""

    decision: str = Field(description="One decision code from the playbook, or 'needs_operator' when escalating.")
    reason: str = Field(description="One or two sentences explaining the decision.")
    escalate: bool = Field(description="True only when the playbook does not clearly cover this case.")


def build_prompt(playbook_text: str) -> ChatPromptTemplate:
    """Turn the playbook into a prompt template. This is also what we push to Prompt Hub."""
    # Curly braces have special meaning in templates, so escape any in the playbook.
    safe_playbook = playbook_text.replace("{", "{{").replace("}", "}}")
    system = SYSTEM_TEMPLATE.replace("{playbook}", safe_playbook)
    return ChatPromptTemplate.from_messages(
        [("system", system), ("human", "Handoff record:\n{case_json}")]
    )


# The Claude model, set up to return JSON matching AgentOutput.
# method="json_schema" uses Claude's structured outputs feature, which
# guarantees the reply matches the schema.
_llm = ChatAnthropic(model=MODEL, max_tokens=16000, effort="medium")
_structured_llm = _llm.with_structured_output(AgentOutput, method="json_schema")


class AgentState(TypedDict, total=False):
    """What flows through the graph."""

    playbook: str
    case: dict
    result: dict


def decide(state: AgentState) -> AgentState:
    """The single step of the graph: read playbook + case, ask Claude, return its answer."""
    prompt = build_prompt(state["playbook"])
    messages = prompt.invoke({"case_json": json.dumps(state["case"], indent=2)})
    output: AgentOutput = _structured_llm.invoke(messages)
    result = output.model_dump()
    # Keep the output consistent: an escalation never carries a real decision.
    if result["escalate"]:
        result["decision"] = NEEDS_OPERATOR
    return {"result": result}


def build_graph():
    """Wire up the graph: START -> decide -> END."""
    graph = StateGraph(AgentState)
    graph.add_node("decide", decide)
    graph.add_edge(START, "decide")
    graph.add_edge("decide", END)
    return graph.compile()


agent = build_graph()


def run_agent(playbook_text: str, case: dict) -> dict:
    """Convenience wrapper: run the agent on one case and return its JSON answer."""
    return agent.invoke({"playbook": playbook_text, "case": case})["result"]
