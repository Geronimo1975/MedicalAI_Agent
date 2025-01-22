import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from .base import BaseChatModel

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
