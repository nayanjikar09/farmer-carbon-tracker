from fastapi import APIRouter
from models import ProductionIn
from crud import create_batch, list_batches, production_report

router = APIRouter()

@router.post("")
def add_batch(data: ProductionIn):
    return create_batch(data)

@router.get("")
def all_batches():
    return list_batches()

@router.get("/report")
def report():
    return production_report()