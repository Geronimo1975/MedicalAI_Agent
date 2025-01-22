from flask_babel import Babel
from deep_translator import GoogleTranslator
from langdetect import detect
from typing import Dict, Optional, List
import json
import os
from functools import lru_cache
from datetime import datetime, timedelta

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

        self.medical_terms = {}
        self.translations_cache = {}
        self.cache_expiry = timedelta(hours=24)
        self._load_medical_terms()

    def init_app(self, app):
        """Initialize the Flask application with Babel support."""
        self.babel.init_app(app)

    def _load_medical_terms(self):
        """Load medical terminology translations from JSON files."""
        translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
        os.makedirs(translations_dir, exist_ok=True)

        for lang in self.supported_languages:
            try:
                file_path = os.path.join(translations_dir, f'medical_terms_{lang}.json')
                if not os.path.exists(file_path):
                    # Create empty medical terms file if it doesn't exist
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump({}, f, ensure_ascii=False, indent=2)

                with open(file_path, 'r', encoding='utf-8') as f:
                    self.medical_terms[lang] = json.load(f)
            except Exception as e:
                print(f"Error loading medical terms for {lang}: {str(e)}")
                self.medical_terms[lang] = {}

    @lru_cache(maxsize=1000)
    def detect_language(self, text: str) -> str:
        """Detect the language of the input text with caching."""
        try:
            return detect(text)
        except:
            return 'en'  # Default to English if detection fails

    def add_medical_term(self, term: str, translations: Dict[str, str]) -> bool:
        """Add a new medical term with its translations to all supported languages."""
        try:
            for lang, translation in translations.items():
                if lang in self.supported_languages:
                    if lang not in self.medical_terms:
                        self.medical_terms[lang] = {}
                    self.medical_terms[lang][term] = translation

            # Save updated terms to files
            for lang in translations.keys():
                if lang in self.supported_languages:
                    file_path = os.path.join(
                        os.path.dirname(__file__),
                        'translations',
                        f'medical_terms_{lang}.json'
                    )
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.medical_terms[lang], f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error adding medical term: {str(e)}")
            return False

    def translate_text(self, text: str, target_lang: str, source_lang: Optional[str] = None) -> str:
        """Translate text while preserving medical terminology."""
        if not source_lang:
            source_lang = self.detect_language(text)

        if source_lang == target_lang:
            return text

        cache_key = f"{text}:{source_lang}:{target_lang}"
        if cache_key in self.translations_cache:
            cached_translation, timestamp = self.translations_cache[cache_key]
            if timestamp + self.cache_expiry > datetime.now():
                return cached_translation

        try:
            # First, protect medical terms by tokenizing them
            protected_text = self._protect_medical_terms(text, source_lang)

            # Translate the text
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            translated_text = translator.translate(protected_text)

            # Restore medical terms in the target language
            final_text = self._restore_medical_terms(translated_text, target_lang)

            # Cache the translation
            self.translations_cache[cache_key] = (final_text, datetime.now())

            return final_text
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text  # Return original text if translation fails

    def _protect_medical_terms(self, text: str, source_lang: str) -> str:
        """Replace medical terms with placeholders to protect them during translation."""
        protected_text = text
        terms = self.medical_terms.get(source_lang, {})

        for term in sorted(terms.keys(), key=len, reverse=True):  # Process longer terms first
            placeholder = f"__MEDICAL_TERM_{hash(term)}__"
            protected_text = protected_text.replace(term, placeholder)

        return protected_text

    def _restore_medical_terms(self, text: str, target_lang: str) -> str:
        """Restore medical terms in the target language."""
        restored_text = text
        source_terms = self.medical_terms.get('en', {})  # Use English as source
        target_terms = self.medical_terms.get(target_lang, {})

        for term in sorted(source_terms.keys(), key=len, reverse=True):
            placeholder = f"__MEDICAL_TERM_{hash(term)}__"
            target_term = target_terms.get(term, term)  # Fall back to English if no translation
            restored_text = restored_text.replace(placeholder, target_term)

        return restored_text

    def get_supported_languages(self) -> Dict[str, str]:
        """Return a dictionary of supported languages."""
        return self.supported_languages.copy()

    def get_medical_terms(self, language: str) -> Dict[str, str]:
        """Get all medical terms for a specific language."""
        return self.medical_terms.get(language, {}).copy()

    def clear_cache(self):
        """Clear the translations cache."""
        self.translations_cache.clear()