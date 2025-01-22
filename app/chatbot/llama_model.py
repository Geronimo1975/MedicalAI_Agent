import torch
from transformers import pipeline
from .base import BaseChatModel

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
