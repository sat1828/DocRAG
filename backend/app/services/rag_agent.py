"""
LangGraph-based RAG agent with multi-round reasoning.
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
import structlog
import time
import re

from app.core.config import settings
from app.services.embeddings import embedding_service
from app.services.chroma_client import chroma_service
from app.services.gst_tools import gst_tools

logger = structlog.get_logger()


@tool
def gst_calculator(base_amount: float, rate: float, gst_type: str = "cgst_sgst") -> dict:
    """Calculate GST tax breakdown for Indian invoices."""
    return gst_tools.calculate_gst(base_amount, rate, gst_type)


@tool
def extract_gstins(text: str) -> List[str]:
    """Extract GSTINs from document text."""
    return gst_tools.extract_gstins(text)


@tool
def extract_hsn_codes(text: str) -> List[str]:
    """Extract HSN codes from document text."""
    return gst_tools.extract_hsn_codes(text)


@tool
def flag_legal_risks(text: str) -> List[Dict[str, Any]]:
    """Flag potential legal risks in contracts."""
    return gst_tools.flag_legal_risks(text)


class AgentState(TypedDict):
    """State for the RAG agent workflow."""
    messages: Annotated[List, lambda x, y: x + y]
    query: str
    user_id: str
    document_id: Optional[str]
    retrieved_chunks: List[Dict[str, Any]]
    context: str
    sources: List[Dict[str, Any]]
    confidence: float
    hallucination_risk: str
    response_time_ms: float


class RAGAgent:
    """Agentic RAG pipeline with guardrails and tool calling."""

    def __init__(self):
        self.llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.1,
            num_ctx=4096
        )
        self.tools = [gst_calculator, extract_gstins, extract_hsn_codes, flag_legal_risks]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.system_prompt = (
            "You are an expert Indian tax and legal assistant specializing in GST, contracts, and compliance.\n"
            "RULES:\n"
            "1. Answer ONLY using the provided context from the documents\n"
            "2. Cite specific page numbers and quote relevant snippets\n"
            "3. If the context doesn't contain the answer, say 'I cannot confirm this from the documents provided'\n"
            "4. For GST calculations, use the gst_calculator tool\n"
            "5. Flag any compliance risks or suspicious clauses you identify\n"
            "6. Respond in the user's language (English or Hinglish)\n"
            "7. Never hallucinate information not present in the context\n"
            "8. Be precise with numbers, amounts, and dates\n"
            "\nFORMAT YOUR RESPONSE:\n"
            "- Start with a direct answer\n"
            "- Provide supporting evidence with citations\n"
            "- Mention confidence level if uncertain\n"
            "- Flag risks if applicable"
        )
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        workflow.add_node("retrieve", self._retrieve)
        workflow.add_node("generate", self._generate)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_node("verify", self._verify)
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_conditional_edges(
            "generate",
            self._should_use_tools,
            {"tools": "tools", "verify": "verify"}
        )
        workflow.add_edge("tools", "generate")
        workflow.add_edge("verify", END)
        return workflow.compile()

    async def run(self, query: str, user_id: str, document_id: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()
        initial_state = AgentState(
            messages=[HumanMessage(content=query)],
            query=query,
            user_id=user_id,
            document_id=document_id,
            retrieved_chunks=[],
            context="",
            sources=[],
            confidence=0.0,
            hallucination_risk="unknown",
            response_time_ms=0.0
        )
        try:
            result = await self.graph.ainvoke(initial_state)
            result["response_time_ms"] = (time.time() - start_time) * 1000.0
            final_message = result["messages"][-1]
            answer = final_message.content if hasattr(final_message, "content") else str(final_message)
            sources = self._extract_sources(result.get("retrieved_chunks", []))
            return {
                "answer": answer,
                "sources": sources,
                "confidence": result.get("confidence", 0.0),
                "hallucination_risk": result.get("hallucination_risk", "unknown"),
                "tool_calls": [],
                "response_time_ms": result["response_time_ms"]
            }
        except Exception as e:
            logger.error("RAG agent failed", error=str(e), exc_info=True)
            return {
                "answer": "I encountered an error while processing your query. Please try again.",
                "sources": [],
                "confidence": 0.0,
                "hallucination_risk": "unknown",
                "tool_calls": [],
                "response_time_ms": (time.time() - start_time) * 1000.0
            }

    def _retrieve(self, state: AgentState) -> Dict[str, Any]:
        collection_name = "user_" + str(state["user_id"])
        where_filter = {"user_id": state["user_id"]}
        if state["document_id"]:
            where_filter["doc_id"] = state["document_id"]
        query_embedding = embedding_service.embed_query(state["query"])
        results = chroma_service.query(collection_name, query_embedding, where_filter, n_results=10)
        chunks = []
        if results.get("ids") and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                chunks.append({
                    "id": doc_id,
                    "content": results["documents"][0][i] if results.get("documents") else "",
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else 1.0
                })
        chunks.sort(key=lambda x: x["distance"])
        context_parts = []
        for i, chunk in enumerate(chunks[:5]):
            page = chunk["metadata"].get("page_number", "Unknown")
            modality = chunk["metadata"].get("modality", "text")
            context_parts.append(
                "[Source " + str(i+1) + " - Page " + str(page) + " - " + modality + "]\n" + chunk["content"]
            )
        return {"retrieved_chunks": chunks[:5], "context": "\n\n".join(context_parts)}

    def _generate(self, state: AgentState) -> Dict[str, Any]:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content="Context:\n" + state["context"] + "\n\nQuestion: " + state["query"])
        ]
        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def _should_use_tools(self, state: AgentState) -> str:
        messages = state["messages"]
        if messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
            return "tools"
        return "verify"

    def _verify(self, state: AgentState) -> Dict[str, Any]:
        messages = state["messages"]
        if not messages:
            return {"confidence": 0.0, "hallucination_risk": "high"}
        answer = messages[-1].content if hasattr(messages[-1], "content") else ""
        context = state.get("context", "")
        answer_sentences = [s.strip() for s in answer.split(".") if len(s.strip()) > 20]
        grounded_count = 0
        for sentence in answer_sentences:
            words = sentence.lower().split()
            matches = sum(1 for w in words if w in context.lower())
            if matches > len(words) * 0.3:
                grounded_count += 1
        grounded_ratio = grounded_count / max(len(answer_sentences), 1)
        if grounded_ratio > 0.7:
            return {"confidence": min(0.85 + grounded_ratio * 0.15, 1.0), "hallucination_risk": "low"}
        elif grounded_ratio > 0.4:
            return {"confidence": 0.6 + grounded_ratio * 0.25, "hallucination_risk": "medium"}
        else:
            return {"confidence": 0.3 + grounded_ratio * 0.3, "hallucination_risk": "high"}

    def _extract_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sources = []
        for chunk in chunks[:3]:
            metadata = chunk["metadata"]
            sources.append({
                "page": metadata.get("page_number", 0),
                "modality": metadata.get("modality", "text"),
                "snippet": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                "confidence": round(1.0 - chunk.get("distance", 0.5), 2),
                "document_id": metadata.get("doc_id")
            })
        return sources


rag_agent = RAGAgent()
