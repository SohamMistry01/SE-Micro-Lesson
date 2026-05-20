import operator
import tiktoken
from typing import List, TypedDict, Annotated, Optional
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph
from modules.config import settings
from typing import cast, Any

LLM_MODELS = [
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-guard-4-12b",
    "moonshotai/kimi-k2-instruct",
]

api_key = settings.GROQ_API_KEY


class OverallState(TypedDict):
    file_contents: List[str]
    file_summaries: Annotated[List[str], operator.add]
    final_microlesson: str
    category: str
    priority_llm: Optional[str]
    prompt_template: str


class FileProcessingState(TypedDict):
    content: str
    priority_llm: Optional[str]


def count_tokens(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def chunk_text(text: str, chunk_token_limit=3500) -> List[str]:
    words = text.split()
    chunks, current, token_count = [], [], 0
    for w in words:
        t = count_tokens(w)
        if token_count + t > chunk_token_limit and current:
            chunks.append(" ".join(current))
            current, token_count = [], 0
        current.append(w)
        token_count += t
    if current:
        chunks.append(" ".join(current))
    return chunks


def process_file_node(state: OverallState):
    all_file_summaries = []
    priority = state.get("priority_llm")

    # Dynamically reorder LLM models based on user priority
    active_models = LLM_MODELS.copy()
    if priority and priority in active_models:
        active_models.remove(priority)
        active_models.insert(0, priority)
    elif priority and priority not in active_models:
        # If user passes an unlisted valid groq model, prioritize it anyway
        active_models.insert(0, priority)

    # Loop over all files natively instead of using LangGraph 'Send'
    for file_idx, text in enumerate(state["file_contents"], start=1):
        chunks = chunk_text(text)
        chunk_summaries = []

        print(
            f"   --> Processing file {file_idx}/{len(state['file_contents'])} with {len(chunks)} chunks..."
        )
        for i, chunk in enumerate(chunks):
            model_name = active_models[i % len(active_models)]
            try:
                llm = ChatGroq(model=model_name, temperature=0.3, api_key=api_key)
                prompt = ChatPromptTemplate.from_template(
                    """Summarize this chunk using clean Markdown.
                    - Use '##' for headers.
                    - Use bullet points.
                    Chunk:\n{content}\n\nSummary:"""
                )
                chain = prompt.pipe(llm).pipe(StrOutputParser())
                summary = chain.invoke({"content": chunk}).strip()
                chunk_summaries.append(summary)
            except Exception as e:
                print(f"      [Error] {model_name}: {e}")
                chunk_summaries.append("")

        all_file_summaries.append("\n\n".join(chunk_summaries))

    return {"file_summaries": all_file_summaries}


def generate_microlesson_node(state: OverallState):
    print("🔹 Generating Final Micro-Lesson...")
    all_summaries = "\n\n".join(state["file_summaries"])
    prompt_str = state["prompt_template"]

    final_llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.3, api_key=api_key)
    final_prompt = ChatPromptTemplate.from_template(prompt_str)

    chain = final_prompt.pipe(final_llm).pipe(StrOutputParser())
    return {"final_microlesson": chain.invoke({"content": all_summaries})}


workflow = StateGraph(OverallState)
workflow.add_node("process_file", process_file_node)
workflow.add_node("generate_microlesson", generate_microlesson_node)

# Use explicit entry and finish points instead of START/END constants
workflow.set_entry_point("process_file")
workflow.add_edge("process_file", "generate_microlesson")
workflow.set_finish_point("generate_microlesson")

app_graph = workflow.compile()


# --- 5. Pipeline Execution ---
def run_rag_pipeline(
    contents: List[str],
    category: str,
    priority_llm: Optional[str],
    prompt_template: str,
) -> str:
    result = app_graph.invoke(
        cast(
            Any,
            {
                "file_contents": contents,
                "category": category,
                "priority_llm": priority_llm,
                "prompt_template": prompt_template,
                "file_summaries": [],
            },
        )
    )
    return result.get("final_microlesson", "")
