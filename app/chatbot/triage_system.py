```python
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json

@dataclass
class TriageAssessment:
    level: str  # emergency, urgent, non_urgent
    confidence_score: float
    reasoning: List[str]
    recommendations: List[str]
    required_vitals: List[str]
    red_flags: List[str]
    follow_up_questions: List[str]

class AdvancedTriageSystem:
    def __init__(self):
        self.emergency_symptoms = {
            "chest_pain": {
                "keywords": ["chest pain", "chest pressure", "heart attack", "crushing"],
                "severity_multiplier": 2.0,
                "required_vitals": ["blood_pressure", "heart_rate", "oxygen_saturation"],
                "follow_up": [
                    "Is the pain crushing or pressure-like?",
                    "Does it radiate to your arm or jaw?",
                    "Are you experiencing shortness of breath?"
                ]
            },
            "difficulty_breathing": {
                "keywords": ["shortness of breath", "can't breathe", "breathing difficulty"],
                "severity_multiplier": 1.8,
                "required_vitals": ["oxygen_saturation", "respiratory_rate"],
                "follow_up": [
                    "Are you able to speak in full sentences?",
                    "How long has this been occurring?",
                    "Any associated chest pain?"
                ]
            },
            "stroke_symptoms": {
                "keywords": ["face drooping", "arm weakness", "speech difficulty"],
                "severity_multiplier": 2.0,
                "required_vitals": ["blood_pressure", "blood_glucose"],
                "follow_up": [
                    "When did these symptoms start?",
                    "Can you raise both arms equally?",
                    "Can you smile for me - is your face even?"
                ]
            }
        }
        
        self.urgent_symptoms = {
            "severe_pain": {
                "keywords": ["severe pain", "worst pain", "10 out of 10"],
                "severity_multiplier": 1.5,
                "follow_up": [
                    "On a scale of 1-10, how severe is the pain?",
                    "What makes it better or worse?",
                    "Any associated symptoms?"
                ]
            },
            "high_fever": {
                "keywords": ["high fever", "temperature", "103", "104"],
                "severity_multiplier": 1.3,
                "required_vitals": ["temperature"],
                "follow_up": [
                    "What is your current temperature?",
                    "Any shaking or chills?",
                    "How long has the fever lasted?"
                ]
            }
        }
        
        self.risk_factors = {
            "age_65_plus": 1.2,
            "pregnancy": 1.3,
            "immunocompromised": 1.4,
            "diabetes": 1.1,
            "heart_disease": 1.2,
            "respiratory_condition": 1.2
        }

    def assess_triage_level(
        self,
        symptoms: List[str],
        severity_scores: Dict[str, float],
        risk_factors: List[str],
        vital_signs: Optional[Dict[str, float]] = None,
        additional_info: Optional[Dict[str, str]] = None
    ) -> TriageAssessment:
        """
        Perform comprehensive triage assessment based on symptoms and patient factors.
        """
        base_score = 0.0
        reasoning = []
        red_flags = []
        required_vitals = set()
        follow_up_questions = set()
        
        # Check for emergency symptoms
        for symptom, details in self.emergency_symptoms.items():
            if self._has_matching_keywords(symptoms, details["keywords"]):
                base_score += 10.0 * details["severity_multiplier"]
                reasoning.append(f"Emergency symptom detected: {symptom}")
                red_flags.append(symptom)
                required_vitals.update(details.get("required_vitals", []))
                follow_up_questions.update(details.get("follow_up", []))
        
        # Check for urgent symptoms
        for symptom, details in self.urgent_symptoms.items():
            if self._has_matching_keywords(symptoms, details["keywords"]):
                base_score += 7.0 * details["severity_multiplier"]
                reasoning.append(f"Urgent symptom detected: {symptom}")
                required_vitals.update(details.get("required_vitals", []))
                follow_up_questions.update(details.get("follow_up", []))
        
        # Apply risk factor multipliers
        risk_multiplier = 1.0
        for factor in risk_factors:
            if factor in self.risk_factors:
                risk_multiplier *= self.risk_factors[factor]
                reasoning.append(f"Risk factor present: {factor}")
        
        final_score = base_score * risk_multiplier
        
        # Determine triage level and recommendations
        triage_level, confidence, recommendations = self._calculate_triage_level(
            final_score,
            len(red_flags),
            vital_signs or {}
        )
        
        return TriageAssessment(
            level=triage_level,
            confidence_score=confidence,
            reasoning=reasoning,
            recommendations=recommendations,
            required_vitals=list(required_vitals),
            red_flags=red_flags,
            follow_up_questions=list(follow_up_questions)
        )

    def _has_matching_keywords(self, symptoms: List[str], keywords: List[str]) -> bool:
        """Check if any of the keywords match in the symptoms list."""
        symptoms_text = " ".join(symptoms).lower()
        return any(keyword.lower() in symptoms_text for keyword in keywords)

    def _calculate_triage_level(
        self,
        score: float,
        red_flag_count: int,
        vital_signs: Dict[str, float]
    ) -> Tuple[str, float, List[str]]:
        """
        Calculate final triage level, confidence score, and recommendations.
        """
        recommendations = []
        
        # Emergency conditions
        if red_flag_count > 0 or score >= 15.0:
            confidence = min(0.95, 0.75 + (score - 15.0) * 0.02)
            recommendations = [
                "Immediate emergency medical attention required",
                "Call emergency services (911) immediately",
                "Do not drive yourself to the hospital"
            ]
            return "emergency", confidence, recommendations
        
        # Urgent conditions
        if score >= 8.0:
            confidence = min(0.90, 0.70 + (score - 8.0) * 0.025)
            recommendations = [
                "Seek medical care within the next 24 hours",
                "Monitor symptoms closely",
                "If symptoms worsen, seek immediate emergency care"
            ]
            return "urgent", confidence, recommendations
        
        # Non-urgent conditions
        confidence = min(0.85, 0.60 + score * 0.03)
        recommendations = [
            "Schedule an appointment with your primary care provider",
            "Monitor symptoms and maintain a symptom diary",
            "Practice self-care measures as appropriate"
        ]
        return "non_urgent", confidence, recommendations

    def generate_follow_up_assessment(
        self,
        initial_assessment: TriageAssessment,
        new_symptoms: List[str],
        vital_signs: Dict[str, float]
    ) -> TriageAssessment:
        """
        Generate a follow-up assessment based on new information and vitals.
        """
        # Implementation for follow-up assessment logic
        # This would incorporate the new information to refine the triage level
        pass
```
