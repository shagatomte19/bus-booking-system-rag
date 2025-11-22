import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..query_router import get_query_router, QueryRouter
from ..schemas import ProviderQuestionRequest, ProviderQuestionResponse

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.post("/ask", response_model=ProviderQuestionResponse)
def ask_provider_question(
    request: ProviderQuestionRequest,
    db: Session = Depends(get_db),
    query_router: QueryRouter = Depends(get_query_router)
):
    """
    Ask any question - about routes, prices, or provider information
    The system will automatically detect the query type and respond appropriately
    """
    try:
        result = query_router.answer_question(request.question, db)
        
        return ProviderQuestionResponse(
            answer=result["answer"],
            sources=result.get("sources", [])
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )
    
# @router.post("/reindex")
# def reindex_documents(rag: RAGPipeline = Depends(get_rag_pipeline)):
#     """
#     Manually reindex provider documents
#     """
#     try:
#         providers_dir = "/app/data/providers"
        
#         # Check if directory exists
#         if not os.path.exists(providers_dir):
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"Providers directory not found: {providers_dir}"
#             )
        
#         # List files in directory
#         files = os.listdir(providers_dir)
#         txt_files = [f for f in files if f.endswith('.txt')]
        
#         if not txt_files:
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"No .txt files found in {providers_dir}. Found: {files}"
#             )
        
#         # Clear existing documents
#         try:
#             rag.chroma_client.delete_collection("bus_providers")
#             rag.collection = rag.chroma_client.get_or_create_collection(
#                 name="bus_providers",
#                 metadata={"description": "Bus provider information and policies"}
#             )
#         except:
#             pass
        
#         # Reindex
#         rag.index_documents(providers_dir)
        
#         count = rag.collection.count()
        
#         return {
#             "message": "Reindexing completed",
#             "document_count": count,
#             "txt_files_found": txt_files
#         }
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error reindexing: {str(e)}"
#         )