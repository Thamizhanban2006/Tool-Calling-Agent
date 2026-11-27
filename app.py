"""Streamlit interface for the book reading planner."""

import json

import streamlit as st

import agent_core

st.set_page_config(page_title="Book Reading Planner", page_icon="📚")
st.title("📚 Book Reading Planner")
st.caption("Browse a small book catalog, estimate reading time, and draft a simple plan.")

api_key = st.sidebar.text_input(
    "Your Gemini API key",
    type="password",
    help="Get a free key at aistudio.google.com.",
)
st.sidebar.caption("The key is used for Gemini requests and is not written to project files.")

if "chat" not in st.session_state:
    st.session_state["chat"] = []
if "history" not in st.session_state:
    st.session_state["history"] = []

if st.sidebar.button("Clear chat"):
    st.session_state["chat"] = []
    st.session_state["history"] = []

if not api_key:
    st.info("Paste your Gemini API key in the sidebar to start.")
    st.stop()

graph = agent_core.build_graph(agent_core.make_llm(api_key))

for role, text, steps, stopped in st.session_state["chat"]:
    with st.chat_message(role):
        st.write(text)
        if role == "assistant":
            if steps:
                with st.expander(f"Agent steps ({len(steps)} tool call{'s' if len(steps) != 1 else ''})"):
                    for number, step in enumerate(steps, 1):
                        st.markdown(f"**{number}. `{step['tool']}`**")
                        st.code(json.dumps(step["args"], ensure_ascii=False), language="json")
                        st.text(f"Result: {step['result'][:300]}")
            else:
                st.caption("No tool calls.")
            if stopped:
                st.warning("The step limit stopped this run.")

question = st.chat_input("Ask about books or a reading plan")
if question:
    st.session_state["chat"].append(("user", question, [], False))
    answer, steps, stopped, history = agent_core.run_agent(
        graph,
        st.session_state["history"],
        question,
    )
    st.session_state["history"] = history
    st.session_state["chat"].append(("assistant", answer, steps, stopped))
    st.rerun()
