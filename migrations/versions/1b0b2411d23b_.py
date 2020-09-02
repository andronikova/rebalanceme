"""empty message

Revision ID: 1b0b2411d23b
Revises: 
Create Date: 2020-08-29 18:41:43.462998

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1b0b2411d23b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('portfolio')
    op.drop_table('cash')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cash',
    sa.Column('userid', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('rub', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('euro', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('usd', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('userid', name='cash_pkey')
    )
    op.create_table('portfolio',
    sa.Column('userid', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('ticker', sa.VARCHAR(length=64), autoincrement=False, nullable=True),
    sa.Column('number', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('fraction', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('userid', name='portfolio_pkey')
    )
    # ### end Alembic commands ###