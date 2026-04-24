from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from .config import settings

DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class RegimenFiscal(str, enum.Enum):
    sueldos = "sueldos"
    actividades_empresariales = "actividades_empresariales"
    arrendamiento = "arrendamiento"
    resico_pf = "resico_pf"
    resico_pm = "resico_pm"
    general_pm = "general_pm"
    honorarios = "honorarios"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    nombre = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    # Billing / usage
    plan = Column(String(20), default="free", nullable=False)
    queries_this_month = Column(Integer, default=0, nullable=False)
    queries_reset_date = Column(DateTime(timezone=True), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    clientes = relationship("Cliente", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")


class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rfc = Column(String(13), nullable=False, index=True)
    razon_social = Column(String(255), nullable=False)
    regimen_fiscal = Column(String(100))
    actividad = Column(String(255))
    correo = Column(String(255))
    telefono = Column(String(20))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="clientes")
    conversations = relationship("Conversation", back_populates="cliente")
    documentos = relationship("Documento", back_populates="cliente")


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    title = Column(String(255), default="Nueva consulta")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="conversations")
    cliente = relationship("Cliente", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    tools_used = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    conversation = relationship("Conversation", back_populates="messages")


class EstadoDocumento(str, enum.Enum):
    pendiente = "pendiente"
    procesando = "procesando"
    extraido = "extraido"
    error = "error"


class TipoArchivo(str, enum.Enum):
    xml = "xml"
    pdf = "pdf"
    imagen = "imagen"


class Documento(Base):
    __tablename__ = "documentos"
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # archivo original
    nombre_archivo = Column(String(255), nullable=False)
    tipo_archivo = Column(String(20), nullable=False)
    file_path = Column(Text, nullable=True)
    # datos extraídos del CFDI / factura
    uuid_cfdi = Column(String(50), nullable=True, index=True)
    tipo_comprobante = Column(String(10), nullable=True)   # I=Ingreso, E=Egreso, T=Traslado, N=Nómina, P=Pago
    serie = Column(String(25), nullable=True)
    folio = Column(String(40), nullable=True)
    fecha_emision = Column(DateTime(timezone=True), nullable=True)
    emisor_rfc = Column(String(15), nullable=True)
    emisor_nombre = Column(String(255), nullable=True)
    receptor_rfc = Column(String(15), nullable=True)
    receptor_nombre = Column(String(255), nullable=True)
    subtotal = Column(Float, nullable=True)
    descuento = Column(Float, nullable=True, default=0)
    iva_trasladado = Column(Float, nullable=True, default=0)
    iva_retenido = Column(Float, nullable=True, default=0)
    isr_retenido = Column(Float, nullable=True, default=0)
    total = Column(Float, nullable=True)
    moneda = Column(String(10), nullable=True, default="MXN")
    tipo_cambio = Column(Float, nullable=True, default=1)
    conceptos = Column(JSON, nullable=True)
    # estado del procesamiento
    estado = Column(String(20), default="pendiente", nullable=False)
    error_msg = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    cliente = relationship("Cliente", back_populates="documentos")


class LawUpdate(Base):
    __tablename__ = "law_updates"
    id = Column(Integer, primary_key=True)
    ley = Column(String(50), index=True)
    tipo = Column(String(50))
    titulo = Column(Text, nullable=False)
    url = Column(Text)
    fecha_publicacion = Column(DateTime(timezone=True), nullable=True)
    resumen = Column(Text, nullable=True)
    indexado = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("DB tables created OK")
