"""indices rotas e viagens

Revision ID: 85e987590bfa
Revises: 27ae0312b82d
Create Date: 2026-06-22 19:22:17.994740

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '85e987590bfa'
down_revision: Union[str, Sequence[str], None] = '27ae0312b82d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f('ix_rotas_destino'), 'rotas', ['destino'], unique=False)
    op.create_index(op.f('ix_rotas_dias_semana'), 'rotas', ['dias_semana'], unique=False)
    op.create_index(op.f('ix_rotas_origem'), 'rotas', ['origem'], unique=False)

    # batch_alter_table garante compatibilidade com SQLite (que não suporta
    # ALTER COLUMN nativo). Em Postgres roda como ALTER COLUMN direto.
    with op.batch_alter_table('viagens') as batch_op:
        batch_op.alter_column(
            'status',
            existing_type=sa.VARCHAR(),
            nullable=False,
            existing_server_default=None,
        )

    op.create_index(op.f('ix_viagens_data'), 'viagens', ['data'], unique=False)
    op.create_index(op.f('ix_viagens_status'), 'viagens', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_viagens_status'), table_name='viagens')
    op.drop_index(op.f('ix_viagens_data'), table_name='viagens')

    with op.batch_alter_table('viagens') as batch_op:
        batch_op.alter_column(
            'status',
            existing_type=sa.VARCHAR(),
            nullable=True,
        )

    op.drop_index(op.f('ix_rotas_origem'), table_name='rotas')
    op.drop_index(op.f('ix_rotas_dias_semana'), table_name='rotas')
    op.drop_index(op.f('ix_rotas_destino'), table_name='rotas')
