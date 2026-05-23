from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..models import RequestedItem

router = APIRouter(prefix="/api/requested-items", tags=["Requested Items"])


class RequestedItemCreate(BaseModel):
    product_name: str
    notes: Optional[str] = None


class RequestedItemUpdate(BaseModel):
    notes: Optional[str] = None


@router.post("/")
def create_requested_item(payload: RequestedItemCreate, db: Session = Depends(get_db)):
    name = payload.product_name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Product name is required")

    existing = db.query(RequestedItem).filter(func.lower(RequestedItem.product_name) == func.lower(name)).first()
    if existing:
        existing.request_count += 1
        existing.last_requested_at = datetime.utcnow()
        if payload.notes:
            existing.notes = payload.notes
        db.commit()
        db.refresh(existing)
        return {
            "id": existing.id,
            "product_name": existing.product_name,
            "notes": existing.notes,
            "request_count": existing.request_count,
            "last_requested_at": existing.last_requested_at.isoformat() if existing.last_requested_at else None,
            "created_at": existing.created_at.isoformat() if existing.created_at else None,
            "updated": True,
        }

    item = RequestedItem(
        product_name=name,
        notes=payload.notes,
        request_count=1,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "product_name": item.product_name,
        "notes": item.notes,
        "request_count": item.request_count,
        "last_requested_at": item.last_requested_at.isoformat() if item.last_requested_at else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated": False,
    }


@router.get("/")
def list_requested_items(
    search: str = "",
    sort_by: str = "request_count",
    db: Session = Depends(get_db),
):
    q = db.query(RequestedItem)

    if search:
        q = q.filter(RequestedItem.product_name.ilike(f"%{search}%"))

    if sort_by == "name":
        q = q.order_by(RequestedItem.product_name.asc())
    else:
        q = q.order_by(RequestedItem.request_count.desc(), RequestedItem.last_requested_at.desc())

    items = q.all()
    return [
        {
            "id": i.id,
            "product_name": i.product_name,
            "notes": i.notes,
            "request_count": i.request_count,
            "last_requested_at": i.last_requested_at.isoformat() if i.last_requested_at else None,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in items
    ]


@router.put("/{item_id}")
def update_requested_item(item_id: int, payload: RequestedItemUpdate, db: Session = Depends(get_db)):
    item = db.query(RequestedItem).filter(RequestedItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Requested item not found")

    if payload.notes is not None:
        item.notes = payload.notes

    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "product_name": item.product_name,
        "notes": item.notes,
        "request_count": item.request_count,
        "last_requested_at": item.last_requested_at.isoformat() if item.last_requested_at else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.delete("/{item_id}")
def delete_requested_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(RequestedItem).filter(RequestedItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Requested item not found")

    db.delete(item)
    db.commit()
    return {"detail": "Requested item removed", "id": item_id}
