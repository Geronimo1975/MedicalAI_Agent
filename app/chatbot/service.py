import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from .base import BaseChatModel
from .llama_model import LlamaChatModel
from .huggingface_model import HuggingFaceChatModel
from .openai_model import OpenAIChatModel
from .document_processor import DocumentProcessor
from .risk_assessment import RiskAssessment
from ..models import ChatSession, ChatMessage, db
from ..translations import TranslationService
from .preventive_care import PreventiveCareService
from .triage_system import AdvancedTriageSystem, TriageAssessment

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
    _translator = TranslationService()
    _preventive_care = PreventiveCareService()
    _triage_system = AdvancedTriageSystem()  # Add the new triage system

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

        initial_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content="Hello! I'm here to help assess your symptoms. What symptoms are you experiencing today, and when did they start?",
            language='en'
        )
        db.session.add(initial_message)
        db.session.commit()

        return session

    @staticmethod
    def get_chat_history(session_id: int) -> list:
        """Get the chat history for a session."""
        return ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp).all()

    @staticmethod
    def add_message(session_id: int, role: str, content: str, language: str = 'en') -> ChatMessage:
        """Add a message to the chat history."""
        message = ChatMessage(session_id=session_id, role=role, content=content, language=language)
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
    def get_response(cls, session_id: int, user_message: str, target_lang: str = 'en') -> str:
        """Get a response from the chatbot with integrated risk assessment and triage."""
        source_lang = cls._translator.detect_language(user_message)
        english_message = user_message if source_lang == 'en' else cls._translator.translate_text(user_message, 'en', source_lang)

        cls.add_message(session_id, "user", user_message, language=source_lang)

        # Extract symptoms and get chat history
        symptoms = cls.extract_symptoms(english_message)
        messages = cls.get_conversation_messages(session_id)

        # Extract risk factors and patient info
        patient_factors = cls._extract_patient_factors(messages)
        risk_factors = [factor for factor in patient_factors.keys()]

        # Perform triage assessment
        triage_assessment = cls._triage_system.assess_triage_level(
            symptoms=symptoms,
            severity_scores={symptom: 5.0 for symptom in symptoms},  # Default severity
            risk_factors=risk_factors
        )

        # Update session with triage information
        current_session = ChatSession.query.get(session_id)
        if current_session:
            current_session.triage_level = triage_assessment.level
            current_session.risk_score = triage_assessment.confidence_score * 10
            current_session.symptoms = symptoms
            db.session.commit()

        # Generate response based on triage assessment
        response_parts = []

        # Add immediate emergency warning if needed
        if triage_assessment.level == "emergency":
            response_parts.append(
                "⚠️ EMERGENCY MEDICAL ATTENTION REQUIRED ⚠️\n"
                "Based on your symptoms, you should seek immediate medical care. "
                "Please call emergency services (911) or go to the nearest emergency room immediately."
            )

        # Add triage assessment explanation
        response_parts.append(
            f"\nBased on my assessment (confidence: {triage_assessment.confidence_score:.0%}):"
        )
        for reason in triage_assessment.reasoning:
            response_parts.append(f"- {reason}")

        # Add recommendations
        response_parts.append("\nRecommendations:")
        for rec in triage_assessment.recommendations:
            response_parts.append(f"- {rec}")

        # Add follow-up questions if not emergency
        if triage_assessment.level != "emergency" and triage_assessment.follow_up_questions:
            response_parts.append("\nTo better assess your condition, please answer:")
            for question in triage_assessment.follow_up_questions[:3]:  # Limit to top 3 questions
                response_parts.append(f"- {question}")

        # Combine all parts and translate if needed
        english_response = "\n".join(response_parts)
        final_response = english_response if target_lang == 'en' else cls._translator.translate_text(
            english_response, target_lang, 'en'
        )

        cls.add_message(session_id, "assistant", final_response, language=target_lang)
        return final_response

    @staticmethod
    def extract_symptoms(message_content: str) -> List[str]:
        """Extract symptom IDs from message content using keyword matching."""
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
        factors = {}

        text = " ".join(msg["content"].lower() for msg in messages)

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