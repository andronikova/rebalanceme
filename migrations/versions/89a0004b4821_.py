"""empty message

Revision ID: 89a0004b4821
Revises: 359ab9379570
Create Date: 2020-10-19 14:59:15.355069

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '89a0004b4821'
down_revision = '359ab9379570'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_db', 'reportfrequency')
    op.drop_column('user_db', 'reportday')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_db', sa.Column('reportday', sa.VARCHAR(length=64), autoincrement=False, nullable=True))
    op.add_column('user_db', sa.Column('reportfrequency', sa.INTEGER(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
