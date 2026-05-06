"""
Alembic initial migration - creates all database tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = '2026_01_01_000000_initial_migration'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all database tables."""
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('user', 'admin', name='user_role'), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.Enum('pending', 'processing', 'ready', 'error', name='doc_status'), nullable=False, server_default='pending'),
        sa.Column('metadata_json', postgresql.JSONB, nullable=True),
        sa.Column('chroma_collection_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_documents_user_status', 'documents', ['user_id', 'status'])
    op.create_index('idx_documents_created', 'documents', ['created_at'])
    
    # Chat sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(500), nullable=True, server_default='New Chat'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_chat_sessions_user', 'chat_sessions', ['user_id', 'created_at'])
    
    # Chat messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sources_json', postgresql.JSONB, nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_chat_messages_session', 'chat_messages', ['session_id', 'created_at'])
    
    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('details_json', postgresql.JSONB, nullable=True),
        sa.Column('ip_address', postgresql.INET, nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_audit_logs_user_action', 'audit_logs', ['user_id', 'action'])
    op.create_index('idx_audit_logs_timestamp', 'audit_logs', ['timestamp'])


def downgrade() -> None:
    """Drop all database tables."""
    op.drop_table('audit_logs')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('documents')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE user_role')
    op.execute('DROP TYPE doc_status')
