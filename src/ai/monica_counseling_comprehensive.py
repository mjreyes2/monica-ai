"""
Monica's Comprehensive Counseling & Therapy Knowledge Base
Deep, evidence-based knowledge of all therapeutic modalities
With academic research integration and free literature sources
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

# FREE ACADEMIC RESEARCH SOURCES
ACADEMIC_SOURCES = {
    "pubmed": {
        "name": "PubMed / NCBI",
        "url": "https://pubmed.ncbi.nlm.nih.gov/",
        "api": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
        "description": "Free access to biomedical and life sciences literature",
        "type": "database"
    },
    "google_scholar": {
        "name": "Google Scholar",
        "url": "https://scholar.google.com/",
        "description": "Search across scholarly literature",
        "type": "search_engine"
    },
    "pmc": {
        "name": "PubMed Central (PMC)",
        "url": "https://www.ncbi.nlm.nih.gov/pmc/",
        "description": "Free full-text archive of biomedical and life sciences literature",
        "type": "database"
    },
    "cochrane": {
        "name": "Cochrane Library",
        "url": "https://www.cochranelibrary.com/",
        "description": "Systematic reviews of healthcare interventions",
        "type": "database"
    },
    "psycinfo_free": {
        "name": "APA PsycNet (Free Resources)",
        "url": "https://psycnet.apa.org/",
        "description": "Psychology research from APA",
        "type": "database"
    },
    "eric": {
        "name": "ERIC (Education Resources)",
        "url": "https://eric.ed.gov/",
        "description": "Education research and information",
        "type": "database"
    },
    "semantic_scholar": {
        "name": "Semantic Scholar",
        "url": "https://www.semanticscholar.org/",
        "api": "https://api.semanticscholar.org/",
        "description": "AI-powered research tool for scientific literature",
        "type": "search_engine"
    },
    "core": {
        "name": "CORE",
        "url": "https://core.ac.uk/",
        "description": "World's largest collection of open access research papers",
        "type": "database"
    },
    "doaj": {
        "name": "Directory of Open Access Journals",
        "url": "https://doaj.org/",
        "description": "Open access, peer-reviewed journals",
        "type": "database"
    },
    "arxiv": {
        "name": "arXiv",
        "url": "https://arxiv.org/",
        "description": "Open access to scientific papers (includes quantitative psychology)",
        "type": "preprint"
    }
}

# COMPREHENSIVE COUNSELING MODALITIES
COUNSELING_MODALITIES = {
    # COGNITIVE-BEHAVIORAL APPROACHES
    "cbt": {
        "name": "Cognitive Behavioral Therapy (CBT)",
        "founder": "Aaron Beck (1960s)",
        "theoretical_basis": "Thoughts, feelings, and behaviors are interconnected; changing maladaptive thoughts changes emotions and behaviors",
        "key_concepts": {
            "cognitive_distortions": [
                {"name": "All-or-nothing thinking", "description": "Seeing things in black and white categories"},
                {"name": "Overgeneralization", "description": "Seeing a single negative event as a never-ending pattern"},
                {"name": "Mental filter", "description": "Dwelling on negatives while filtering out positives"},
                {"name": "Disqualifying the positive", "description": "Rejecting positive experiences"},
                {"name": "Jumping to conclusions", "description": "Mind reading or fortune telling without evidence"},
                {"name": "Magnification/Minimization", "description": "Exaggerating negatives, shrinking positives"},
                {"name": "Emotional reasoning", "description": "Assuming feelings reflect reality"},
                {"name": "Should statements", "description": "Rigid rules about how things should be"},
                {"name": "Labeling", "description": "Attaching negative labels to self or others"},
                {"name": "Personalization", "description": "Blaming self for things outside one's control"}
            ],
            "cognitive_triad": "Negative views of self, world, and future (in depression)",
            "automatic_thoughts": "Spontaneous, often negative thoughts that arise in situations",
            "core_beliefs": "Deep, fundamental beliefs about self, others, and world"
        },
        "techniques": [
            {"name": "Cognitive restructuring", "description": "Identifying and challenging distorted thoughts"},
            {"name": "Behavioral experiments", "description": "Testing beliefs through real-world experiments"},
            {"name": "Thought records", "description": "Documenting situations, thoughts, emotions, and alternative thoughts"},
            {"name": "Socratic questioning", "description": "Guided discovery through questions"},
            {"name": "Activity scheduling", "description": "Planning pleasurable and mastery activities"},
            {"name": "Graded exposure", "description": "Gradual confrontation of feared situations"},
            {"name": "Behavioral activation", "description": "Increasing engagement in positive activities"},
            {"name": "Problem-solving training", "description": "Systematic approach to solving problems"},
            {"name": "Relaxation training", "description": "Progressive muscle relaxation, breathing exercises"}
        ],
        "evidence_base": {
            "effectiveness": "Strong evidence for depression, anxiety disorders, PTSD, OCD, eating disorders, insomnia",
            "meta_analyses": [
                "Hofmann et al. (2012) - CBT effective for anxiety, depression, substance use",
                "Butler et al. (2006) - Large effects for unipolar depression, GAD, panic, social phobia",
                "Cuijpers et al. (2019) - CBT as effective as antidepressants for depression"
            ],
            "nice_guidelines": "Recommended first-line treatment for depression and anxiety (UK NICE)"
        },
        "session_structure": {
            "typical_length": "12-20 sessions",
            "session_format": [
                "Mood check and agenda setting",
                "Bridge from previous session",
                "Review homework",
                "Work on agenda items",
                "Assign new homework",
                "Summary and feedback"
            ]
        },
        "conditions_treated": ["Depression", "Anxiety disorders", "PTSD", "OCD", "Panic disorder", "Social anxiety", 
                              "Phobias", "Eating disorders", "Insomnia", "Chronic pain", "Substance use disorders"]
    },
    
    "dbt": {
        "name": "Dialectical Behavior Therapy (DBT)",
        "founder": "Marsha Linehan (1980s)",
        "theoretical_basis": "Combines CBT with mindfulness and acceptance; balances change and acceptance (dialectics)",
        "key_concepts": {
            "dialectics": "Synthesis of opposites; both acceptance AND change",
            "biosocial_theory": "Emotional vulnerability + invalidating environment = emotion dysregulation",
            "wise_mind": "Integration of emotional mind and rational mind"
        },
        "skill_modules": {
            "mindfulness": {
                "description": "Being present without judgment",
                "what_skills": ["Observe", "Describe", "Participate"],
                "how_skills": ["Non-judgmentally", "One-mindfully", "Effectively"]
            },
            "distress_tolerance": {
                "description": "Surviving crises without making things worse",
                "crisis_survival": ["TIPP (Temperature, Intense exercise, Paced breathing, Paired muscle relaxation)",
                                   "STOP skill", "Pros and cons", "Distraction (ACCEPTS)", "Self-soothing"],
                "reality_acceptance": ["Radical acceptance", "Turning the mind", "Willingness vs willfulness"]
            },
            "emotion_regulation": {
                "description": "Understanding and managing emotions",
                "skills": ["Identifying emotions", "Checking the facts", "Opposite action", 
                          "Problem solving", "ABC PLEASE (Accumulate positives, Build mastery, Cope ahead, treat PhysicaL illness, balance Eating, avoid mood-Altering substances, balance Sleep, get Exercise)"]
            },
            "interpersonal_effectiveness": {
                "description": "Getting needs met while maintaining relationships and self-respect",
                "skills": ["DEAR MAN (Describe, Express, Assert, Reinforce, Mindful, Appear confident, Negotiate)",
                          "GIVE (Gentle, Interested, Validate, Easy manner)",
                          "FAST (Fair, no Apologies, Stick to values, Truthful)"]
            }
        },
        "treatment_modes": [
            "Individual therapy (1x/week)",
            "Skills training group (2-2.5 hours/week)",
            "Phone coaching (as needed for crises)",
            "Therapist consultation team"
        ],
        "evidence_base": {
            "effectiveness": "Strong evidence for BPD, self-harm, suicidal behavior; growing evidence for other conditions",
            "key_studies": [
                "Linehan et al. (2006) - Reduced suicide attempts and self-harm in BPD",
                "Stoffers et al. (2012) - Cochrane review supporting DBT for BPD",
                "DeCou et al. (2019) - Meta-analysis: DBT reduces self-harm and suicidal ideation"
            ]
        },
        "conditions_treated": ["Borderline personality disorder", "Self-harm", "Suicidal behavior", 
                              "Eating disorders", "Substance use", "PTSD", "Treatment-resistant depression"]
    },
    
    "act": {
        "name": "Acceptance and Commitment Therapy (ACT)",
        "founder": "Steven Hayes (1980s-1990s)",
        "theoretical_basis": "Relational Frame Theory; psychological flexibility through acceptance and values-based action",
        "key_concepts": {
            "psychological_flexibility": "Ability to be present, open up, and do what matters",
            "hexaflex_model": {
                "acceptance": "Opening up to unwanted experiences without struggle",
                "cognitive_defusion": "Seeing thoughts as thoughts, not literal truths",
                "present_moment": "Flexible attention to the here and now",
                "self_as_context": "Transcendent sense of self; observer perspective",
                "values": "Chosen life directions that give meaning",
                "committed_action": "Taking effective action guided by values"
            },
            "experiential_avoidance": "Attempting to avoid or control unwanted internal experiences (problematic)",
            "creative_hopelessness": "Recognizing that control strategies haven't worked"
        },
        "techniques": [
            {"name": "Defusion exercises", "examples": ["Milk, milk, milk", "Leaves on a stream", "Thanking your mind"]},
            {"name": "Mindfulness practices", "examples": ["Breath awareness", "Body scan", "Noticing thoughts"]},
            {"name": "Values clarification", "examples": ["Values card sort", "Eulogy exercise", "Life compass"]},
            {"name": "Committed action", "examples": ["SMART goals", "Willingness exercises", "Behavioral experiments"]},
            {"name": "Metaphors", "examples": ["Passengers on the bus", "Tug of war with monster", "Quicksand"]}
        ],
        "evidence_base": {
            "effectiveness": "Growing evidence for depression, anxiety, chronic pain, substance use",
            "meta_analyses": [
                "A-Tjak et al. (2015) - ACT effective for depression, anxiety, addiction, somatic health",
                "Gloster et al. (2020) - ACT effective across multiple conditions",
                "Hughes et al. (2017) - ACT effective for chronic pain"
            ]
        },
        "conditions_treated": ["Depression", "Anxiety", "Chronic pain", "OCD", "Substance use", 
                              "Psychosis", "Eating disorders", "Workplace stress"]
    },
    
    # PSYCHODYNAMIC APPROACHES
    "psychodynamic": {
        "name": "Psychodynamic Therapy",
        "founders": "Sigmund Freud (psychoanalysis), later developments by many theorists",
        "theoretical_basis": "Unconscious processes, early experiences, and relationships shape current functioning",
        "key_concepts": {
            "unconscious": "Mental processes outside awareness that influence behavior",
            "defense_mechanisms": [
                {"name": "Repression", "description": "Pushing threatening thoughts out of awareness"},
                {"name": "Denial", "description": "Refusing to accept reality"},
                {"name": "Projection", "description": "Attributing own unacceptable feelings to others"},
                {"name": "Displacement", "description": "Redirecting emotions to safer target"},
                {"name": "Rationalization", "description": "Creating logical explanations for irrational behavior"},
                {"name": "Sublimation", "description": "Channeling unacceptable impulses into acceptable activities"},
                {"name": "Reaction formation", "description": "Behaving opposite to true feelings"},
                {"name": "Intellectualization", "description": "Using abstract thinking to avoid emotions"}
            ],
            "transference": "Unconsciously redirecting feelings about past figures onto therapist",
            "countertransference": "Therapist's emotional reactions to client",
            "attachment_patterns": "Early relationship patterns that repeat in adult relationships",
            "object_relations": "Internalized representations of self and others"
        },
        "techniques": [
            "Free association",
            "Dream analysis",
            "Interpretation of defenses",
            "Analysis of transference",
            "Working through",
            "Exploration of early experiences"
        ],
        "modern_variants": [
            {"name": "Short-term psychodynamic therapy", "duration": "12-24 sessions"},
            {"name": "Mentalization-based therapy (MBT)", "focus": "Understanding mental states"},
            {"name": "Transference-focused psychotherapy (TFP)", "focus": "BPD treatment"},
            {"name": "Intensive short-term dynamic psychotherapy (ISTDP)", "focus": "Rapid access to unconscious"}
        ],
        "evidence_base": {
            "meta_analyses": [
                "Shedler (2010) - Effect sizes comparable to other therapies",
                "Leichsenring & Rabung (2008) - Long-term psychodynamic effective for complex disorders",
                "Driessen et al. (2015) - Short-term psychodynamic effective for depression"
            ]
        },
        "conditions_treated": ["Depression", "Anxiety", "Personality disorders", "Relationship issues", 
                              "Complex trauma", "Identity issues"]
    },
    
    # HUMANISTIC APPROACHES
    "person_centered": {
        "name": "Person-Centered Therapy (Rogerian)",
        "founder": "Carl Rogers (1940s-1950s)",
        "theoretical_basis": "Humans have innate tendency toward growth (actualizing tendency); therapeutic relationship is curative",
        "core_conditions": {
            "unconditional_positive_regard": {
                "description": "Accepting client without judgment",
                "importance": "Creates safety for self-exploration"
            },
            "empathy": {
                "description": "Deeply understanding client's experience from their frame of reference",
                "importance": "Client feels understood and validated"
            },
            "congruence": {
                "description": "Therapist is genuine and authentic",
                "importance": "Models authenticity, builds trust"
            }
        },
        "key_concepts": {
            "actualizing_tendency": "Innate drive toward growth and fulfillment",
            "self_concept": "How person views themselves",
            "conditions_of_worth": "Conditions placed on receiving love/acceptance",
            "incongruence": "Gap between self-concept and experience",
            "organismic_valuing": "Internal wisdom about what is good for growth"
        },
        "therapeutic_stance": "Non-directive; follows client's lead; trusts client's wisdom",
        "evidence_base": {
            "research": [
                "Elliott et al. (2013) - Meta-analysis supporting person-centered therapy",
                "Core conditions consistently linked to positive outcomes across therapies"
            ]
        }
    },
    
    "gestalt": {
        "name": "Gestalt Therapy",
        "founders": "Fritz Perls, Laura Perls, Paul Goodman (1940s-1950s)",
        "theoretical_basis": "Focus on present moment awareness; integration of fragmented parts of self",
        "key_concepts": {
            "here_and_now": "Focus on present experience",
            "awareness": "Full contact with current experience",
            "contact_boundary": "Interface between self and environment",
            "unfinished_business": "Unexpressed feelings from past",
            "figure_ground": "What stands out vs. background"
        },
        "techniques": [
            {"name": "Empty chair", "description": "Dialogue with absent person or part of self"},
            {"name": "Two-chair work", "description": "Dialogue between conflicting parts"},
            {"name": "Exaggeration", "description": "Amplifying gestures or statements"},
            {"name": "Body awareness", "description": "Attending to physical sensations"},
            {"name": "Dream work", "description": "Acting out dream elements as parts of self"}
        ]
    },
    
    "existential": {
        "name": "Existential Therapy",
        "founders": "Rollo May, Irvin Yalom, Viktor Frankl",
        "theoretical_basis": "Confronting fundamental concerns of existence; finding meaning",
        "ultimate_concerns": {
            "death": "Awareness of mortality and its implications",
            "freedom": "Responsibility for choices; groundlessness",
            "isolation": "Fundamental aloneness despite connections",
            "meaninglessness": "Need to create meaning in indifferent universe"
        },
        "key_concepts": {
            "authenticity": "Living in accordance with true self",
            "bad_faith": "Self-deception; avoiding responsibility",
            "anxiety": "Response to confronting existence; can be growth-promoting",
            "logotherapy": "Frankl's meaning-centered approach"
        }
    },
    
    # TRAUMA-FOCUSED APPROACHES
    "emdr": {
        "name": "Eye Movement Desensitization and Reprocessing (EMDR)",
        "founder": "Francine Shapiro (1987)",
        "theoretical_basis": "Adaptive Information Processing model; bilateral stimulation facilitates processing of traumatic memories",
        "eight_phases": [
            {"phase": 1, "name": "History taking", "description": "Gather history, identify targets"},
            {"phase": 2, "name": "Preparation", "description": "Establish safety, teach coping skills"},
            {"phase": 3, "name": "Assessment", "description": "Identify target memory, negative cognition, positive cognition, emotions, body sensations"},
            {"phase": 4, "name": "Desensitization", "description": "Process memory with bilateral stimulation"},
            {"phase": 5, "name": "Installation", "description": "Strengthen positive cognition"},
            {"phase": 6, "name": "Body scan", "description": "Check for residual body tension"},
            {"phase": 7, "name": "Closure", "description": "Return to equilibrium"},
            {"phase": 8, "name": "Reevaluation", "description": "Check progress in next session"}
        ],
        "bilateral_stimulation": ["Eye movements", "Tapping", "Auditory tones"],
        "evidence_base": {
            "effectiveness": "Strong evidence for PTSD; WHO and APA recommended",
            "key_studies": [
                "Shapiro & Maxfield (2002) - EMDR effective for PTSD",
                "Bisson et al. (2013) - Cochrane review supporting EMDR for PTSD",
                "WHO (2013) - Recommends EMDR for PTSD in adults and children"
            ]
        },
        "conditions_treated": ["PTSD", "Complex trauma", "Phobias", "Anxiety", "Depression", "Grief"]
    },
    
    "cpt": {
        "name": "Cognitive Processing Therapy (CPT)",
        "founders": "Patricia Resick (1988)",
        "theoretical_basis": "Trauma disrupts beliefs about self, others, world; therapy addresses 'stuck points'",
        "key_concepts": {
            "stuck_points": "Problematic beliefs that maintain PTSD symptoms",
            "assimilation": "Altering memory to fit existing beliefs (problematic)",
            "accommodation": "Modifying beliefs to account for trauma (healthy)",
            "over_accommodation": "Overgeneralizing from trauma (problematic)"
        },
        "themes_addressed": ["Safety", "Trust", "Power/Control", "Esteem", "Intimacy"],
        "protocol": {
            "sessions": "12 sessions typically",
            "components": [
                "Education about PTSD and thoughts",
                "Impact statement (meaning of trauma)",
                "ABC worksheets (activating event, belief, consequence)",
                "Challenging questions",
                "Patterns of problematic thinking",
                "Challenging beliefs worksheets",
                "Themes modules"
            ]
        },
        "evidence_base": {
            "effectiveness": "Strong evidence for PTSD; VA/DoD recommended",
            "key_studies": [
                "Resick et al. (2002) - CPT effective for rape-related PTSD",
                "Monson et al. (2006) - CPT effective for veterans"
            ]
        }
    },
    
    "prolonged_exposure": {
        "name": "Prolonged Exposure (PE)",
        "founder": "Edna Foa",
        "theoretical_basis": "Emotional processing theory; avoidance maintains fear; exposure allows habituation and cognitive change",
        "components": [
            {"name": "Psychoeducation", "description": "Understanding PTSD and treatment rationale"},
            {"name": "Breathing retraining", "description": "Relaxation technique"},
            {"name": "In vivo exposure", "description": "Gradual confrontation of avoided situations"},
            {"name": "Imaginal exposure", "description": "Revisiting trauma memory in imagination"}
        ],
        "evidence_base": {
            "effectiveness": "Strong evidence; gold standard for PTSD",
            "key_studies": [
                "Powers et al. (2010) - Meta-analysis: PE highly effective for PTSD",
                "Foa et al. (2018) - PE effective across trauma types"
            ]
        }
    },
    
    # FAMILY AND SYSTEMS APPROACHES
    "family_systems": {
        "name": "Family Systems Therapy",
        "founders": "Murray Bowen, Salvador Minuchin, Virginia Satir, and others",
        "theoretical_basis": "Family is a system; individual symptoms reflect family dynamics",
        "key_concepts": {
            "differentiation": "Ability to maintain self while staying connected (Bowen)",
            "triangulation": "Third party drawn into two-person conflict",
            "boundaries": "Rules defining who participates and how (Minuchin)",
            "enmeshment": "Overly diffuse boundaries",
            "disengagement": "Overly rigid boundaries",
            "homeostasis": "System's tendency to maintain status quo",
            "circular_causality": "Behaviors mutually influence each other"
        },
        "approaches": [
            {"name": "Structural family therapy", "focus": "Restructuring family organization"},
            {"name": "Strategic family therapy", "focus": "Changing problematic interaction patterns"},
            {"name": "Bowenian therapy", "focus": "Differentiation, multigenerational patterns"},
            {"name": "Narrative family therapy", "focus": "Re-authoring family stories"},
            {"name": "Solution-focused family therapy", "focus": "Building on strengths and solutions"}
        ]
    },
    
    "emotionally_focused": {
        "name": "Emotionally Focused Therapy (EFT)",
        "founder": "Sue Johnson (1980s)",
        "theoretical_basis": "Attachment theory; distress in relationships stems from unmet attachment needs",
        "key_concepts": {
            "attachment_needs": "Need for secure emotional bond",
            "negative_cycles": "Pursue-withdraw or attack-defend patterns",
            "primary_emotions": "Underlying vulnerable emotions (fear, sadness)",
            "secondary_emotions": "Reactive emotions that mask primary (anger)"
        },
        "stages": [
            {"stage": 1, "name": "De-escalation", "goals": ["Identify negative cycle", "Access underlying emotions"]},
            {"stage": 2, "name": "Restructuring", "goals": ["Promote new interactions", "Create bonding events"]},
            {"stage": 3, "name": "Consolidation", "goals": ["Integrate changes", "New solutions to old problems"]}
        ],
        "evidence_base": {
            "effectiveness": "Strong evidence for couple distress",
            "key_studies": [
                "Johnson et al. (1999) - 70-75% recovery rate for couple distress",
                "Wiebe & Johnson (2016) - Meta-analysis supporting EFT"
            ]
        }
    },
    
    # MINDFULNESS-BASED APPROACHES
    "mbsr": {
        "name": "Mindfulness-Based Stress Reduction (MBSR)",
        "founder": "Jon Kabat-Zinn (1979)",
        "theoretical_basis": "Mindfulness practice reduces stress and improves well-being",
        "program_structure": {
            "duration": "8 weeks",
            "sessions": "Weekly 2.5-hour classes + day-long retreat",
            "home_practice": "45 minutes daily"
        },
        "practices": [
            "Body scan meditation",
            "Sitting meditation",
            "Mindful movement (yoga)",
            "Walking meditation",
            "Mindful eating"
        ],
        "evidence_base": {
            "effectiveness": "Strong evidence for stress, anxiety, chronic pain, depression relapse prevention",
            "meta_analyses": [
                "Grossman et al. (2004) - MBSR effective for various conditions",
                "Khoury et al. (2013) - Mindfulness-based therapy effective for anxiety, depression"
            ]
        }
    },
    
    "mbct": {
        "name": "Mindfulness-Based Cognitive Therapy (MBCT)",
        "founders": "Zindel Segal, Mark Williams, John Teasdale (1990s)",
        "theoretical_basis": "Combines mindfulness with CBT; prevents depression relapse by changing relationship to thoughts",
        "key_concepts": {
            "decentering": "Seeing thoughts as mental events, not facts",
            "rumination": "Repetitive negative thinking (target of intervention)",
            "automatic_pilot": "Mindless, habitual responding"
        },
        "evidence_base": {
            "effectiveness": "Strong evidence for preventing depression relapse",
            "key_studies": [
                "Teasdale et al. (2000) - MBCT reduces relapse in recurrent depression",
                "Kuyken et al. (2016) - MBCT as effective as maintenance antidepressants"
            ],
            "nice_guidelines": "Recommended for recurrent depression (UK NICE)"
        }
    },
    
    # NEWER/EMERGING APPROACHES
    "ifs": {
        "name": "Internal Family Systems (IFS)",
        "founder": "Richard Schwartz (1980s-1990s)",
        "theoretical_basis": "Mind is naturally multiple; healing comes from Self-leadership of parts",
        "key_concepts": {
            "self": "Core, undamaged essence with qualities of compassion, curiosity, calm, clarity, courage, creativity, connectedness, confidence",
            "parts": {
                "exiles": "Young, wounded parts carrying pain and trauma",
                "managers": "Protective parts that try to control and prevent pain",
                "firefighters": "Reactive parts that extinguish pain when it emerges (often through impulsive behaviors)"
            },
            "unburdening": "Process of releasing extreme beliefs and emotions from parts"
        },
        "therapeutic_process": [
            "Access the Self",
            "Identify and befriend protectors",
            "Get permission to work with exiles",
            "Witness and validate exile's experience",
            "Retrieve and unburden the exile",
            "Invite protectors to take on new roles"
        ],
        "evidence_base": {
            "growing_research": [
                "Haddock et al. (2017) - IFS effective for depression and anxiety",
                "Increasing RCTs being conducted"
            ]
        }
    },
    
    "somatic_experiencing": {
        "name": "Somatic Experiencing (SE)",
        "founder": "Peter Levine",
        "theoretical_basis": "Trauma is stored in the body; healing requires completing thwarted survival responses",
        "key_concepts": {
            "titration": "Processing trauma in small, manageable doses",
            "pendulation": "Moving between activation and calm",
            "discharge": "Releasing trapped survival energy",
            "felt_sense": "Internal body awareness"
        }
    },
    
    "sensorimotor": {
        "name": "Sensorimotor Psychotherapy",
        "founder": "Pat Ogden",
        "theoretical_basis": "Body-based approach to trauma; integrates somatic, emotional, and cognitive processing",
        "key_concepts": {
            "window_of_tolerance": "Optimal zone of arousal for processing",
            "hyperarousal": "Too much activation (anxiety, panic)",
            "hypoarousal": "Too little activation (numbness, dissociation)"
        }
    },
    
    # SPECIALIZED APPROACHES
    "motivational_interviewing": {
        "name": "Motivational Interviewing (MI)",
        "founders": "William Miller, Stephen Rollnick (1980s)",
        "theoretical_basis": "Ambivalence is normal; change talk predicts behavior change",
        "spirit": ["Partnership", "Acceptance", "Compassion", "Evocation"],
        "core_skills": {
            "oars": {
                "O": "Open questions",
                "A": "Affirmations",
                "R": "Reflections",
                "S": "Summaries"
            }
        },
        "key_concepts": {
            "change_talk": "Client statements favoring change (DARN-CAT: Desire, Ability, Reasons, Need, Commitment, Activation, Taking steps)",
            "sustain_talk": "Client statements favoring status quo",
            "rolling_with_resistance": "Avoiding argumentation"
        },
        "evidence_base": {
            "effectiveness": "Strong evidence for substance use, health behaviors",
            "meta_analyses": [
                "Lundahl et al. (2010) - MI effective across multiple behaviors",
                "Hettema et al. (2005) - MI effective for substance use"
            ]
        }
    },
    
    "solution_focused": {
        "name": "Solution-Focused Brief Therapy (SFBT)",
        "founders": "Steve de Shazer, Insoo Kim Berg (1980s)",
        "theoretical_basis": "Focus on solutions rather than problems; clients have resources",
        "key_techniques": [
            {"name": "Miracle question", "description": "If problem solved overnight, what would be different?"},
            {"name": "Exception questions", "description": "When is the problem less severe or absent?"},
            {"name": "Scaling questions", "description": "On a scale of 1-10, where are you now?"},
            {"name": "Coping questions", "description": "How have you managed to cope?"},
            {"name": "Compliments", "description": "Highlighting strengths and resources"}
        ],
        "evidence_base": {
            "research": [
                "Gingerich & Peterson (2013) - SFBT effective for various problems",
                "Kim (2008) - Meta-analysis supporting SFBT"
            ]
        }
    }
}

# MENTAL HEALTH CONDITIONS DATABASE
MENTAL_HEALTH_CONDITIONS = {
    "depression": {
        "name": "Major Depressive Disorder",
        "dsm5_criteria": {
            "required": "5+ symptoms for 2+ weeks, including depressed mood OR anhedonia",
            "symptoms": [
                "Depressed mood most of the day",
                "Markedly diminished interest or pleasure (anhedonia)",
                "Significant weight change or appetite change",
                "Insomnia or hypersomnia",
                "Psychomotor agitation or retardation",
                "Fatigue or loss of energy",
                "Feelings of worthlessness or excessive guilt",
                "Diminished concentration or indecisiveness",
                "Recurrent thoughts of death or suicidal ideation"
            ]
        },
        "evidence_based_treatments": ["CBT", "Behavioral Activation", "IPT", "MBCT (relapse prevention)", "Antidepressants"],
        "prevalence": "~7% of US adults annually"
    },
    "anxiety_disorders": {
        "generalized_anxiety": {
            "name": "Generalized Anxiety Disorder (GAD)",
            "key_features": "Excessive worry about multiple domains, difficult to control, for 6+ months",
            "treatments": ["CBT", "ACT", "Relaxation training", "SSRIs/SNRIs"]
        },
        "panic_disorder": {
            "name": "Panic Disorder",
            "key_features": "Recurrent unexpected panic attacks + worry about future attacks",
            "treatments": ["CBT (especially interoceptive exposure)", "SSRIs"]
        },
        "social_anxiety": {
            "name": "Social Anxiety Disorder",
            "key_features": "Fear of social situations due to potential scrutiny/judgment",
            "treatments": ["CBT", "Exposure therapy", "Social skills training", "SSRIs"]
        },
        "specific_phobias": {
            "name": "Specific Phobias",
            "key_features": "Marked fear of specific object or situation",
            "treatments": ["Exposure therapy (gold standard)", "CBT"]
        }
    },
    "ptsd": {
        "name": "Post-Traumatic Stress Disorder",
        "dsm5_clusters": {
            "intrusion": "Flashbacks, nightmares, intrusive memories",
            "avoidance": "Avoiding reminders of trauma",
            "negative_cognitions_mood": "Negative beliefs, emotional numbing, detachment",
            "arousal_reactivity": "Hypervigilance, startle response, sleep problems, irritability"
        },
        "evidence_based_treatments": ["Prolonged Exposure", "CPT", "EMDR", "Written Exposure Therapy"],
        "prevalence": "~6% lifetime prevalence"
    },
    "ocd": {
        "name": "Obsessive-Compulsive Disorder",
        "key_features": {
            "obsessions": "Intrusive, unwanted thoughts causing anxiety",
            "compulsions": "Repetitive behaviors to reduce anxiety"
        },
        "common_themes": ["Contamination", "Harm", "Symmetry", "Forbidden thoughts", "Hoarding"],
        "evidence_based_treatments": ["ERP (Exposure and Response Prevention)", "CBT", "SSRIs (high dose)"]
    },
    "bpd": {
        "name": "Borderline Personality Disorder",
        "key_features": [
            "Frantic efforts to avoid abandonment",
            "Unstable relationships",
            "Identity disturbance",
            "Impulsivity",
            "Suicidal/self-harm behavior",
            "Affective instability",
            "Chronic emptiness",
            "Intense anger",
            "Transient paranoia or dissociation"
        ],
        "evidence_based_treatments": ["DBT", "MBT", "TFP", "Schema therapy"]
    }
}


class AcademicResearchHelper:
    """
    Helper for searching academic literature.
    Connects to free, evidence-based sources.
    """
    
    def __init__(self):
        self.sources = ACADEMIC_SOURCES
        print("[OK] Academic Research Helper initialized")
        print(f"   [BOOK] {len(self.sources)} free academic sources available")
    
    def search_pubmed(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search PubMed for academic articles.
        Returns article metadata.
        """
        try:
            # PubMed E-utilities API
            base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
            
            # Search for articles
            search_url = f"{base_url}esearch.fcgi?db=pubmed&term={query}&retmax={max_results}&retmode=json"
            response = requests.get(search_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                id_list = data.get("esearchresult", {}).get("idlist", [])
                
                if not id_list:
                    return []
                
                # Get article details
                ids = ",".join(id_list)
                summary_url = f"{base_url}esummary.fcgi?db=pubmed&id={ids}&retmode=json"
                summary_response = requests.get(summary_url, timeout=10)
                
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    results = []
                    
                    for pmid in id_list:
                        article = summary_data.get("result", {}).get(pmid, {})
                        if article:
                            results.append({
                                "pmid": pmid,
                                "title": article.get("title", ""),
                                "authors": [a.get("name", "") for a in article.get("authors", [])[:3]],
                                "journal": article.get("source", ""),
                                "year": article.get("pubdate", "")[:4],
                                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                            })
                    
                    return results
        except Exception as e:
            print(f"PubMed search error: {e}")
        
        return []
    
    def search_semantic_scholar(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search Semantic Scholar for papers.
        """
        try:
            url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit={limit}&fields=title,authors,year,url,citationCount"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for paper in data.get("data", []):
                    results.append({
                        "title": paper.get("title", ""),
                        "authors": [a.get("name", "") for a in paper.get("authors", [])[:3]],
                        "year": paper.get("year"),
                        "citations": paper.get("citationCount", 0),
                        "url": paper.get("url", "")
                    })
                
                return results
        except Exception as e:
            print(f"Semantic Scholar search error: {e}")
        
        return []
    
    def get_search_urls(self, query: str) -> Dict[str, str]:
        """
        Generate search URLs for various academic databases.
        """
        encoded_query = query.replace(" ", "+")
        
        return {
            "PubMed": f"https://pubmed.ncbi.nlm.nih.gov/?term={encoded_query}",
            "Google Scholar": f"https://scholar.google.com/scholar?q={encoded_query}",
            "PubMed Central": f"https://www.ncbi.nlm.nih.gov/pmc/?term={encoded_query}",
            "Semantic Scholar": f"https://www.semanticscholar.org/search?q={encoded_query}",
            "CORE": f"https://core.ac.uk/search?q={encoded_query}",
            "DOAJ": f"https://doaj.org/search/articles?ref=homepage-box&source={{%22query%22:{{%22query_string%22:{{%22query%22:%22{encoded_query}%22}}}}}}"
        }
    
    def list_sources(self) -> List[Dict]:
        """List all available academic sources."""
        return [
            {"name": s["name"], "url": s["url"], "description": s["description"]}
            for s in self.sources.values()
        ]


class ComprehensiveCounselingSystem:
    """
    Comprehensive counseling knowledge system with research integration.
    """
    
    def __init__(self):
        self.modalities = COUNSELING_MODALITIES
        self.conditions = MENTAL_HEALTH_CONDITIONS
        self.research_helper = AcademicResearchHelper()
        
        print("[OK] Comprehensive Counseling System initialized")
        print(f"   [BRAIN] {len(self.modalities)} therapeutic modalities")
        print(f"   [LIST] {len(self.conditions)} mental health conditions")
        print("   [BOOK] Academic research integration enabled")
    
    def get_modality(self, modality: str) -> Optional[Dict]:
        """Get detailed information about a therapy modality."""
        return self.modalities.get(modality.lower().replace(" ", "_").replace("-", "_"))
    
    def get_condition(self, condition: str) -> Optional[Dict]:
        """Get information about a mental health condition."""
        condition_key = condition.lower().replace(" ", "_")
        
        # Check main conditions
        if condition_key in self.conditions:
            return self.conditions[condition_key]
        
        # Check nested conditions (e.g., anxiety disorders)
        for category, data in self.conditions.items():
            if isinstance(data, dict):
                for sub_key, sub_data in data.items():
                    if condition_key in sub_key or (isinstance(sub_data, dict) and 
                        condition_key in sub_data.get("name", "").lower()):
                        return sub_data
        
        return None
    
    def get_treatments_for_condition(self, condition: str) -> List[str]:
        """Get evidence-based treatments for a condition."""
        cond_data = self.get_condition(condition)
        if cond_data:
            return cond_data.get("evidence_based_treatments", 
                   cond_data.get("treatments", []))
        return []
    
    def search_modalities(self, query: str) -> List[Dict]:
        """Search modalities by keyword."""
        query_lower = query.lower()
        results = []
        
        for key, modality in self.modalities.items():
            if (query_lower in modality.get("name", "").lower() or
                query_lower in str(modality).lower()):
                results.append({"key": key, "name": modality.get("name", ""), "data": modality})
        
        return results
    
    def compare_modalities(self, mod1: str, mod2: str) -> Dict:
        """Compare two therapeutic modalities."""
        m1 = self.get_modality(mod1)
        m2 = self.get_modality(mod2)
        
        if not m1 or not m2:
            return {"error": "One or both modalities not found"}
        
        return {
            "modality_1": {
                "name": m1.get("name"),
                "founder": m1.get("founder", "Various"),
                "theoretical_basis": m1.get("theoretical_basis", "")[:200] + "..."
            },
            "modality_2": {
                "name": m2.get("name"),
                "founder": m2.get("founder", "Various"),
                "theoretical_basis": m2.get("theoretical_basis", "")[:200] + "..."
            }
        }
    
    def research_topic(self, topic: str) -> Dict:
        """
        Research a counseling topic using academic sources.
        Returns search URLs and any available results.
        """
        # Get search URLs
        urls = self.research_helper.get_search_urls(topic)
        
        # Try to get some results from PubMed
        pubmed_results = self.research_helper.search_pubmed(topic, max_results=5)
        
        return {
            "topic": topic,
            "search_urls": urls,
            "pubmed_results": pubmed_results,
            "tip": "Click the URLs above to access free academic literature on this topic"
        }
    
    def list_all_modalities(self) -> List[str]:
        """List all available modalities."""
        return [m.get("name", k) for k, m in self.modalities.items()]
    
    def get_technique(self, modality: str, technique_name: str) -> Optional[Dict]:
        """Get details about a specific technique within a modality."""
        mod = self.get_modality(modality)
        if not mod:
            return None
        
        techniques = mod.get("techniques", [])
        for tech in techniques:
            if isinstance(tech, dict):
                if technique_name.lower() in tech.get("name", "").lower():
                    return tech
            elif isinstance(tech, str) and technique_name.lower() in tech.lower():
                return {"name": tech}
        
        return None


# Singleton
_counseling_system = None

def get_counseling_system() -> ComprehensiveCounselingSystem:
    global _counseling_system
    if _counseling_system is None:
        _counseling_system = ComprehensiveCounselingSystem()
    return _counseling_system


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("MONICA COMPREHENSIVE COUNSELING SYSTEM TEST")
    print("=" * 70)
    
    system = get_counseling_system()
    
    # Test modality lookup
    print("\n--- CBT Overview ---")
    cbt = system.get_modality("cbt")
    if cbt:
        print(f"Name: {cbt['name']}")
        print(f"Founder: {cbt['founder']}")
        print(f"Cognitive Distortions: {len(cbt['key_concepts']['cognitive_distortions'])}")
        print(f"Techniques: {len(cbt['techniques'])}")
    
    # Test condition lookup
    print("\n--- Depression Treatments ---")
    treatments = system.get_treatments_for_condition("depression")
    print(f"Evidence-based treatments: {treatments}")
    
    # Test research
    print("\n--- Research: 'CBT depression efficacy' ---")
    research = system.research_topic("CBT depression efficacy")
    print(f"Search URLs generated: {len(research['search_urls'])}")
    if research['pubmed_results']:
        print(f"PubMed results: {len(research['pubmed_results'])}")
        for r in research['pubmed_results'][:2]:
            print(f"  - {r['title'][:60]}... ({r['year']})")
    
    # List academic sources
    print("\n--- Free Academic Sources ---")
    sources = system.research_helper.list_sources()
    for s in sources[:5]:
        print(f"  [BOOK] {s['name']}: {s['url']}")
    
    print("\n" + "=" * 70)
    print("[OK] Counseling System test complete!")
    print("=" * 70)
