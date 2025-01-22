from openai import OpenAI
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from datetime import datetime
import os
import torch
from abc import ABC, abstractmethod
from .models import ChatSession, ChatMessage, db

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

class BaseChatModel(ABC):
    @abstractmethod
    def generate_response(self, messages):
        pass

    @abstractmethod
    def generate_summary(self, messages):
        pass

    @abstractmethod
    def determine_triage_level(self, messages):
        pass

class OpenAIChatModel(BaseChatModel):
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = "gpt-4"

    def generate_response(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content

    def generate_summary(self, messages):
        summary_response = self.client.chat.completions.create(
            model=self.model,
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
        return summary_response.choices[0].message.content

    def determine_triage_level(self, messages):
        triage_response = self.client.chat.completions.create(
            model=self.model,
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
        return triage_response.choices[0].message.content.strip().lower()

class HuggingFaceChatModel(BaseChatModel):
    def __init__(self):
        model_name = "microsoft/BioGPT-Large"  # Medical domain-specific model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        if torch.cuda.is_available():
            self.model = self.model.cuda()
        self.model.eval()

    def _format_messages(self, messages):
        formatted_text = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            formatted_text += f"{role}: {content}\n"
        return formatted_text

    def generate_response(self, messages):
        input_text = self._format_messages(messages)
        inputs = self.tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
        if torch.cuda.is_available():
            inputs = inputs.to("cuda")

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=200,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response.split("assistant:")[-1].strip()

    def generate_summary(self, messages):
        summary_prompt = "Summarize the following medical conversation:\n" + self._format_messages(messages)
        inputs = self.tokenizer(summary_prompt, return_tensors="pt", max_length=512, truncation=True)
        if torch.cuda.is_available():
            inputs = inputs.to("cuda")

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=200,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True
            )

        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    def determine_triage_level(self, messages):
        triage_prompt = "Based on this medical conversation, respond with only one of these triage levels: urgent, non-urgent, or seek_immediate_care.\n" + self._format_messages(messages)
        inputs = self.tokenizer(triage_prompt, return_tensors="pt", max_length=512, truncation=True)
        if torch.cuda.is_available():
            inputs = inputs.to("cuda")

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=20,
                num_return_sequences=1,
                temperature=0.1,
                do_sample=True
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True).lower()
        if "urgent" in response:
            return "urgent"
        elif "seek_immediate_care" in response:
            return "seek_immediate_care"
        return "non-urgent"

class LlamaChatModel(BaseChatModel):
    def __init__(self):
        model_name = "meta-llama/Llama-2-7b-chat-hf"
        self.pipeline = pipeline(
            "text-generation",
            model=model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )

    def _format_messages(self, messages):
        formatted_text = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            formatted_text += f"<{role}>{content}</{role}>"
        return formatted_text

    def generate_response(self, messages):
        prompt = self._format_messages(messages)
        response = self.pipeline(
            prompt,
            max_length=500,
            temperature=0.7,
            num_return_sequences=1
        )[0]["generated_text"]

        return response.split("<assistant>")[-1].split("</assistant>")[0].strip()

    def generate_summary(self, messages):
        summary_prompt = "<system>Summarize the medical conversation and key points discussed.</system>" + self._format_messages(messages)
        response = self.pipeline(
            summary_prompt,
            max_length=200,
            temperature=0.7,
            num_return_sequences=1
        )[0]["generated_text"]

        return response.split("<assistant>")[-1].split("</assistant>")[0].strip()

    def determine_triage_level(self, messages):
        triage_prompt = "<system>Based on the conversation, determine the triage level. Respond with only: urgent, non-urgent, or seek_immediate_care.</system>" + self._format_messages(messages)
        response = self.pipeline(
            triage_prompt,
            max_length=20,
            temperature=0.1,
            num_return_sequences=1
        )[0]["generated_text"].lower()

        if "urgent" in response:
            return "urgent"
        elif "seek_immediate_care" in response:
            return "seek_immediate_care"
        return "non-urgent"

class ChatbotService:
    _model = None
    _model_type = os.environ.get("CHATBOT_MODEL", "openai")  # openai, huggingface, or llama

    @classmethod
    def get_model(cls):
        if cls._model is None:
            if cls._model_type == "huggingface":
                cls._model = HuggingFaceChatModel()
            elif cls._model_type == "llama":
                cls._model = LlamaChatModel()
            else:
                cls._model = OpenAIChatModel()
        return cls._model

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
        """Format chat history for model input."""
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
            # Get response from the model
            model = cls.get_model()
            assistant_message = model.generate_response(messages)

            # Add assistant response to history
            cls.add_message(session_id, "assistant", assistant_message)

            # Check if we should update triage level
            if len(messages) > 5:  # After a few exchanges, try to determine urgency
                triage_level = model.determine_triage_level(messages)
                if triage_level in ['urgent', 'non-urgent', 'seek_immediate_care']:
                    session = ChatSession.query.get(session_id)
                    session.triage_level = triage_level
                    db.session.commit()

            return assistant_message

        except Exception as e:
            error_message = "I apologize, but I'm having trouble processing your request. Please try again or seek immediate medical attention if you're experiencing severe symptoms."
            cls.add_message(session_id, "assistant", error_message)
            return error_message

    @classmethod
    def end_session(cls, session_id):
        """End a chat session and generate a summary."""
        session = ChatSession.query.get(session_id)
        if session and not session.ended_at:
            messages = ChatbotService.get_conversation_messages(session_id)

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