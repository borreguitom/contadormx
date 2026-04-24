from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.services.agent import run_agent
from app.core.database import get_db, User, Conversation, Message
from app.core.deps import get_current_user, check_query_limit

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    client_context: Optional[str] = None
    use_web_search: bool = False
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    content: str
    tools_used: list[str]
    input_tokens: int
    output_tokens: int
    conversation_id: int


class ConversationSummary(BaseModel):
    id: int
    title: str
    created_at: str

    class Config:
        from_attributes = True


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not req.messages:
        raise HTTPException(status_code=400, detail="Se requiere al menos un mensaje")

    allowed, msg, reset_happened = check_query_limit(current_user)
    if not allowed:
        raise HTTPException(status_code=402, detail=msg)
    if reset_happened:
        await db.flush()

    # Find or create conversation
    conv: Conversation | None = None
    if req.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == req.conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        conv = result.scalar_one_or_none()

    if not conv:
        last_user = next((m for m in reversed(req.messages) if m.role == "user"), None)
        raw = last_user.content if last_user else "Nueva consulta"
        title = raw[:57] + "…" if len(raw) > 60 else raw
        conv = Conversation(user_id=current_user.id, title=title)
        db.add(conv)
        await db.flush()  # assign ID without committing

    # Persist the new user message
    last_user_msg = req.messages[-1]
    db.add(Message(conversation_id=conv.id, role="user", content=last_user_msg.content))

    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    result = await run_agent(
        messages=messages,
        client_context=req.client_context,
        use_web_search=req.use_web_search,
    )

    # Persist assistant response
    db.add(Message(
        conversation_id=conv.id,
        role="assistant",
        content=result["content"],
        tools_used=",".join(result.get("tools_used", [])) or None,
    ))

    current_user.queries_this_month = (current_user.queries_this_month or 0) + 1
    await db.commit()

    return ChatResponse(**result, conversation_id=conv.id)


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .limit(30)
    )
    convs = result.scalars().all()
    return [
        ConversationSummary(
            id=c.id,
            title=c.title or "Sin título",
            created_at=c.created_at.strftime("%d %b %Y") if c.created_at else "",
        )
        for c in convs
    ]


@router.get("/conversations/{conv_id}")
async def get_conversation(
    conv_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(404, "Conversación no encontrada")

    msgs_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at)
    )
    msgs = msgs_result.scalars().all()

    return {
        "id": conv.id,
        "title": conv.title,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "tools_used": m.tools_used.split(",") if m.tools_used else [],
            }
            for m in msgs
        ],
    }
