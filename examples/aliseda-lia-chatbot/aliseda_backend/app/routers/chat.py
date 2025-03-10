from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.services.simplified_service import SimplifiedLlamaService

router = APIRouter()
llama_service = SimplifiedLlamaService()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat request with the Aliseda Inmobiliaria real estate assistant
    """
    try:
        # Extract property filters from the request
        property_filters = {}
        if request.property_type:
            property_filters["property_type"] = request.property_type
        if request.location:
            property_filters["location"] = request.location
        if request.price_range:
            property_filters["price_range"] = request.price_range
        if request.additional_filters:
            property_filters.update(request.additional_filters)
        
        # Process the chat with the Llama service
        result = await llama_service.chat(request.messages, property_filters)
        
        return ChatResponse(
            response=result["response"],
            property_suggestions=result["property_suggestions"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")
