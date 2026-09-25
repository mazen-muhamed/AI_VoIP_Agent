from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_add_username_to_users'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('username', sa.String(100), nullable=True))
    op.create_index('ix_user_username', 'users', ['username'])

    # Create unique constraint on (username, tenant_id)
    op.create_unique_constraint('uq_user_username_tenant', 'users', ['username', 'tenant_id'])


def downgrade() -> None:
    op.drop_constraint('uq_user_username_tenant', 'users', type_='unique')
    op.drop_index('ix_user_username', table_name='users')
    op.drop_column('users', 'username')
