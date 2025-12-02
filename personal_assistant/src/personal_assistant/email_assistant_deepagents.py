"""Email assistant using deepagents library with custom HITL middleware.

This is the migration of email_assistant_hitl_memory.py to use the deepagents library's
create_deep_agent() pattern instead of manual graph construction. All functionality is
preserved including HITL logic, memory system, and custom tools.

Usage:
    python -m examples.personal_assistant.email_assistant_deepagents
"""

from typing import Literal

from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.store.base import BaseStore
from langgraph.types import interrupt, Command

from deepagents import create_deep_agent
from deepagents.backends import StoreBackend

from .middleware import EmailAssistantHITLMiddleware
from .schemas import State, StateInput, EmailAssistantState, UserPreferences, RouterSchema
from .tools import get_tools
from .utils import format_email_markdown, parse_email, get_memory, update_memory
from .prompts import triage_user_prompt, default_triage_instructions, triage_system_prompt, default_background

def triage_router(state: State, store: BaseStore) -> Command[Literal["triage_interrupt_handler", "response_agent", "__end__"]]:
    """Analyze email content to decide if we should respond, notify, or ignore.

    The triage step prevents the assistant from wasting time on:
    - Marketing emails and spam
    - Company-wide announcements
    - Messages meant for other teams
    """
    
    # Parse the email input
    author, to, subject, email_thread = parse_email(state["email_input"])
    user_prompt = triage_user_prompt.format(
        author=author, to=to, subject=subject, email_thread=email_thread
    )

    # Create email markdown for Agent Inbox in case of notification  
    email_markdown = format_email_markdown(subject, author, to, email_thread)

    # Search for existing triage_preferences memory
    triage_instructions = get_memory(store, ("email_assistant", "triage_preferences"), default_triage_instructions)

    # Format system prompt with background and triage instructions
    system_prompt = triage_system_prompt.format(
        background=default_background,
        triage_instructions=triage_instructions,
    )

    llm = ChatAnthropic(model="claude-sonnet-4-5-20250929", temperature=0)
    llm_router = llm.with_structured_output(RouterSchema) 

    # Run the router LLM
    result = llm_router.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    # Decision
    classification = result.classification

    # Process the classification decision
    if classification == "respond":
        print("📧 Classification: RESPOND - This email requires a response")
        # Next node
        goto = "response_agent"
        # Update the state
        update = {
            "classification_decision": result.classification,
            "messages": [{"role": "user",
                            "content": f"Respond to the email: {email_markdown}"
                        }],
        }
        
    elif classification == "ignore":
        print("🚫 Classification: IGNORE - This email can be safely ignored")

        # Next node
        goto = END
        # Update the state
        update = {
            "classification_decision": classification,
        }

    elif classification == "notify":
        print("🔔 Classification: NOTIFY - This email contains important information") 

        # Next node
        goto = "triage_interrupt_handler"
        # Update the state
        update = {
            "classification_decision": classification,
        }

    else:
        raise ValueError(f"Invalid classification: {classification}")
    
    return Command(goto=goto, update=update)

def triage_interrupt_handler(state: State, store: BaseStore) -> Command[Literal["response_agent", "__end__"]]:
    """Handles interrupts from the triage step"""
    
    # Parse the email input
    author, to, subject, email_thread = parse_email(state["email_input"])

    # Create email markdown for Agent Inbox in case of notification  
    email_markdown = format_email_markdown(subject, author, to, email_thread)

    # Create messages
    messages = [{"role": "user",
                "content": f"Email to notify user about: {email_markdown}"
                }]

    # Create interrupt for Agent Inbox
    request = {
        "action_request": {
            "action": f"Email Assistant: {state['classification_decision']}",
            "args": {}
        },
        "config": {
            "allow_ignore": True,  
            "allow_respond": True,
            "allow_edit": False, 
            "allow_accept": False,  
        },
        # Email to show in Agent Inbox
        "description": email_markdown,
    }

    # Send to Agent Inbox and wait for response
    response = interrupt([request])[0]

    # If user provides feedback, go to response agent and use feedback to respond to email   
    if response["type"] == "response":
        # Add feedback to messages 
        user_input = response["args"]
        messages.append({"role": "user",
                        "content": f"User wants to reply to the email. Use this feedback to respond: {user_input}"
                        })
        # Update memory with feedback
        update_memory(store, ("email_assistant", "triage_preferences"), [{
            "role": "user",
            "content": f"The user decided to respond to the email, so update the triage preferences to capture this."
        }] + messages)

        goto = "response_agent"

    # If user ignores email, go to END
    elif response["type"] == "ignore":
        # Make note of the user's decision to ignore the email
        messages.append({"role": "user",
                        "content": f"The user decided to ignore the email even though it was classified as notify. Update triage preferences to capture this."
                        })
        # Update memory with feedback 
        update_memory(store, ("email_assistant", "triage_preferences"), messages)
        goto = END

    # Catch all other responses
    else:
        raise ValueError(f"Invalid response: {response}")

    # Update the state 
    update = {
        "messages": messages,
    }

    return Command(goto=goto, update=update)

def create_email_assistant(for_deployment=False):
    """Create and configure the email assistant agent.

    Args:
        for_deployment: If True, don't pass store/checkpointer (for LangGraph deployment).
                       If False, create InMemoryStore and MemorySaver for local testing.

    Returns:
        CompiledStateGraph: Configured email assistant agent
    """
    # Initialize model
    model = ChatAnthropic(model="claude-sonnet-4-5-20250929", temperature=0)

    # Get tools
    tools = get_tools(
        [
            "write_email",
            "schedule_meeting",
            "check_calendar_availability",
            "Question",
            "Done",
        ]
    )

    # Initialize persistence based on deployment mode
    if for_deployment:
        # In deployment, LangGraph platform provides store and checkpointer
        # We need to pass a store to middleware, but it will be overridden by platform
        # Use a placeholder that the middleware can work with during initialization
        store = InMemoryStore()  # Placeholder - will be overridden by platform
        store_kwarg = {}  # Don't pass store to create_deep_agent
        checkpointer_kwarg = {}  # Don't pass checkpointer to create_deep_agent
    else:
        # Local testing mode - create and use our own store and checkpointer
        store = InMemoryStore()
        checkpointer = MemorySaver()
        store_kwarg = {"store": store}
        checkpointer_kwarg = {"checkpointer": checkpointer}

    # Create custom HITL middleware
    hitl_middleware = EmailAssistantHITLMiddleware(
        store=store,
        interrupt_on={
            "write_email": True,
            "schedule_meeting": True,
            "Question": True,
        },
    )

    # Create agent with deepagents library
    agent = create_deep_agent(
        model=model,
        tools=tools,
        middleware=[hitl_middleware], # Custom middleware added to default stack
        backend=lambda rt: StoreBackend(rt), # Persistent storage for memory
        context_schema=EmailAssistantState,
        **store_kwarg,
        **checkpointer_kwarg,
    )


    # Build overall workflow
    overall_workflow = (
        StateGraph(State, input=StateInput)
        .add_node(triage_router)
        .add_node(triage_interrupt_handler)
        .add_node("response_agent", agent)
        .add_edge(START, "triage_router")
    )

    # Compile with store/checkpointer based on deployment mode
    if for_deployment:
        # In deployment, platform provides store/checkpointer
        email_assistant = overall_workflow.compile()
    else:
        # In local testing, use our store/checkpointer
        email_assistant = overall_workflow.compile(store=store, checkpointer=checkpointer)

    return email_assistant


def main():
    """Example usage of the email assistant."""
    # Create agent
    agent = create_email_assistant()

    # Example email input
    email_input = {
        "author": "jane@example.com",
        "to": "lance@langchain.dev",
        "subject": "Quick question about next week",
        "email_thread": "Hi Lance,\n\nCan we meet next Tuesday at 2pm to discuss the project roadmap?\n\nBest,\nJane",
    }

    # Format email for message
    author, to, subject, email_thread = parse_email(email_input)
    email_markdown = format_email_markdown(subject, author, to, email_thread)

    # Configure thread
    config = {"configurable": {"thread_id": "test-thread-1"}}

    # Invoke agent
    print("=" * 80)
    print("EMAIL ASSISTANT EXAMPLE")
    print("=" * 80)
    print("\nProcessing email:")
    print(email_markdown)
    print("=" * 80)

    # Pass email_input to top-level state (triage_router expects this)
    result = agent.invoke(
        {"email_input": email_input},
        config=config,
    )

    print("\nAgent result:")
    print(result)
    print("=" * 80)


if __name__ == "__main__":
    main()
