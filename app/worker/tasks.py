import asyncio
import os
import logging
import uuid
from app.config.celery_app import celery_app
from app.services.ingestion_service import IngestionService, _task_store, IngestionTask, IngestionStatus
from app.config.settings import get_settings
from app.providers.qdrant_vector_store import QdrantVectorStore

logger = logging.getLogger(__name__)

# Reinitialize components for the worker context
settings = get_settings()
qdrant_store = QdrantVectorStore(settings)
ingestion_service = IngestionService(vector_store=qdrant_store)

@celery_app.task(bind=True, name="process_document_ingestion")
def process_document_ingestion(self, task_id: str, document_id: str, filename: str, temp_filepath: str):
    """
    Background Celery task to process document ingestion.
    """
    logger.info(f"Starting Celery task for ingestion: {task_id}")
    
    # Re-create the task in the worker's local memory store (for status checks if routed to same worker)
    # Note: In production, `_task_store` should be Redis so API can read the progress.
    # For now, we update the local store and rely on the synchronous result or logs.
    task = IngestionTask(
        task_id=task_id,
        document_id=document_id,
        filename=filename,
        status=IngestionStatus.PROCESSING
    )
    _task_store[task_id] = task
    
    try:
        # Read the file from the temporary path
        with open(temp_filepath, "rb") as f:
            content = f.read()
            
        # Run the async ingestion processing synchronously in this thread
        asyncio.run(ingestion_service._process_ingestion(task, content))
        
        # After successful ingestion, invalidate cache (update knowledge base version)
        from app.providers.redis_provider import redis_provider
        asyncio.run(redis_provider.increment_knowledge_base_version())
        
        return {
            "task_id": task_id,
            "status": task.status.value,
            "chunks_processed": task.chunks_processed
        }
    except Exception as e:
        logger.error(f"Celery task failed for {task_id}: {e}")
        task.status = IngestionStatus.FAILED
        task.error = str(e)
        raise e
    finally:
        # Cleanup temp file
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
                logger.info(f"Deleted temp file {temp_filepath}")
            except Exception as cleanup_err:
                logger.warning(f"Failed to delete temp file {temp_filepath}: {cleanup_err}")
