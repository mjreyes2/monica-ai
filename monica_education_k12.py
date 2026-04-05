"""
Monica's K-12 Education Knowledge Base
Complete curriculum from Kindergarten through 12th Grade
Covers all subjects taught in modern schools
"""

import json
import os
from typing import Dict, List, Any

# K-12 CURRICULUM DATABASE
K12_CURRICULUM = {
    # KINDERGARTEN (Age 5-6)
    "kindergarten": {
        "grade": "K",
        "age_range": "5-6 years",
        "subjects": {
            "reading_readiness": {
                "skills": [
                    "Letter recognition (A-Z, uppercase and lowercase)",
                    "Letter sounds (phonics basics)",
                    "Rhyming words",
                    "Print awareness (left to right, top to bottom)",
                    "Sight words (the, and, is, it, to, a, I, you, we, my)",
                    "Story comprehension (beginning, middle, end)",
                    "Vocabulary building (colors, shapes, animals, family)"
                ]
            },
            "math": {
                "skills": [
                    "Counting 1-20 (and beyond)",
                    "Number recognition 0-20",
                    "One-to-one correspondence",
                    "Basic shapes (circle, square, triangle, rectangle)",
                    "Comparing (more, less, same)",
                    "Sorting and classifying",
                    "Patterns (AB, ABC patterns)",
                    "Basic addition/subtraction concepts"
                ]
            },
            "science": {
                "topics": [
                    "Five senses",
                    "Living vs non-living things",
                    "Weather and seasons",
                    "Plants and animals",
                    "Basic body parts"
                ]
            },
            "social_studies": {
                "topics": [
                    "Family and community",
                    "Rules and responsibilities",
                    "Holidays and traditions",
                    "Maps and globes introduction"
                ]
            }
        }
    },
    
    # GRADE 1 (Age 6-7)
    "grade_1": {
        "grade": "1",
        "age_range": "6-7 years",
        "subjects": {
            "reading": {
                "skills": [
                    "Phonics (consonant blends, digraphs)",
                    "Sight words (100+ Dolch words)",
                    "Reading fluency",
                    "Comprehension strategies",
                    "Story elements (characters, setting, plot)"
                ]
            },
            "writing": {
                "skills": [
                    "Sentence writing",
                    "Capital letters and periods",
                    "Simple paragraphs",
                    "Handwriting (print)"
                ]
            },
            "math": {
                "skills": [
                    "Addition facts to 20",
                    "Subtraction facts to 20",
                    "Place value (tens and ones)",
                    "Counting to 100",
                    "Skip counting by 2s, 5s, 10s",
                    "Telling time (hour, half hour)",
                    "Money (penny, nickel, dime, quarter)",
                    "Measurement (length, weight)"
                ]
            }
        }
    },
    
    # GRADE 2 (Age 7-8)
    "grade_2": {
        "grade": "2",
        "age_range": "7-8 years",
        "subjects": {
            "reading": {
                "skills": [
                    "Fluent reading",
                    "Vocabulary expansion",
                    "Main idea and details",
                    "Making inferences",
                    "Comparing texts"
                ]
            },
            "math": {
                "skills": [
                    "Addition/subtraction to 100",
                    "Introduction to multiplication",
                    "Place value to 1000",
                    "Telling time (5-minute intervals)",
                    "Money counting and making change",
                    "Basic fractions (1/2, 1/3, 1/4)",
                    "Geometry (2D and 3D shapes)"
                ]
            }
        }
    },
    
    # GRADE 3 (Age 8-9)
    "grade_3": {
        "grade": "3",
        "age_range": "8-9 years",
        "subjects": {
            "reading": {
                "skills": [
                    "Chapter books",
                    "Literary elements",
                    "Point of view",
                    "Research skills"
                ]
            },
            "math": {
                "skills": [
                    "Multiplication tables (0-10)",
                    "Division concepts",
                    "Fractions on number line",
                    "Area and perimeter",
                    "Word problems"
                ]
            },
            "science": {
                "topics": [
                    "Life cycles",
                    "Ecosystems",
                    "States of matter",
                    "Simple machines"
                ]
            }
        }
    },
    
    # GRADE 4 (Age 9-10)
    "grade_4": {
        "grade": "4",
        "age_range": "9-10 years",
        "subjects": {
            "math": {
                "skills": [
                    "Multi-digit multiplication",
                    "Long division",
                    "Equivalent fractions",
                    "Decimals introduction",
                    "Factors and multiples",
                    "Angles and angle measurement"
                ]
            },
            "science": {
                "topics": [
                    "Earth's systems",
                    "Electricity and magnetism",
                    "Food chains and webs",
                    "Rocks and minerals"
                ]
            },
            "social_studies": {
                "topics": [
                    "State history",
                    "US regions",
                    "Government basics",
                    "Economics introduction"
                ]
            }
        }
    },
    
    # GRADE 5 (Age 10-11)
    "grade_5": {
        "grade": "5",
        "age_range": "10-11 years",
        "subjects": {
            "math": {
                "skills": [
                    "Decimal operations",
                    "Fraction operations",
                    "Order of operations",
                    "Coordinate plane",
                    "Volume calculations",
                    "Data analysis"
                ]
            },
            "science": {
                "topics": [
                    "Human body systems",
                    "Matter and energy",
                    "Earth and space",
                    "Scientific method"
                ]
            }
        }
    },
    
    # GRADE 6 (Age 11-12) - Middle School
    "grade_6": {
        "grade": "6",
        "age_range": "11-12 years",
        "subjects": {
            "math": {
                "skills": [
                    "Ratios and proportions",
                    "Percent calculations",
                    "Integers and rational numbers",
                    "Algebraic expressions",
                    "One-step equations",
                    "Statistical measures"
                ]
            },
            "science": {
                "topics": [
                    "Cells and organisms",
                    "Earth science",
                    "Physical science basics",
                    "Scientific inquiry"
                ]
            },
            "english": {
                "skills": [
                    "Essay writing",
                    "Literary analysis",
                    "Research papers",
                    "Grammar and mechanics"
                ]
            }
        }
    },
    
    # GRADE 7 (Age 12-13)
    "grade_7": {
        "grade": "7",
        "age_range": "12-13 years",
        "subjects": {
            "pre_algebra": {
                "skills": [
                    "Two-step equations",
                    "Inequalities",
                    "Proportional relationships",
                    "Geometry (angles, triangles)",
                    "Probability",
                    "Statistics"
                ]
            },
            "life_science": {
                "topics": [
                    "Cell biology",
                    "Genetics and heredity",
                    "Evolution",
                    "Ecology"
                ]
            }
        }
    },
    
    # GRADE 8 (Age 13-14)
    "grade_8": {
        "grade": "8",
        "age_range": "13-14 years",
        "subjects": {
            "algebra_1_intro": {
                "skills": [
                    "Linear equations",
                    "Systems of equations",
                    "Functions",
                    "Exponents and radicals",
                    "Pythagorean theorem",
                    "Transformations"
                ]
            },
            "physical_science": {
                "topics": [
                    "Motion and forces",
                    "Energy",
                    "Waves",
                    "Chemical reactions"
                ]
            }
        }
    },
    
    # GRADE 9 (Age 14-15) - High School
    "grade_9": {
        "grade": "9",
        "age_range": "14-15 years",
        "subjects": {
            "algebra_1": {
                "skills": [
                    "Linear functions and graphs",
                    "Systems of equations",
                    "Quadratic equations",
                    "Polynomials",
                    "Factoring",
                    "Radical expressions"
                ]
            },
            "biology": {
                "topics": [
                    "Cell structure and function",
                    "DNA and genetics",
                    "Evolution and natural selection",
                    "Ecology and ecosystems",
                    "Human biology"
                ]
            },
            "english_9": {
                "skills": [
                    "Literary analysis",
                    "Argumentative writing",
                    "Research skills",
                    "Vocabulary development"
                ]
            }
        }
    },
    
    # GRADE 10 (Age 15-16)
    "grade_10": {
        "grade": "10",
        "age_range": "15-16 years",
        "subjects": {
            "geometry": {
                "skills": [
                    "Points, lines, planes",
                    "Angles and angle relationships",
                    "Triangle congruence and similarity",
                    "Quadrilaterals and polygons",
                    "Circles",
                    "Area and volume",
                    "Coordinate geometry",
                    "Transformations",
                    "Trigonometric ratios",
                    "Proofs"
                ]
            },
            "chemistry": {
                "topics": [
                    "Atomic structure",
                    "Periodic table",
                    "Chemical bonding",
                    "Chemical reactions",
                    "Stoichiometry",
                    "States of matter",
                    "Solutions",
                    "Acids and bases"
                ]
            },
            "world_history": {
                "topics": [
                    "Ancient civilizations",
                    "Medieval period",
                    "Renaissance and Reformation",
                    "Age of Exploration",
                    "Industrial Revolution",
                    "World Wars",
                    "Modern era"
                ]
            }
        }
    },
    
    # GRADE 11 (Age 16-17)
    "grade_11": {
        "grade": "11",
        "age_range": "16-17 years",
        "subjects": {
            "algebra_2": {
                "skills": [
                    "Complex numbers",
                    "Polynomial functions",
                    "Rational functions",
                    "Exponential functions",
                    "Logarithmic functions",
                    "Sequences and series",
                    "Probability and statistics",
                    "Matrices",
                    "Conic sections"
                ]
            },
            "physics": {
                "topics": [
                    "Kinematics",
                    "Dynamics (Newton's laws)",
                    "Work and energy",
                    "Momentum",
                    "Rotational motion",
                    "Waves and sound",
                    "Electricity and magnetism",
                    "Optics"
                ]
            },
            "us_history": {
                "topics": [
                    "Colonial America",
                    "American Revolution",
                    "Constitution and government",
                    "Civil War and Reconstruction",
                    "Industrialization",
                    "World Wars",
                    "Civil Rights Movement",
                    "Modern America"
                ]
            }
        }
    },
    
    # GRADE 12 (Age 17-18)
    "grade_12": {
        "grade": "12",
        "age_range": "17-18 years",
        "subjects": {
            "pre_calculus": {
                "skills": [
                    "Functions and graphs",
                    "Polynomial and rational functions",
                    "Exponential and logarithmic functions",
                    "Trigonometry",
                    "Analytic trigonometry",
                    "Vectors",
                    "Parametric equations",
                    "Polar coordinates",
                    "Limits introduction"
                ]
            },
            "calculus_intro": {
                "skills": [
                    "Limits and continuity",
                    "Derivatives",
                    "Applications of derivatives",
                    "Integrals introduction"
                ]
            },
            "ap_courses": {
                "available": [
                    "AP Calculus AB/BC",
                    "AP Physics",
                    "AP Chemistry",
                    "AP Biology",
                    "AP English Literature",
                    "AP US History",
                    "AP Computer Science"
                ]
            },
            "government_economics": {
                "topics": [
                    "US Government structure",
                    "Constitution and Bill of Rights",
                    "Political parties and elections",
                    "Microeconomics",
                    "Macroeconomics",
                    "Personal finance"
                ]
            }
        }
    }
}


class K12EducationSystem:
    """Complete K-12 education curriculum for Monica"""
    
    def __init__(self):
        self.curriculum = K12_CURRICULUM
        self.grade_levels = list(K12_CURRICULUM.keys())
        print(f"✅ K-12 Education System initialized")
        print(f"   📚 {len(self.grade_levels)} grade levels (K-12)")
    
    def get_grade_curriculum(self, grade: str) -> Dict:
        """Get curriculum for a specific grade"""
        grade_key = f"grade_{grade}" if grade.isdigit() else grade
        return self.curriculum.get(grade_key, {})
    
    def get_subject(self, grade: str, subject: str) -> Dict:
        """Get specific subject for a grade"""
        curriculum = self.get_grade_curriculum(grade)
        subjects = curriculum.get("subjects", {})
        return subjects.get(subject, {})
    
    def list_subjects_for_grade(self, grade: str) -> List[str]:
        """List all subjects for a grade"""
        curriculum = self.get_grade_curriculum(grade)
        return list(curriculum.get("subjects", {}).keys())
    
    def search_topic(self, topic: str) -> List[Dict]:
        """Search for a topic across all grades"""
        results = []
        topic_lower = topic.lower()
        
        for grade_key, grade_data in self.curriculum.items():
            for subject_name, subject_data in grade_data.get("subjects", {}).items():
                # Search in skills
                for skill in subject_data.get("skills", []):
                    if topic_lower in skill.lower():
                        results.append({
                            "grade": grade_data.get("grade", grade_key),
                            "subject": subject_name,
                            "content": skill,
                            "type": "skill"
                        })
                # Search in topics
                for t in subject_data.get("topics", []):
                    if topic_lower in t.lower():
                        results.append({
                            "grade": grade_data.get("grade", grade_key),
                            "subject": subject_name,
                            "content": t,
                            "type": "topic"
                        })
        
        return results


# Singleton
_k12_system = None

def get_k12_education() -> K12EducationSystem:
    global _k12_system
    if _k12_system is None:
        _k12_system = K12EducationSystem()
    return _k12_system


if __name__ == "__main__":
    k12 = get_k12_education()
    
    print("\n--- Grade 10 Geometry ---")
    geo = k12.get_subject("10", "geometry")
    for skill in geo.get("skills", [])[:5]:
        print(f"  • {skill}")
    
    print("\n--- Search: 'fractions' ---")
    results = k12.search_topic("fractions")
    for r in results:
        print(f"  Grade {r['grade']}: {r['content']}")
