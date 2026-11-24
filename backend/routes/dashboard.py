from fastapi import APIRouter
from crud import dashboard_summary

router = APIRouter()

@router.get("")
def summary():
    return dashboard_summary()