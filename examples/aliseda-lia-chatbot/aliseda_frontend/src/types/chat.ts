export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface Property {
  id: string;
  title: string;
  type: string;
  location: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  area: number;
  description: string;
  image_url: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  property_type?: string;
  location?: string;
  price_range?: string;
  additional_filters?: Record<string, any>;
}

export interface ChatResponse {
  response: string;
  property_suggestions?: Property[];
}
