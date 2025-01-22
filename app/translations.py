from flask_babel import Babel
from deep_translator import GoogleTranslator
from langdetect import detect
from typing import Dict, Optional
import json
import os

class TranslationService:
    def __init__(self, app=None):
        self.babel = Babel()
        if app is not None:
            self.init_app(app)
        
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'zh': 'Chinese',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese'
        }
        
        self._load_medical_terms()
    
    def init_app(self, app):
        self.babel.init_app(app)
        
    def _load_medical_terms(self):
        """Load medical terminology translations from JSON files."""
        self.medical_terms = {}
        translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
        
        for lang in self.supported_languages:
            try:
                with open(os.path.join(translations_dir, f'medical_terms_{lang}.json'), 'r', encoding='utf-8') as f:
                    self.medical_terms[lang] = json.load(f)
            except FileNotFoundError:
                self.medical_terms[lang] = {}
    
    def detect_language(self, text: str) -> str:
        """Detect the language of the input text."""
        try:
            return detect(text)
        except:
            return 'en'  # Default to English if detection fails
    
    def translate_text(self, text: str, target_lang: str, source_lang: Optional[str] = None) -> str:
        """Translate text while preserving medical terminology."""
        if not source_lang:
            source_lang = self.detect_language(text)
            
        if source_lang == target_lang:
            return text
            
        try:
            # First, protect medical terms by tokenizing them
            protected_text = self._protect_medical_terms(text, source_lang)
            
            # Translate the text
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            translated_text = translator.translate(protected_text)
            
            # Restore medical terms in the target language
            final_text = self._restore_medical_terms(translated_text, target_lang)
            
            return final_text
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text  # Return original text if translation fails
    
    def _protect_medical_terms(self, text: str, source_lang: str) -> str:
        """Replace medical terms with placeholders to protect them during translation."""
        protected_text = text
        terms = self.medical_terms.get(source_lang, {})
        
        for term, _ in terms.items():
            placeholder = f"__MEDICAL_TERM_{hash(term)}__"
            protected_text = protected_text.replace(term, placeholder)
            
        return protected_text
    
    def _restore_medical_terms(self, text: str, target_lang: str) -> str:
        """Restore medical terms in the target language."""
        restored_text = text
        source_terms = self.medical_terms.get('en', {})  # Use English as source
        target_terms = self.medical_terms.get(target_lang, {})
        
        for term in source_terms:
            placeholder = f"__MEDICAL_TERM_{hash(term)}__"
            target_term = target_terms.get(term, term)  # Fall back to English if no translation
            restored_text = restored_text.replace(placeholder, target_term)
            
        return restored_text
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Return a dictionary of supported languages."""
        return self.supported_languages.copy()
