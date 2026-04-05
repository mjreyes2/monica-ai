"""
Monica University - Subjects Part D
Teaching Pedagogy, Public Speaking (Toastmasters), Interviewing Techniques,
ADHD/Neurodivergent Learning Awareness
"""
from ai.monica_university import QuizQuestion

SUBJECTS_D = {}

# ---------- TEACHING PEDAGOGY & LEARNING STYLES ----------
SUBJECTS_D["teaching_pedagogy"] = {
    "name": "Teaching Pedagogy & Learning Styles",
    "overview": "The science and art of teaching. Understanding how people learn, different learning styles, effective teaching strategies, and how to adapt instruction for diverse learners including neurodivergent students.",
    "topics": {
        "learning_styles": {
            "title": "Learning Styles & Modalities",
            "content": """VARK MODEL (Fleming):
- Visual: Learns best through images, diagrams, charts, maps, color-coding. Use whiteboards, mind maps, infographics, videos.
- Auditory: Learns through listening and discussion. Lectures, podcasts, read-aloud, verbal explanations, group discussion.
- Reading/Writing: Prefers text-based information. Notes, lists, textbooks, written instructions, essays.
- Kinesthetic: Learns by doing. Hands-on activities, experiments, role-play, building models, movement.

GARDNER'S MULTIPLE INTELLIGENCES: Linguistic, Logical-Mathematical, Spatial, Musical, Bodily-Kinesthetic, Interpersonal, Intrapersonal, Naturalistic.

KOLB'S EXPERIENTIAL LEARNING CYCLE: Concrete Experience -> Reflective Observation -> Abstract Conceptualization -> Active Experimentation.

BLOOM'S TAXONOMY (learning depth): Remember -> Understand -> Apply -> Analyze -> Evaluate -> Create. Move students progressively up the hierarchy.

KEY PRINCIPLE: Most people are multimodal learners - they benefit from MULTIPLE modalities combined. The best teaching uses visual + auditory + kinesthetic simultaneously.""",
            "key_formulas": [],
        },
        "effective_teaching": {
            "title": "Effective Teaching Strategies",
            "content": """SCAFFOLDING: Start with high support, gradually reduce as learner gains competence. Zone of Proximal Development (Vygotsky): target just beyond current ability.

CHUNKING: Break complex material into small, digestible pieces. 7+/-2 items in working memory at once (Miller's Law). Use numbered steps, bullet points.

SPACED REPETITION: Review material at increasing intervals (1 day, 3 days, 1 week, 2 weeks, 1 month). Far more effective than cramming.

ACTIVE RECALL: Testing yourself is more effective than re-reading. Flashcards, practice problems, teach-back method.

SOCRATIC METHOD: Ask guiding questions instead of giving answers. "What do you think happens when...?" Develops critical thinking.

DIFFERENTIATED INSTRUCTION: Adjust content, process, and product based on student readiness, interest, and learning profile.

FORMATIVE ASSESSMENT: Frequent low-stakes checks for understanding. Thumbs up/down, exit tickets, quick quizzes. Adjust teaching based on results.

METACOGNITION: Teach students HOW to learn. Study strategies, self-monitoring, goal-setting, reflection.

MOTIVATION: Intrinsic > extrinsic. Connect material to learner's interests and goals. Celebrate progress, not just outcomes. Growth mindset (Dweck): intelligence is developable, not fixed.""",
            "key_formulas": [],
        },
        "neurodivergent_teaching": {
            "title": "Teaching Neurodivergent Learners (ADHD, Autism, etc.)",
            "content": """ADHD-SPECIFIC STRATEGIES:
- Chunk lessons into 10-15 minute segments with brief breaks or activity changes.
- Use timers and visible schedules. Predictability reduces anxiety.
- Offer movement breaks - standing, stretching, fidget tools.
- Present information multimodally: say it, show it, do it.
- Use high-interest topics as entry points (gamification, real-world applications).
- Minimize distractions: clean workspace, one task at a time.
- Immediate feedback, not delayed. Celebrate small wins.
- Use color-coding, highlighting, visual organizers.
- Allow extra processing time. Don't rush responses.
- Body doubling: work alongside the learner.
- Hyperfocus is a strength - channel it into deep dives on topics of interest.

ANXIETY/DEPRESSION CONSIDERATIONS:
- Create psychologically safe environment. No judgment for mistakes.
- Validate feelings before teaching. "I understand this feels overwhelming."
- Break tasks into micro-steps. "Just do the first problem."
- Offer choices for autonomy. "Would you like to start with topic A or B?"
- Normalize struggle. "This IS hard. You're doing well to try."

OCD CONSIDERATIONS:
- Be patient with repetitive questions or behaviors.
- Provide clear, consistent structure.
- Avoid ambiguity - give definitive answers when possible.

ECHOLALIA CONSIDERATIONS:
- Recognize repetition as a communication strategy, not defiance.
- Use echolalia therapeutically - model correct/expanded phrases.
- Give processing time before expecting novel responses.
- Use visual supports alongside verbal instructions.

UNIVERSAL DESIGN FOR LEARNING (UDL):
- Multiple means of ENGAGEMENT (why learn? motivation, self-regulation)
- Multiple means of REPRESENTATION (what to learn? visual, auditory, text)
- Multiple means of ACTION & EXPRESSION (how to show learning? write, speak, build, draw)""",
            "key_formulas": [],
        },
        "assessment_methods": {
            "title": "Assessment & Feedback Methods",
            "content": """FORMATIVE (during learning): Quizzes, discussions, think-pair-share, observation, exit tickets, concept maps. Low-stakes, for adjustment.

SUMMATIVE (after learning): Tests, projects, presentations, portfolios. Higher-stakes, for evaluation.

AUTHENTIC ASSESSMENT: Real-world tasks demonstrating competence. Portfolio, case study, simulation, teaching others.

RUBRICS: Clear criteria and expectations. Holistic (overall quality) or Analytic (criteria-by-criteria).

FEEDBACK PRINCIPLES:
- Specific, not vague: "Your thesis is clear but needs evidence" vs "good job."
- Timely: As soon after the work as possible.
- Actionable: Tell them WHAT to do, not just what's wrong.
- Balanced: Strengths AND areas for improvement (sandwich method).
- Growth-oriented: "You haven't mastered this YET" (growth mindset language).

SELF-ASSESSMENT: Teach learners to evaluate their own work against criteria. Builds metacognition and independence.""",
            "key_formulas": [],
        },
    },
    "quiz_questions": [
        QuizQuestion("teaching_pedagogy", "learning_styles", "What are the 4 VARK learning modalities?", "Visual, Auditory, Reading/Writing, Kinesthetic", ["Visual, Audio, Recall, Knowledge", "Verbal, Active, Reading, Kinetic", "Vision, Attention, Retention, Knowledge"], "VARK: Visual, Auditory, Read/Write, Kinesthetic - most people use a mix."),
        QuizQuestion("teaching_pedagogy", "effective_teaching", "What is the Zone of Proximal Development?", "The gap between what a learner can do alone and what they can do with help", ["The area where learning is impossible", "The comfort zone", "The testing zone"], "Vygotsky's ZPD: optimal learning happens just beyond current ability, with scaffolding."),
        QuizQuestion("teaching_pedagogy", "neurodivergent_teaching", "What is the recommended lesson chunk length for ADHD learners?", "10-15 minutes with breaks or activity changes", ["60 minutes minimum", "30 minutes straight", "5 minutes only"], "ADHD working memory fatigues quickly; short chunks with variety maintain engagement."),
    ],
}

# ---------- PUBLIC SPEAKING (Toastmasters International) ----------
SUBJECTS_D["public_speaking"] = {
    "name": "Public Speaking & Presentation",
    "overview": "The art and science of speaking effectively to an audience. Based on principles from Toastmasters International, Dale Carnegie, and communication research. Covers speech structure, delivery, overcoming fear, persuasion, and professional presentation skills.",
    "topics": {
        "speech_fundamentals": {
            "title": "Speech Fundamentals (Toastmasters Pathways)",
            "content": """TOASTMASTERS INTERNATIONAL: Founded 1924. World's largest public speaking organization. 16,800+ clubs in 143 countries. Pathways education program.

THE 3 PILLARS OF A GREAT SPEECH:
1. CONTENT: What you say. Clear message, supporting evidence, memorable stories.
2. DELIVERY: How you say it. Voice, gestures, eye contact, movement, pauses.
3. CONNECTION: How the audience feels. Empathy, relevance, authenticity.

SPEECH STRUCTURE (Classic 3-part):
- Opening (10%): Hook the audience. Startling fact, question, story, quote, humor.
- Body (80%): 3 main points maximum. Each with evidence/story. Transitions between.
- Closing (10%): Summarize, call to action, memorable final line. Never end with "that's it."

TOASTMASTERS SPEECH PROJECTS (Competent Communicator):
1. Ice Breaker: Introduce yourself (4-6 min)
2. Organize Your Speech: Clear structure, transitions
3. Get to the Point: Specific purpose, focused message
4. How to Say It: Word choice, vivid language
5. Your Body Speaks: Gestures, movement, facial expressions
6. Vocal Variety: Pace, pitch, volume, pauses
7. Research Your Topic: Support with facts and sources
8. Get Comfortable with Visual Aids: Slides, props, demos
9. Persuade with Power: Logic, emotion, credibility (Aristotle's ethos/pathos/logos)
10. Inspire Your Audience: Motivational speaking""",
            "key_formulas": [],
        },
        "delivery_techniques": {
            "title": "Delivery & Performance Techniques",
            "content": """VOICE:
- Volume: Project from diaphragm, not throat. Vary volume for emphasis.
- Pace: Average 130-150 words/min. Slow down for key points. Speed up for excitement.
- Pitch: Vary high and low. Monotone kills engagement.
- PAUSE: The most powerful tool. Pause before key points. Pause after. Let silence work.
- Articulation: Enunciate clearly. Practice tongue twisters.

BODY LANGUAGE:
- Eye contact: 3-5 seconds per person/section. Don't stare or scan.
- Gestures: Natural, purposeful. Open palms = honesty. Pointing = authority.
- Posture: Stand tall, feet shoulder-width. Grounded but not rigid.
- Movement: Purposeful. Move to new position for new point. Don't pace.
- Facial expressions: Match your message. Smile when appropriate.

OVERCOMING NERVOUSNESS:
- Reframe: Nervous energy = excitement energy. Same physiology, different label.
- Prepare: Know your material cold. Practice 7+ times. Record yourself.
- Breathe: Deep diaphragmatic breaths before speaking. 4-7-8 technique.
- Focus on audience: Serve THEM, not yourself. Take attention off your anxiety.
- Power posing: 2 minutes of expansive posture before speaking (Amy Cuddy research).
- Start strong: Memorize your first 30 seconds. Confidence builds from a strong start.

DALE CARNEGIE'S PRINCIPLES: Be genuinely interested in your audience. Talk about their interests. Make them feel important. Use their names.""",
            "key_formulas": [],
        },
        "persuasion_rhetoric": {
            "title": "Persuasion & Rhetoric",
            "content": """ARISTOTLE'S 3 APPEALS:
- Ethos (Credibility): Why should they listen to YOU? Experience, expertise, character, trustworthiness.
- Pathos (Emotion): Stories, vivid imagery, humor, fear, hope, anger. Emotion drives action.
- Logos (Logic): Facts, statistics, expert testimony, logical arguments. Evidence supports claims.

MONROE'S MOTIVATED SEQUENCE (5 steps for persuasive speeches):
1. Attention: Grab interest with hook.
2. Need: Establish the problem. Make audience feel the urgency.
3. Satisfaction: Present your solution.
4. Visualization: Paint a picture of the future WITH and WITHOUT your solution.
5. Action: Tell them exactly what to do next.

STORYTELLING: The most powerful persuasion tool. Structure: Character + Conflict + Resolution + Lesson. Make the audience the hero, not yourself.

RHETORICAL DEVICES: Anaphora (repetition at start: "I have a dream..."), Tricolon (rule of 3), Antithesis (contrast), Metaphor, Rhetorical questions.

HANDLING Q&A: Listen fully. Repeat/rephrase. Answer concisely. Bridge back to your message. "I don't know" is acceptable - offer to follow up.""",
            "key_formulas": [],
        },
    },
    "quiz_questions": [
        QuizQuestion("public_speaking", "speech_fundamentals", "What are Aristotle's three modes of persuasion?", "Ethos (credibility), Pathos (emotion), Logos (logic)", ["Volume, Pitch, Pace", "Opening, Body, Closing", "Attention, Interest, Desire"], "Aristotle identified these 2,300 years ago and they still define persuasive communication."),
        QuizQuestion("public_speaking", "delivery_techniques", "What is the most powerful vocal tool in public speaking?", "The pause", ["Speaking loudly", "Speaking fast", "Using filler words"], "Pauses create anticipation, emphasize points, and give the audience time to process."),
        QuizQuestion("public_speaking", "persuasion_rhetoric", "What are the 5 steps of Monroe's Motivated Sequence?", "Attention, Need, Satisfaction, Visualization, Action", ["Introduction, Body, Conclusion, Q&A, Exit", "Ethos, Pathos, Logos, Kairos, Telos", "Hook, Story, Evidence, Summary, Close"], "Monroe's sequence is the gold standard for persuasive speeches."),
    ],
}

# ---------- INTERVIEWING TECHNIQUES ----------
SUBJECTS_D["interviewing"] = {
    "name": "Interviewing Techniques",
    "overview": "Comprehensive guide to job interviews, behavioral interviews, technical interviews, and informational interviews. From preparation to follow-up.",
    "topics": {
        "interview_preparation": {
            "title": "Interview Preparation",
            "content": """BEFORE THE INTERVIEW:
- Research the company: mission, values, recent news, products, competitors, culture.
- Study the job description: match YOUR skills to THEIR requirements. Prepare specific examples.
- Prepare your stories: Use the STAR method for 8-10 key experiences.
- Practice common questions: Tell me about yourself, strengths/weaknesses, why this company, why should we hire you.
- Prepare questions to ASK: Shows genuine interest. Never say "I have no questions."
  Good: "What does success look like in this role in the first 90 days?"
  Good: "What's the team culture like? How do you collaborate?"
  Good: "What are the biggest challenges facing the team right now?"

LOGISTICS: Arrive 10-15 min early. Bring copies of resume. Know interviewer names. Dress one level above the company norm.

YOUR ELEVATOR PITCH (Tell me about yourself):
- Present: "I'm currently a [role] at [company] where I [key responsibility]."
- Past: "Before that, I [relevant experience that built skills for this role]."
- Future: "I'm excited about this opportunity because [connection to role/company]."
- 60-90 seconds max. Tailored to the specific role.""",
            "key_formulas": [],
        },
        "behavioral_interviews": {
            "title": "Behavioral Interview Techniques",
            "content": """STAR METHOD (for behavioral questions):
- Situation: Set the scene. Where, when, what was the context?
- Task: What was your responsibility? What challenge did you face?
- Action: What specifically did YOU do? (Not "we" - focus on your contribution)
- Result: What was the outcome? Quantify if possible. What did you learn?

COMMON BEHAVIORAL QUESTIONS & HOW TO ANSWER:
- "Tell me about a time you failed." -> Show self-awareness, learning, and growth.
- "Describe a conflict with a coworker." -> Show communication, empathy, resolution skills.
- "When did you go above and beyond?" -> Show initiative, dedication, impact.
- "How do you handle pressure/deadlines?" -> Show organization, prioritization, calm under stress.
- "Give an example of leadership." -> Show influence, vision, team development.

TIPS:
- Be specific, not general. Names, numbers, outcomes.
- "I" not "we" - own your contributions.
- Keep answers 2-3 minutes. Don't ramble.
- It's OK to pause and think. "That's a great question, let me think about the best example."
- If you don't have a perfect example, say what you WOULD do and share a related story.

WEAKNESSES QUESTION: Choose a real but non-critical weakness. Show what you're doing about it. "I tend to take on too much - I've been working on delegating and using project management tools to track capacity." """,
            "key_formulas": [],
        },
        "interview_types": {
            "title": "Interview Types & Special Situations",
            "content": """PHONE/VIDEO SCREENING: Usually 20-30 min with HR/recruiter. Focus on fit, salary expectations, availability. Have resume and notes visible. Smile - it changes your voice tone.

PANEL INTERVIEW: Multiple interviewers. Address each person. Make eye contact with questioner AND others. Note names and roles.

TECHNICAL INTERVIEW: Problem-solving demonstration. Talk through your thinking aloud. Ask clarifying questions. It's about process, not just the answer. Practice on platforms like LeetCode, HackerRank.

CASE INTERVIEW (consulting): Structure your answer. State assumptions. Use frameworks (SWOT, Porter's 5 Forces). Think aloud. Check math.

INFORMATIONAL INTERVIEW: NOT a job interview. Learning about a field/company. Ask about their path, industry trends, advice. Always follow up with thanks.

GROUP INTERVIEW: Multiple candidates together. Be collaborative, not competitive. Show leadership AND teamwork. Don't dominate or disappear.

AFTER THE INTERVIEW:
- Send thank-you email within 24 hours. Reference something specific discussed.
- Reiterate your interest and fit.
- If you don't hear back in the stated timeline, one polite follow-up is appropriate.
- Reflect: What went well? What could improve? Write notes while fresh.

SALARY NEGOTIATION: Research market range (Glassdoor, Levels.fyi, LinkedIn). Let them state first if possible. Negotiate based on value, not need. "Based on my experience and market data, I was expecting X-Y range." """,
            "key_formulas": [],
        },
    },
    "quiz_questions": [
        QuizQuestion("interviewing", "behavioral_interviews", "What does STAR stand for in behavioral interviews?", "Situation, Task, Action, Result", ["Skills, Training, Application, Review", "Start, Think, Act, Reflect", "Story, Theme, Argument, Resolution"], "STAR gives structure to behavioral answers: context, your role, what you did, the outcome."),
        QuizQuestion("interviewing", "interview_preparation", "When answering 'Tell me about yourself,' what structure works best?", "Present role, Past experience, Future goals (connected to this role)", ["Life story from childhood", "List of skills", "Salary expectations"], "Present-Past-Future keeps it relevant, concise, and forward-looking."),
    ],
}
