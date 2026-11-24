from fastapi import APIRouter
from models import CollectionIn, ReceiveIn
from crud import create_collection, list_collections as _list, mark_received, recommend_route

router = APIRouter()

@router.post("")
def add_collection(data: CollectionIn):
    return create_collection(data)

@router.get("")
def all_collections():
    return _list()

@router.get("/route")
def get_route():
    return recommend_route()

@router.patch("/{collection_id}/receive")
def receive(collection_id: int, data: ReceiveIn):
    return mark_received(collection_id, data.actual_weight_tonnes)