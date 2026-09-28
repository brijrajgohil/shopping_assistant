from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import AgentTool
from google.genai import types

from app.callbacks.audit import record_pending_refund
from app.callbacks.security import check_order_access
from app.tools.knowledge_tools import search_knowledge
from app.tools.order_tools import get_order_status, request_refund


MODEL = "gemini-2.5-flash-lite"


def create_model() -> Gemini:
    """Create the model configuration used by each agent."""
    return Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=1),
    )


# ------------------------------------------------------------------
# Order specialist
# ------------------------------------------------------------------

order_agent = Agent(
    name="order_agent",
    model=create_model(),
    description=(
        "Handles order status, shipment, tracking, delivery, "
        "and estimated-delivery questions."
    ),
    instruction="""
    You are the ShopAssist order specialist.

    Use get_order_status for questions about:
    - order status
    - shipping carrier
    - tracking number
    - estimated delivery
    - recorded delivery

    Requirements:
    - An order ID is required.
    - Never invent order information.
    - Only report information returned by get_order_status.
    - If the tool returns status "blocked" or "error", clearly explain
      the returned error message.
    - Keep your response concise.
    """,
    tools=[get_order_status],
    before_tool_callback=check_order_access,
)


# ------------------------------------------------------------------
# Refund specialist
# ------------------------------------------------------------------

refund_agent = Agent(
    name="refund_agent",
    model=create_model(),
    description=(
        "Handles explicit customer requests to request a refund "
        "for an order."
    ),
    instruction="""
    You are the ShopAssist refund specialist.

    Use request_refund only when the customer explicitly asks to
    request a refund.

    A refund request requires:
    - an order ID
    - a reason for the refund

    If either is missing, ask the customer for it.

    Requirements:
    - Never invent an order ID, reason, price, or refund status.
    - Explain approval_required and approval_status returned by the tool.
    - A recorded or approved request does not mean money was refunded.
    - Never tell the customer that the refund has been issued.
    - If the tool returns status "blocked" or "error", clearly explain
      the returned error message.
    """,
    tools=[request_refund],
    before_tool_callback=check_order_access,
    after_tool_callback=record_pending_refund,
)


# ------------------------------------------------------------------
# Policy/RAG specialist
# ------------------------------------------------------------------

policy_agent = Agent(
    name="policy_agent",
    model=create_model(),
    description=(
        "Answers general ShopAssist return, refund, and shipping-policy "
        "questions using the policy knowledge base."
    ),
    instruction="""
    You are the ShopAssist policy specialist.

    Use search_knowledge for general questions about:
    - return policies
    - refund policies
    - shipping policies

    Requirements:
    - Base your answer only on information returned by search_knowledge.
    - Do not use policy documents for order-specific information.
    - Do not invent policy rules.
    - If policy information is unavailable, clearly say so.
    - Keep your response concise.
    """,
    tools=[search_knowledge],
)


# ------------------------------------------------------------------
# Root coordinator
# ------------------------------------------------------------------

root_agent = Agent(
    name="shopassist_agent",
    model=create_model(),
    description=(
        "Coordinates ShopAssist order, refund, and policy specialists."
    ),
    instruction="""
    You are the coordinator for ShopAssist customer support.

    Delegate work to the appropriate specialist:

    - Use order_agent for order status, shipment, tracking,
      delivery, and estimated-delivery questions.
    - Use refund_agent when the customer explicitly requests a refund.
    - Use policy_agent for general return, refund, or shipping-policy
      questions.

    A request can contain more than one task.

    When that happens:
    1. Call every specialist needed to answer the request.
    2. Call specialists one at a time.
    3. Wait for their results.
    4. Combine the results into one concise response.

    Do not answer order or policy questions from your own knowledge.
    Do not invent information.

    Do not treat a general policy question as a refund request.
    Only call refund_agent when the customer explicitly asks to
    request a refund.
    """,
    tools=[
        AgentTool(agent=order_agent),
        AgentTool(agent=refund_agent),
        AgentTool(agent=policy_agent),
    ],
)


app = App(
    name="app",
    root_agent=root_agent,
)