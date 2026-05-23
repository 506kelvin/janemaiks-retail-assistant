"""initial_schema

Revision ID: 05a2fdf06ae6
Revises:
Create Date: 2026-05-23 12:09:37.803672

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "05a2fdf06ae6"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("supplier", sa.String(200), nullable=True),
        sa.Column("aliases", sa.Text(), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("search_keywords", sa.Text(), nullable=True),
        sa.Column("wholesale_price", sa.Float(), nullable=False),
        sa.Column("quantity_in_package", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("unit_type", sa.String(50), nullable=True, server_default=sa.text("'piece'")),
        sa.Column("retail_price", sa.Float(), nullable=True),
        sa.Column("profit_per_item", sa.Float(), nullable=True),
        sa.Column("profit_margin_percent", sa.Float(), nullable=True),
        sa.Column("package_cost_price", sa.Float(), nullable=True),
        sa.Column("package_quantity", sa.Integer(), nullable=True, server_default=sa.text("1")),
        sa.Column("package_unit_type", sa.String(50), nullable=True, server_default=sa.text("'piece'")),
        sa.Column("unit_cost_price", sa.Float(), nullable=True),
        sa.Column("wholesale_selling_price", sa.Float(), nullable=True),
        sa.Column("suggested_retail_price", sa.Float(), nullable=True),
        sa.Column("actual_retail_price", sa.Float(), nullable=True),
        sa.Column("profit_margin_per_unit", sa.Float(), nullable=True),
        sa.Column("allow_manual_override", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("rounding_strategy", sa.String(20), nullable=True, server_default=sa.text("'none'")),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("date_added", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_products_id"), "products", ["id"])
    op.create_index(op.f("ix_products_name"), "products", ["name"])

    op.create_table(
        "inventory",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity_available", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("low_stock_threshold", sa.Float(), nullable=True, server_default=sa.text("10")),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_inventory_id"), "inventory", ["id"])
    op.create_index(op.f("ix_inventory_product_id"), "inventory", ["product_id"])

    op.create_table(
        "stock_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("transaction_type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_stock_transactions_id"), "stock_transactions", ["id"])
    op.create_index(op.f("ix_stock_transactions_product_id"), "stock_transactions", ["product_id"])

    op.create_table(
        "chat_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(100), nullable=True),
        sa.Column("user_query", sa.Text(), nullable=False),
        sa.Column("bot_response", sa.Text(), nullable=False),
        sa.Column("products_referenced", sa.Text(), nullable=True),
        sa.Column("was_helpful", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("clarification_state", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_history_id"), "chat_history", ["id"])
    op.create_index(op.f("ix_chat_history_session_id"), "chat_history", ["session_id"])

    op.create_table(
        "sales",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sale_date", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sales_id"), "sales", ["id"])

    op.create_table(
        "sale_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sale_id", sa.Integer(), sa.ForeignKey("sales.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("product_name", sa.String(200), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False, server_default=sa.text("1")),
        sa.Column("selling_price", sa.Float(), nullable=False),
        sa.Column("subtotal", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sale_items_id"), "sale_items", ["id"])
    op.create_index(op.f("ix_sale_items_sale_id"), "sale_items", ["sale_id"])

    op.create_table(
        "requested_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(200), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("last_requested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_requested_items_id"), "requested_items", ["id"])
    op.create_index(op.f("ix_requested_items_product_name"), "requested_items", ["product_name"])


def downgrade() -> None:
    op.drop_table("requested_items")
    op.drop_table("sale_items")
    op.drop_table("sales")
    op.drop_table("chat_history")
    op.drop_table("stock_transactions")
    op.drop_table("inventory")
    op.drop_table("products")
