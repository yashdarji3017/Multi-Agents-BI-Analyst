"""Column mapping between raw CSV schemas and canonical analytical fields."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CanonicalField(BaseModel):
    """Definition of an internal canonical analytical field."""

    key: str
    description: str
    required: bool = True
    aliases: List[str] = Field(default_factory=list)


CANONICAL_FIELDS: Dict[str, CanonicalField] = {
    "order_id": CanonicalField(
        key="order_id",
        description="Unique identifier for the transaction order",
        required=True,
        aliases=["order id", "order_id", "orderid", "invoice_no", "invoice no", "transaction_id"],
    ),
    "order_date": CanonicalField(
        key="order_date",
        description="Transaction or order placement timestamp",
        required=True,
        aliases=["order date", "order_date", "orderdate", "date", "invoice_date", "sale_date"],
    ),
    "sales": CanonicalField(
        key="sales",
        description="Transaction sales or revenue value in currency units",
        required=True,
        aliases=["sales", "revenue", "sale_amount", "amount", "total_sales", "order_total"],
    ),
    "product_name": CanonicalField(
        key="product_name",
        description="Name or title of the product",
        required=True,
        aliases=["product name", "product_name", "productname", "item_name", "description", "title"],
    ),
    "category": CanonicalField(
        key="category",
        description="Top-level product category",
        required=True,
        aliases=["category", "product_category", "product category", "department", "item_group"],
    ),
    "region": CanonicalField(
        key="region",
        description="Geographic region or territory of sale",
        required=True,
        aliases=["region", "sales_region", "territory", "zone", "geographic_region"],
    ),

    "quantity": CanonicalField(
        key="quantity",
        description="Number of product units purchased",
        required=False,
        aliases=["quantity", "qty", "units", "units_sold", "volume"],
    ),
    "discount": CanonicalField(
        key="discount",
        description="Discount fraction or percentage applied",
        required=False,
        aliases=["discount", "discount_rate", "discount_pct", "discount_amount"],
    ),
    "profit": CanonicalField(
        key="profit",
        description="Net profit or margin amount in currency units",
        required=False,
        aliases=["profit", "net_profit", "margin", "earnings", "net_income"],
    ),
    "segment": CanonicalField(
        key="segment",
        description="Customer market segment (e.g., Consumer, Corporate)",
        required=False,
        aliases=["segment", "customer_segment", "customer segment", "client_type"],
    ),
    "sub_category": CanonicalField(
        key="sub_category",
        description="Granular product sub-category",
        required=False,
        aliases=["sub-category", "sub_category", "subcategory", "item_subgroup"],
    ),
    "city": CanonicalField(
        key="city",
        description="City where order was delivered",
        required=False,
        aliases=["city", "customer_city"],
    ),
    "state": CanonicalField(
        key="state",
        description="State or province where order was delivered",
        required=False,
        aliases=["state", "province", "customer_state"],
    ),
}


class ColumnMapper:
    """Detects and maps raw CSV column names to canonical schema fields."""

    @staticmethod
    def detect_mapping(columns: List[str]) -> Dict[str, str]:
        """Maps raw column names to canonical field keys.

        Returns a dictionary mapping: canonical_key -> raw_column_name.
        """
        mapping: Dict[str, str] = {}
        normalized_cols = {col.strip().lower().replace("-", " ").replace("_", " "): col for col in columns}

        for canonical_key, field_def in CANONICAL_FIELDS.items():

            if canonical_key in normalized_cols:
                mapping[canonical_key] = normalized_cols[canonical_key]
                continue


            matched = False
            for alias in field_def.aliases:
                clean_alias = alias.strip().lower().replace("-", " ").replace("_", " ")
                if clean_alias in normalized_cols:
                    mapping[canonical_key] = normalized_cols[clean_alias]
                    matched = True
                    break


            if not matched:
                for clean_name, orig_name in normalized_cols.items():
                    if canonical_key == "sales" and clean_name == "sales":
                        mapping[canonical_key] = orig_name
                        break
                    if canonical_key == "order_date" and "order" in clean_name and "date" in clean_name:
                        mapping[canonical_key] = orig_name
                        break
                    if canonical_key == "product_name" and "product" in clean_name and "name" in clean_name:
                        mapping[canonical_key] = orig_name
                        break

        return mapping

    @staticmethod
    def get_missing_required_fields(mapping: Dict[str, str]) -> List[str]:
        """Returns a list of required canonical fields that were not matched."""
        missing = []
        for key, field_def in CANONICAL_FIELDS.items():
            if field_def.required and key not in mapping:
                missing.append(key)
        return missing
