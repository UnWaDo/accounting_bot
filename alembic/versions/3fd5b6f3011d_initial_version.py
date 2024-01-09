"""Initial version

Revision ID: 3fd5b6f3011d
Revises: 
Create Date: 2024-01-10 01:09:44.813051

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3fd5b6f3011d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'accounts', sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('start_date',
                  sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('start_balance', sa.DECIMAL(scale=2), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('code'),
        sa.UniqueConstraint('name'))
    op.create_table(
        'organizations', sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('shortcut', sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('name'),
        sa.UniqueConstraint('shortcut'))
    op.create_table(
        'bank_accounts', sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('annual_interest', sa.DECIMAL(scale=2), nullable=False),
        sa.Column('interest_period', sa.Interval(), nullable=False),
        sa.Column('bank_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['bank_id'],
            ['organizations.id'],
        ), sa.ForeignKeyConstraint(
            ['id'],
            ['accounts.id'],
        ), sa.PrimaryKeyConstraint('id'))
    op.create_table(
        'transactions', sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.UUID(), nullable=False),
        sa.Column('value', sa.DECIMAL(scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('timing',
                  sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('reason', sa.String(length=20), nullable=True),
        sa.Column('category', sa.String(length=10), nullable=True),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['account_id'],
            ['accounts.id'],
        ), sa.PrimaryKeyConstraint('id'))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('transactions')
    op.drop_table('bank_accounts')
    op.drop_table('organizations')
    op.drop_table('accounts')
    # ### end Alembic commands ###