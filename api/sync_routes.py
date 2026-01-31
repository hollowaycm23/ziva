"""
API Endpoints para Sincronização com Gabrielle
"""
from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from core.sync_manager import SyncManager

router = APIRouter(prefix="/sync", tags=["sync"])
sync_manager = SyncManager()


class MarkSyncedRequest(BaseModel):
    point_ids: List[str]


@router.get("/pending")
async def get_pending_sync(limit: int = 100):
    """
    Retorna documentos pendentes de sincronização.

    Gabrielle chama este endpoint para buscar novos documentos.
    """
    try:
        docs = sync_manager.get_pending_sync(limit=limit)
        return {
            "status": "success",
            "count": len(docs),
            "documents": docs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark_synced")
async def mark_synced(request: MarkSyncedRequest):
    """
    Marca documentos como sincronizados.

    Gabrielle chama após sync bem-sucedido.
    """
    try:
        sync_manager.mark_as_synced(request.point_ids)
        return {
            "status": "success",
            "count": len(request.point_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_staging():
    """
    Remove documentos já sincronizados do staging.
    """
    try:
        count = sync_manager.clear_synced_staging()
        return {
            "status": "success",
            "removed": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_sync_stats():
    """
    Estatísticas de sincronização.
    """
    try:
        stats = sync_manager.get_stats()
        return {
            "status": "success",
            **stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
