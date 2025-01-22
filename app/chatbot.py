from openai import OpenAI
from datetime import datetime
import os
from .models import ChatSession, ChatMessage, db

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are a medical triage assistant. Your role is to:
1. Ask relevant questions about the patient's symptoms
2. Assess the urgency of their condition
3. Provide basic health guidance
4. Determine if immediate medical attention is needed

Important guidelines:
- Always maintain a professional and calm tone
- For any life-threatening symptoms, immediately advise seeking emergency care
- Be clear about the limitations of AI medical advice
- Recommend consulting a healthcare provider for proper diagnosis
- Focus on gathering key symptom information
- Avoid making definitive diagnoses

Triage levels:
- urgent: Needs immediate medical attention (emergency)
- non-urgent: Can wait for regular appointment
- seek_immediate_care: Should see doctor within 24 hours

Start by asking about their main symptoms and concerns."""

class ChatbotService:
    @staticmethod
    def create_session(user_id):
        """Create a new chat session for a user."""
        session = ChatSession(user_id=user_id)
        db.session.add(session)
        db.session.commit()
        
        # Add initial message from assistant
        initial_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content="Hello! I'm here to help assess your symptoms. Please describe what's bothering you."
        )
        db.session.add(initial_message)
        db.session.commit()
        
        return session

    @staticmethod
    def get_chat_history(session_id):
        """Get the chat history for a session."""
        return ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp).all()

    @staticmethod
    def add_message(session_id, role, content):
        """Add a message to the chat history."""
        message = ChatMessage(session_id=session_id, role=role, content=content)
        db.session.add(message)
        db.session.commit()
        return message

    @staticmethod
    def get_conversation_messages(session_id):
        """Format chat history for OpenAI API."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        chat_history = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp).all()
        
        for msg in chat_history:
            messages.append({"role": msg.role, "content": msg.content})
            
        return messages

    @classmethod
    def get_response(cls, session_id, user_message):
        """Get a response from the chatbot."""
        # Add user message to history
        cls.add_message(session_id, "user", user_message)
        
        # Get conversation history
        messages = cls.get_conversation_messages(session_id)
        
        try:
            # Get response from OpenAI
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            # Extract response content
            assistant_message = response.choices[0].message.content
            
            # Add assistant response to history
            cls.add_message(session_id, "assistant", assistant_message)
            
            # Check if we should update triage level
            if len(messages) > 5:  # After a few exchanges, try to determine urgency
                triage_response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "Based on the conversation, determine the triage level: 'urgent', 'non-urgent', or 'seek_immediate_care'. Respond with ONLY the triage level, nothing else."
                        },
                        *messages
                    ],
                    temperature=0,
                    max_tokens=20
                )
                
                triage_level = triage_response.choices[0].message.content.strip().lower()
                if triage_level in ['urgent', 'non-urgent', 'seek_immediate_care']:
                    session = ChatSession.query.get(session_id)
                    session.triage_level = triage_level
                    db.session.commit()
            
            return assistant_message
            
        except Exception as e:
            error_message = "I apologize, but I'm having trouble processing your request. Please try again or seek immediate medical attention if you're experiencing severe symptoms."
            cls.add_message(session_id, "assistant", error_message)
            return error_message

    @staticmethod
    def end_session(session_id):
        """End a chat session and generate a summary."""
        session = ChatSession.query.get(session_id)
        if session and not session.ended_at:
            messages = ChatbotService.get_conversation_messages(session_id)
            
            try:
                # Generate session summary
                summary_response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "Summarize the medical conversation and key points discussed. Be concise but include important symptoms and recommendations."
                        },
                        *messages
                    ],
                    temperature=0.7,
                    max_tokens=200
                )
                
                session.summary = summary_response.choices[0].message.content
                session.ended_at = datetime.utcnow()
                db.session.commit()
                
                return session.summary
                
            except Exception as e:
                session.ended_at = datetime.utcnow()
                session.summary = "Session ended. Summary generation failed."
                db.session.commit()
                return session.summary
