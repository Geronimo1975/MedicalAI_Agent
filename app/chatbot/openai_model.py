from openai import OpenAI
import os
from .base import BaseChatModel

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
