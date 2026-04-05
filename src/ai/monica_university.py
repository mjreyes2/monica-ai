"""
Monica AI - University-Level Teaching System

Comprehensive teaching across 20+ academic subjects with:
- Deep conceptual knowledge (not skeleton data)
- Quiz system with multiple question types
- Progress tracking per subject/topic
- Integration with downloaded textbook PDFs
- Adaptive difficulty based on performance

Subjects: Mathematics, Chemistry, Statistics, Research Methods, Psychology,
Biology, Physics, Engineering, Drama, Computer Science, Electrical Engineering,
Geography, Geometry, Telemetry, Aeronautics, Microbiology, Human Anatomy,
Human Sexuality, The Brain, The Nervous System
"""

import json
import random
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger("Monica.University")


@dataclass
class QuizQuestion:
    subject: str
    topic: str
    question: str
    correct_answer: str
    wrong_answers: List[str]
    explanation: str
    difficulty: str = "intermediate"  # beginner, intermediate, advanced


@dataclass
class TopicProgress:
    times_studied: int = 0
    quiz_correct: int = 0
    quiz_wrong: int = 0
    last_studied: float = 0.0
    mastered: bool = False


@dataclass 
class SubjectProgress:
    topics: Dict[str, TopicProgress] = field(default_factory=dict)
    total_time_minutes: float = 0.0


# ============================================================
# SUBJECT KNOWLEDGE DATABASE
# Each subject has: overview, topics with deep content, quiz questions
# ============================================================

SUBJECTS = {}

# ---------- MATHEMATICS ----------
SUBJECTS["mathematics"] = {
    "name": "Mathematics",
    "overview": "The study of numbers, quantities, structures, patterns, and change. Mathematics is the foundation of all sciences and engineering.",
    "topics": {
        "algebra": {
            "title": "Algebra",
            "content": """Algebra is the branch of mathematics dealing with symbols and rules for manipulating those symbols. It is the unifying thread of almost all mathematics.

KEY CONCEPTS:
- Variables and Expressions: A variable represents an unknown quantity. An expression like 3x + 5 combines variables, constants, and operations.
- Linear Equations: ax + b = 0. The solution is x = -b/a. These graph as straight lines.
- Quadratic Equations: ax^2 + bx + c = 0. Solutions via factoring, completing the square, or the quadratic formula: x = (-b +/- sqrt(b^2 - 4ac)) / 2a.
- The discriminant (b^2 - 4ac) determines the nature of roots: positive = 2 real roots, zero = 1 repeated root, negative = 2 complex roots.
- Systems of Equations: Multiple equations with multiple unknowns. Solved by substitution, elimination, or matrices.
- Polynomials: Expressions with multiple terms. Degree determines behavior. Factor theorem: if f(a) = 0, then (x-a) is a factor.
- Rational Expressions: Fractions with polynomials. Domain excludes values making denominator zero.
- Inequalities: Similar to equations but direction of inequality flips when multiplying/dividing by negative numbers.
- Logarithms: Inverse of exponentiation. log_b(x) = y means b^y = x. Properties: log(ab) = log(a) + log(b), log(a/b) = log(a) - log(b), log(a^n) = n*log(a).
- Sequences and Series: Arithmetic (common difference d), Geometric (common ratio r). Sum formulas: arithmetic S = n/2(a1 + an), geometric S = a1(1-r^n)/(1-r).""",
            "key_formulas": ["ax^2+bx+c=0 -> x=(-b+/-sqrt(b^2-4ac))/2a", "log_b(xy)=log_b(x)+log_b(y)", "S_n=n/2(a_1+a_n)"],
        },
        "calculus": {
            "title": "Calculus",
            "content": """Calculus studies continuous change through derivatives (rates of change) and integrals (accumulation).

DIFFERENTIAL CALCULUS:
- Limits: lim(x->a) f(x) = L means f(x) approaches L as x approaches a. Foundation of all calculus.
- Derivatives: f'(x) = lim(h->0) [f(x+h) - f(x)] / h. Measures instantaneous rate of change.
- Rules: Power rule (d/dx x^n = nx^(n-1)), Product rule (fg)' = f'g + fg', Quotient rule, Chain rule (d/dx f(g(x)) = f'(g(x))*g'(x)).
- Applications: velocity/acceleration, optimization (find max/min by setting f'(x)=0), related rates, linear approximation.
- Mean Value Theorem: If f is continuous on [a,b] and differentiable on (a,b), there exists c in (a,b) where f'(c) = (f(b)-f(a))/(b-a).

INTEGRAL CALCULUS:
- Definite integral: integral from a to b of f(x)dx = area under curve.
- Fundamental Theorem: If F'(x) = f(x), then integral from a to b of f(x)dx = F(b) - F(a).
- Techniques: substitution, integration by parts (integral u dv = uv - integral v du), partial fractions, trigonometric substitution.
- Applications: area between curves, volumes of revolution (disk/washer/shell methods), arc length, work, center of mass.

MULTIVARIABLE CALCULUS:
- Partial derivatives, gradient vectors, directional derivatives.
- Multiple integrals (double, triple), change of variables (Jacobian).
- Vector calculus: line integrals, surface integrals, Green's theorem, Stokes' theorem, Divergence theorem.""",
            "key_formulas": ["f'(x)=lim(h->0)[f(x+h)-f(x)]/h", "integral f(x)dx = F(x)+C where F'=f", "(fg)'=f'g+fg'"],
        },
        "linear_algebra": {
            "title": "Linear Algebra",
            "content": """Study of vectors, matrices, linear transformations, and vector spaces.

VECTORS: Quantities with magnitude and direction. Addition, scalar multiplication, dot product (a.b = |a||b|cos(theta)), cross product.
MATRICES: Rectangular arrays of numbers. Operations: addition, scalar multiplication, matrix multiplication (AB != BA in general).
- Determinant: scalar value encoding volume scaling. det(A) = 0 means A is singular (not invertible).
- Inverse: A^(-1) exists iff det(A) != 0. AA^(-1) = I (identity matrix).
- Eigenvalues/Eigenvectors: Av = lambda*v. Found by solving det(A - lambda*I) = 0. Critical in physics, engineering, data science.
- Linear transformations: functions T: V -> W preserving addition and scalar multiplication.
- Vector spaces: sets closed under addition and scalar multiplication. Basis, dimension, span, linear independence.
- Applications: solving systems of equations (Gaussian elimination), computer graphics, quantum mechanics, machine learning (PCA, SVD).""",
            "key_formulas": ["Av=lambda*v (eigenvalue equation)", "det(A-lambda*I)=0", "a.b=|a||b|cos(theta)"],
        },
        "geometry_and_trigonometry": {
            "title": "Geometry & Trigonometry",
            "content": """Geometry studies shapes, sizes, positions. Trigonometry studies relationships between angles and sides of triangles.

EUCLIDEAN GEOMETRY: Points, lines, planes, angles. Parallel lines cut by transversals create equal/supplementary angles.
- Triangles: angle sum = 180 degrees. Types: equilateral, isosceles, scalene, right. Area = (1/2)bh.
- Pythagorean theorem: a^2 + b^2 = c^2 (right triangles only).
- Circles: circumference = 2*pi*r, area = pi*r^2. Inscribed angle = half central angle.
- Similar triangles: proportional sides, equal angles. AA, SAS, SSS similarity.

TRIGONOMETRY: sin, cos, tan and their inverses.
- Unit circle: sin(theta) = y-coordinate, cos(theta) = x-coordinate.
- Identities: sin^2 + cos^2 = 1, tan = sin/cos, double angle formulas, sum/difference formulas.
- Law of sines: a/sin(A) = b/sin(B) = c/sin(C). Law of cosines: c^2 = a^2 + b^2 - 2ab*cos(C).
- Applications: surveying, navigation, wave analysis, signal processing.

ANALYTIC GEOMETRY: Coordinate systems, distance formula, midpoint formula.
- Conic sections: circles (x^2+y^2=r^2), ellipses, parabolas, hyperbolas.
- Transformations: translation, rotation, reflection, dilation.""",
            "key_formulas": ["a^2+b^2=c^2", "sin^2(x)+cos^2(x)=1", "A=pi*r^2"],
        },
    },
    "quiz_questions": [
        QuizQuestion("mathematics", "algebra", "What is the quadratic formula for ax^2+bx+c=0?", "x = (-b +/- sqrt(b^2-4ac)) / 2a", ["x = -b/2a", "x = (-b +/- sqrt(b^2+4ac)) / 2a", "x = (b +/- sqrt(b^2-4ac)) / a"], "The quadratic formula gives both solutions to any quadratic equation."),
        QuizQuestion("mathematics", "algebra", "If the discriminant b^2-4ac is negative, how many real solutions does the quadratic have?", "Zero real solutions (two complex solutions)", ["One real solution", "Two real solutions", "Infinitely many solutions"], "A negative discriminant means the square root is imaginary, giving complex conjugate roots."),
        QuizQuestion("mathematics", "calculus", "What is the derivative of x^n?", "n*x^(n-1)", ["x^(n+1)/(n+1)", "n*x^n", "x^(n-1)"], "The power rule: bring the exponent down and reduce it by 1."),
        QuizQuestion("mathematics", "calculus", "The Fundamental Theorem of Calculus connects which two operations?", "Differentiation and integration", ["Addition and subtraction", "Multiplication and division", "Limits and sequences"], "It states that integration and differentiation are inverse operations."),
        QuizQuestion("mathematics", "linear_algebra", "What does it mean if the determinant of a matrix is zero?", "The matrix is singular (not invertible)", ["The matrix is the identity", "The matrix has all positive eigenvalues", "The matrix is symmetric"], "A zero determinant means the transformation collapses space, losing dimension."),
        QuizQuestion("mathematics", "geometry_and_trigonometry", "In a right triangle, what does the Pythagorean theorem state?", "a^2 + b^2 = c^2 where c is the hypotenuse", ["a + b = c", "a^2 + b^2 = c", "a*b = c^2"], "The sum of squares of the two shorter sides equals the square of the hypotenuse."),
    ],
}

# ---------- CHEMISTRY ----------
SUBJECTS["chemistry"] = {
    "name": "Chemistry",
    "overview": "The study of matter, its properties, composition, structure, and the changes it undergoes during chemical reactions.",
    "topics": {
        "atomic_structure": {
            "title": "Atomic Structure",
            "content": """Atoms are the fundamental building blocks of all matter.

SUBATOMIC PARTICLES: Protons (positive, in nucleus), Neutrons (neutral, in nucleus), Electrons (negative, in orbitals).
- Atomic number (Z) = number of protons = defines the element.
- Mass number (A) = protons + neutrons. Isotopes have same Z but different A.
- Electron configuration: electrons fill orbitals following the Aufbau principle (lowest energy first), Pauli exclusion principle (max 2 electrons per orbital with opposite spins), and Hund's rule (fill degenerate orbitals singly first).
- Orbital shapes: s (spherical), p (dumbbell), d (clover), f (complex).
- Quantum numbers: n (principal/shell), l (angular momentum/subshell), ml (magnetic/orbital orientation), ms (spin +1/2 or -1/2).
- Periodic trends: atomic radius decreases across a period (more protons pull electrons closer), increases down a group. Ionization energy and electronegativity increase across a period.""",
            "key_formulas": ["Z = atomic number = protons", "A = mass number = protons + neutrons"],
        },
        "chemical_bonding": {
            "title": "Chemical Bonding",
            "content": """Atoms bond to achieve stable electron configurations (usually octet rule).

IONIC BONDS: Transfer of electrons between metals and nonmetals. Na gives electron to Cl -> Na+ Cl-. Strong electrostatic attraction. High melting points, conduct electricity when dissolved.
COVALENT BONDS: Sharing of electron pairs between nonmetals. H2: each H shares 1 electron. Can be single, double, or triple bonds.
- Polar covalent: unequal sharing due to electronegativity difference (e.g., H-Cl). Creates dipole moment.
- Nonpolar covalent: equal sharing (e.g., O2, N2).
METALLIC BONDS: Sea of delocalized electrons shared among metal cations. Explains conductivity, malleability, luster.
MOLECULAR GEOMETRY (VSEPR): Electron pairs repel each other to minimize energy.
- 2 electron groups: linear (180 degrees). 3: trigonal planar (120). 4: tetrahedral (109.5). 5: trigonal bipyramidal. 6: octahedral.
- Lone pairs compress bond angles (e.g., water is bent ~104.5 degrees, not tetrahedral 109.5).
INTERMOLECULAR FORCES: London dispersion (all molecules), dipole-dipole (polar molecules), hydrogen bonding (H bonded to N, O, or F).""",
            "key_formulas": ["Bond order = (bonding electrons - antibonding electrons) / 2"],
        },
        "reactions_stoichiometry": {
            "title": "Reactions & Stoichiometry",
            "content": """Chemical reactions transform reactants into products while conserving mass and atoms.

TYPES OF REACTIONS:
- Synthesis: A + B -> AB (e.g., 2Na + Cl2 -> 2NaCl)
- Decomposition: AB -> A + B (e.g., 2H2O -> 2H2 + O2)
- Single replacement: A + BC -> AC + B (activity series determines feasibility)
- Double replacement: AB + CD -> AD + CB (precipitation, acid-base)
- Combustion: fuel + O2 -> CO2 + H2O (exothermic)
- Redox: electron transfer. Oxidation = loss of electrons. Reduction = gain of electrons.

STOICHIOMETRY: Quantitative relationships in reactions.
- Mole concept: 1 mole = 6.022 x 10^23 particles (Avogadro's number).
- Molar mass: mass of 1 mole in grams (from periodic table).
- Balanced equations give mole ratios. E.g., 2H2 + O2 -> 2H2O means 2 mol H2 reacts with 1 mol O2.
- Limiting reagent: the reactant that runs out first determines the maximum product.
- Percent yield = (actual yield / theoretical yield) x 100%.

SOLUTIONS: Molarity (M) = moles solute / liters solution. Dilution: M1V1 = M2V2.""",
            "key_formulas": ["n = mass / molar_mass", "M = mol / L", "M1V1 = M2V2"],
        },
        "thermodynamics_kinetics": {
            "title": "Thermodynamics & Kinetics",
            "content": """Thermodynamics studies energy changes; kinetics studies reaction rates.

THERMODYNAMICS:
- First Law: Energy is conserved. delta_U = q + w (internal energy = heat + work).
- Enthalpy (H): Heat at constant pressure. delta_H < 0 = exothermic, delta_H > 0 = endothermic.
- Hess's Law: Total enthalpy change is path-independent (sum of steps = overall).
- Entropy (S): Measure of disorder. Second Law: total entropy of universe always increases.
- Gibbs Free Energy: delta_G = delta_H - T*delta_S. If delta_G < 0, reaction is spontaneous.

KINETICS:
- Rate = change in concentration / time. Rate = k[A]^m[B]^n (rate law).
- Order: zero (rate independent of concentration), first (rate proportional to [A]), second (rate proportional to [A]^2).
- Activation energy (Ea): minimum energy needed for reaction. Arrhenius equation: k = A*e^(-Ea/RT).
- Catalysts lower Ea without being consumed. Enzymes are biological catalysts.
- Collision theory: molecules must collide with correct orientation and sufficient energy.""",
            "key_formulas": ["delta_G = delta_H - T*delta_S", "k = A*e^(-Ea/RT)", "Rate = k[A]^m[B]^n"],
        },
        "organic_chemistry": {
            "title": "Organic Chemistry",
            "content": """Study of carbon-containing compounds — the chemistry of life.

HYDROCARBONS: Alkanes (C-C single bonds, saturated), Alkenes (C=C double bond), Alkynes (C triple bond C), Aromatics (benzene ring).
- Naming: methane (1C), ethane (2C), propane (3C), butane (4C), pentane (5C)...
- Isomers: same formula, different structure. Constitutional isomers, stereoisomers (cis/trans, enantiomers).

FUNCTIONAL GROUPS:
- Alcohols (-OH): methanol, ethanol. Hydrogen bonding gives high boiling points.
- Aldehydes (-CHO) and Ketones (C=O): carbonyl chemistry.
- Carboxylic acids (-COOH): acetic acid, amino acids. Weak acids.
- Amines (-NH2): organic bases. Building blocks of proteins.
- Esters (-COO-): formed from acid + alcohol. Responsible for fruity smells.
- Ethers (-O-): R-O-R. Diethyl ether was an early anesthetic.

REACTIONS: Substitution (SN1, SN2), Elimination (E1, E2), Addition (to double bonds), Polymerization.
BIOCHEMISTRY: Proteins (amino acid polymers), Carbohydrates (sugars), Lipids (fats), Nucleic acids (DNA/RNA).""",
            "key_formulas": ["CnH(2n+2) for alkanes", "CnH(2n) for alkenes"],
        },
    },
    "quiz_questions": [
        QuizQuestion("chemistry", "atomic_structure", "What quantum number describes the shape of an orbital?", "Angular momentum quantum number (l)", ["Principal quantum number (n)", "Magnetic quantum number (ml)", "Spin quantum number (ms)"], "l=0 is s (sphere), l=1 is p (dumbbell), l=2 is d, l=3 is f."),
        QuizQuestion("chemistry", "chemical_bonding", "What type of bond involves the transfer of electrons?", "Ionic bond", ["Covalent bond", "Metallic bond", "Hydrogen bond"], "Ionic bonds form between metals (lose electrons) and nonmetals (gain electrons)."),
        QuizQuestion("chemistry", "reactions_stoichiometry", "What is Avogadro's number?", "6.022 x 10^23", ["3.14 x 10^8", "6.626 x 10^-34", "1.602 x 10^-19"], "One mole of any substance contains 6.022 x 10^23 particles."),
        QuizQuestion("chemistry", "thermodynamics_kinetics", "If delta_G is negative, the reaction is:", "Spontaneous", ["Non-spontaneous", "At equilibrium", "Impossible"], "Negative Gibbs free energy means the reaction will proceed without external energy input."),
    ],
}

# Store remaining subjects in a continuation module to keep file size manageable
# Import them from the companion file
from ai.monica_university_subjects import SUBJECTS_PART2

SUBJECTS.update(SUBJECTS_PART2)


class MonicaUniversity:
    """Monica's comprehensive teaching system for 20+ academic subjects."""

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            try:
                from config.settings import config
                data_dir = Path(config.BASE_DIR) / "data" / "user_profile"
            except Exception:
                data_dir = Path("data/user_profile")

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file = self.data_dir / "university_progress.json"
        self.progress: Dict[str, SubjectProgress] = {}
        self._load_progress()
        logger.info(f"MonicaUniversity initialized with {len(SUBJECTS)} subjects")

    def _load_progress(self):
        try:
            if self.progress_file.exists():
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for subj, sp in data.items():
                    progress = SubjectProgress()
                    progress.total_time_minutes = sp.get("total_time_minutes", 0)
                    for topic_name, tp in sp.get("topics", {}).items():
                        progress.topics[topic_name] = TopicProgress(**tp)
                    self.progress[subj] = progress
        except Exception as e:
            logger.debug(f"Could not load university progress: {e}")

    def _save_progress(self):
        try:
            data = {}
            for subj, sp in self.progress.items():
                data[subj] = {
                    "total_time_minutes": sp.total_time_minutes,
                    "topics": {k: asdict(v) for k, v in sp.topics.items()},
                }
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.debug(f"Could not save progress: {e}")

    def get_subjects_list(self) -> str:
        lines = ["I can teach you these subjects:\n"]
        for key, subj in sorted(SUBJECTS.items()):
            topic_count = len(subj.get("topics", {}))
            quiz_count = len(subj.get("quiz_questions", []))
            prog = self.progress.get(key)
            status = ""
            if prog and prog.topics:
                mastered = sum(1 for t in prog.topics.values() if t.mastered)
                status = f" [{mastered}/{topic_count} mastered]"
            lines.append(f"  - {subj['name']} ({topic_count} topics, {quiz_count} quiz questions){status}")
        lines.append(f"\nTotal: {len(SUBJECTS)} subjects")
        lines.append("Say 'teach me [subject]' or 'quiz me on [subject]' to begin.")
        return "\n".join(lines)

    def teach_subject(self, subject_key: str, topic_key: str = None) -> str:
        subj = SUBJECTS.get(subject_key.lower())
        if not subj:
            return f"Subject '{subject_key}' not found. {self.get_subjects_list()}"

        topics = subj.get("topics", {})
        if not topics:
            return f"No detailed topics available for {subj['name']} yet."

        if topic_key and topic_key in topics:
            topic = topics[topic_key]
            self._record_study(subject_key, topic_key)
            formulas = topic.get("key_formulas", [])
            formula_str = "\n  ".join(formulas) if formulas else "None listed"
            return f"## {topic['title']}\n\n{topic['content']}\n\nKey Formulas:\n  {formula_str}"

        # No specific topic — give overview + topic list
        topic_list = "\n".join(f"  - {k}: {v['title']}" for k, v in topics.items())
        return f"## {subj['name']}\n\n{subj['overview']}\n\nAvailable Topics:\n{topic_list}\n\nSay 'teach me {subject_key} [topic]' for details."

    def quiz(self, subject_key: str, count: int = 5) -> List[Dict[str, Any]]:
        subj = SUBJECTS.get(subject_key.lower())
        if not subj:
            return []
        questions = subj.get("quiz_questions", [])
        if not questions:
            return []
        selected = random.sample(questions, min(count, len(questions)))
        result = []
        for q in selected:
            options = [q.correct_answer] + q.wrong_answers[:3]
            random.shuffle(options)
            result.append({
                "question": q.question,
                "options": options,
                "correct": q.correct_answer,
                "explanation": q.explanation,
                "topic": q.topic,
                "difficulty": q.difficulty,
            })
        return result

    def check_answer(self, subject_key: str, topic: str, user_answer: str, correct_answer: str) -> Tuple[bool, str]:
        is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
        if subject_key not in self.progress:
            self.progress[subject_key] = SubjectProgress()
        sp = self.progress[subject_key]
        if topic not in sp.topics:
            sp.topics[topic] = TopicProgress()
        tp = sp.topics[topic]
        if is_correct:
            tp.quiz_correct += 1
        else:
            tp.quiz_wrong += 1
        if tp.quiz_correct >= 10 and tp.quiz_correct / max(1, tp.quiz_correct + tp.quiz_wrong) > 0.8:
            tp.mastered = True
        self._save_progress()
        return is_correct, "Correct!" if is_correct else f"The correct answer is: {correct_answer}"

    def _record_study(self, subject_key: str, topic_key: str):
        if subject_key not in self.progress:
            self.progress[subject_key] = SubjectProgress()
        sp = self.progress[subject_key]
        if topic_key not in sp.topics:
            sp.topics[topic_key] = TopicProgress()
        tp = sp.topics[topic_key]
        tp.times_studied += 1
        tp.last_studied = time.time()
        self._save_progress()

    def get_teaching_context(self, user_text: str) -> str:
        text_lower = user_text.lower()
        context_parts = []
        for key, subj in SUBJECTS.items():
            if key in text_lower or subj["name"].lower() in text_lower:
                context_parts.append(f"[SUBJECT: {subj['name']}]\n{subj['overview']}")
                for tk, tv in subj.get("topics", {}).items():
                    if tk in text_lower or tv["title"].lower() in text_lower:
                        context_parts.append(f"\n[TOPIC: {tv['title']}]\n{tv['content'][:1500]}")
                break
        return "\n".join(context_parts) if context_parts else ""

    def get_progress_summary(self) -> str:
        if not self.progress:
            return "No study progress yet. Start by saying 'teach me [subject]'."
        lines = ["Your Study Progress:\n"]
        for subj_key, sp in sorted(self.progress.items()):
            subj_name = SUBJECTS.get(subj_key, {}).get("name", subj_key)
            mastered = sum(1 for t in sp.topics.values() if t.mastered)
            total = len(sp.topics)
            correct = sum(t.quiz_correct for t in sp.topics.values())
            wrong = sum(t.quiz_wrong for t in sp.topics.values())
            lines.append(f"  {subj_name}: {mastered}/{total} topics mastered, {correct}/{correct+wrong} quiz correct")
        return "\n".join(lines)


# Singleton
_university = None

def get_university() -> MonicaUniversity:
    global _university
    if _university is None:
        _university = MonicaUniversity()
    return _university
