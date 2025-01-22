from flask import Flask, request, jsonify
from translations import TranslationService
import os

app = Flask(__name__)
translation_service = TranslationService(app)

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.get_json()
        text = data.get('text')
        target_lang = data.get('targetLang')
        source_lang = data.get('sourceLang')

        if not text or not target_lang:
            return jsonify({"error": "Missing required parameters"}), 400

        translated_text = translation_service.translate_text(text, target_lang, source_lang)
        return jsonify({"translatedText": translated_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/detect-language', methods=['POST'])
def detect_language():
    try:
        data = request.get_json()
        text = data.get('text')

        if not text:
            return jsonify({"error": "Text is required"}), 400

        language = translation_service.detect_language(text)
        return jsonify({"language": language})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/supported-languages', methods=['GET'])
def get_supported_languages():
    try:
        languages = translation_service.get_supported_languages()
        return jsonify(languages)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/medical-terms/<language>', methods=['GET'])
def get_medical_terms(language):
    try:
        terms = translation_service.get_medical_terms(language)
        return jsonify(terms)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/medical-terms', methods=['POST'])
def add_medical_term():
    try:
        data = request.get_json()
        term = data.get('term')
        translations = data.get('translations')

        if not term or not translations:
            return jsonify({"error": "Term and translations are required"}), 400

        success = translation_service.add_medical_term(term, translations)
        if success:
            return jsonify({"message": "Medical term added successfully"})
        else:
            return jsonify({"error": "Failed to add medical term"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5001))
    app.run(host='0.0.0.0', port=port)
