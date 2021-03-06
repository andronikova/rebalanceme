"""empty message

Revision ID: 359ab9379570
Revises: b7dae9ed110e
Create Date: 2020-10-15 13:41:20.623256

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '359ab9379570'
down_revision = 'b7dae9ed110e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('week_db',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('monday', sa.Boolean(), nullable=True),
    sa.Column('tuesday', sa.Boolean(), nullable=True),
    sa.Column('wednesday', sa.Boolean(), nullable=True),
    sa.Column('thursday', sa.Boolean(), nullable=True),
    sa.Column('friday', sa.Boolean(), nullable=True),
    sa.Column('saturday', sa.Boolean(), nullable=True),
    sa.Column('sunday', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('userid')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('week_db')
    # ### end Alembic commands ###
