import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [messages, setMessages] = useState([
    { text: "Hi, I’m Atlas, your personal AI travel assistant. I can help you plan a trip, recommend destinations, recommend hotels, or answer any travel-related questions.", sender: "bot" },
    { text: "What do you want to do?", sender: "bot" }
  ]);
  const [hotels, setHotels] = useState([]); 
  
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [plan, setPlan] = useState();
  const toggleChat = () => {
    setIsChatOpen(!isChatOpen);
  };
  

  const handleSendMessage = async () => {
    if (input.trim()) {
      // Create a new user message object
      const userMessage = { text: input, sender: "user" };
      
      // Update the messages state with the new user message
      setMessages(prevMessages => [...prevMessages, userMessage]);
      setInput('');  // Clear the input field
      setLoading(true);  // Set loading state to true

      try {
        // Send the user message along with the full conversation history
        const response = await fetch('/chatbot_conversation', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ message: input, messages: [...messages, userMessage] }) 
        });

        const data = await response.json();

        // Append the bot's response to the conversation
        setMessages(prevMessages => [
          ...prevMessages,
          { text: data.response, sender: "bot" }
        ]);
      } catch (error) {
        console.error("Error sending message:", error);
      } finally {
        setLoading(false);  // Stop loading once the response is received
      }
    }
  };
  const handelPlanDesplay = async () => {
    setLoading(true); // Show loading state
    // Function to toggle chat window

    try {
      const response = await fetch('/get_plan', { // Update with the actual backend endpoint
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ messages }) // Sending the conversation history if needed
      });
  
      const data = await response.json();
  
      // Assuming the backend response includes a list of hotels and a travel plan
      if (data.hotels) {
        setHotels(data.hotels); // Store hotel recommendations in state
      }
  
      setPlan(data.plan); // Store the full travel plan
      setMessages(prevMessages => [
        ...prevMessages,
        { text: 'Here is your travel plan!', sender: 'bot' },
      ]);
    } catch (error) {
      console.error('Error fetching plan:', error);
    } finally {
      setLoading(false); // Stop loading
    }
  };



  useEffect(() => {
    // Scroll to the bottom of the messages
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="app">
      <button className="chatbot-toggle-btn" onClick={toggleChat}>
        💬
      </button>
      {isChatOpen && (
        <div className="container">
          <section className="left-section">
            <div className="chat-container scrollable-section">
              <div className="messages">
                {messages.map((message, index) => (
                  <div key={index} className={`message ${message.sender}`}>
                    <div className="message-text">{message.text}</div>
                  </div>
                ))}
                <div ref={messagesEndRef} /> {/* Scroll to this element */}
              </div>
              <div className="input-container">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Start messaging"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !loading) {
                      handleSendMessage();
                    }
                  }}
                />
                <button onClick={handleSendMessage} disabled={loading}>Send</button>
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
};

export default App;
