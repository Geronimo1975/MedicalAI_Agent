from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import json
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta

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
    temporal_patterns: Dict[str, float] = None  # Time-based patterns
    interaction_patterns: Dict[str, float] = None  # Symptom interactions

class RiskAssessment:
    def __init__(self, knowledge_base_path: str = "app/data/medical_knowledge.json"):
        self.symptoms_db: Dict[str, Symptom] = {}
        self.symptom_vectors = None
        self.symptom_names = []
        self.temporal_weights = {
            'morning': 1.2,
            'afternoon': 1.0,
            'evening': 1.1,
            'night': 1.3
        }
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
                        risk_factors=symptom_data['risk_factors'],
                        temporal_patterns=symptom_data.get('temporal_patterns', {}),
                        interaction_patterns=symptom_data.get('interaction_patterns', {})
                    )
                    self.symptoms_db[symptom.id] = symptom
                    self.symptom_names.append(symptom.name)
        except FileNotFoundError:
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

    def analyze_temporal_patterns(self, symptom_history: List[Dict]) -> Dict[str, List[Dict]]:
        """Analyze temporal patterns in symptom occurrences."""
        patterns = {
            'daily_patterns': [],
            'weekly_patterns': [],
            'severity_trends': [],
            'correlations': []
        }

        if not symptom_history:
            return patterns

        # Group symptoms by time of day
        time_groups = {'morning': [], 'afternoon': [], 'evening': [], 'night': []}
        for entry in symptom_history:
            timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            hour = timestamp.hour

            if 5 <= hour < 12:
                time_groups['morning'].append(entry)
            elif 12 <= hour < 17:
                time_groups['afternoon'].append(entry)
            elif 17 <= hour < 22:
                time_groups['evening'].append(entry)
            else:
                time_groups['night'].append(entry)

        # Analyze daily patterns
        for period, entries in time_groups.items():
            if entries:
                avg_severity = sum(e.get('severity', 0) for e in entries) / len(entries)
                patterns['daily_patterns'].append({
                    'period': period,
                    'frequency': len(entries),
                    'avg_severity': avg_severity,
                    'common_symptoms': self._get_common_symptoms(entries)
                })

        # Analyze weekly patterns
        days_data = {}
        for entry in symptom_history:
            timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            day = timestamp.strftime('%A')
            if day not in days_data:
                days_data[day] = []
            days_data[day].append(entry)

        for day, entries in days_data.items():
            patterns['weekly_patterns'].append({
                'day': day,
                'frequency': len(entries),
                'symptoms': self._get_common_symptoms(entries)
            })

        # Analyze severity trends
        sorted_entries = sorted(symptom_history,
                              key=lambda x: datetime.fromisoformat(x['timestamp'].replace('Z', '+00:00')))

        if len(sorted_entries) >= 2:
            severity_trend = self._calculate_severity_trend(sorted_entries)
            patterns['severity_trends'].append({
                'trend': severity_trend,
                'start_date': sorted_entries[0]['timestamp'],
                'end_date': sorted_entries[-1]['timestamp']
            })

        # Analyze symptom correlations
        patterns['correlations'] = self._analyze_symptom_correlations(symptom_history)

        return patterns

    def _get_common_symptoms(self, entries: List[Dict]) -> List[Dict]:
        """Get most common symptoms from a list of entries."""
        symptom_count = {}
        for entry in entries:
            symptom = entry.get('symptom', '')
            if symptom:
                if symptom not in symptom_count:
                    symptom_count[symptom] = 0
                symptom_count[symptom] += 1

        return [{'symptom': s, 'count': c}
                for s, c in sorted(symptom_count.items(),
                                 key=lambda x: x[1],
                                 reverse=True)][:3]

    def _calculate_severity_trend(self, entries: List[Dict]) -> str:
        """Calculate the trend in symptom severity over time."""
        if len(entries) < 2:
            return "insufficient_data"

        severities = [e.get('severity', 0) for e in entries]
        first_half = sum(severities[:len(severities) // 2]) / (len(severities) // 2)
        second_half = sum(severities[len(severities) // 2:]) / (len(severities) - len(severities) // 2)

        diff = second_half - first_half
        if diff > 0.5:
            return "increasing"
        elif diff < -0.5:
            return "decreasing"
        return "stable"

    def _analyze_symptom_correlations(self, history: List[Dict]) -> List[Dict]:
        """Analyze correlations between different symptoms."""
        correlations = []
        symptom_pairs = {}

        # Group symptoms by day to find co-occurring symptoms
        day_groups = {}
        for entry in history:
            timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            day = timestamp.date().isoformat()
            if day not in day_groups:
                day_groups[day] = set()
            day_groups[day].add(entry.get('symptom', ''))

        # Calculate co-occurrence frequencies
        for day_symptoms in day_groups.values():
            day_symptoms = list(day_symptoms)
            for i in range(len(day_symptoms)):
                for j in range(i + 1, len(day_symptoms)):
                    pair = tuple(sorted([day_symptoms[i], day_symptoms[j]]))
                    if pair not in symptom_pairs:
                        symptom_pairs[pair] = 0
                    symptom_pairs[pair] += 1

        # Convert to correlation list
        for (symptom1, symptom2), count in sorted(symptom_pairs.items(),
                                                key=lambda x: x[1],
                                                reverse=True):
            correlations.append({
                'symptoms': [symptom1, symptom2],
                'co_occurrence_count': count,
                'strength': 'high' if count > 3 else 'medium' if count > 1 else 'low'
            })

        return correlations[:5]  # Return top 5 correlations

    def generate_insights(self, patterns: Dict[str, List[Dict]]) -> Dict[str, List[str]]:
        """Generate insights from analyzed patterns."""
        insights = {
            'trends': [],
            'recommendations': []
        }

        # Analyze daily patterns
        if patterns['daily_patterns']:
            worst_period = max(patterns['daily_patterns'],
                             key=lambda x: x['avg_severity'])
            insights['trends'].append(
                f"Symptoms tend to be more severe during {worst_period['period']}")

        # Analyze weekly patterns
        if patterns['weekly_patterns']:
            most_frequent_day = max(patterns['weekly_patterns'],
                                  key=lambda x: x['frequency'])
            insights['trends'].append(
                f"Symptoms are most frequent on {most_frequent_day['day']}")

        # Analyze severity trends
        if patterns['severity_trends']:
            trend = patterns['severity_trends'][0]['trend']
            insights['trends'].append(
                f"Overall symptom severity is {trend}")

        # Generate recommendations based on patterns
        if patterns['daily_patterns']:
            worst_period = max(patterns['daily_patterns'],
                             key=lambda x: x['avg_severity'])
            insights['recommendations'].append(
                f"Consider preventive measures before {worst_period['period']}")

        # Add recommendations based on correlations
        if patterns['correlations']:
            for correlation in patterns['correlations'][:2]:
                if correlation['strength'] == 'high':
                    symptoms = ' and '.join(correlation['symptoms'])
                    insights['recommendations'].append(
                        f"Monitor {symptoms} together as they frequently co-occur")

        return insights