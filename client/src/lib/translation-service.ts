import type { SelectUser } from "@db/schema";

export interface TranslationResponse {
  translatedText: string;
}

export interface LanguageResponse {
  language: string;
}

export interface AddMedicalTermRequest {
  term: string;
  translations: Record<string, string>;
}

export class TranslationService {
  async translateText(text: string, targetLang: string, sourceLang?: string): Promise<string> {
    try {
      const response = await fetch('/api/translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text, targetLang, sourceLang }),
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Translation failed: ${response.statusText}`);
      }

      const data: TranslationResponse = await response.json();
      return data.translatedText;
    } catch (error) {
      console.error('Translation error:', error);
      throw error;
    }
  }

  async detectLanguage(text: string): Promise<string> {
    try {
      const response = await fetch('/api/detect-language', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Language detection failed: ${response.statusText}`);
      }

      const data: LanguageResponse = await response.json();
      return data.language;
    } catch (error) {
      console.error('Language detection error:', error);
      throw error;
    }
  }

  async getSupportedLanguages(): Promise<Record<string, string>> {
    try {
      const response = await fetch('/api/supported-languages', {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch supported languages: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.error('Supported languages fetch error:', error);
      throw error;
    }
  }

  async getMedicalTerms(language: string): Promise<Record<string, string>> {
    try {
      const response = await fetch(`/api/medical-terms/${language}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch medical terms: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.error('Medical terms fetch error:', error);
      throw error;
    }
  }

  async addMedicalTerm(term: string, translations: Record<string, string>): Promise<void> {
    try {
      const response = await fetch('/api/medical-terms', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ term, translations }),
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to add medical term: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Medical term addition error:', error);
      throw error;
    }
  }
}

export const translationService = new TranslationService();
