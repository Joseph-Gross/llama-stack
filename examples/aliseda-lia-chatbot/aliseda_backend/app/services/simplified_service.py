import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from app.models.chat import ChatMessage

# Load environment variables
load_dotenv()

# Sample real estate data for demonstration
SAMPLE_PROPERTIES = [
    {
        "id": "prop1",
        "title": "Luxury Apartment in Madrid",
        "type": "apartment",
        "location": "Madrid",
        "price": 350000,
        "bedrooms": 3,
        "bathrooms": 2,
        "area": 120,
        "description": "Beautiful luxury apartment in the heart of Madrid with modern amenities.",
        "image_url": "https://example.com/images/prop1.jpg"
    },
    {
        "id": "prop2",
        "title": "Beachfront Villa in Barcelona",
        "type": "villa",
        "location": "Barcelona",
        "price": 850000,
        "bedrooms": 5,
        "bathrooms": 4,
        "area": 280,
        "description": "Stunning beachfront villa with panoramic sea views and private pool.",
        "image_url": "https://example.com/images/prop2.jpg"
    },
    {
        "id": "prop3",
        "title": "Townhouse in Valencia",
        "type": "townhouse",
        "location": "Valencia",
        "price": 220000,
        "bedrooms": 2,
        "bathrooms": 1,
        "area": 90,
        "description": "Charming townhouse in a quiet neighborhood of Valencia with garden.",
        "image_url": "https://example.com/images/prop3.jpg"
    }
]

class SimplifiedLlamaService:
    """
    A simplified service that simulates LLM responses for the real estate chatbot
    This is used for testing and development until we can properly integrate with Llama Stack
    """
    
    def __init__(self):
        pass
        
    async def search_properties(self, query: str) -> Dict[str, Any]:
        """
        Custom tool to search for properties based on query
        """
        # Filter the sample data based on the query
        filtered_properties = []
        query_lower = query.lower()
        
        # Split query into keywords for better matching
        keywords = query_lower.split()
        
        for prop in SAMPLE_PROPERTIES:
            # Check if any keyword matches any property field
            for keyword in keywords:
                if (keyword in prop["title"].lower() or 
                    keyword in prop["location"].lower() or 
                    keyword in prop["type"].lower() or 
                    keyword in prop["description"].lower()):
                    filtered_properties.append(prop)
                    break  # Add property once if any keyword matches
                
        return {
            "query": query,
            "results": filtered_properties,
            "count": len(filtered_properties)
        }
    
    async def chat(self, messages: List[ChatMessage], property_filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a chat conversation with a simulated real estate agent
        """
        # Get the last user message
        last_message = next((m for m in reversed(messages) if m.role == "user"), None)
        
        if not last_message:
            return {
                "response": "I'm sorry, I didn't receive a message to respond to.",
                "property_suggestions": []
            }
        
        # Extract query from the last message
        query = last_message.content.lower()
        
        # Add property filters to the query if available
        if property_filters:
            for key, value in property_filters.items():
                if value:
                    query += f" {value}"
        
        # Search for properties based on the query
        search_results = await self.search_properties(query)
        
        # Generate a response based on the search results
        if search_results["count"] > 0:
            response = f"I found {search_results['count']} properties that match your criteria. "
            
            if "madrid" in query or "barcelona" in query or "valencia" in query:
                response += f"These are great options in the area you're interested in. "
            
            if "apartment" in query:
                response += "The apartments I found have modern amenities and great locations. "
            elif "villa" in query:
                response += "The villas I found offer spacious living and luxury features. "
            elif "townhouse" in query:
                response += "The townhouses I found provide a good balance of space and value. "
            
            response += "Would you like more details about any of these properties?"
        else:
            response = "I couldn't find any properties matching your criteria. Would you like to try a different search or expand your criteria?"
        
        return {
            "response": response,
            "property_suggestions": search_results["results"]
        }
