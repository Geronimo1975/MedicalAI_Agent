from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
from .risk_assessment import RiskAssessment

@dataclass
class PreventiveRecommendation:
    category: str
    priority: str
    title: str
    description: str
    reasoning: str
    suggested_timeline: str
    confidence_score: int
    data_points: Dict
    source_references: Optional[Dict] = None

class PreventiveCareService:
    def __init__(self, knowledge_base_path: str = "app/data/preventive_care_knowledge.json"):
        self.risk_assessor = RiskAssessment()
        self.guidelines = self._load_guidelines(knowledge_base_path)
        self.age_based_screenings = {
            "18-39": [
                "blood_pressure",
                "cholesterol",
                "depression",
                "diabetes"
            ],
            "40-49": [
                "blood_pressure",
                "cholesterol",
                "depression",
                "diabetes",
                "mammogram",
                "colorectal_cancer"
            ],
            "50+": [
                "blood_pressure",
                "cholesterol",
                "depression",
                "diabetes",
                "mammogram",
                "colorectal_cancer",
                "osteoporosis",
                "lung_cancer"
            ]
        }
        
    def _load_guidelines(self, path: str) -> Dict:
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._get_default_guidelines()
            
    def _get_default_guidelines(self) -> Dict:
        """Provide default guidelines if knowledge base file is not found."""
        return {
            "lifestyle": {
                "exercise": {
                    "title": "Regular Physical Activity",
                    "description": "Engage in at least 150 minutes of moderate aerobic activity weekly",
                    "risk_factors": ["obesity", "diabetes", "hypertension"],
                    "benefits": ["cardiovascular_health", "weight_management", "mental_health"],
                    "priority_multiplier": 1.5
                },
                "nutrition": {
                    "title": "Balanced Diet Plan",
                    "description": "Follow a balanced diet rich in fruits, vegetables, and whole grains",
                    "risk_factors": ["obesity", "diabetes", "cardiovascular_disease"],
                    "benefits": ["weight_management", "diabetes_prevention", "heart_health"],
                    "priority_multiplier": 1.3
                }
            },
            "screening": {
                "blood_pressure": {
                    "title": "Regular Blood Pressure Monitoring",
                    "description": "Monitor blood pressure at least annually",
                    "risk_factors": ["hypertension", "obesity", "family_history"],
                    "benefits": ["cardiovascular_health", "stroke_prevention"],
                    "priority_multiplier": 1.8
                }
            }
        }

    def generate_recommendations(
        self,
        patient_data: Dict,
        symptom_history: List[Dict],
        risk_factors: Dict[str, float]
    ) -> List[PreventiveRecommendation]:
        """Generate personalized preventive care recommendations."""
        recommendations = []
        
        # Calculate base risk scores
        risk_scores = self.risk_assessor.calculate_risk_score(
            symptoms=[s['symptom'] for s in symptom_history],
            patient_factors=risk_factors
        )
        
        # Analyze patterns
        patterns = self.risk_assessor.analyze_temporal_patterns(symptom_history)
        
        # Get age-appropriate screenings
        age = patient_data.get('age', 0)
        age_group = "50+" if age >= 50 else "40-49" if age >= 40 else "18-39"
        recommended_screenings = self.age_based_screenings[age_group]
        
        # Generate lifestyle recommendations
        for category, items in self.guidelines['lifestyle'].items():
            for item_id, details in items.items():
                if self._should_recommend(details, risk_factors, patterns):
                    confidence = self._calculate_confidence(
                        details,
                        risk_factors,
                        risk_scores
                    )
                    
                    recommendations.append(PreventiveRecommendation(
                        category="lifestyle",
                        priority=self._calculate_priority(confidence),
                        title=details['title'],
                        description=details['description'],
                        reasoning=self._generate_reasoning(details, risk_factors, patterns),
                        suggested_timeline=self._get_timeline(details, confidence),
                        confidence_score=confidence,
                        data_points={
                            'risk_factors': risk_factors,
                            'patterns': patterns,
                            'age_group': age_group
                        },
                        source_references={
                            'guidelines': details.get('source', 'Standard medical guidelines'),
                            'last_updated': datetime.now().isoformat()
                        }
                    ))
        
        # Generate screening recommendations
        for screening in recommended_screenings:
            if screening in self.guidelines['screening']:
                details = self.guidelines['screening'][screening]
                confidence = self._calculate_confidence(
                    details,
                    risk_factors,
                    risk_scores
                )
                
                recommendations.append(PreventiveRecommendation(
                    category="screening",
                    priority=self._calculate_priority(confidence),
                    title=details['title'],
                    description=details['description'],
                    reasoning=self._generate_reasoning(details, risk_factors, patterns),
                    suggested_timeline=self._get_timeline(details, confidence),
                    confidence_score=confidence,
                    data_points={
                        'risk_factors': risk_factors,
                        'patterns': patterns,
                        'age_group': age_group
                    }
                ))
        
        # Sort recommendations by confidence score
        recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
        return recommendations

    def _should_recommend(
        self,
        details: Dict,
        risk_factors: Dict[str, float],
        patterns: Dict
    ) -> bool:
        """Determine if a recommendation should be made based on patient factors."""
        # Check if any risk factors match
        risk_factor_match = any(
            factor in risk_factors 
            for factor in details['risk_factors']
        )
        
        # Check pattern relevance
        pattern_relevance = self._check_pattern_relevance(
            details,
            patterns
        )
        
        return risk_factor_match or pattern_relevance

    def _calculate_confidence(
        self,
        details: Dict,
        risk_factors: Dict[str, float],
        risk_scores: Dict[str, float]
    ) -> int:
        """Calculate confidence score for a recommendation."""
        base_score = 50  # Start with a base score
        
        # Add points for matching risk factors
        for factor in details['risk_factors']:
            if factor in risk_factors:
                base_score += 10 * risk_factors[factor]
        
        # Adjust based on overall risk assessment
        base_score += risk_scores['total_risk'] * 2
        
        # Apply priority multiplier
        base_score *= details.get('priority_multiplier', 1.0)
        
        # Ensure score is between 0 and 100
        return min(100, max(0, int(base_score)))

    def _calculate_priority(self, confidence: int) -> str:
        """Determine priority level based on confidence score."""
        if confidence >= 80:
            return "high"
        elif confidence >= 60:
            return "medium"
        return "low"

    def _generate_reasoning(
        self,
        details: Dict,
        risk_factors: Dict[str, float],
        patterns: Dict
    ) -> str:
        """Generate explanation for the recommendation."""
        reasons = []
        
        # Add risk factor based reasons
        matching_risks = [
            factor for factor in details['risk_factors']
            if factor in risk_factors
        ]
        if matching_risks:
            reasons.append(
                f"Based on your risk factors: {', '.join(matching_risks)}"
            )
        
        # Add benefit-based reasons
        reasons.append(
            f"This can help with: {', '.join(details['benefits'])}"
        )
        
        # Add pattern-based insights if available
        if patterns.get('trends'):
            relevant_trends = [
                trend for trend in patterns['trends']
                if any(benefit in trend.lower() for benefit in details['benefits'])
            ]
            if relevant_trends:
                reasons.append(f"Relevant patterns observed: {relevant_trends[0]}")
        
        return " ".join(reasons)

    def _get_timeline(self, details: Dict, confidence: int) -> str:
        """Generate a suggested timeline based on recommendation details and confidence."""
        if confidence >= 80:
            return "Start within 1 week"
        elif confidence >= 60:
            return "Start within 1 month"
        return "Start within 3 months"

    def _check_pattern_relevance(self, details: Dict, patterns: Dict) -> bool:
        """Check if observed patterns make this recommendation relevant."""
        if not patterns.get('trends'):
            return False
            
        return any(
            benefit in trend.lower()
            for trend in patterns['trends']
            for benefit in details['benefits']
        )
