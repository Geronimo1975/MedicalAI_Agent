import os
from datetime import datetime
from typing import List, Dict
from .base import BaseChatModel
from .llama_model import LlamaChatModel
from .huggingface_model import HuggingFaceChatModel
from .openai_model import OpenAIChatModel
from .document_processor import DocumentProcessor
from .risk_assessment import RiskAssessment
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
    _model_type = os.environ.get("CHATBOT_MODEL", "openai")
    _doc_processor = DocumentProcessor()
    _risk_assessor = RiskAssessment()

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
        """Get a response from the chatbot with integrated risk assessment."""
        # Add user message to history
        cls.add_message(session_id, "user", user_message)

        # Extract symptoms from user message
        symptoms = cls.extract_symptoms(user_message)

        # Get conversation history and relevant context
        context = cls._doc_processor.get_relevant_context(user_message)
        messages = cls.get_conversation_messages(session_id)

        # If symptoms were detected, perform risk assessment
        risk_assessment_info = ""
        if symptoms:
            # Extract patient factors from conversation history
            patient_factors = cls._extract_patient_factors(messages)

            # Calculate risk score
            risk_scores = cls._risk_assessor.calculate_risk_score(symptoms, patient_factors)

            # Get suggested symptoms to check
            suggested_symptoms = cls._risk_assessor.suggest_additional_symptoms(symptoms)

            # Get recommendations
            recommendations = cls._risk_assessor.get_severity_recommendations(risk_scores['total_risk'])

            # Format risk assessment information
            risk_assessment_info = f"\n\nRisk Assessment:\n" \
                                 f"- Overall Risk Score: {risk_scores['total_risk']}/10\n" \
                                 f"- Severity Score: {risk_scores['severity_score']}\n" \
                                 f"- Symptom Correlation: {risk_scores['correlation_score']}\n" \
                                 f"\nRecommendations:\n{recommendations}\n"

            if suggested_symptoms:
                risk_assessment_info += f"\nSuggested symptoms to check:\n" \
                                      f"- {', '.join(suggested_symptoms)}"

        # Add context and risk assessment to the last user message
        messages[-1]["content"] = (
            f"Context from medical documentation:\n{context}\n\n"
            f"User message: {user_message}\n"
            f"{risk_assessment_info}"
        )

        try:
            # Get response from the model
            model = cls.get_model()
            assistant_message = model.generate_response(messages)

            # Add assistant response to history
            cls.add_message(session_id, "assistant", assistant_message)

            # Update triage level based on risk assessment
            if symptoms:
                risk_score = risk_scores['total_risk']
                triage_level = (
                    "urgent" if risk_score >= 8.0
                    else "seek_immediate_care" if risk_score >= 6.0
                    else "non-urgent"
                )

                session = ChatSession.query.get(session_id)
                session.triage_level = triage_level
                db.session.commit()

            return assistant_message

        except Exception as e:
            error_message = "I apologize, but I'm having trouble processing your request. " \
                          "If you're experiencing severe or life-threatening symptoms, " \
                          "please seek immediate medical attention by calling emergency " \
                          "services or going to the nearest emergency room."
            cls.add_message(session_id, "assistant", error_message)
            return error_message

    @staticmethod
    def extract_symptoms(message_content: str) -> List[str]:
        """Extract symptom IDs from message content using keyword matching."""
        # This is a simple implementation - in production, you'd want to use
        # more sophisticated NLP techniques
        symptoms = []
        symptom_keywords = {
            'fever': ['fever', 'high temperature', 'feeling hot'],
            'shortness_of_breath': ['shortness of breath', 'difficulty breathing', 'breathless'],
            'chest_pain': ['chest pain', 'chest pressure', 'heart pain'],
            'headache': ['headache', 'head pain', 'migraine'],
            'fatigue': ['fatigue', 'tired', 'exhausted', 'no energy'],
            'nausea': ['nausea', 'feeling sick', 'queasy']
        }

        message_lower = message_content.lower()
        for symptom_id, keywords in symptom_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                symptoms.append(symptom_id)

        return symptoms

    @staticmethod
    def _extract_patient_factors(messages: List[Dict[str, str]]) -> Dict[str, float]:
        """Extract patient risk factors from conversation history."""
        # This is a simple implementation - in production, you'd want to use
        # more sophisticated NLP techniques
        factors = {}

        # Combine all messages into one text for analysis
        text = " ".join(msg["content"].lower() for msg in messages)

        # Check for various risk factors
        if any(age in text for age in ['elderly', 'senior', 'over 65', '65+']):
            factors['age_65_plus'] = 1.0

        if any(condition in text for condition in ['diabetes', 'diabetic']):
            factors['diabetes'] = 1.0

        if any(condition in text for condition in ['asthma', 'asthmatic']):
            factors['asthma'] = 1.0

        if 'smoke' in text or 'smoking' in text:
            factors['smoking'] = 1.0

        if any(condition in text for condition in ['obese', 'obesity', 'overweight']):
            factors['obesity'] = 1.0

        if 'pregnant' in text or 'pregnancy' in text:
            factors['pregnancy'] = 1.0

        return factors

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