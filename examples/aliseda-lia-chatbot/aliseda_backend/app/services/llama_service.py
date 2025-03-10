import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient

from app.models.chat import ChatMessage

# Load environment variables
load_dotenv()

# Llama Stack configuration
LLAMA_STACK_HOST = os.getenv("LLAMA_STACK_HOST", "localhost")
LLAMA_STACK_PORT = int(os.getenv("LLAMA_STACK_PORT", "5001"))
LLAMA_MODEL_NAME = os.getenv("LLAMA_MODEL_NAME", "meta-llama/Llama-3.2-3B-Instruct")

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


class LlamaService:
    def __init__(self):
        self.client = LlamaStackClient(host=LLAMA_STACK_HOST, port=LLAMA_STACK_PORT)
        
    async def search_properties(self, query: str) -> Dict[str, Any]:
        """
        Custom tool to search for properties based on query
        """
        # In a real implementation, this would query a database or external API
        # For demo purposes, we'll filter the sample data based on the query
        filtered_properties = []
        query_lower = query.lower()
        
        for prop in SAMPLE_PROPERTIES:
            if (query_lower in prop["title"].lower() or 
                query_lower in prop["location"].lower() or 
                query_lower in prop["type"].lower() or 
                query_lower in prop["description"].lower()):
                filtered_properties.append(prop)
                
        return {
            "query": query,
            "results": filtered_properties,
            "count": len(filtered_properties)
        }
    
    async def create_agent(self) -> Agent:
        """
        Create a Llama Stack agent with custom real estate tools
        """
        # Create a custom property search tool
        property_search_tool = CustomTool(
            name="property_search",
            description="Search for properties based on criteria like location, type, price range",
            function=self.search_properties,
            parameters={
                "query": {
                    "type": "string",
                    "description": "The search query for properties (e.g., 'apartments in Madrid', 'villas with pool')"
                }
            }
        )
        
        # Create agent configuration with real estate specific system prompt
        agent_config = AgentConfig(
            system_prompt="""You are a helpful real estate assistant for Aliseda Inmobiliaria, a leading real estate company in Spain.
            Your goal is to help users find properties that match their needs and answer questions about real estate in Spain.
            You can search for properties using the property_search tool.
            Always be professional, helpful, and provide detailed information about properties when available.
            If you don't know something, admit it and offer to help in other ways.
            """,
            model=LLAMA_MODEL_NAME,
            tools=[property_search_tool]
        )
        
        # Create the agent
        agent = await self.client.agents.create(config=agent_config)
        return agent
    
    async def chat(self, messages: List[ChatMessage], property_filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a chat conversation with the real estate agent
        """
        # Create agent if not already created
        agent = await self.create_agent()
        
        # Format messages for the agent
        formatted_messages = []
        for msg in messages:
            if msg.role == "user":
                # If there are property filters, add them to the user's message
                content = msg.content
                if property_filters and msg is messages[-1]:  # Only add to the last user message
                    filter_text = "\n\nProperty filters:"
                    for key, value in property_filters.items():
                        if value:
                            filter_text += f"\n- {key}: {value}"
                    content += filter_text
                
                formatted_messages.append({"role": "user", "content": content})
            else:
                formatted_messages.append({"role": msg.role, "content": msg.content})
        
        # Create a new turn with the formatted messages
        turn = await agent.create_turn(messages=formatted_messages)
        
        # Get the response
        response_text = ""
        property_suggestions = []
        
        async for event in turn.stream():
            if event.type == "turn_complete":
                response_text = event.payload.messages[-1].content
                
                # Check if any property search tool was called
                for step in event.payload.steps:
                    if step.type == "tool_execution" and step.tool_name == "property_search":
                        if hasattr(step, 'response') and step.response:
                            try:
                                # Extract property suggestions from tool response
                                if isinstance(step.response, dict) and "results" in step.response:
                                    property_suggestions = step.response["results"]
                            except Exception as e:
                                print(f"Error extracting property suggestions: {e}")
        
        return {
            "response": response_text,
            "property_suggestions": property_suggestions
        }
