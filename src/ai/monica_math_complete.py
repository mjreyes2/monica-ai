"""
Monica's Complete Mathematics Knowledge Base
From Basic Arithmetic to Advanced Calculus and Beyond
"""

import json
from typing import Dict, List, Any

# COMPLETE MATHEMATICS CURRICULUM
MATHEMATICS_KNOWLEDGE = {
    # ARITHMETIC
    "arithmetic": {
        "title": "Arithmetic",
        "description": "Foundation of all mathematics",
        "topics": {
            "number_systems": {
                "natural_numbers": "Counting numbers: 1, 2, 3, ...",
                "whole_numbers": "Natural numbers + 0: 0, 1, 2, 3, ...",
                "integers": "Whole numbers + negatives: ..., -2, -1, 0, 1, 2, ...",
                "rational_numbers": "Numbers expressible as fractions: p/q where q≠0",
                "irrational_numbers": "Cannot be expressed as fractions: π, √2, e",
                "real_numbers": "All rational and irrational numbers",
                "complex_numbers": "a + bi where i = √(-1)"
            },
            "operations": {
                "addition": {"symbol": "+", "properties": ["Commutative", "Associative", "Identity (0)"]},
                "subtraction": {"symbol": "-", "properties": ["Not commutative", "Not associative"]},
                "multiplication": {"symbol": "×", "properties": ["Commutative", "Associative", "Identity (1)", "Distributive"]},
                "division": {"symbol": "÷", "properties": ["Not commutative", "Not associative"]}
            },
            "order_of_operations": {
                "PEMDAS": ["Parentheses", "Exponents", "Multiplication/Division (left to right)", "Addition/Subtraction (left to right)"]
            }
        }
    },
    
    # PRE-ALGEBRA
    "pre_algebra": {
        "title": "Pre-Algebra",
        "description": "Bridge between arithmetic and algebra",
        "topics": {
            "variables_expressions": {
                "variables": "Letters representing unknown values",
                "expressions": "Combinations of numbers, variables, and operations",
                "evaluating": "Substituting values for variables"
            },
            "equations": {
                "one_step": "x + 5 = 12, solve for x",
                "two_step": "2x + 3 = 11, solve for x",
                "properties": ["Addition property", "Subtraction property", "Multiplication property", "Division property"]
            },
            "inequalities": {
                "symbols": ["< (less than)", "> (greater than)", "≤ (less than or equal)", "≥ (greater than or equal)"],
                "graphing": "Number line representation"
            },
            "ratios_proportions": {
                "ratio": "Comparison of two quantities (a:b or a/b)",
                "proportion": "Equation stating two ratios are equal",
                "cross_multiplication": "If a/b = c/d, then ad = bc"
            },
            "percents": {
                "definition": "Per hundred (out of 100)",
                "conversions": "Decimal ↔ Percent ↔ Fraction",
                "applications": ["Discounts", "Tax", "Interest", "Tips"]
            }
        }
    },
    
    # ALGEBRA 1
    "algebra_1": {
        "title": "Algebra 1",
        "description": "Foundation of algebraic thinking",
        "topics": {
            "linear_equations": {
                "slope_intercept_form": "y = mx + b",
                "point_slope_form": "y - y₁ = m(x - x₁)",
                "standard_form": "Ax + By = C",
                "slope": "m = (y₂ - y₁)/(x₂ - x₁) = rise/run",
                "graphing": "Plot y-intercept, use slope to find more points"
            },
            "systems_of_equations": {
                "methods": ["Graphing", "Substitution", "Elimination"],
                "solutions": ["One solution (intersecting lines)", "No solution (parallel lines)", "Infinite solutions (same line)"]
            },
            "polynomials": {
                "definition": "Expression with variables and coefficients",
                "operations": ["Addition", "Subtraction", "Multiplication"],
                "degree": "Highest power of the variable",
                "types": ["Monomial (1 term)", "Binomial (2 terms)", "Trinomial (3 terms)"]
            },
            "factoring": {
                "gcf": "Greatest Common Factor",
                "difference_of_squares": "a² - b² = (a+b)(a-b)",
                "trinomials": "x² + bx + c = (x + p)(x + q) where pq = c and p+q = b",
                "grouping": "Factor by grouping for 4+ terms"
            },
            "quadratic_equations": {
                "standard_form": "ax² + bx + c = 0",
                "quadratic_formula": "x = (-b ± √(b²-4ac)) / 2a",
                "discriminant": "b² - 4ac determines number of solutions",
                "methods": ["Factoring", "Completing the square", "Quadratic formula", "Graphing"]
            },
            "exponents": {
                "rules": {
                    "product": "aᵐ · aⁿ = aᵐ⁺ⁿ",
                    "quotient": "aᵐ / aⁿ = aᵐ⁻ⁿ",
                    "power": "(aᵐ)ⁿ = aᵐⁿ",
                    "zero": "a⁰ = 1 (a ≠ 0)",
                    "negative": "a⁻ⁿ = 1/aⁿ"
                }
            },
            "radicals": {
                "definition": "√a is the number that when squared gives a",
                "simplifying": "√(ab) = √a · √b",
                "rationalizing": "Eliminate radicals from denominator"
            }
        }
    },
    
    # COLLEGE ALGEBRA
    "college_algebra": {
        "title": "College Algebra",
        "description": "Advanced algebraic concepts for higher education",
        "topics": {
            "functions": {
                "definition": "Relation where each input has exactly one output",
                "notation": "f(x) = expression",
                "domain": "Set of all valid inputs",
                "range": "Set of all possible outputs",
                "types": ["Linear", "Quadratic", "Polynomial", "Rational", "Radical", "Exponential", "Logarithmic"],
                "operations": ["Addition", "Subtraction", "Multiplication", "Division", "Composition f(g(x))"],
                "inverse": "f⁻¹(x) where f(f⁻¹(x)) = x"
            },
            "polynomial_functions": {
                "end_behavior": "Determined by leading coefficient and degree",
                "zeros": "x-intercepts, roots, solutions",
                "multiplicity": "Number of times a zero repeats",
                "rational_root_theorem": "Possible rational roots = ±(factors of constant)/(factors of leading coefficient)"
            },
            "rational_functions": {
                "definition": "f(x) = p(x)/q(x) where p and q are polynomials",
                "vertical_asymptotes": "Where denominator = 0",
                "horizontal_asymptotes": "Behavior as x → ±∞",
                "holes": "Common factors in numerator and denominator"
            },
            "exponential_functions": {
                "form": "f(x) = abˣ",
                "growth": "b > 1",
                "decay": "0 < b < 1",
                "natural_base": "e ≈ 2.71828",
                "compound_interest": "A = P(1 + r/n)ⁿᵗ",
                "continuous_growth": "A = Peʳᵗ"
            },
            "logarithmic_functions": {
                "definition": "logₐ(x) = y means aʸ = x",
                "common_log": "log(x) = log₁₀(x)",
                "natural_log": "ln(x) = logₑ(x)",
                "properties": {
                    "product": "log(ab) = log(a) + log(b)",
                    "quotient": "log(a/b) = log(a) - log(b)",
                    "power": "log(aⁿ) = n·log(a)",
                    "change_of_base": "logₐ(x) = log(x)/log(a)"
                }
            },
            "matrices": {
                "operations": ["Addition", "Subtraction", "Scalar multiplication", "Matrix multiplication"],
                "determinant": "2×2: ad - bc",
                "inverse": "A⁻¹ where AA⁻¹ = I",
                "applications": ["Solving systems", "Transformations"]
            },
            "sequences_series": {
                "arithmetic": {
                    "formula": "aₙ = a₁ + (n-1)d",
                    "sum": "Sₙ = n(a₁ + aₙ)/2"
                },
                "geometric": {
                    "formula": "aₙ = a₁ · rⁿ⁻¹",
                    "sum_finite": "Sₙ = a₁(1 - rⁿ)/(1 - r)",
                    "sum_infinite": "S = a₁/(1 - r) if |r| < 1"
                }
            },
            "conic_sections": {
                "circle": "(x-h)² + (y-k)² = r²",
                "ellipse": "(x-h)²/a² + (y-k)²/b² = 1",
                "hyperbola": "(x-h)²/a² - (y-k)²/b² = 1",
                "parabola": "y = a(x-h)² + k or x = a(y-k)² + h"
            }
        }
    },
    
    # GEOMETRY
    "geometry": {
        "title": "Geometry",
        "description": "Study of shapes, sizes, and properties of space",
        "topics": {
            "basic_concepts": {
                "point": "Location with no size",
                "line": "Infinite set of points extending in both directions",
                "plane": "Flat surface extending infinitely",
                "segment": "Part of a line with two endpoints",
                "ray": "Part of a line with one endpoint"
            },
            "angles": {
                "types": {
                    "acute": "0° < angle < 90°",
                    "right": "angle = 90°",
                    "obtuse": "90° < angle < 180°",
                    "straight": "angle = 180°",
                    "reflex": "180° < angle < 360°"
                },
                "relationships": {
                    "complementary": "Sum = 90°",
                    "supplementary": "Sum = 180°",
                    "vertical": "Opposite angles formed by intersecting lines (equal)"
                }
            },
            "triangles": {
                "by_sides": {
                    "equilateral": "All sides equal",
                    "isosceles": "Two sides equal",
                    "scalene": "No sides equal"
                },
                "by_angles": {
                    "acute": "All angles < 90°",
                    "right": "One angle = 90°",
                    "obtuse": "One angle > 90°"
                },
                "properties": {
                    "angle_sum": "Sum of angles = 180°",
                    "exterior_angle": "Equal to sum of remote interior angles",
                    "triangle_inequality": "Sum of any two sides > third side"
                },
                "congruence": ["SSS", "SAS", "ASA", "AAS", "HL (right triangles)"],
                "similarity": ["AA", "SAS", "SSS"],
                "area": "A = (1/2)bh",
                "pythagorean_theorem": "a² + b² = c² (right triangles)"
            },
            "quadrilaterals": {
                "parallelogram": {
                    "properties": ["Opposite sides parallel and equal", "Opposite angles equal", "Diagonals bisect each other"],
                    "area": "A = bh"
                },
                "rectangle": {
                    "properties": ["All angles 90°", "Diagonals equal"],
                    "area": "A = lw"
                },
                "rhombus": {
                    "properties": ["All sides equal", "Diagonals perpendicular"],
                    "area": "A = (1/2)d₁d₂"
                },
                "square": {
                    "properties": ["All sides equal", "All angles 90°"],
                    "area": "A = s²"
                },
                "trapezoid": {
                    "properties": ["One pair of parallel sides"],
                    "area": "A = (1/2)(b₁ + b₂)h"
                }
            },
            "circles": {
                "parts": ["Center", "Radius", "Diameter", "Chord", "Arc", "Sector", "Tangent", "Secant"],
                "circumference": "C = 2πr = πd",
                "area": "A = πr²",
                "arc_length": "s = (θ/360°) × 2πr",
                "sector_area": "A = (θ/360°) × πr²",
                "inscribed_angle": "Half the central angle"
            },
            "3d_shapes": {
                "prism": {
                    "volume": "V = Bh (B = base area)",
                    "surface_area": "SA = 2B + Ph (P = perimeter)"
                },
                "cylinder": {
                    "volume": "V = πr²h",
                    "surface_area": "SA = 2πr² + 2πrh"
                },
                "pyramid": {
                    "volume": "V = (1/3)Bh"
                },
                "cone": {
                    "volume": "V = (1/3)πr²h",
                    "surface_area": "SA = πr² + πrl (l = slant height)"
                },
                "sphere": {
                    "volume": "V = (4/3)πr³",
                    "surface_area": "SA = 4πr²"
                }
            },
            "coordinate_geometry": {
                "distance": "d = √[(x₂-x₁)² + (y₂-y₁)²]",
                "midpoint": "M = ((x₁+x₂)/2, (y₁+y₂)/2)",
                "slope": "m = (y₂-y₁)/(x₂-x₁)"
            },
            "transformations": {
                "translation": "Slide (x, y) → (x+a, y+b)",
                "reflection": "Flip across a line",
                "rotation": "Turn around a point",
                "dilation": "Scale by factor k"
            },
            "trigonometry_basics": {
                "ratios": {
                    "sine": "sin(θ) = opposite/hypotenuse",
                    "cosine": "cos(θ) = adjacent/hypotenuse",
                    "tangent": "tan(θ) = opposite/adjacent"
                },
                "sohcahtoa": "Memory aid for trig ratios"
            }
        }
    },
    
    # TRIGONOMETRY
    "trigonometry": {
        "title": "Trigonometry",
        "description": "Study of triangles and circular functions",
        "topics": {
            "unit_circle": {
                "definition": "Circle with radius 1 centered at origin",
                "coordinates": "(cos θ, sin θ)",
                "special_angles": {
                    "0°": "(1, 0)",
                    "30°": "(√3/2, 1/2)",
                    "45°": "(√2/2, √2/2)",
                    "60°": "(1/2, √3/2)",
                    "90°": "(0, 1)"
                }
            },
            "trig_functions": {
                "primary": ["sin", "cos", "tan"],
                "reciprocal": {
                    "csc": "1/sin",
                    "sec": "1/cos",
                    "cot": "1/tan"
                }
            },
            "identities": {
                "pythagorean": [
                    "sin²θ + cos²θ = 1",
                    "1 + tan²θ = sec²θ",
                    "1 + cot²θ = csc²θ"
                ],
                "sum_difference": [
                    "sin(A±B) = sinA·cosB ± cosA·sinB",
                    "cos(A±B) = cosA·cosB ∓ sinA·sinB",
                    "tan(A±B) = (tanA ± tanB)/(1 ∓ tanA·tanB)"
                ],
                "double_angle": [
                    "sin(2θ) = 2sinθ·cosθ",
                    "cos(2θ) = cos²θ - sin²θ = 2cos²θ - 1 = 1 - 2sin²θ",
                    "tan(2θ) = 2tanθ/(1 - tan²θ)"
                ]
            },
            "law_of_sines": "a/sinA = b/sinB = c/sinC",
            "law_of_cosines": "c² = a² + b² - 2ab·cosC",
            "inverse_functions": ["arcsin (sin⁻¹)", "arccos (cos⁻¹)", "arctan (tan⁻¹)"]
        }
    },
    
    # CALCULUS
    "calculus": {
        "title": "Calculus",
        "description": "Study of change and accumulation",
        "topics": {
            "limits": {
                "definition": "Value a function approaches as input approaches a value",
                "notation": "lim(x→a) f(x) = L",
                "properties": ["Sum", "Difference", "Product", "Quotient", "Constant multiple"],
                "techniques": ["Direct substitution", "Factoring", "Rationalization", "L'Hôpital's rule"],
                "special_limits": {
                    "lim(x→0) sin(x)/x": "= 1",
                    "lim(x→∞) (1 + 1/x)ˣ": "= e"
                }
            },
            "continuity": {
                "definition": "f is continuous at a if lim(x→a) f(x) = f(a)",
                "types_of_discontinuity": ["Removable", "Jump", "Infinite"]
            },
            "derivatives": {
                "definition": "f'(x) = lim(h→0) [f(x+h) - f(x)]/h",
                "interpretation": ["Instantaneous rate of change", "Slope of tangent line"],
                "rules": {
                    "constant": "d/dx[c] = 0",
                    "power": "d/dx[xⁿ] = nxⁿ⁻¹",
                    "sum": "d/dx[f + g] = f' + g'",
                    "product": "d/dx[fg] = f'g + fg'",
                    "quotient": "d/dx[f/g] = (f'g - fg')/g²",
                    "chain": "d/dx[f(g(x))] = f'(g(x)) · g'(x)"
                },
                "special_derivatives": {
                    "d/dx[sin x]": "cos x",
                    "d/dx[cos x]": "-sin x",
                    "d/dx[tan x]": "sec² x",
                    "d/dx[eˣ]": "eˣ",
                    "d/dx[ln x]": "1/x",
                    "d/dx[aˣ]": "aˣ · ln(a)"
                },
                "applications": [
                    "Related rates",
                    "Optimization",
                    "Linear approximation",
                    "Motion problems"
                ]
            },
            "integrals": {
                "indefinite": "∫f(x)dx = F(x) + C where F'(x) = f(x)",
                "definite": "∫[a,b] f(x)dx = F(b) - F(a)",
                "fundamental_theorem": "d/dx[∫[a,x] f(t)dt] = f(x)",
                "techniques": [
                    "Substitution (u-sub)",
                    "Integration by parts: ∫udv = uv - ∫vdu",
                    "Partial fractions",
                    "Trigonometric substitution"
                ],
                "applications": [
                    "Area under curve",
                    "Volume of revolution",
                    "Arc length",
                    "Work",
                    "Average value"
                ]
            },
            "series": {
                "taylor_series": "f(x) = Σ f⁽ⁿ⁾(a)(x-a)ⁿ/n!",
                "maclaurin_series": "Taylor series centered at a=0",
                "common_series": {
                    "eˣ": "1 + x + x²/2! + x³/3! + ...",
                    "sin x": "x - x³/3! + x⁵/5! - ...",
                    "cos x": "1 - x²/2! + x⁴/4! - ...",
                    "1/(1-x)": "1 + x + x² + x³ + ... (|x| < 1)"
                },
                "convergence_tests": ["Ratio test", "Root test", "Comparison test", "Integral test"]
            }
        }
    },
    
    # QUANTUM PHYSICS
    "quantum_physics": {
        "title": "Quantum Physics",
        "description": "Physics of the very small - atoms and subatomic particles",
        "topics": {
            "foundations": {
                "wave_particle_duality": "Matter exhibits both wave and particle properties",
                "planck_constant": "h = 6.626 × 10⁻³⁴ J·s",
                "photoelectric_effect": "E = hf (Einstein, light as photons)",
                "de_broglie_wavelength": "λ = h/p = h/(mv)"
            },
            "heisenberg_uncertainty": {
                "principle": "Cannot simultaneously know exact position and momentum",
                "formula": "Δx · Δp ≥ ℏ/2",
                "implications": "Fundamental limit to measurement precision"
            },
            "schrodinger_equation": {
                "time_independent": "Ĥψ = Eψ",
                "time_dependent": "iℏ ∂ψ/∂t = Ĥψ",
                "wave_function": "ψ(x,t) - probability amplitude",
                "probability": "|ψ|² gives probability density"
            },
            "quantum_states": {
                "superposition": "System can be in multiple states simultaneously",
                "entanglement": "Correlated quantum states across distance",
                "measurement": "Collapses superposition to definite state"
            },
            "atomic_structure": {
                "orbitals": ["s", "p", "d", "f"],
                "quantum_numbers": {
                    "n": "Principal (energy level)",
                    "l": "Angular momentum (orbital shape)",
                    "ml": "Magnetic (orbital orientation)",
                    "ms": "Spin (±1/2)"
                },
                "pauli_exclusion": "No two electrons can have same quantum numbers"
            },
            "applications": [
                "Quantum computing",
                "Quantum cryptography",
                "Quantum sensors",
                "Quantum teleportation"
            ]
        }
    },
    
    # GENERAL RELATIVITY
    "general_relativity": {
        "title": "General Relativity",
        "description": "Einstein's theory of gravity as curved spacetime",
        "topics": {
            "special_relativity": {
                "postulates": [
                    "Laws of physics same in all inertial frames",
                    "Speed of light constant (c ≈ 3×10⁸ m/s)"
                ],
                "time_dilation": "t' = t/√(1 - v²/c²)",
                "length_contraction": "L' = L√(1 - v²/c²)",
                "mass_energy": "E = mc²",
                "relativistic_momentum": "p = γmv where γ = 1/√(1 - v²/c²)"
            },
            "general_relativity": {
                "equivalence_principle": "Gravity and acceleration are indistinguishable",
                "curved_spacetime": "Mass/energy curves spacetime",
                "geodesics": "Objects follow shortest paths in curved spacetime",
                "einstein_field_equations": "Gμν + Λgμν = (8πG/c⁴)Tμν"
            },
            "predictions": {
                "gravitational_time_dilation": "Clocks run slower in stronger gravity",
                "gravitational_lensing": "Light bends around massive objects",
                "gravitational_waves": "Ripples in spacetime (detected 2015)",
                "black_holes": "Regions where gravity prevents light escape",
                "frame_dragging": "Rotating masses drag spacetime"
            },
            "black_holes": {
                "schwarzschild_radius": "rs = 2GM/c²",
                "event_horizon": "Boundary of no return",
                "singularity": "Point of infinite density",
                "hawking_radiation": "Black holes emit radiation (quantum effect)"
            },
            "cosmology": {
                "expanding_universe": "Hubble's law: v = H₀d",
                "big_bang": "Universe began ~13.8 billion years ago",
                "dark_energy": "Accelerating expansion",
                "dark_matter": "Invisible matter affecting galaxy rotation"
            }
        }
    },
    
    # STATISTICS
    "statistics": {
        "title": "Statistics",
        "description": "Science of collecting, analyzing, and interpreting data",
        "topics": {
            "descriptive": {
                "central_tendency": {
                    "mean": "Average: Σx/n",
                    "median": "Middle value when sorted",
                    "mode": "Most frequent value"
                },
                "dispersion": {
                    "range": "Max - Min",
                    "variance": "σ² = Σ(x - μ)²/n",
                    "standard_deviation": "σ = √variance",
                    "iqr": "Q3 - Q1"
                }
            },
            "probability": {
                "basic": "P(A) = favorable outcomes / total outcomes",
                "addition": "P(A or B) = P(A) + P(B) - P(A and B)",
                "multiplication": "P(A and B) = P(A) × P(B|A)",
                "conditional": "P(A|B) = P(A and B) / P(B)",
                "bayes_theorem": "P(A|B) = P(B|A)P(A) / P(B)"
            },
            "distributions": {
                "normal": "Bell curve, μ and σ parameters",
                "binomial": "n trials, probability p",
                "poisson": "Events in fixed interval",
                "t_distribution": "Small samples, unknown σ"
            },
            "inferential": {
                "hypothesis_testing": ["Null hypothesis", "Alternative hypothesis", "p-value", "Significance level"],
                "confidence_intervals": "Range likely containing true parameter",
                "regression": "y = mx + b (linear relationship)"
            }
        }
    }
}


class CompleteMathSystem:
    """Complete mathematics knowledge system"""
    
    def __init__(self):
        self.knowledge = MATHEMATICS_KNOWLEDGE
        self.subjects = list(MATHEMATICS_KNOWLEDGE.keys())
        print(f"✅ Complete Math System initialized")
        print(f"   📐 {len(self.subjects)} major areas")
    
    def get_subject(self, subject: str) -> Dict:
        return self.knowledge.get(subject, {})
    
    def get_topic(self, subject: str, topic: str) -> Any:
        subj = self.get_subject(subject)
        return subj.get("topics", {}).get(topic, {})
    
    def search(self, query: str) -> List[Dict]:
        results = []
        query_lower = query.lower()
        
        def search_dict(d, path=""):
            if isinstance(d, dict):
                for k, v in d.items():
                    new_path = f"{path}/{k}" if path else k
                    if query_lower in k.lower():
                        results.append({"path": new_path, "content": v})
                    search_dict(v, new_path)
            elif isinstance(d, str) and query_lower in d.lower():
                results.append({"path": path, "content": d})
            elif isinstance(d, list):
                for item in d:
                    if isinstance(item, str) and query_lower in item.lower():
                        results.append({"path": path, "content": item})
        
        search_dict(self.knowledge)
        return results[:20]  # Limit results


_math_system = None

def get_math_system() -> CompleteMathSystem:
    global _math_system
    if _math_system is None:
        _math_system = CompleteMathSystem()
    return _math_system


if __name__ == "__main__":
    math = get_math_system()
    
    print("\n--- Calculus Derivatives ---")
    deriv = math.get_topic("calculus", "derivatives")
    print(f"Rules: {list(deriv.get('rules', {}).keys())}")
    
    print("\n--- Search: 'pythagorean' ---")
    results = math.search("pythagorean")
    for r in results[:5]:
        print(f"  {r['path']}: {r['content']}")
