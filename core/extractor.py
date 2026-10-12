
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda


# ==========================================
# 1. LOAD ENVIRONMENT VARIABLES
# ==========================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")


# ==========================================
# 2. CREATE LLM
# ==========================================

def get_llm():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY not found in project .env file."
        )

    return ChatGroq(
        model="openai/gpt-oss-20b",
        api_key=api_key,
        temperature=0.2,
    )


# ==========================================
# 3. BUILD LCEL CHAIN
# ==========================================

def build_chain(system_prompt: str):
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{text}"),
    ])

    return (
        RunnablePassthrough()
        | RunnableLambda(lambda x: {"text": x})
        | prompt
        | llm
        | StrOutputParser()
    )


# ==========================================
# 4. EXTRACT ACTION ITEMS
# ==========================================

def extract_action_items(transcript: str) -> str:
    chain = build_chain(
        "You are an expert meeting analyst. "
        "Extract only action items explicitly supported by the transcript. "
        "For each action item provide:\n"
        "- Task description\n"
        "- Owner, if mentioned\n"
        "- Deadline, if mentioned\n"
        "If the owner or deadline is missing, write 'Not specified'. "
        "Do not invent tasks, owners, or deadlines. "
        "Format the output as a numbered list. "
        "If none are found, say 'No action items found.'"
    )

    return chain.invoke(transcript)


# ==========================================
# 5. EXTRACT KEY DECISIONS
# ==========================================

def extract_key_decisions(transcript: str) -> str:
    chain = build_chain(
        "You are an expert meeting analyst. "
        "Extract key decisions that were actually agreed upon "
        "in the transcript. Distinguish confirmed decisions from "
        "ideas or suggestions. Do not invent decisions. "
        "Format the output as a numbered list. "
        "If none are found, say 'No key decisions found.'"
    )

    return chain.invoke(transcript)


# ==========================================
# 6. EXTRACT OPEN QUESTIONS
# ==========================================

def extract_questions(transcript: str) -> str:
    chain = build_chain(
        "You are an expert meeting analyst. "
        "Extract unresolved questions, unanswered queries, "
        "and topics explicitly requiring follow-up. "
        "Do not include questions that were clearly answered "
        "unless further follow-up is needed. "
        "Do not invent questions. "
        "Format the output as a numbered list. "
        "If none are found, say 'No open questions found.'"
    )

    return chain.invoke(transcript)


