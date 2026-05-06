"""
Generate all production-ready Python files with guaranteed correct syntax.
Run: python generate_clean.py
"""
import os

base = r"D:\Multi\indian-sme-doc-intelligence-rag\backend\app"

# ===== 1. core/security.py =====
security = '''"""
Security utilities for JWT authentication and password hashing.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import TokenData

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(datetime.UTC) + expires_delta
    else:
        expire = datetime.now(datetime.UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(datetime.UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenData(email=email)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    from sqlalchemy import select
    from uuid import UUID

    token_data = decode_token(credentials.credentials)

    user_id = token_data.email
    try:
        uuid_obj = UUID(user_id)
        result = await db.execute(select(User).where(User.id == uuid_obj))
    except (ValueError, AttributeError):
        result = await db.execute(select(User).where(User.email == user_id))

    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Check if the current user has admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
'''

# ===== 2. core/config.py =====
config = '''"""
Application configuration settings.
All environment variables are loaded and validated here.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/rag_db"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@postgres:5432/rag_db"

    # Ollama
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.3:8b"

    # JWT Authentication
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "/data/chroma"

    # File Upload
    MAX_PDF_PAGES: int = 100
    MAX_FILE_SIZE_MB: int = 50

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Environment
    ENVIRONMENT: str = "development"

    # BM25 + Hybrid Search
    BM25_ENABLED: bool = True

    # Cross-Encoder Reranking
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
'''

# ===== 3. routers/auth.py =====
auth = '''"""
Authentication router - handles user registration, login, and profile.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_current_user,
    decode_token,
    jwt,
    JWTError,
)
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, Token, UserResponse
from app.utils.validators import sanitize_input

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user = User(
        email=sanitize_input(user_data.email),
        hashed_password=get_password_hash(user_data.password),
        role="user"
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    access_token = create_access_token(data={"sub": str(new_user.id), "email": new_user.email})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id), "email": new_user.email})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token(data={"sub": str(user.id), "email": user.email})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token."""
    try:
        payload = jwt.decode(refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        email = payload.get("email")
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")

        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id), "email": user.email})

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )
'''

# ===== 4. services/gst_tools.py =====
gst_tools = '''"""
GST and Indian legal compliance tools.
"""
import re
from typing import List, Dict, Any, Optional
from app.utils.validators import validate_gstin_format
import structlog

logger = structlog.get_logger()


class GSTTools:
    """Tools for GST validation, extraction, and calculations."""

    @staticmethod
    def validate_gstin(gstin: str) -> Dict[str, Any]:
        is_valid_format = validate_gstin_format(gstin)
        return {
            "gstin": gstin,
            "valid_format": is_valid_format,
            "state_code": gstin[:2] if is_valid_format and len(gstin) >= 2 else None,
            "pan": gstin[2:12] if is_valid_format and len(gstin) == 15 else None,
        }

    @staticmethod
    def extract_gstins(text: str) -> List[str]:
        gstin_pattern = re.compile(r'\\b\\d{2}[A-Z]{5}\\d{4}[A-Z]{1}[1-9A-Z]{1}Z[\\dA-Z]{1}\\b')
        matches = gstin_pattern.findall(text)
        valid_gstins = [g for g in matches if validate_gstin_format(g)]
        logger.info("Extracted GSTINs from text", count=len(valid_gstins))
        return valid_gstins

    @staticmethod
    def extract_hsn_codes(text: str) -> List[str]:
        hsn_pattern = re.compile(r'(?:HSN\\s*(?:Code)?:?\\s*)(\\d{4,8})', re.IGNORECASE)
        matches = hsn_pattern.findall(text)
        if len(matches) < 3:
            standalone_pattern = re.compile(r'(?:^|\\s)(\\d{4}(?:\\d{2}(?:\\d{2})?))(?:\\s|$)')
            matches.extend(standalone_pattern.findall(text))
        unique_hsns = list(set(matches))
        logger.info("Extracted HSN codes", count=len(unique_hsns))
        return unique_hsns

    @staticmethod
    def calculate_gst(amount: float, rate: float, gst_type: str = "both") -> Dict[str, float]:
        total_gst = amount * (rate / 100.0)
        if gst_type == "igst":
            return {
                "base_amount": amount,
                "igst": round(total_gst, 2),
                "cgst": 0.0,
                "sgst": 0.0,
                "total_gst": round(total_gst, 2),
                "total_amount": round(amount + total_gst, 2)
            }
        else:
            half_gst = total_gst / 2.0
            return {
                "base_amount": amount,
                "igst": 0.0,
                "cgst": round(half_gst, 2),
                "sgst": round(half_gst, 2),
                "total_gst": round(total_gst, 2),
                "total_amount": round(amount + total_gst, 2)
            }

    @staticmethod
    def verify_tax_totals(base_amount: float, cgst: float, sgst: float, igst: float, total_amount: float) -> Dict[str, Any]:
        calculated_total = base_amount + cgst + sgst + igst
        discrepancy = abs(calculated_total - total_amount)
        is_valid = discrepancy < 1.0
        return {
            "valid": is_valid,
            "base_amount": base_amount,
            "total_tax": cgst + sgst + igst,
            "calculated_total": round(calculated_total, 2),
            "reported_total": total_amount,
            "discrepancy": round(discrepancy, 2),
            "flags": [] if is_valid else ["Tax total mismatch detected"]
        }

    @staticmethod
    def flag_legal_risks(text: str) -> List[Dict[str, Any]]:
        risks = []
        if re.search(r'force\\s*majeure|act\\s*of\\s*god|unforeseen\\s*events', text, re.IGNORECASE):
            risks.append({"category": "Force Majeure", "severity": "medium", "description": "Force Majeure clause detected", "section": "Extract"})
        if re.search(r'penalty|liquidated\\s*damages|compensation\\s*for\\s*breach', text, re.IGNORECASE):
            risks.append({"category": "Penalty Clause", "severity": "high", "description": "Penalty clause found", "section": "Extract"})
        if re.search(r'termination|terminate\\s*agreement|notice\\s*period', text, re.IGNORECASE):
            risks.append({"category": "Termination", "severity": "medium", "description": "Termination clause detected", "section": "Extract"})
        if re.search(r'jurisdiction|arbitration|dispute\\s*resolution', text, re.IGNORECASE):
            risks.append({"category": "Dispute Resolution", "severity": "medium", "description": "Jurisdiction clause found", "section": "Extract"})
        if re.search(r'gst|goods\\s*and\\s*services\\s*tax', text, re.IGNORECASE):
            if not GSTTools.extract_gstins(text):
                risks.append({"category": "GST Compliance", "severity": "high", "description": "GST mentioned but no valid GSTIN", "section": "N/A"})
        if re.search(r'indemnif|hold\\s*harmless', text, re.IGNORECASE):
            risks.append({"category": "Indemnity", "severity": "high", "description": "Indemnity clause detected", "section": "Extract"})
        logger.info("Legal risk analysis completed", risks_found=len(risks))
        return risks


gst_tools = GSTTools()
'''

# ===== 5. services/chroma_client.py =====
chroma = '''"""
ChromaDB service for vector storage and similarity search.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class ChromaService:
    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        logger.info("ChromaDB initialized", persist_dir=self.persist_dir)

    def get_or_create_collection(self, collection_name: str):
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]], documents: List[str]) -> None:
        collection = self.get_or_create_collection(collection_name)
        collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
        logger.info("Added documents to ChromaDB", collection=collection_name, count=len(ids))

    def query(self, collection_name: str, query_embedding: List[float], filter: Dict[str, Any], n_results: int = 10):
        try:
            collection = self.get_or_create_collection(collection_name)
            results = collection.query(
                query_embeddings=[query_embedding],
                where=filter,
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            return results
        except Exception as e:
            logger.error("ChromaDB query failed", error=str(e))
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    def delete_collection(self, collection_name: str) -> None:
        try:
            self.client.delete_collection(name=collection_name)
        except Exception as e:
            logger.warning("Failed to delete collection", error=str(e))

    def delete_documents(self, collection_name: str, filter: Dict[str, Any]) -> None:
        try:
            collection = self.get_or_create_collection(collection_name)
            collection.delete(where=filter)
        except Exception as e:
            logger.error("Failed to delete documents", error=str(e))

    def get_collection_stats(self, collection_name: str):
        try:
            collection = self.get_or_create_collection(collection_name)
            return {"count": collection.count(), "name": collection_name}
        except Exception as e:
            logger.error("Failed to get collection stats", error=str(e))
            return {"count": 0, "name": collection_name}


chroma_service = ChromaService()
'''

# ===== 6. services/embeddings.py =====
embeddings = '''"""
Embedding service for text and multimodal embeddings.
"""
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import structlog
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = structlog.get_logger()


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info("Loading embedding model", model=model_name)
        self.text_model = SentenceTransformer(model_name)
        self.embedding_dimension = 384
        logger.info("Embedding service initialized", dimension=self.embedding_dimension)

    def embed_text(self, texts: Union[str, List[str]]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.text_model.encode(texts, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        embedding = self.text_model.encode([query], show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
        return embedding[0].tolist()

    async def batch_embed(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        def encode_batch(batch):
            return self.text_model.encode(batch, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            tasks = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                task = loop.run_in_executor(executor, encode_batch, batch)
                tasks.append(task)
            results = await asyncio.gather(*tasks)

        all_embeddings = []
        for batch_result in results:
            all_embeddings.extend(batch_result.tolist())
        return all_embeddings


embedding_service = EmbeddingService()
'''

# ===== 7. services/rag_agent.py =====
rag_agent = '''"""
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
    def __init__(self):
        self.llm = ChatOllama(model=settings.OLLAMA_MODEL, base_url=settings.OLLAMA_BASE_URL, temperature=0.1, num_ctx=4096)
        self.tools = [gst_calculator, extract_gstins, extract_hsn_codes, flag_legal_risks]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.system_prompt = """You are an expert Indian tax and legal assistant specializing in GST, contracts, and compliance.

RULES:
1. Answer ONLY using the provided context from the documents
2. Cite specific page numbers and quote relevant snippets
3. If the context doesn't contain the answer, say "I cannot confirm this from the documents provided"
4. For GST calculations, use the gst_calculator tool
5. Flag any compliance risks or suspicious clauses you identify
6. Respond in the user's language (English or Hinglish)
7. Never hallucinate information not present in the context
8. Be precise with numbers, amounts, and dates"""

        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("retrieve", self._retrieve)
        workflow.add_node("generate", self._generate)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_node("verify", self._verify)
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_conditional_edges("generate", self._should_use_tools, {"tools": "tools", "verify": "verify"})
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
            return {"answer": "Error processing query.", "sources": [], "confidence": 0.0, "hallucination_risk": "unknown", "tool_calls": [], "response_time_ms": (time.time() - start_time) * 1000.0}

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
            context_parts.append("[Source " + str(i+1) + " - Page " + str(page) + " - " + modality + "]\n" + chunk["content"])
        return {"retrieved_chunks": chunks[:5], "context": "\n\n".join(context_parts)}

    def _generate(self, state: AgentState) -> Dict[str, Any]:
        messages = [SystemMessage(content=self.system_prompt), HumanMessage(content="Context:\n" + state["context"] + "\n\nQuestion: " + state["query"])]
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
'''

# Write all files
files = {
    os.path.join(base, "core", "security.py"): security,
    os.path.join(base, "core", "config.py"): config,
    os.path.join(base, "routers", "auth.py"): auth,
    os.path.join(base, "services", "gst_tools.py"): gst_tools,
    os.path.join(base, "services", "chroma_client.py"): chroma,
    os.path.join(base, "services", "embeddings.py"): embeddings,
    os.path.join(base, "services", "rag_agent.py"): rag_agent,
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {path}")

# Delete demo_server.py
demo = os.path.join(base, "..", "demo_server.py")
if os.path.exists(demo):
    os.remove(demo)
    print(f"Deleted: {demo}")

# Verify syntax
import ast
print("\nVerifying syntax...")
all_ok = True
for path in files.keys():
    try:
        with open(path, "r", encoding="utf-8") as f:
            ast.parse(f.read())
        print(f"OK: {os.path.basename(path)}")
    except SyntaxError as e:
        print(f"SYNTAX ERROR in {os.path.basename(path)} at line {e.lineno}: {e.msg}")
        all_ok = False

if all_ok:
    print("\nALL FILES ARE SYNTACTICALLY CORRECT!")
else:
    print("\nSOME FILES STILL HAVE SYNTAX ERRORS!")
