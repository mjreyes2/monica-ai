"""
Monica University - Subjects Part B
Physics, Computer Science, Engineering, Electrical Engineering, Geography
"""
from ai.monica_university import QuizQuestion

SUBJECTS_B = {}

# ---------- PHYSICS ----------
SUBJECTS_B["physics"] = {
    "name": "Physics",
    "overview": "The fundamental science studying matter, energy, space, and time.",
    "topics": {
        "mechanics": {
            "title": "Classical Mechanics",
            "content": """KINEMATICS: Position, Velocity (dx/dt), Acceleration (dv/dt).
Equations: v=v0+at, x=x0+v0t+(1/2)at^2, v^2=v0^2+2a(x-x0).

NEWTON'S LAWS: 1) Inertia 2) F=ma 3) Action-reaction.

ENERGY: Work W=Fd*cos(theta). KE=(1/2)mv^2. PE=mgh. Conservation: KE+PE=constant.
MOMENTUM: p=mv. Conserved in closed systems. Impulse J=F*dt=dp.

ROTATIONAL: Torque tau=rxF, Angular momentum L=I*omega.
GRAVITY: F=Gm1m2/r^2. Orbits, Kepler's laws.""",
            "key_formulas": ["F=ma", "KE=(1/2)mv^2", "PE=mgh", "F=Gm1m2/r^2"],
        },
        "electromagnetism": {
            "title": "Electromagnetism",
            "content": """ELECTROSTATICS: Coulomb's law F=kq1q2/r^2. Electric field E=kQ/r^2. Potential V=kQ/r. Capacitance C=Q/V.

CIRCUITS: Ohm's law V=IR. Power P=IV=I^2R. Series: R_total=R1+R2. Parallel: 1/R_total=1/R1+1/R2.
Kirchhoff's: Junction (current in=out), Loop (voltage drops sum to 0).

MAGNETISM: Moving charges create B fields. Force F=qvxB. Faraday's law: EMF=-d(phi)/dt.
Maxwell's Equations unify E&M and predict electromagnetic waves.

EM SPECTRUM: Radio, microwave, infrared, visible, UV, X-ray, gamma. All travel at c=3x10^8 m/s.""",
            "key_formulas": ["F=kq1q2/r^2", "V=IR", "EMF=-d(phi)/dt"],
        },
        "thermodynamics": {
            "title": "Thermodynamics",
            "content": """LAWS: 0th: Thermal equilibrium is transitive. 1st: dU=Q-W (energy conserved). 2nd: Entropy always increases. 3rd: S->0 as T->0K.

HEAT TRANSFER: Conduction (contact), Convection (fluid flow), Radiation (EM waves, P=sigma*A*T^4).

IDEAL GAS: PV=nRT. Boyle's (PV=const at fixed T), Charles's (V/T=const at fixed P).

ENGINES: Efficiency=W/Q_hot=1-Q_cold/Q_hot. Carnot max=1-T_cold/T_hot.""",
            "key_formulas": ["PV=nRT", "dU=Q-W", "Carnot=1-T_cold/T_hot"],
        },
        "modern_physics": {
            "title": "Modern Physics",
            "content": """SPECIAL RELATIVITY: c constant for all observers. Time dilation dt=gamma*dt0 (gamma=1/sqrt(1-v^2/c^2)). Length contraction. E=mc^2.

QUANTUM MECHANICS: Wave-particle duality. Photoelectric effect E=hf. de Broglie lambda=h/(mv).
Heisenberg: dx*dp>=h/(4pi). Schrodinger equation describes quantum states.
Quantum tunneling: particles cross classically forbidden barriers.

NUCLEAR: Alpha/Beta/Gamma decay. Half-life N(t)=N0*(1/2)^(t/t_half).
Fission (heavy nuclei split) and Fusion (light nuclei combine).""",
            "key_formulas": ["E=mc^2", "E=hf", "lambda=h/(mv)", "N(t)=N0*(1/2)^(t/t_half)"],
        },
    },
    "quiz_questions": [
        QuizQuestion("physics", "mechanics", "What is Newton's second law?", "F=ma", ["Action-reaction", "Inertia", "Energy conservation"], "Force equals mass times acceleration."),
        QuizQuestion("physics", "electromagnetism", "What is Ohm's Law?", "V=IR", ["F=ma", "E=mc^2", "PV=nRT"], "Voltage equals current times resistance."),
        QuizQuestion("physics", "modern_physics", "What does E=mc^2 mean?", "Mass and energy are interconvertible", ["Energy equals momentum", "Light has mass", "Time is relative"], "Small mass contains enormous energy, with c^2 as conversion factor."),
    ],
}

# ---------- COMPUTER SCIENCE ----------
SUBJECTS_B["computer_science"] = {
    "name": "Computer Science",
    "overview": "Study of computation, algorithms, data structures, software engineering, and information processing.",
    "topics": {
        "algorithms": {
            "title": "Algorithms & Complexity",
            "content": """BIG-O: O(1) constant, O(log n) binary search, O(n) linear scan, O(n log n) merge sort, O(n^2) bubble sort, O(2^n) exponential, O(n!) factorial.

SORTING: Bubble O(n^2), Merge O(n log n) stable, Quick O(n log n) avg in-place, Heap O(n log n).
SEARCHING: Linear O(n), Binary O(log n) requires sorted, Hash table O(1) avg.

GRAPH ALGORITHMS: BFS (level-by-level, shortest unweighted path), DFS (depth-first, cycle detection), Dijkstra (weighted shortest path), Dynamic Programming (overlapping subproblems).""",
            "key_formulas": ["O(1)<O(log n)<O(n)<O(n log n)<O(n^2)<O(2^n)"],
        },
        "data_structures": {
            "title": "Data Structures",
            "content": """ARRAYS: O(1) access, O(n) insert/delete. Contiguous memory.
LINKED LISTS: O(1) insert/delete at known pos, O(n) access. Nodes with pointers.
STACKS: LIFO. Push/pop. Function calls, undo, expression parsing.
QUEUES: FIFO. Enqueue/dequeue. Scheduling, BFS.

TREES: Binary Tree, BST (left<parent<right, O(log n) balanced), AVL/Red-Black (self-balancing), Heap (priority queue), Trie (prefix search, autocomplete).

HASH TABLES: Key-value O(1) avg. Collision handling: chaining, open addressing.

GRAPHS: Vertices+edges. Adjacency matrix/list. Directed/undirected. Weighted/unweighted. Social networks, maps, dependencies.""",
            "key_formulas": [],
        },
        "operating_systems": {
            "title": "Operating Systems",
            "content": """PROCESSES: Running program with own memory. Threads share memory. Scheduling: round-robin, priority. Synchronization: mutexes, semaphores. Deadlock: circular resource wait.

MEMORY: Virtual memory (each process own address space). Paging (fixed blocks, page table). Page replacement: LRU, FIFO. Caching: L1/L2/L3/disk/web.

FILE SYSTEMS: FAT32, NTFS, ext4. Directories, permissions, journaling.

ARCHITECTURE: Von Neumann (CPU+Memory+I/O). Instruction cycle: Fetch->Decode->Execute->Store. Pipelining overlaps stages.""",
            "key_formulas": [],
        },
        "networking": {
            "title": "Computer Networking",
            "content": """OSI MODEL (7 layers): Physical, Data Link, Network, Transport, Session, Presentation, Application.
TCP/IP MODEL (4 layers): Network Access, Internet, Transport, Application.

KEY PROTOCOLS: HTTP/HTTPS (web), TCP (reliable, ordered), UDP (fast, unreliable), IP (addressing/routing), DNS (domain->IP), DHCP (auto IP assignment), SSH (secure shell), FTP (file transfer).

IP ADDRESSING: IPv4 (32-bit, 4.3 billion addresses), IPv6 (128-bit). Subnetting, CIDR notation.
SECURITY: Firewalls, encryption (TLS/SSL), VPN, authentication. Common attacks: DDoS, SQL injection, XSS, phishing.""",
            "key_formulas": [],
        },
    },
    "quiz_questions": [
        QuizQuestion("computer_science", "algorithms", "What is the time complexity of binary search?", "O(log n)", ["O(n)", "O(n^2)", "O(1)"], "Binary search halves search space each step."),
        QuizQuestion("computer_science", "data_structures", "Which data structure uses LIFO?", "Stack", ["Queue", "Linked List", "Hash Table"], "Last In, First Out - like a stack of plates."),
    ],
}

# ---------- ENGINEERING ----------
SUBJECTS_B["engineering"] = {
    "name": "Engineering",
    "overview": "Application of scientific and mathematical principles to design, build, and analyze structures, machines, and systems.",
    "topics": {
        "statics_and_dynamics": {
            "title": "Statics & Dynamics",
            "content": """STATICS: Equilibrium: sum(F)=0, sum(M)=0. Free body diagrams essential.
Forces: Weight(mg), Normal, Friction(f<=mu_s*N), Tension, Spring(F=-kx).
Trusses: Method of joints, method of sections. Centroids.

DYNAMICS: Newton's 2nd rotational: tau=I*alpha. Work-energy: net work=delta(KE). Impulse: F*dt=m*dv.
Vibrations: SHM x(t)=A*cos(omega*t+phi). Period T=2pi*sqrt(m/k).

MATERIALS: Stress=F/A (Pa). Strain=dL/L. Young's Modulus E=stress/strain. Yield strength, ultimate strength.""",
            "key_formulas": ["stress=F/A", "E=stress/strain", "T=2pi*sqrt(m/k)"],
        },
        "fluid_mechanics": {
            "title": "Fluid Mechanics",
            "content": """FLUID STATICS: Pressure P=rho*g*h. Pascal's principle: pressure transmitted equally. Archimedes: buoyant force = weight of displaced fluid.

FLUID DYNAMICS: Continuity equation A1*v1=A2*v2. Bernoulli's: P+(1/2)rho*v^2+rho*g*h=constant.
Reynolds number Re=rho*v*D/mu. Re<2300 laminar, Re>4000 turbulent.

APPLICATIONS: Pipe flow, aerodynamics (lift and drag), pumps, turbines, hydraulic systems.
Navier-Stokes equations govern all fluid motion (one of the millennium prize problems).""",
            "key_formulas": ["P=rho*g*h", "A1v1=A2v2", "Bernoulli: P+(1/2)rho*v^2+rho*g*h=const"],
        },
        "thermodynamics_engineering": {
            "title": "Engineering Thermodynamics",
            "content": """CYCLES: Carnot (max efficiency, 2 isothermal+2 adiabatic), Otto (gasoline, 2 isochoric+2 adiabatic), Diesel (higher compression), Rankine (steam power: pump->boiler->turbine->condenser).

REFRIGERATION: Reversed heat engine. COP=Q_cold/W. Heat pumps: COP=Q_hot/W.
HEAT EXCHANGERS: Counter-flow more efficient than parallel-flow.
PSYCHROMETRICS: Air-water vapor mixtures. HVAC design. Humidity, dew point.""",
            "key_formulas": ["Carnot=1-T_cold/T_hot", "COP_ref=Q_cold/W"],
        },
    },
    "quiz_questions": [
        QuizQuestion("engineering", "statics_and_dynamics", "What two conditions define static equilibrium?", "Sum of forces=0 AND sum of moments=0", ["Forces=0 only", "Energy=0", "Velocity=0"], "Both translational and rotational equilibrium required."),
        QuizQuestion("engineering", "fluid_mechanics", "What does Bernoulli's equation describe?", "Conservation of energy in fluid flow", ["Conservation of mass", "Conservation of momentum", "Heat transfer"], "Higher velocity = lower pressure along a streamline."),
    ],
}

# ---------- ELECTRICAL ENGINEERING ----------
SUBJECTS_B["electrical_engineering"] = {
    "name": "Electrical Engineering",
    "overview": "Design and analysis of electrical systems, circuits, electronics, power systems, and signal processing.",
    "topics": {
        "circuit_analysis": {
            "title": "Circuit Analysis",
            "content": """COMPONENTS: Resistor (V=IR), Capacitor (I=C*dV/dt, stores charge), Inductor (V=L*dI/dt, stores energy in magnetic field).

KIRCHHOFF'S LAWS: KCL: currents in=currents out at node. KVL: voltage drops around loop=0.

METHODS: Mesh analysis (KVL on loops), Node analysis (KCL at nodes), Thevenin (Vth+Rth series), Norton (In parallel Rn), Superposition (sum individual source responses).

AC CIRCUITS: Phasors (complex representation), Impedance Z=R+jX.
Power: P=Vrms*Irms*cos(phi). Resonance: f0=1/(2pi*sqrt(LC)).""",
            "key_formulas": ["V=IR", "f0=1/(2pi*sqrt(LC))", "P=Vrms*Irms*cos(phi)"],
        },
        "digital_electronics": {
            "title": "Digital Electronics",
            "content": """LOGIC GATES: AND, OR, NOT, NAND, NOR, XOR. NAND and NOR are universal.
BOOLEAN ALGEBRA: De Morgan's: (AB)'=A'+B', (A+B)'=A'B'.

COMBINATIONAL: Multiplexers, Adders (half/full), Encoders/Decoders.
SEQUENTIAL: Flip-flops (SR, D, JK, T), Registers, Counters, State machines.

MICROPROCESSORS: CPU=ALU+Control+Registers. RISC vs CISC.
Memory hierarchy: Registers->Cache->RAM->SSD/HDD. ADC/DAC converters.""",
            "key_formulas": ["De Morgan: (AB)'=A'+B'"],
        },
        "signals_and_systems": {
            "title": "Signals & Systems",
            "content": """SIGNALS: Continuous vs discrete. Periodic vs aperiodic. Deterministic vs random.
Fourier analysis: Any periodic signal = sum of sinusoids. Frequency domain representation.

SYSTEMS: Linear, time-invariant (LTI). Transfer function H(s). Convolution: y(t)=x(t)*h(t).
Laplace Transform: Convert differential equations to algebraic. s-domain analysis.

FILTERS: Low-pass (passes low frequencies), High-pass, Band-pass, Band-stop.
Cutoff frequency, roll-off rate, Butterworth/Chebyshev/Bessel designs.

CONTROL SYSTEMS: Feedback loops. PID controller (Proportional+Integral+Derivative). Stability analysis (Bode plots, Nyquist, root locus).""",
            "key_formulas": [],
        },
    },
    "quiz_questions": [
        QuizQuestion("electrical_engineering", "circuit_analysis", "What does KCL state?", "Currents entering a node equal currents leaving", ["Voltage around loop=0", "Power conserved", "Resistance adds in series"], "KCL: conservation of charge at junction."),
        QuizQuestion("electrical_engineering", "digital_electronics", "Which gates are universal?", "NAND and NOR", ["AND and OR", "XOR and XNOR", "NOT and AND"], "Any logic function can be built with only NAND or only NOR gates."),
    ],
}

# ---------- GEOGRAPHY ----------
SUBJECTS_B["geography"] = {
    "name": "Geography",
    "overview": "Study of Earth's landscapes, environments, and human-environment relationships.",
    "topics": {
        "physical_geography": {
            "title": "Physical Geography",
            "content": """PLATE TECTONICS: ~15 major plates. Divergent (spread, new crust), Convergent (collide, mountains/volcanoes), Transform (slide past, earthquakes).

CLIMATE: Koppen zones (Tropical, Arid, Temperate, Continental, Polar). Atmospheric circulation: Hadley/Ferrel/Polar cells. Coriolis effect deflects air. Ocean currents (Gulf Stream). Climate change from greenhouse gases.

GEOMORPHOLOGY: Erosion, weathering, deposition shape landforms. Rivers, glaciers, deserts, coasts.

BIOMES: Tropical rainforest, savanna, desert, temperate grassland/forest, taiga, tundra, aquatic.""",
            "key_formulas": [],
        },
        "human_geography": {
            "title": "Human Geography",
            "content": """POPULATION: Demographic transition model (high birth/death -> low birth/death). Population pyramids show age-sex distribution. Urbanization accelerating globally.

ECONOMIC: Primary (agriculture, mining), Secondary (manufacturing), Tertiary (services), Quaternary (information/research). GDP, development indices.

CULTURAL: Language families, religion distributions, cultural diffusion, globalization.

GEOPOLITICS: Nation-states, borders, territorial disputes. International organizations (UN, EU, NATO). Resources and conflict.""",
            "key_formulas": [],
        },
    },
    "quiz_questions": [
        QuizQuestion("geography", "physical_geography", "What happens at convergent plate boundaries?", "Plates collide causing subduction, mountains, or volcanoes", ["Plates separate", "Plates slide past", "Nothing"], "Creates Himalayas-type mountains and volcanic arcs."),
    ],
}
