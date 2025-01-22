import os
from datetime import datetime
from .base import BaseChatModel
from .llama_model import LlamaChatModel
from .huggingface_model import HuggingFaceChatModel
from .openai_model import OpenAIChatModel
from .document_processor import DocumentProcessor
from ..models import ChatSession, ChatMessage, db

SYSTEM_PROMPT = """You are an advanced medical pre-screening assistant. Your role is to:

1. Systematically assess patient symptoms through structured questions
2. Identify red flag symptoms that require immediate attention
3. Evaluate symptom severity and duration
4. Determine appropriate triage level based on medical guidelines

Assessment Guidelines:
- Start with open-ended questions about main symptoms
- Follow up with specific questions about:
  * Symptom duration and progression
  * Pain levels (1-10 scale if applicable)
  * Associated symptoms
  * Recent medical history
  * Existing conditions and medications
  * Vital signs if known (temperature, blood pressure, etc.)

Red Flag Symptoms (requiring immediate attention):
- Chest pain or pressure
- Difficulty breathing
- Severe abdominal pain
- Sudden severe headache
- Signs of stroke (FAST: Face drooping, Arm weakness, Speech difficulty, Time to call emergency)
- Loss of consciousness
- Severe allergic reactions

Triage Levels and Response:
1. EMERGENCY (urgent):
   - Life-threatening conditions
   - Severe trauma
   - Requires immediate medical attention

2. URGENT (seek_immediate_care):
   - Conditions requiring treatment within 24 hours
   - Significant discomfort or concern
   - May worsen if not treated soon

3. NON-URGENT (routine):
   - Chronic or minor conditions
   - Can wait for regular appointment
   - Manageable symptoms

Important Notes:
- Always maintain a professional and calm tone
- Be thorough but efficient in questioning
- Clearly explain your triage recommendations
- Emphasize that this is pre-screening only and not a diagnosis
- Recommend emergency services for any life-threatening symptoms

Begin by asking: "What symptoms are you experiencing today, and when did they start?"
"""

class ChatbotService:
    _model = None
    _model_type = os.environ.get("CHATBOT_MODEL", "openai")  # openai, huggingface, or llama
    _doc_processor = DocumentProcessor()

    @classmethod
    def get_model(cls) -> BaseChatModel:
        if cls._model is None:
            if cls._model_type == "huggingface":
                cls._model = HuggingFaceChatModel()
            elif cls._model_type == "llama":
                cls._model = LlamaChatModel()
            else:
                cls._model = OpenAIChatModel()
        return cls._model

    @staticmethod
    def create_session(user_id: int) -> ChatSession:
        """Create a new chat session for a user."""
        session = ChatSession(user_id=user_id)
        db.session.add(session)
        db.session.commit()

        # Add initial message from assistant
        initial_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content="Hello! I'm here to help assess your symptoms. What symptoms are you experiencing today, and when did they start?"
        )
        db.session.add(initial_message)
        db.session.commit()

        return session

    @staticmethod
    def get_chat_history(session_id: int) -> list:
        """Get the chat history for a session."""
        return ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp).all()

    @staticmethod
    def add_message(session_id: int, role: str, content: str) -> ChatMessage:
        """Add a message to the chat history."""
        message = ChatMessage(session_id=session_id, role=role, content=content)
        db.session.add(message)
        db.session.commit()
        return message

    @staticmethod
    def get_conversation_messages(session_id: int) -> list:
        """Format chat history for model input."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        chat_history = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp).all()

        for msg in chat_history:
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    @classmethod
    def get_response(cls, session_id: int, user_message: str) -> str:
        """Get a response from the chatbot."""
        # Add user message to history
        cls.add_message(session_id, "user", user_message)

        # Get relevant context from medical documentation
        context = cls._doc_processor.get_relevant_context(user_message)

        # Get conversation history
        messages = cls.get_conversation_messages(session_id)

        # Add context to the last user message
        messages[-1]["content"] = f"Context from medical documentation:\n{context}\n\nUser message: {user_message}"

        try:
            # Get response from the model
            model = cls.get_model()
            assistant_message = model.generate_response(messages)

            # Add assistant response to history
            cls.add_message(session_id, "assistant", assistant_message)

            # Update triage level after each exchange
            triage_level = model.determine_triage_level(messages)
            if triage_level in ['urgent', 'non-urgent', 'seek_immediate_care']:
                session = ChatSession.query.get(session_id)
                session.triage_level = triage_level
                db.session.commit()

            return assistant_message

        except Exception as e:
            error_message = "I apologize, but I'm having trouble processing your request. If you're experiencing severe or life-threatening symptoms, please seek immediate medical attention by calling emergency services or going to the nearest emergency room."
            cls.add_message(session_id, "assistant", error_message)
            return error_message

    @classmethod
    def end_session(cls, session_id: int) -> str:
        """End a chat session and generate a summary."""
        session = ChatSession.query.get(session_id)
        if session and not session.ended_at:
            messages = cls.get_conversation_messages(session_id)

            try:
                # Generate session summary using the current model
                model = cls.get_model()
                summary = model.generate_summary(messages)

                session.summary = summary
                session.ended_at = datetime.utcnow()
                db.session.commit()

                return summary

            except Exception as e:
                session.ended_at = datetime.utcnow()
                session.summary = "Session ended. Summary generation failed."
                db.session.commit()
                return session.summary

        return "Session already ended or not found."