from fastapi import APIRouter
from models import FarmerIn
from crud import create_farmer, list_farmers as _list, farmer_payment_report

router = APIRouter()

@router.post("")
def add_farmer(data: FarmerIn):
    return create_farmer(data)

@router.get("")
def all_farmers():
    return _list()

@router.get("/payments")
def payments():
    return farmer_payment_report()