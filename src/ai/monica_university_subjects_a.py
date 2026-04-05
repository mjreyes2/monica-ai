"""
Monica University - Subjects Part A
Statistics, Research Methods, Psychology, Biology
"""
from ai.monica_university import QuizQuestion

SUBJECTS_A = {}

# ---------- STATISTICS ----------
SUBJECTS_A["statistics"] = {
    "name": "Statistics",
    "overview": "The science of collecting, analyzing, interpreting, and presenting data. Statistics underpins scientific research, business decisions, medicine, and public policy.",
    "topics": {
        "descriptive_statistics": {
            "title": "Descriptive Statistics",
            "content": """Descriptive statistics summarize and organize data.

MEASURES OF CENTRAL TENDENCY:
- Mean: Sum of values / count. Sensitive to outliers.
- Median: Middle value when ordered. Robust to outliers.
- Mode: Most frequent value.

MEASURES OF SPREAD:
- Range: Max - Min.
- Variance: Average squared deviation from mean. Sample: s^2 = sum(xi-xbar)^2/(n-1).
- Standard Deviation: sqrt(variance). Same units as data.
- IQR: Q3 - Q1. Middle 50% of data.

DISTRIBUTIONS:
- Normal (bell curve): mean=median=mode. 68% within 1 SD, 95% within 2 SD, 99.7% within 3 SD.
- Skewness: Right-skewed = mean > median. Left-skewed = mean < median.
- Z-score: z = (x - mean) / SD. How many SDs from the mean.""",
            "key_formulas": ["mean = sum(x)/n", "s^2 = sum(xi-xbar)^2/(n-1)", "z = (x-mu)/sigma"],
        },
        "probability": {
            "title": "Probability Theory",
            "content": """Probability quantifies uncertainty.

RULES:
- P(A) between 0 and 1. P(not A) = 1 - P(A).
- Addition: P(A or B) = P(A) + P(B) - P(A and B).
- Multiplication (independent): P(A and B) = P(A) * P(B).
- Conditional: P(A|B) = P(A and B) / P(B).
- Bayes' Theorem: P(A|B) = P(B|A)*P(A) / P(B).

DISTRIBUTIONS:
- Binomial: n trials, probability p. P(X=k) = C(n,k)*p^k*(1-p)^(n-k). Mean=np.
- Normal: Continuous bell curve. Central Limit Theorem: sample means approach normal.
- Poisson: Events in interval. P(X=k) = lambda^k * e^(-lambda) / k!.
- t-distribution: Like normal but heavier tails for small samples.
- Chi-square: Goodness-of-fit and independence tests.""",
            "key_formulas": ["P(A|B) = P(B|A)*P(A)/P(B)", "E(X) = sum(x*P(x))"],
        },
        "inferential_statistics": {
            "title": "Inferential Statistics",
            "content": """Making conclusions about populations from samples.

HYPOTHESIS TESTING:
- Null hypothesis (H0): no effect. Alternative (H1): there is an effect.
- P-value: probability of data assuming H0 true. If p < alpha (0.05), reject H0.
- Type I error (false positive): rejecting true H0. Type II (false negative): failing to reject false H0.
- Power = 1 - beta = probability of correctly rejecting false H0.

COMMON TESTS:
- Z-test / t-test: Compare means. t-test for small samples or unknown sigma.
- Chi-square: Categorical data independence/goodness-of-fit.
- ANOVA: Compare 3+ group means. F = between-group variance / within-group variance.
- Correlation: Pearson r (-1 to +1). r^2 = variance explained.

CONFIDENCE INTERVALS: CI = xbar +/- z*(sigma/sqrt(n)).
REGRESSION: y = a + bx. Least squares. R^2 measures fit.""",
            "key_formulas": ["CI = xbar +/- z*(sigma/sqrt(n))", "t = (xbar-mu)/(s/sqrt(n))"],
        },
    },
    "quiz_questions": [
        QuizQuestion("statistics", "descriptive_statistics", "What percentage of data falls within 2 SDs of the mean in a normal distribution?", "Approximately 95%", ["About 68%", "About 50%", "About 99.7%"], "The empirical rule: 68-95-99.7 for 1-2-3 standard deviations."),
        QuizQuestion("statistics", "probability", "In Bayes' theorem, what is P(A) called?", "The prior probability", ["The posterior", "The likelihood", "The marginal"], "P(A) is what we believe before seeing evidence B."),
        QuizQuestion("statistics", "inferential_statistics", "If p-value is 0.03 and alpha is 0.05, what do we conclude?", "Reject the null hypothesis", ["Fail to reject H0", "Accept H0", "Inconclusive"], "0.03 < 0.05, so result is statistically significant."),
    ],
}

# ---------- RESEARCH METHODS ----------
SUBJECTS_A["research_methods"] = {
    "name": "Research Methods",
    "overview": "Systematic approaches to investigating questions through empirical observation and analysis.",
    "topics": {
        "scientific_method": {
            "title": "The Scientific Method",
            "content": """Steps: 1) Observation 2) Question 3) Literature Review 4) Hypothesis (testable, falsifiable) 5) Experimental Design 6) Data Collection 7) Analysis 8) Conclusion 9) Peer Review & Replication.

KEY PRINCIPLES:
- Falsifiability (Popper): Claims must be capable of being proven false.
- Operationalization: Define abstract concepts in measurable terms.
- Reproducibility: Others should replicate your results.
- Parsimony (Occam's Razor): Simplest explanation is preferred.""",
            "key_formulas": [],
        },
        "experimental_design": {
            "title": "Experimental Design",
            "content": """Experiments establish cause-and-effect.

COMPONENTS: Independent Variable (manipulated), Dependent Variable (measured), Control Group, Experimental Group, Confounding Variables (must be controlled).

DESIGNS:
- Between-subjects: Different participants per condition. Random assignment.
- Within-subjects: Same participants, all conditions. Order effects possible.
- Factorial: 2+ IVs. Reveals interaction effects.
- Quasi-experimental: No random assignment. Weaker causal claims.
- Correlational: Measures relationship without manipulation. Correlation != causation.

VALIDITY: Internal (IV caused DV change?), External (generalizable?), Construct (measuring what we think?).
SAMPLING: Random, Stratified, Convenience, Snowball.""",
            "key_formulas": [],
        },
        "qualitative_methods": {
            "title": "Qualitative Research",
            "content": """Non-numerical data exploration.

APPROACHES: Interviews (structured/semi/unstructured), Focus Groups, Ethnography (immersive observation), Case Study, Content Analysis, Grounded Theory (theory from data), Phenomenology (lived experience).

ANALYSIS: Thematic analysis (identify patterns), Coding (open, axial, selective), Triangulation (multiple sources), Saturation (no new themes emerging).

STRENGTHS: Rich detail, context, meaning. Good for exploring new phenomena.
LIMITATIONS: Subjective, hard to generalize, time-intensive, researcher bias.""",
            "key_formulas": [],
        },
    },
    "quiz_questions": [
        QuizQuestion("research_methods", "scientific_method", "What makes a hypothesis scientific (Popper)?", "It must be falsifiable", ["Must be proven true", "Must be popular", "Must be complex"], "Falsifiability: possible evidence could prove it wrong."),
        QuizQuestion("research_methods", "experimental_design", "What is the manipulated variable called?", "Independent variable", ["Dependent variable", "Confounding variable", "Control variable"], "The IV is deliberately changed to see its effect on the DV."),
    ],
}

# ---------- PSYCHOLOGY ----------
SUBJECTS_A["psychology"] = {
    "name": "Psychology",
    "overview": "Scientific study of mind and behavior, encompassing biological, cognitive, developmental, social, and clinical perspectives.",
    "topics": {
        "biological_psychology": {
            "title": "Biological Psychology",
            "content": """How brain and body create behavior.

NEURONS: ~86 billion. Dendrites receive, axon transmits, synaptic terminals release neurotransmitters.
- Action potential: All-or-none. Resting -70mV -> depolarization -> threshold -> fire -> repolarize.

KEY NEUROTRANSMITTERS:
- Dopamine: Reward, motivation, movement. Low=Parkinson's.
- Serotonin: Mood, sleep, appetite. Low=depression.
- GABA: Primary inhibitory. Reduces neural activity.
- Glutamate: Primary excitatory. Learning/memory.
- Norepinephrine: Arousal, alertness, fight-or-flight.
- Acetylcholine: Muscle movement, memory. Depleted in Alzheimer's.
- Endorphins: Natural pain relief.

BRAIN REGIONS: Frontal (planning, personality), Temporal (hearing, memory), Parietal (touch, spatial), Occipital (vision), Cerebellum (coordination), Amygdala (fear), Hippocampus (memory), Hypothalamus (homeostasis).""",
            "key_formulas": [],
        },
        "learning_and_memory": {
            "title": "Learning & Memory",
            "content": """CLASSICAL CONDITIONING (Pavlov): US->UR naturally. Pair NS with US. NS becomes CS->CR.
Extinction: CR fades without US. Spontaneous recovery: CR reappears.

OPERANT CONDITIONING (Skinner):
- Positive reinforcement: Add reward -> increase behavior.
- Negative reinforcement: Remove aversive -> increase behavior.
- Positive punishment: Add aversive -> decrease behavior.
- Negative punishment: Remove pleasant -> decrease behavior.
- Schedules: Fixed/variable ratio/interval. Variable-ratio most resistant to extinction.

MEMORY: Sensory (<1s) -> Short-term (~30s, 7+/-2 items) -> Long-term.
- Declarative: Episodic (events) + Semantic (facts).
- Procedural: Skills, habits (implicit).
- Encoding: Deep processing > shallow. Elaborative rehearsal > rote.
- Forgetting: Decay, interference, retrieval failure.""",
            "key_formulas": [],
        },
        "abnormal_psychology": {
            "title": "Abnormal Psychology",
            "content": """ANXIETY DISORDERS: GAD (excessive worry), Panic Disorder, Phobias, Social Anxiety, OCD (obsessions+compulsions), PTSD (after trauma).

MOOD DISORDERS: Major Depression (sadness, fatigue, worthlessness 2+ weeks), Bipolar (depression + mania cycles).

SCHIZOPHRENIA: Positive symptoms (hallucinations, delusions), Negative (flat affect, avolition), Cognitive (memory, attention deficits). Dopamine hypothesis.

PERSONALITY DISORDERS: Borderline (instability), Narcissistic (grandiosity), Antisocial (disregard for rights).

TREATMENTS: CBT, psychodynamic, humanistic therapy. Medications: SSRIs, antipsychotics, mood stabilizers. Combined approach often most effective.""",
            "key_formulas": [],
        },
        "developmental_psychology": {
            "title": "Developmental Psychology",
            "content": """PIAGET'S STAGES: 1) Sensorimotor (0-2, object permanence) 2) Preoperational (2-7, egocentrism) 3) Concrete Operational (7-11, conservation) 4) Formal Operational (11+, abstract reasoning).

ERIKSON'S 8 STAGES: Trust vs Mistrust -> Autonomy vs Shame -> Initiative vs Guilt -> Industry vs Inferiority -> Identity vs Role Confusion -> Intimacy vs Isolation -> Generativity vs Stagnation -> Integrity vs Despair.

KOHLBERG'S MORAL DEVELOPMENT: Preconventional (self-interest), Conventional (social norms), Postconventional (universal principles).

ATTACHMENT (Bowlby/Ainsworth): Secure, Avoidant, Anxious-ambivalent, Disorganized.

ADOLESCENCE: Identity formation, prefrontal cortex matures ~25, risk-taking.
AGING: Fluid intelligence declines, crystallized stable/increases. Neuroplasticity persists.""",
            "key_formulas": [],
        },
    },
    "quiz_questions": [
        QuizQuestion("psychology", "biological_psychology", "Which neurotransmitter is associated with reward?", "Dopamine", ["Serotonin", "GABA", "Acetylcholine"], "Dopamine drives the reward system. Linked to addiction and Parkinson's."),
        QuizQuestion("psychology", "learning_and_memory", "What is negative reinforcement?", "Removing an aversive stimulus to increase behavior", ["Adding punishment", "Taking away reward", "Ignoring behavior"], "Negative=remove, reinforcement=increase behavior."),
        QuizQuestion("psychology", "developmental_psychology", "When does object permanence develop (Piaget)?", "Sensorimotor stage (0-2 years)", ["Preoperational", "Concrete operational", "Formal operational"], "Object permanence develops around 8-12 months."),
    ],
}

# ---------- BIOLOGY ----------
SUBJECTS_A["biology"] = {
    "name": "Biology",
    "overview": "Study of living organisms: structure, function, growth, evolution, and ecosystem interactions.",
    "topics": {
        "cell_biology": {
            "title": "Cell Biology",
            "content": """Cells are the basic units of life.

PROKARYOTIC vs EUKARYOTIC: Prokaryotes (bacteria) lack nucleus. Eukaryotes (animals, plants, fungi) have membrane-bound organelles.

KEY ORGANELLES: Nucleus (DNA), Mitochondria (ATP via cellular respiration: C6H12O6+6O2->6CO2+6H2O+36ATP), ER (rough=protein, smooth=lipid), Golgi (packaging), Lysosomes (digestion), Ribosomes (protein synthesis), Cell Membrane (phospholipid bilayer), Chloroplasts (photosynthesis in plants).

CELL DIVISION:
- Mitosis: 1 cell -> 2 identical diploid cells. PMAT phases.
- Meiosis: 1 cell -> 4 haploid gametes. Crossing over creates diversity.
- Cell cycle: G1->S(DNA replication)->G2->M. Checkpoints prevent errors.""",
            "key_formulas": ["C6H12O6+6O2->6CO2+6H2O+~36ATP"],
        },
        "genetics": {
            "title": "Genetics",
            "content": """DNA STRUCTURE: Double helix. A-T, G-C base pairs. Replication is semi-conservative.

CENTRAL DOGMA: DNA->(transcription)->mRNA->(translation)->Protein.
- Codons: 3-base mRNA sequences code for amino acids. AUG=start, UAA/UAG/UGA=stop.

MENDELIAN GENETICS: Dominant/recessive alleles. Punnett squares. Monohybrid 3:1 ratio. Dihybrid 9:3:3:1.

BEYOND MENDEL: Incomplete dominance, Codominance (AB blood), Polygenic traits, X-linked inheritance.

MUTATIONS: Point mutations, insertions, deletions, frameshifts. Can be silent, harmful, or beneficial.""",
            "key_formulas": ["DNA: A-T, G-C", "RNA: A-U, G-C"],
        },
        "evolution": {
            "title": "Evolution",
            "content": """NATURAL SELECTION (Darwin): Variation exists -> struggle for survival -> fittest reproduce -> traits inherited.

EVIDENCE: Fossils, comparative anatomy (homologous structures), molecular biology (DNA similarity), biogeography, direct observation.

SELECTION TYPES: Directional (one extreme favored), Stabilizing (middle favored), Disruptive (both extremes), Sexual selection.

SPECIATION: Allopatric (geographic separation), Sympatric (same area, reproductive isolation).

HARDY-WEINBERG: p^2+2pq+q^2=1. Conditions: no mutation, random mating, no selection, large population, no migration. Deviation = evolution.""",
            "key_formulas": ["p^2+2pq+q^2=1", "p+q=1"],
        },
        "ecology": {
            "title": "Ecology",
            "content": """LEVELS: Organism->Population->Community->Ecosystem->Biome->Biosphere.

POPULATION: Exponential growth (dN/dt=rN), Logistic growth (dN/dt=rN(K-N)/K, K=carrying capacity).
r-selected: many offspring, little care. K-selected: few offspring, extensive care.

INTERACTIONS: Competition, Predation, Mutualism (both benefit), Commensalism (one benefits), Parasitism (one harmed).

ENERGY FLOW: Sun->Producers->Primary consumers->Secondary->Decomposers. ~10% energy transfer per level.
NUTRIENT CYCLES: Carbon, Nitrogen, Water, Phosphorus.""",
            "key_formulas": ["dN/dt=rN", "dN/dt=rN(K-N)/K"],
        },
    },
    "quiz_questions": [
        QuizQuestion("biology", "cell_biology", "What is the powerhouse of the cell?", "Mitochondria", ["Nucleus", "Ribosome", "Golgi"], "Mitochondria convert glucose to ATP energy."),
        QuizQuestion("biology", "genetics", "What is the central dogma?", "DNA -> RNA -> Protein", ["Protein->RNA->DNA", "RNA->DNA->Protein", "DNA->Protein->RNA"], "Information flows DNA through RNA to protein."),
        QuizQuestion("biology", "evolution", "What conditions maintain Hardy-Weinberg equilibrium?", "No mutation, random mating, no selection, large population, no migration", ["Only large population", "Only random mating", "Only no mutation"], "All five conditions must be met; violation means evolution."),
    ],
}
