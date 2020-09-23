"""empty message

Revision ID: db961d48434d
Revises: 3c8495dbf54f
Create Date: 2020-09-23 16:48:28.438253

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'db961d48434d'
down_revision = '3c8495dbf54f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('portfolio_db', sa.Column('userid', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('portfolio_db', 'userid')
    # ### end Alembic commands ###
