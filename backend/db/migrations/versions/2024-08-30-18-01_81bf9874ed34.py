"""empty message

Revision ID: 81bf9874ed34
Revises: 819cbf6e030b
Create Date: 2024-08-30 18:01:25.924417

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "81bf9874ed34"
down_revision = "819cbf6e030b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("login", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=50), nullable=False),
        sa.Column("password", sa.String(length=128), nullable=False),
        sa.Column("status_id", sa.Integer(), nullable=True),
        sa.Column("last_login_ip", sa.String(length=20), nullable=True),
        sa.Column("last_login_dt", sa.DateTime(), nullable=True),
        sa.Column("created_dt", sa.DateTime(), nullable=True),
        sa.Column("updated_dt", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("login"),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("value", sa.String(length=512), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("is_alive", sa.Boolean(), nullable=True),
        sa.Column("ttl_sec", sa.BigInteger(), nullable=False),
        sa.Column("created_dt", sa.DateTime(), nullable=True),
        sa.Column("updated_dt", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    # ### end Alembic commands ###
