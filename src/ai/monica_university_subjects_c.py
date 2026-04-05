"""
Monica University - Subjects Part C
Microbiology, Human Anatomy, Human Sexuality, The Brain, The Nervous System,
Telemetry, Aeronautics, Drama, Geometry
"""
from ai.monica_university import QuizQuestion

SUBJECTS_C = {}

# ---------- MICROBIOLOGY ----------
SUBJECTS_C["microbiology"] = {
    "name": "Microbiology",
    "overview": "Study of microscopic organisms: bacteria, viruses, fungi, protists, and their roles in health, disease, ecology, and biotechnology.",
    "topics": {
        "bacteria": {
            "title": "Bacteriology",
            "content": """STRUCTURE: Cell wall (peptidoglycan), membrane, cytoplasm, ribosomes, nucleoid (circular DNA), plasmids.
Gram-positive: thick peptidoglycan, stain purple (Staph, Strep). Gram-negative: thin wall + outer membrane (LPS), stain pink (E.coli, Salmonella).
Shapes: Cocci (spheres), Bacilli (rods), Spirilla (spirals).

METABOLISM: Obligate aerobes (need O2), Obligate anaerobes (killed by O2), Facultative anaerobes (either).
Reproduction: Binary fission (~20 min for E.coli). Genetic variation via mutation, conjugation, transformation, transduction.

PATHOGENESIS: Virulence factors: toxins, adhesins, capsules, enzymes.
ANTIBIOTICS: Target cell wall (penicillin), protein synthesis (tetracycline), DNA replication (fluoroquinolones).
Resistance: beta-lactamases, efflux pumps. MRSA and superbugs are growing threats.""",
            "key_formulas": [],
        },
        "virology": {
            "title": "Virology",
            "content": """STRUCTURE: Nucleic acid (DNA or RNA) + protein capsid +/- lipid envelope. 20-300nm. Not living.
REPLICATION: Attachment->Entry->Replication->Assembly->Release (lysis or budding).
TYPES: DNA viruses (herpes), RNA viruses (influenza, SARS-CoV-2), Retroviruses (HIV: RNA->DNA via reverse transcriptase).
Lytic cycle (immediate kill) vs Lysogenic (integrate, can activate later).

VACCINES: Attenuated, Inactivated, Subunit, mRNA (COVID). Herd immunity varies by disease.""",
            "key_formulas": [],
        },
        "immunology": {
            "title": "Immunology",
            "content": """INNATE: Barriers (skin, mucous), Cells (neutrophils, macrophages, NK cells), Chemical (complement, interferons, inflammation).

ADAPTIVE: Humoral (B cells make antibodies: IgG, IgM, IgA, IgE). Cell-mediated (CD8+ cytotoxic T cells kill infected cells, CD4+ helper T cells coordinate response).
MHC I on all nucleated cells (present to CD8+). MHC II on APCs (present to CD4+).
Memory cells enable faster secondary response (basis of vaccination).

DISORDERS: Autoimmune (lupus, MS), Immunodeficiency (HIV destroys CD4+), Allergy (hypersensitivity).""",
            "key_formulas": [],
        },
    },
    "quiz_questions": [
        QuizQuestion("microbiology", "bacteria", "What distinguishes Gram-positive from Gram-negative?", "Gram+ have thick peptidoglycan; Gram- have thin wall + outer membrane", ["Size only", "Shape only", "No cell wall"], "Gram stain reveals wall structure, critical for antibiotic choice."),
        QuizQuestion("microbiology", "virology", "Why are viruses obligate intracellular parasites?", "They cannot reproduce without host cell machinery", ["Too small", "Lack DNA", "Antibiotic resistant"], "Viruses lack ribosomes and metabolic machinery."),
    ],
}

# ---------- HUMAN ANATOMY ----------
SUBJECTS_C["human_anatomy"] = {
    "name": "Human Anatomy",
    "overview": "Study of the structure of the human body, from cells and tissues to organs and organ systems.",
    "topics": {
        "skeletal_system": {
            "title": "Skeletal System",
            "content": """206 BONES: Axial (80: skull, spine, ribs) + Appendicular (126: limbs, girdles).
Types: Long (femur), Short (carpals), Flat (skull), Irregular (vertebrae), Sesamoid (patella).
Structure: Compact bone (dense) + Spongy bone (marrow). Osteoblasts build, Osteoclasts break down.
Red marrow: blood cell production. Yellow marrow: fat storage.

JOINTS: Fibrous (immovable), Cartilaginous (limited), Synovial (free movement).
Synovial types: Ball-and-socket (hip), Hinge (elbow), Pivot, Saddle, Gliding.
Ligaments: bone-to-bone. Tendons: muscle-to-bone.

SPINE: 7 cervical, 12 thoracic, 5 lumbar, 5 sacral (fused), 4 coccygeal (fused).""",
            "key_formulas": [],
        },
        "muscular_system": {
            "title": "Muscular System",
            "content": """TYPES: Skeletal (voluntary, striated, ~600 muscles), Cardiac (involuntary, striated, heart), Smooth (involuntary, organs/vessels).

STRUCTURE: Muscle->Fascicles->Fibers->Myofibrils->Sarcomeres (actin+myosin).
Sliding Filament Theory: Myosin heads pull actin, shortening sarcomere. Requires ATP + calcium.

KEY MUSCLES: Deltoid (shoulder), Biceps/Triceps (arm), Pectoralis (chest), Rectus abdominis (abs), Quadriceps/Hamstrings (thigh), Gastrocnemius (calf), Trapezius/Lats (back), Glutes (buttocks).

ACTIONS: Agonist (prime mover), Antagonist (opposes), Synergist (assists), Fixator (stabilizes).
Contractions: Concentric (shortens), Eccentric (lengthens under load), Isometric (no change).""",
            "key_formulas": [],
        },
        "cardiovascular_system": {
            "title": "Cardiovascular System",
            "content": """HEART: 4 chambers. Right side->lungs (pulmonary), Left side->body (systemic).
Valves: Tricuspid, Mitral/Bicuspid, Pulmonary, Aortic. Prevent backflow.
Conduction: SA node (pacemaker)->AV node->Bundle of His->Purkinje fibers. ~72 bpm.
Cardiac output CO=HR*SV (~5 L/min at rest). Systole ~120 mmHg, Diastole ~80 mmHg.

VESSELS: Arteries (from heart, thick walls), Veins (to heart, valves), Capillaries (exchange).
BLOOD: ~5L. Plasma (55%), RBCs (hemoglobin carries O2), WBCs (immune), Platelets (clotting).
Blood types: A, B, AB (universal recipient), O (universal donor). Rh +/-.""",
            "key_formulas": ["CO=HR*SV"],
        },
        "respiratory_system": {
            "title": "Respiratory System",
            "content": """ANATOMY: Nose/mouth->Pharynx->Larynx->Trachea->Bronchi->Bronchioles->Alveoli.
~300 million alveoli provide ~70 m^2 surface area for gas exchange.

GAS EXCHANGE: O2 diffuses from alveoli into blood (binds hemoglobin). CO2 diffuses from blood into alveoli (exhaled).
Dalton's law: total pressure = sum of partial pressures. Henry's law: gas solubility proportional to partial pressure.

BREATHING MECHANICS: Diaphragm contracts (flattens)->thoracic cavity expands->air pressure drops->air flows in (inspiration). Relaxation->passive expiration.
Tidal volume ~500mL. Vital capacity ~4.8L. Residual volume ~1.2L.

REGULATION: Medulla oblongata controls rhythm. Chemoreceptors detect CO2/pH changes (primary drive) and O2 levels.""",
            "key_formulas": [],
        },
        "digestive_system": {
            "title": "Digestive System",
            "content": """GI TRACT: Mouth (mechanical + salivary amylase)->Esophagus (peristalsis)->Stomach (HCl + pepsin, pH 1.5-3.5)->Small intestine (digestion + absorption)->Large intestine (water absorption)->Rectum.

SMALL INTESTINE (6m): Duodenum (bile + pancreatic enzymes), Jejunum + Ileum (absorption). Villi and microvilli increase surface area ~200 m^2.

ACCESSORY ORGANS: Liver (bile production, detoxification, glycogen storage), Gallbladder (bile storage), Pancreas (digestive enzymes + insulin/glucagon).

NUTRIENTS: Carbs->monosaccharides (glucose). Proteins->amino acids. Fats->fatty acids+glycerol.
Absorption via enterocytes. Fats go to lymphatic system; others to portal vein->liver.""",
            "key_formulas": [],
        },
    },
    "quiz_questions": [
        QuizQuestion("human_anatomy", "skeletal_system", "How many bones in adult body?", "206", ["300", "150", "256"], "206 bones. Babies born with ~270 that fuse."),
        QuizQuestion("human_anatomy", "cardiovascular_system", "What is the heart's pacemaker?", "SA node", ["AV node", "Bundle of His", "Purkinje fibers"], "SA node generates electrical impulse initiating each heartbeat."),
        QuizQuestion("human_anatomy", "respiratory_system", "What is the primary chemical drive for breathing?", "CO2/pH levels detected by chemoreceptors", ["O2 levels", "Heart rate", "Blood pressure"], "Rising CO2 lowers blood pH, stimulating the medulla to increase breathing rate."),
    ],
}

# ---------- HUMAN SEXUALITY ----------
SUBJECTS_C["human_sexuality"] = {
    "name": "Human Sexuality",
    "overview": "Scientific study of human sexual development, reproductive biology, sexual health, identity, and relationships from biological, psychological, and social perspectives.",
    "topics": {
        "reproductive_biology": {
            "title": "Reproductive Biology",
            "content": """MALE REPRODUCTIVE: Testes produce sperm (spermatogenesis, ~74 days) and testosterone. Epididymis (maturation)->Vas deferens->Urethra. Seminal vesicles, prostate, bulbourethral glands produce seminal fluid.

FEMALE REPRODUCTIVE: Ovaries produce oocytes and estrogen/progesterone. Ovulation ~day 14 of 28-day cycle. Fallopian tubes (fertilization site)->Uterus (implantation)->Cervix->Vagina.

MENSTRUAL CYCLE: Follicular phase (FSH stimulates follicle)->Ovulation (LH surge)->Luteal phase (corpus luteum produces progesterone)->Menstruation (if no implantation).

FERTILIZATION: Sperm capacitation, acrosome reaction, zona pellucida penetration, cortical reaction prevents polyspermy. Zygote->Morula->Blastocyst->Implantation ~day 6-7.

PREGNANCY: 3 trimesters. Placenta provides nutrients/O2, removes waste. hCG maintains corpus luteum. Fetal development: organogenesis (weeks 3-8), growth and maturation (9-40).""",
            "key_formulas": [],
        },
        "sexual_health": {
            "title": "Sexual Health & STIs",
            "content": """CONTRACEPTION: Barrier (condoms - also STI prevention), Hormonal (pill, patch, IUD - prevent ovulation/implantation), Permanent (vasectomy, tubal ligation), Emergency (Plan B).

SEXUALLY TRANSMITTED INFECTIONS:
- Bacterial: Chlamydia, Gonorrhea, Syphilis - treatable with antibiotics.
- Viral: HIV (attacks CD4+ T cells), HPV (can cause cervical cancer, vaccine available), Herpes (HSV, lifelong), Hepatitis B.
- Parasitic: Trichomoniasis.
Prevention: Condoms, vaccination (HPV, Hep B), regular testing, communication.

SEXUAL RESPONSE: Masters & Johnson model: Excitement->Plateau->Orgasm->Resolution.
Kaplan's model adds Desire phase. Biopsychosocial factors influence response.

GENDER & IDENTITY: Biological sex (chromosomes XX/XY, hormones, anatomy), Gender identity (internal sense), Gender expression (outward presentation), Sexual orientation (attraction pattern). These are independent dimensions.""",
            "key_formulas": [],
        },
    },
    "quiz_questions": [
        QuizQuestion("human_sexuality", "reproductive_biology", "When does ovulation typically occur in a 28-day cycle?", "Around day 14", ["Day 1", "Day 28", "Day 7"], "LH surge triggers ovulation approximately mid-cycle."),
        QuizQuestion("human_sexuality", "sexual_health", "Which STI has an effective vaccine?", "HPV (Human Papillomavirus)", ["HIV", "Herpes", "Chlamydia"], "HPV vaccine prevents the strains causing most cervical cancers and genital warts."),
    ],
}

# ---------- THE BRAIN ----------
SUBJECTS_C["the_brain"] = {
    "name": "The Brain",
    "overview": "The brain contains ~86 billion neurons. It controls all body functions, processes sensory information, stores memories, and generates consciousness.",
    "topics": {
        "brain_anatomy": {
            "title": "Brain Structure & Regions",
            "content": """CEREBRUM (85% of mass):
- Frontal: Executive function, planning, personality, speech (Broca's area), motor cortex.
- Parietal: Somatosensory (touch, pain), spatial awareness.
- Temporal: Hearing, language comprehension (Wernicke's), memory (hippocampus), emotion (amygdala).
- Occipital: Visual processing.

DEEP STRUCTURES: Thalamus (sensory relay), Hypothalamus (homeostasis, hormones), Hippocampus (memory formation, damaged in Alzheimer's), Amygdala (fear, emotional memory), Basal Ganglia (motor, habits, reward - affected in Parkinson's).

CEREBELLUM: Coordination, balance, motor learning. More neurons than rest of brain combined.
BRAINSTEM: Medulla (breathing, heart rate), Pons (sleep), Midbrain (eye movement, reflexes).

LATERALIZATION: Left=language, logic. Right=spatial, creativity. Corpus callosum connects hemispheres (200M+ axons).""",
            "key_formulas": [],
        },
        "neuroplasticity": {
            "title": "Neuroplasticity",
            "content": """Brain's ability to reorganize by forming new connections throughout life.

DEVELOPMENT: Critical periods (language 0-7, vision 0-2). Synaptogenesis (700 new synapses/sec in infancy). Pruning eliminates ~40% by adolescence. Myelination continues to ~25 (prefrontal last).

ADULT PLASTICITY: LTP (Long-Term Potentiation) strengthens repeated connections = learning. LTD weakens unused ones. Neurogenesis in hippocampus (enhanced by exercise, impaired by stress).

BRAIN HEALTH: Positive: exercise (BDNF), sleep (memory consolidation, glymphatic waste clearance), social connection, cognitive challenge, meditation.
Negative: Chronic stress (cortisol damages hippocampus), sleep deprivation, substance abuse, isolation, TBI.
Cognitive reserve: Education and learning build resilience against decline.""",
            "key_formulas": [],
        },
    },
    "quiz_questions": [
        QuizQuestion("the_brain", "brain_anatomy", "Which region forms new long-term memories?", "Hippocampus", ["Amygdala", "Cerebellum", "Thalamus"], "Hippocampus converts short-term to long-term memories. Damage causes amnesia."),
        QuizQuestion("the_brain", "brain_anatomy", "What does Broca's area control?", "Speech production", ["Vision", "Hearing", "Balance"], "Damage causes expressive aphasia (can't produce speech)."),
    ],
}

# ---------- THE NERVOUS SYSTEM ----------
SUBJECTS_C["nervous_system"] = {
    "name": "The Nervous System",
    "overview": "The body's communication network coordinating voluntary and involuntary actions through electrical and chemical signals.",
    "topics": {
        "organization": {
            "title": "Nervous System Organization",
            "content": """CNS: Brain + Spinal cord. Protected by meninges + CSF. 31 spinal nerve pairs.
Gray matter: cell bodies. White matter: myelinated axons.

PNS: All nerves outside CNS.
- Sensory (afferent): receptors->CNS.
- Motor (efferent): CNS->effectors.
  - Somatic: Voluntary skeletal muscle control.
  - Autonomic: Involuntary organ/gland control.
    - Sympathetic: Fight-or-flight (norepinephrine). Increases HR, dilates pupils, inhibits digestion.
    - Parasympathetic: Rest-and-digest (acetylcholine). Slows HR, promotes digestion.
    - Enteric: 'Second brain' in gut. 100M+ neurons. Semi-independent.

REFLEXES: Receptor->Sensory neuron->Integration center->Motor neuron->Effector. Fast, involuntary.""",
            "key_formulas": [],
        },
        "neurons_and_signaling": {
            "title": "Neurons & Signaling",
            "content": """STRUCTURE: Dendrites (receive)->Soma (integrate)->Axon (transmit)->Synaptic terminals (release neurotransmitters).
Myelin: insulation (Schwann cells in PNS, Oligodendrocytes in CNS). Nodes of Ranvier enable saltatory conduction.

ACTION POTENTIAL: Resting -70mV (Na/K pump: 3Na+ out, 2K+ in). Stimulus opens Na+ channels->depolarization to +30mV->Na+ channels close, K+ channels open->repolarization->refractory period. All-or-none, ~100 m/s in myelinated axons.

SYNAPSE: Presynaptic terminal->synaptic cleft->postsynaptic membrane.
Ca2+ influx triggers vesicle fusion, neurotransmitter release. Excitatory (depolarize) or Inhibitory (hyperpolarize) postsynaptic potentials. Summation determines if next neuron fires.

NEUROTRANSMITTERS: Acetylcholine (muscles, memory), Dopamine (reward), Serotonin (mood), GABA (inhibitory), Glutamate (excitatory), Norepinephrine (arousal), Endorphins (pain relief).""",
            "key_formulas": [],
        },
        "disorders": {
            "title": "Neurological Disorders",
            "content": """NEURODEGENERATIVE: Alzheimer's (amyloid plaques, tau tangles, memory loss), Parkinson's (dopamine neuron death, tremor, rigidity), ALS (motor neuron death, Stephen Hawking), Huntington's (genetic, basal ganglia degeneration).

DEMYELINATING: Multiple Sclerosis (immune attacks myelin in CNS, varied symptoms).

SEIZURE DISORDERS: Epilepsy (abnormal electrical activity, various seizure types).

VASCULAR: Stroke - Ischemic (blood clot blocks artery, 87%) or Hemorrhagic (blood vessel ruptures, 13%). Time-critical treatment.

DEVELOPMENTAL: Autism spectrum, ADHD, Cerebral palsy.

PAIN: Nociceptors detect damage. Gate control theory: spinal cord can block pain signals. Referred pain: organ pain felt at distant body surface.""",
            "key_formulas": [],
        },
    },
    "quiz_questions": [
        QuizQuestion("nervous_system", "organization", "What does the sympathetic nervous system do?", "Fight-or-flight: increases HR, dilates pupils, inhibits digestion", ["Rest and digest", "Control skeletal muscles", "Form memories"], "Sympathetic prepares body for action using norepinephrine."),
        QuizQuestion("nervous_system", "neurons_and_signaling", "What maintains the resting membrane potential?", "Na+/K+ ATPase pump (3 Na+ out, 2 K+ in)", ["Calcium channels", "Myelin sheath", "Neurotransmitters"], "The pump creates the -70mV charge difference across the membrane."),
    ],
}

# ---------- TELEMETRY ----------
SUBJECTS_C["telemetry"] = {
    "name": "Telemetry",
    "overview": "The science of remote measurement and data transmission. Used in aerospace, medicine, weather, wildlife tracking, industrial monitoring, and telecommunications.",
    "topics": {
        "fundamentals": {
            "title": "Telemetry Fundamentals",
            "content": """Telemetry = tele (remote) + metron (measure). Automated collection and transmission of data from remote sources.

COMPONENTS: Sensor (measures physical quantity) -> Transducer (converts to electrical signal) -> Transmitter (sends data) -> Communication channel -> Receiver -> Data processing/display.

TYPES:
- Wireless: Radio frequency (RF), satellite, cellular, Bluetooth, WiFi.
- Wired: Ethernet, serial (RS-232/485), fiber optic.
- Acoustic: Underwater telemetry (sonar-based).

SIGNAL PROCESSING: Analog-to-digital conversion (sampling rate >= 2x max frequency per Nyquist theorem). Data compression, error detection/correction (CRC, FEC), encryption.

PROTOCOLS: IRIG (Inter-Range Instrumentation Group) standards for aerospace. MQTT, CoAP for IoT. DICOM for medical imaging. PCM (Pulse Code Modulation) for digital telemetry.

APPLICATIONS: Spacecraft health monitoring (NASA), cardiac telemetry (ECG remote), SCADA (industrial control), weather stations, GPS tracking, Formula 1 race cars (1500+ data points/second).""",
            "key_formulas": ["Nyquist: sampling_rate >= 2 * max_frequency"],
        },
        "medical_telemetry": {
            "title": "Medical Telemetry",
            "content": """Remote monitoring of patient vital signs and physiological data.

CARDIAC TELEMETRY: Continuous ECG monitoring. Detects arrhythmias (afib, vtach, vfib). Electrodes on chest transmit to central monitoring station. Life-saving in ICU and cardiac units.

PULSE OXIMETRY: SpO2 measurement via light absorption through finger/earlobe. Normal 95-100%.

REMOTE PATIENT MONITORING: Wearable devices transmit BP, HR, glucose, weight to healthcare providers. Enables early intervention and reduces hospital readmissions.

BIOTELEMETRY SENSORS: Implantable cardiac monitors (loop recorders), continuous glucose monitors (CGM), smart pills (ingestible sensors for medication adherence).

CHALLENGES: Signal interference, patient privacy (HIPAA), alarm fatigue (too many false alarms), battery life, data overload.""",
            "key_formulas": [],
        },
    },
    "quiz_questions": [
        QuizQuestion("telemetry", "fundamentals", "What is the Nyquist sampling rate?", "At least 2x the maximum signal frequency", ["Equal to signal frequency", "Half the signal frequency", "10x the signal frequency"], "Nyquist theorem: to accurately digitize a signal, sample at >= 2x its highest frequency."),
    ],
}

# ---------- AERONAUTICS ----------
SUBJECTS_C["aeronautics"] = {
    "name": "Aeronautics",
    "overview": "The science and engineering of flight within Earth's atmosphere, and astronautics extends this to space travel.",
    "topics": {
        "principles_of_flight": {
            "title": "Principles of Flight",
            "content": """FOUR FORCES: Lift (upward, from wing), Weight (downward, gravity), Thrust (forward, from engine), Drag (backward, air resistance).

LIFT: Generated by pressure difference above/below wing. Bernoulli's principle: faster air over curved upper surface = lower pressure. Also: Newton's 3rd law - wing deflects air downward, air pushes wing up.
Lift equation: L = (1/2) * rho * v^2 * S * CL (air density * velocity^2 * wing area * lift coefficient).

AIRFOIL: Cross-section of wing. Camber (curvature), chord (length), angle of attack (angle between chord and airflow). Increasing angle of attack increases lift until stall (flow separation, lift drops suddenly).

DRAG: Parasitic (form + skin friction) + Induced (byproduct of lift, wingtip vortices).

FLIGHT CONTROLS: Ailerons (roll), Elevator (pitch), Rudder (yaw). Flaps increase lift at low speeds.

STABILITY: Longitudinal (pitch), Lateral (roll), Directional (yaw). Center of gravity must be forward of center of pressure.""",
            "key_formulas": ["L = (1/2)*rho*v^2*S*CL"],
        },
        "spacecraft_and_orbits": {
            "title": "Spacecraft & Orbital Mechanics",
            "content": """ROCKET PROPULSION: Newton's 3rd law. Exhaust gases pushed backward, rocket pushed forward.
Tsiolkovsky equation: delta_v = ve * ln(m0/mf). ve=exhaust velocity, m0=initial mass, mf=final mass.
Specific impulse (Isp): efficiency metric = thrust / (mass_flow * g). Higher = better.

ORBITS: Governed by gravity. Kepler's Laws:
1. Orbits are ellipses with central body at one focus.
2. Equal areas swept in equal times (faster when closer).
3. T^2 proportional to a^3 (period^2 ~ semi-major axis^3).

Orbital velocity: v = sqrt(GM/r). Escape velocity: ve = sqrt(2GM/r).
LEO: 160-2000 km (ISS at ~408km, 7.66 km/s). GEO: 35,786 km (communications satellites, stationary above equator).

HOHMANN TRANSFER: Minimum-energy orbit change between two circular orbits. Two burns.

REENTRY: Extreme heating from atmospheric friction. Heat shields: ablative (Apollo), thermal tiles (Shuttle), PICA (SpaceX).""",
            "key_formulas": ["delta_v = ve*ln(m0/mf)", "v_orbital = sqrt(GM/r)", "v_escape = sqrt(2GM/r)"],
        },
    },
    "quiz_questions": [
        QuizQuestion("aeronautics", "principles_of_flight", "What are the four forces of flight?", "Lift, Weight, Thrust, Drag", ["Speed, Altitude, Direction, Power", "Gravity, Inertia, Friction, Pressure", "Roll, Pitch, Yaw, Thrust"], "Lift opposes weight, thrust opposes drag. Balance determines flight."),
        QuizQuestion("aeronautics", "spacecraft_and_orbits", "What is escape velocity from Earth's surface?", "About 11.2 km/s", ["3 km/s", "7.9 km/s", "30 km/s"], "v_escape = sqrt(2GM/r). Must exceed this to leave Earth's gravitational pull."),
    ],
}

# ---------- DRAMA / THEATER ----------
SUBJECTS_C["drama"] = {
    "name": "Drama & Theater",
    "overview": "The art of storytelling through live performance, encompassing acting, directing, playwriting, design, and theater history.",
    "topics": {
        "acting_techniques": {
            "title": "Acting Techniques",
            "content": """STANISLAVSKI SYSTEM: Foundation of modern acting. 'Given circumstances' - understand character's world. 'Magic If' - what would I do if I were this character? Emotional memory: draw on personal experience. Objectives and obstacles drive scenes.

METHOD ACTING (Strasberg): Extreme version of Stanislavski. Deep psychological identification with character. Sense memory exercises. Used by Daniel Day-Lewis, Robert De Niro.

MEISNER TECHNIQUE: 'Living truthfully under imaginary circumstances.' Repetition exercises build authentic listening and responding. Focus on the other actor, not self.

CHEKHOV TECHNIQUE (Michael Chekhov): Psychological gesture - physical movement expressing character's inner drive. Atmosphere and imagination-based. Less personal emotional digging than Method.

VIEWPOINTS: Movement/composition technique by Anne Bogart. 9 viewpoints: tempo, duration, kinesthetic response, repetition, shape, gesture, architecture, spatial relationship, topography.

VOICE AND BODY: Breath support (diaphragmatic), resonance, articulation, projection. Alexander Technique (posture/alignment). Laban Movement Analysis (effort/shape). Stage combat.""",
            "key_formulas": [],
        },
        "theater_history": {
            "title": "Theater History",
            "content": """ANCIENT GREECE (5th century BCE): Origin of Western theater. Festivals honoring Dionysus. Tragedy (Aeschylus, Sophocles, Euripides) and Comedy (Aristophanes). Chorus, masks, amphitheaters seating 15,000+. Aristotle's 'Poetics': plot, character, thought, diction, spectacle, song.

ROMAN THEATER: Adapted Greek forms. Plautus and Terence (comedy). Seneca (tragedy, influenced Renaissance). Colosseum spectacles.

MEDIEVAL: Mystery plays (Bible stories), Morality plays (Everyman), performed in churches then streets.

RENAISSANCE: Shakespeare (1564-1616) - 37 plays spanning comedy, tragedy, history, romance. Globe Theatre. Italian Commedia dell'arte (improvised, stock characters: Harlequin, Columbine).

MODERN: Ibsen (realism, 'A Doll's House'), Chekhov (psychological realism), Brecht (epic theater, alienation effect), Beckett (absurdism, 'Waiting for Godot'), Miller ('Death of a Salesman'), Williams ('A Streetcar Named Desire').

CONTEMPORARY: Musical theater (Sondheim, Lin-Manuel Miranda), Devised theater, Immersive theater, Digital/virtual performance.""",
            "key_formulas": [],
        },
        "stagecraft": {
            "title": "Stagecraft & Production",
            "content": """STAGE TYPES: Proscenium (picture frame, audience on one side), Thrust (audience on 3 sides), Arena/Theater-in-the-round (audience surrounds), Black box (flexible), Site-specific.

LIGHTING: Functions: visibility, mood, focus, time/location. Key instruments: Fresnel (soft wash), ERS/Leko (sharp focus), PAR (broad wash), LED (color mixing). Three-point lighting: key, fill, back.

SOUND: Reinforcement (mics + speakers), Sound effects (live + recorded), Music underscoring. Wireless body mics for musicals.

SET DESIGN: Ground plan, elevations, model. Materials: flats (walls), platforms (levels), drops (painted backgrounds). Fly system (raise/lower scenery).

COSTUMES: Period research, character expression, color symbolism, quick changes. Collaboration with director's vision.

DIRECTING: Script analysis, concept development, blocking (actor movement), pacing, working with designers. Director's vision unifies all elements.""",
            "key_formulas": [],
        },
    },
    "quiz_questions": [
        QuizQuestion("drama", "acting_techniques", "Who created the 'System' that is the foundation of modern acting?", "Konstantin Stanislavski", ["Lee Strasberg", "Sanford Meisner", "Stella Adler"], "Stanislavski's System introduced objectives, given circumstances, and emotional truth."),
        QuizQuestion("drama", "theater_history", "Who wrote 'A Doll's House' and pioneered theatrical realism?", "Henrik Ibsen", ["Anton Chekhov", "Arthur Miller", "Tennessee Williams"], "Ibsen is called the father of realism for confronting social issues on stage."),
    ],
}

# ---------- GEOMETRY ----------
SUBJECTS_C["geometry"] = {
    "name": "Geometry",
    "overview": "Study of shapes, sizes, positions, angles, and dimensions of things. From Euclidean plane geometry to solid geometry, coordinate geometry, and non-Euclidean systems.",
    "topics": {
        "euclidean_geometry": {
            "title": "Euclidean Geometry",
            "content": """FUNDAMENTALS: Points (0D), Lines (1D, infinite length), Planes (2D). Postulates: two points determine a line, three non-collinear points determine a plane.

ANGLES: Acute (<90), Right (90), Obtuse (>90), Straight (180), Reflex (>180).
Complementary (sum 90), Supplementary (sum 180), Vertical (equal).

TRIANGLES: Angle sum = 180. Types: Equilateral (60-60-60), Isosceles (2 equal sides), Scalene (all different), Right (one 90).
- Pythagorean theorem: a^2+b^2=c^2. Congruence: SSS, SAS, ASA, AAS. Similarity: AA, SAS, SSS.
- Area = (1/2)bh. Heron's formula: A = sqrt(s(s-a)(s-b)(s-c)) where s=(a+b+c)/2.

QUADRILATERALS: Parallelogram (opposite sides parallel/equal), Rectangle (right angles), Rhombus (equal sides), Square (rectangle+rhombus), Trapezoid (one pair parallel).

CIRCLES: C=2*pi*r, A=pi*r^2. Central angle = arc. Inscribed angle = half arc. Tangent perpendicular to radius.""",
            "key_formulas": ["a^2+b^2=c^2", "A=pi*r^2", "C=2*pi*r", "A_triangle=(1/2)bh"],
        },
        "solid_geometry": {
            "title": "Solid Geometry & 3D Shapes",
            "content": """PRISMS: Two parallel congruent bases. V=Bh (base area * height). SA=2B+Ph (perimeter*height).
CYLINDERS: V=pi*r^2*h. SA=2*pi*r^2+2*pi*r*h.
PYRAMIDS: V=(1/3)Bh. Apex above base center.
CONES: V=(1/3)*pi*r^2*h. Slant height l=sqrt(r^2+h^2). SA=pi*r*l+pi*r^2.
SPHERES: V=(4/3)*pi*r^3. SA=4*pi*r^2.

EULER'S FORMULA for polyhedra: V-E+F=2 (vertices-edges+faces).

COORDINATE GEOMETRY (3D): Distance=sqrt((x2-x1)^2+(y2-y1)^2+(z2-z1)^2). Planes: ax+by+cz=d. Lines parametrically.""",
            "key_formulas": ["V_sphere=(4/3)*pi*r^3", "V_cylinder=pi*r^2*h", "V_cone=(1/3)*pi*r^2*h", "V-E+F=2"],
        },
        "trigonometry_geometry": {
            "title": "Trigonometry in Geometry",
            "content": """UNIT CIRCLE: sin(theta)=y, cos(theta)=x. Radius=1.
Special angles: sin(30)=1/2, sin(45)=sqrt(2)/2, sin(60)=sqrt(3)/2.

IDENTITIES: sin^2+cos^2=1. tan=sin/cos. Double angle: sin(2x)=2sin(x)cos(x), cos(2x)=cos^2(x)-sin^2(x).

LAW OF SINES: a/sin(A)=b/sin(B)=c/sin(C). For any triangle.
LAW OF COSINES: c^2=a^2+b^2-2ab*cos(C). Generalized Pythagorean theorem.

APPLICATIONS: Surveying, navigation, architecture, wave analysis, signal processing.
Area of triangle: A=(1/2)ab*sin(C).""",
            "key_formulas": ["sin^2+cos^2=1", "a/sin(A)=b/sin(B)=c/sin(C)", "c^2=a^2+b^2-2ab*cos(C)"],
        },
    },
    "quiz_questions": [
        QuizQuestion("geometry", "euclidean_geometry", "What is the Pythagorean theorem?", "a^2+b^2=c^2 for right triangles", ["a+b=c", "a^2+b^2=c", "a*b=c^2"], "Sum of squares of legs equals square of hypotenuse."),
        QuizQuestion("geometry", "solid_geometry", "What is the volume of a sphere?", "(4/3)*pi*r^3", ["4*pi*r^2", "pi*r^2*h", "(1/3)*pi*r^2*h"], "V=(4/3)*pi*r^3. Surface area is 4*pi*r^2."),
        QuizQuestion("geometry", "trigonometry_geometry", "What does the Law of Cosines generalize?", "The Pythagorean theorem (works for any triangle)", ["Law of Sines", "Area formula", "Unit circle"], "When C=90, cos(C)=0 and it reduces to a^2+b^2=c^2."),
    ],
}
