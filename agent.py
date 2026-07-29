"""AI shopping assistant: turns a plain-English request into calls against the
shop_api tools (search_catalogue, get_product, check_balance, propose_order,
confirm_and_place_order).

The shop API itself can only filter by an exact category name - nothing
fuzzy, no price or colour filtering. So for anything like "cheap" or a
colour, the agent is instructed to fetch the plain results itself and apply
that judgement in its own reasoning, rather than expecting the API to
understand it.

Buying is two steps, spanning two separate messages: `propose_order` looks
up the price and describes what would be bought, without charging anything;
`confirm_and_place_order` is what actually charges the balance, and only
works on a proposal the *previous* message already made - see `ask()`.
"""
import json
import os
import uuid

from openai import AzureOpenAI, OpenAIError

import shop_api

MAX_TOOL_ITERATIONS = 6

SYSTEM_PROMPT = """\
You are a shopping assistant for a furniture app. You can only act through \
these tools: search_catalogue, get_product, check_balance, propose_order, \
confirm_and_place_order.

search_catalogue only filters by an EXACT category name - it has no price, \
colour, or "vibe" filtering built in. When the user asks for something like \
"cheap", a colour, or a style, call search_catalogue yourself (pass a \
category only if one is obviously implied) and then judge price, colours, \
and names in the results yourself: sort, filter, and pick what best matches \
their request. Never claim the tool itself filtered by something it didn't.

Buying is TWO steps, in two separate messages:
1. When the user asks to buy/order/purchase something, call propose_order. \
It looks up the real price and total but does NOT charge anything. Tell the \
user exactly what you'd be buying and for how much, and ask them to confirm.
2. Only call confirm_and_place_order when the user's message clearly \
confirms that exact proposal (e.g. "yes", "confirm", "go ahead") - this is \
what actually charges the balance, right now, with no undo. If they want \
something different (a different item, a different quantity, or an \
unrelated request), call propose_order again instead of confirming.
Never call propose_order and confirm_and_place_order for the same purchase \
in the same reply - always wait for the user's next message before \
confirming, even if you are certain they want it.

If a pending proposal from an earlier message is given to you below, only \
confirm it if the user's current message clearly agrees to that exact item \
and quantity.

Keep replies short and plain - this is for a non-technical user.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_catalogue",
            "description": (
                "Lists furniture items, optionally filtered by an EXACT category name. "
                "No price, colour, or fuzzy/vibe filtering on the server - for anything "
                "like that, call this and judge the returned price/colours yourself."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Exact category name, e.g. 'Bar furniture'. Omit for all categories.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product",
            "description": (
                "Fetches one exact product by its known item_id. Not for searching - "
                "only for looking up an item you already have the ID for."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "string", "description": "The product's item_id."}
                },
                "required": ["item_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_balance",
            "description": (
                "Returns the current real balance for the shop account. There is only "
                "one account for this whole exercise."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_order",
            "description": (
                "Step 1 of buying: looks up an item and quantity and returns its price "
                "and total - does NOT charge anything. Always call this before buying, "
                "then tell the user the total and ask them to confirm in their next message."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "string", "description": "The product's item_id to buy."},
                    "quantity": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "How many to buy. Defaults to 1.",
                    },
                },
                "required": ["item_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_and_place_order",
            "description": (
                "Step 2 of buying: actually places the real order for the proposal from "
                "the user's PREVIOUS message, charging the balance right now. Takes no "
                "arguments - it always acts on the most recent confirmed proposal. Only "
                "call this when the user's current message clearly confirms that exact "
                "proposal. Calling this in the same reply as propose_order is not allowed."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


class AgentError(Exception):
    """Raised when the assistant itself can't run - bad config, Azure outage,
    etc. Callers should catch this and show a friendly message, the same way
    shop_api.ShopApiError is handled."""


def _client():
    endpoint = os.environ.get("AZURE_ENDPOINT")
    api_key = os.environ.get("AZURE_API_KEY")
    api_version = os.environ.get("API_VERSION")
    if not (endpoint and api_key and api_version):
        raise AgentError(
            "The assistant isn't configured - AZURE_ENDPOINT, AZURE_API_KEY, and "
            "API_VERSION must be set in .env."
        )
    return AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=api_version)


def _describe_proposal(proposal):
    return (
        f"{proposal['quantity']}x {proposal['product_name']} (item_id {proposal['item_id']}) "
        f"for a total of ${proposal['total']:.2f}"
    )


def _run_tool(name, args, shop_user_id, state):
    """Executes one tool call. Returns (result_for_model, trace_line).

    `state` is a dict the caller keeps across every tool call in this one
    `ask()` request: state["confirmable"] is the proposal (if any) that
    already existed when this request started - the only thing
    confirm_and_place_order is allowed to act on. state["to_persist"] is
    what gets returned to the caller to store for the *next* request.
    propose_order updates state["to_persist"] but deliberately never touches
    state["confirmable"], so a propose+confirm pair can't both succeed
    within the same request - confirming always requires a proposal the user
    actually saw in a previous message.
    """
    try:
        if name == "search_catalogue":
            category = args.get("category")
            products = shop_api.get_catalogue(category=category)
            return products, f"Searched catalogue (category={category or 'any'}) -> {len(products)} results"

        if name == "get_product":
            product = shop_api.get_product(args["item_id"])
            return product, f"Looked up product {args['item_id']}"

        if name == "check_balance":
            user = shop_api.get_balance(shop_user_id)
            return user, f"Checked balance -> ${user['balance']:.2f}"

        if name == "propose_order":
            item_id = args["item_id"]
            quantity = int(args.get("quantity", 1))
            product = shop_api.get_product(item_id)
            proposal = {
                "item_id": item_id,
                "quantity": quantity,
                "product_name": product.get("product_name", item_id),
                "total": product["price"] * quantity,
                # Fixed per proposal, not per attempt: if a confirm attempt times out
                # without us learning whether it went through, retrying with this same
                # key returns the original result instead of charging twice.
                "idempotency_key": str(uuid.uuid4()),
            }
            state["to_persist"] = proposal
            return proposal, f"Proposed {_describe_proposal(proposal)} - awaiting confirmation"

        if name == "confirm_and_place_order":
            confirmable = state["confirmable"]
            if not confirmable:
                return (
                    {"error": "Nothing has been confirmed yet - propose the order, show the "
                              "user the price, and wait for their next message before confirming."},
                    "confirm_and_place_order blocked - no confirmed proposal from a prior message",
                )
            result = shop_api.place_order(
                shop_user_id,
                confirmable["item_id"],
                confirmable["quantity"],
                confirmable.get("idempotency_key") or str(uuid.uuid4()),
            )
            state["confirmable"] = None
            state["to_persist"] = None
            return result, (
                f"Confirmed order {result['order_id']} for {confirmable['item_id']} "
                f"x{confirmable['quantity']} -> ${result['total_price']:.2f}, "
                f"remaining balance ${result['remaining_balance']:.2f}"
            )

        return {"error": f"Unknown tool '{name}'."}, f"Unknown tool '{name}' requested"

    except shop_api.ShopApiError as error:
        if name == "confirm_and_place_order":
            # A failure here (especially a timeout) doesn't mean nothing happened -
            # the request may have reached the shop before the connection dropped.
            # The proposal (and its idempotency_key) is deliberately left in place
            # so a retry is safe: same key -> the shop returns the original result
            # instead of charging again.
            return (
                {"error": f"{error} It's not certain whether this order went through - "
                          "the same proposal is still pending, so it's safe to try confirming again."},
                f"confirm_and_place_order failed: {error}",
            )
        return {"error": str(error)}, f"{name} failed: {error}"


def ask(user_message, shop_user_id, pending_purchase=None):
    """Runs the agent loop for one plain-English request.

    pending_purchase is whatever propose_order returned last time (or None) -
    pass back exactly what this function returned as `pending` last call.

    Returns (reply, trace, pending): reply is the assistant's final text,
    trace is a list of short human-readable lines for each tool call
    actually made, and pending is the proposal (or None) to store and pass
    back in on the *next* call.
    """
    client = _client()
    deployment = os.environ.get("DEPLOYMENT")
    if not deployment:
        raise AgentError("The assistant isn't configured - DEPLOYMENT must be set in .env.")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if pending_purchase:
        messages.append({
            "role": "system",
            "content": (
                f"Pending proposal from your previous message: {_describe_proposal(pending_purchase)}. "
                "Only call confirm_and_place_order if the user's message below clearly agrees to "
                "exactly this - otherwise call propose_order again for whatever they actually want."
            ),
        })
    messages.append({"role": "user", "content": user_message})

    # state["confirmable"] is fixed for this whole request - it's what the user
    # actually saw and can legitimately confirm right now. state["to_persist"]
    # starts the same, but propose_order can update it for the next request.
    state = {"confirmable": pending_purchase, "to_persist": pending_purchase}
    trace = []

    try:
        for _ in range(MAX_TOOL_ITERATIONS):
            response = client.chat.completions.create(model=deployment, messages=messages, tools=TOOLS)
            message = response.choices[0].message
            messages.append(message.model_dump())

            if not message.tool_calls:
                return message.content or "Sorry, I don't have a response for that.", trace, state["to_persist"]

            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments or "{}")
                result, trace_line = _run_tool(tool_call.function.name, args, shop_user_id, state)
                trace.append(trace_line)
                messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)}
                )
    except OpenAIError as error:
        raise AgentError(f"The assistant is unavailable right now ({error}).") from error

    return "Sorry, that request took too many steps - try asking something simpler.", trace, state["to_persist"]
