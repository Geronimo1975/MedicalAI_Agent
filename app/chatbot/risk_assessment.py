from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import json
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

class Severity(Enum):
    LOW = 1
    MODERATE = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Symptom:
    id: str
    name: str
    category: str
    severity: Severity
    related_conditions: List[str]
    risk_factors: Dict[str, float]

class RiskAssessment:
    def __init__(self, knowledge_base_path: str = "app/data/medical_knowledge.json"):
        self.symptoms_db: Dict[str, Symptom] = {}
        self.symptom_vectors = None
        self.symptom_names = []
        self.load_knowledge_base(knowledge_base_path)
        self.initialize_correlation_matrix()

    def load_knowledge_base(self, path: str):
        """Load medical knowledge base from JSON file."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                for symptom_data in data['symptoms']:
                    symptom = Symptom(
                        id=symptom_data['id'],
                        name=symptom_data['name'],
                        category=symptom_data['category'],
                        severity=Severity[symptom_data['severity'].upper()],
                        related_conditions=symptom_data['related_conditions'],
                        risk_factors=symptom_data['risk_factors']
                    )
                    self.symptoms_db[symptom.id] = symptom
                    self.symptom_names.append(symptom.name)
        except FileNotFoundError:
            # Initialize with basic symptom data if file not found
            self._initialize_basic_symptoms()

    def _initialize_basic_symptoms(self):
        """Initialize basic symptoms if knowledge base is not available."""
        basic_symptoms = [
            {
                'id': 'fever',
                'name': 'Fever',
                'category': 'General',
                'severity': 'MODERATE',
                'related_conditions': ['infection', 'inflammation'],
                'risk_factors': {'age_65_plus': 1.5, 'immunocompromised': 2.0}
            },
            {
                'id': 'shortness_of_breath',
                'name': 'Shortness of Breath',
                'category': 'Respiratory',
                'severity': 'HIGH',
                'related_conditions': ['respiratory_infection', 'cardiac_condition'],
                'risk_factors': {'smoking': 1.5, 'asthma': 2.0, 'age_65_plus': 1.3}
            }
            # Add more basic symptoms as needed
        ]
        for symptom_data in basic_symptoms:
            symptom = Symptom(
                id=symptom_data['id'],
                name=symptom_data['name'],
                category=symptom_data['category'],
                severity=Severity[symptom_data['severity']],
                related_conditions=symptom_data['related_conditions'],
                risk_factors=symptom_data['risk_factors']
            )
            self.symptoms_db[symptom.id] = symptom
            self.symptom_names.append(symptom.name)

    def initialize_correlation_matrix(self):
        """Initialize symptom correlation matrix using medical knowledge."""
        n_symptoms = len(self.symptoms_db)
        matrix = np.zeros((n_symptoms, n_symptoms))
        
        # Create correlation based on shared conditions and categories
        for i, (_, symptom1) in enumerate(self.symptoms_db.items()):
            for j, (_, symptom2) in enumerate(self.symptoms_db.items()):
                if i != j:
                    # Calculate correlation based on shared conditions
                    shared_conditions = len(set(symptom1.related_conditions) & 
                                         set(symptom2.related_conditions))
                    category_match = float(symptom1.category == symptom2.category)
                    
                    # Combine factors for correlation score
                    matrix[i, j] = (0.5 * shared_conditions + 0.3 * category_match) / \
                                 (1 + 0.5 * abs(symptom1.severity.value - symptom2.severity.value))

        self.symptom_vectors = csr_matrix(matrix)

    def calculate_risk_score(self, 
                           symptoms: List[str], 
                           patient_factors: Dict[str, float] = None) -> Dict[str, float]:
        """
        Calculate risk score based on symptoms and patient factors.
        
        Args:
            symptoms: List of symptom IDs
            patient_factors: Dictionary of patient risk factors and their values
        
        Returns:
            Dictionary containing risk scores and analysis
        """
        if not symptoms:
            return {'total_risk': 0.0, 'severity_score': 0.0, 'correlation_score': 0.0}

        patient_factors = patient_factors or {}
        
        # Calculate base severity score
        severity_score = sum(self.symptoms_db[s].severity.value for s in symptoms if s in self.symptoms_db)
        severity_score /= len(symptoms)

        # Calculate symptom correlation score
        correlation_score = 0.0
        if len(symptoms) > 1:
            symptom_indices = [list(self.symptoms_db.keys()).index(s) for s in symptoms 
                             if s in self.symptoms_db]
            correlations = cosine_similarity(self.symptom_vectors[symptom_indices])
            correlation_score = correlations.mean()

        # Apply patient risk factors
        risk_multiplier = 1.0
        for factor, value in patient_factors.items():
            for symptom_id in symptoms:
                if symptom_id in self.symptoms_db:
                    symptom = self.symptoms_db[symptom_id]
                    if factor in symptom.risk_factors:
                        risk_multiplier += symptom.risk_factors[factor] * value

        # Calculate total risk score
        total_risk = (0.4 * severity_score + 
                     0.3 * correlation_score + 
                     0.3 * (risk_multiplier - 1)) * 10  # Scale to 0-10

        return {
            'total_risk': round(total_risk, 2),
            'severity_score': round(severity_score, 2),
            'correlation_score': round(correlation_score, 2),
            'risk_multiplier': round(risk_multiplier, 2)
        }

    def suggest_additional_symptoms(self, current_symptoms: List[str], 
                                  max_suggestions: int = 3) -> List[str]:
        """Suggest additional symptoms to check based on correlations."""
        if not current_symptoms:
            return []

        current_indices = [list(self.symptoms_db.keys()).index(s) for s in current_symptoms 
                         if s in self.symptoms_db]
        if not current_indices:
            return []

        # Get correlation scores for all symptoms
        correlations = cosine_similarity(self.symptom_vectors[current_indices], 
                                       self.symptom_vectors)
        mean_correlations = correlations.mean(axis=0)

        # Get top correlated symptoms that aren't in current symptoms
        all_symptoms = list(self.symptoms_db.keys())
        suggestions = []
        for idx in np.argsort(mean_correlations)[::-1]:
            symptom_id = all_symptoms[idx]
            if symptom_id not in current_symptoms:
                suggestions.append(self.symptoms_db[symptom_id].name)
                if len(suggestions) >= max_suggestions:
                    break

        return suggestions

    def get_severity_recommendations(self, risk_score: float) -> str:
        """Get recommendations based on risk score."""
        if risk_score >= 8.0:
            return "EMERGENCY: Seek immediate medical attention. Call emergency services or go to the nearest emergency room."
        elif risk_score >= 6.0:
            return "URGENT: Seek medical attention within the next 24 hours. Contact your healthcare provider or visit an urgent care center."
        elif risk_score >= 4.0:
            return "MODERATE: Schedule an appointment with your healthcare provider within the next few days."
        else:
            return "LOW: Monitor symptoms. If they persist or worsen, schedule a routine appointment with your healthcare provider."
