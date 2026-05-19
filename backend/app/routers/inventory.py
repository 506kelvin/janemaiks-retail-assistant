from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product, Inventory, StockTransaction
from ..schemas.inventory import InventoryResponse, StockTransactionCreate, StockTransactionResponse

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


def _get_or_create_inventory(product_id: int, db: Session) -> Inventory:
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inv:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        inv = Inventory(product_id=product_id, quantity_available=0)
        db.add(inv)
        db.commit()
        db.refresh(inv)
    return inv


@router.get("/", response_model=List[InventoryResponse])
def list_inventory(
    low_stock_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    results = []
    inventories = db.query(Inventory).all()
    for inv in inventories:
        product = db.query(Product).filter(Product.id == inv.product_id).first()
        is_low = inv.low_stock_threshold and inv.quantity_available <= inv.low_stock_threshold
        if low_stock_only and not is_low:
            continue
        results.append(InventoryResponse(
            id=inv.id,
            product_id=inv.product_id,
            product_name=product.name if product else None,
            quantity_available=inv.quantity_available,
            low_stock_threshold=inv.low_stock_threshold,
            is_low_stock=is_low,
            updated_at=inv.updated_at,
        ))
    return results


@router.get("/{product_id}", response_model=InventoryResponse)
def get_inventory(product_id: int, db: Session = Depends(get_db)):
    inv = _get_or_create_inventory(product_id, db)
    product = db.query(Product).filter(Product.id == product_id).first()
    is_low = inv.low_stock_threshold and inv.quantity_available <= inv.low_stock_threshold
    return InventoryResponse(
        id=inv.id,
        product_id=inv.product_id,
        product_name=product.name if product else None,
        quantity_available=inv.quantity_available,
        low_stock_threshold=inv.low_stock_threshold,
        is_low_stock=is_low,
        updated_at=inv.updated_at,
    )


@router.post("/transactions", response_model=StockTransactionResponse)
def create_transaction(data: StockTransactionCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    inv = _get_or_create_inventory(data.product_id, db)

    if data.transaction_type == "add":
        inv.quantity_available += data.quantity
    elif data.transaction_type == "deduct":
        if inv.quantity_available < data.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {inv.quantity_available}")
        inv.quantity_available -= data.quantity
    elif data.transaction_type == "adjust":
        inv.quantity_available = data.quantity

    transaction = StockTransaction(
        product_id=data.product_id,
        transaction_type=data.transaction_type,
        quantity=data.quantity,
        notes=data.notes,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/transactions/list", response_model=List[StockTransactionResponse])
def list_transactions(
    product_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(StockTransaction).order_by(StockTransaction.created_at.desc())
    if product_id:
        q = q.filter(StockTransaction.product_id == product_id)
    return q.limit(limit).all()


@router.put("/threshold/{product_id}")
def update_threshold(product_id: int, threshold: float = Query(...), db: Session = Depends(get_db)):
    inv = _get_or_create_inventory(product_id, db)
    inv.low_stock_threshold = threshold
    db.commit()
    return {"message": "Threshold updated", "product_id": product_id, "threshold": threshold}
