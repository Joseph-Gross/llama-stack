import { useState } from 'react';
import { Building, MessageSquare } from 'lucide-react';
import { ChatMessage as ChatMessageComponent } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { PropertyList } from './components/PropertyList';
import { PropertyFilters } from './components/PropertyFilters';
import { chatService } from './services/api';
import { ChatMessage, Property } from './types/chat';

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: 'Hello! I\'m the Aliseda Inmobiliaria real estate assistant. How can I help you find your perfect property today?'
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [properties, setProperties] = useState<Property[]>([]);
  const [filters, setFilters] = useState({
    propertyType: '',
    location: '',
    priceRange: ''
  });

  const handleSendMessage = async (content: string) => {
    // Add user message to chat
    const userMessage: ChatMessage = { role: 'user', content };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Prepare request with messages and filters
      const request = {
        messages: [...messages, userMessage],
        property_type: filters.propertyType || undefined,
        location: filters.location || undefined,
        price_range: filters.priceRange || undefined
      };

      // Send request to API
      const response = await chatService.sendMessage(request);

      // Add assistant response to chat
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: response.response }
      ]);

      // Update property suggestions
      if (response.property_suggestions && response.property_suggestions.length > 0) {
        setProperties(response.property_suggestions);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'I\'m sorry, I encountered an error. Please try again later.'
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyFilters = (newFilters: {
    propertyType: string;
    location: string;
    priceRange: string;
  }) => {
    setFilters(newFilters);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b sticky top-0 z-10 bg-background">
        <div className="container mx-auto py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Building className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold">Aliseda Inmobiliaria</h1>
          </div>
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            <span className="font-medium">LIA Chatbot</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto py-6 px-4 md:px-6 grid md:grid-cols-[1fr_350px] gap-6">
        {/* Chat Section */}
        <div className="flex flex-col h-[calc(100vh-200px)]">
          <div className="flex-1 overflow-y-auto p-4 border rounded-lg mb-4">
            {messages.map((message, index) => (
              <ChatMessageComponent key={index} message={message} />
            ))}
            {isLoading && (
              <div className="flex justify-start mb-4">
                <div className="bg-muted text-muted-foreground max-w-[80%] rounded-lg px-4 py-2">
                  <p className="text-sm">Thinking...</p>
                </div>
              </div>
            )}
          </div>
          <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <PropertyFilters onApplyFilters={handleApplyFilters} />
          <PropertyList properties={properties} />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t py-4">
        <div className="container mx-auto text-center text-sm text-muted-foreground">
          © {new Date().getFullYear()} Aliseda Inmobiliaria. All rights reserved.
        </div>
      </footer>
    </div>
  );
}

export default App;
