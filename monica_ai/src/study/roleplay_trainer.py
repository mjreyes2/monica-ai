"""
Monica Roleplay & Communication Skills Trainer
Helps users practice communication techniques through interactive roleplay scenarios.
Includes assertive communication, DEARMAN, conflict resolution, and more.

Author: Monica AI
Date: December 2025
"""

import random
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class CommunicationStyle(Enum):
    """Communication styles for training."""
    ASSERTIVE = "assertive"
    PASSIVE = "passive"
    AGGRESSIVE = "aggressive"
    PASSIVE_AGGRESSIVE = "passive_aggressive"


class ScenarioCategory(Enum):
    """Categories of roleplay scenarios."""
    WORKPLACE = "workplace"
    PERSONAL = "personal"
    CUSTOMER_SERVICE = "customer_service"
    NEGOTIATION = "negotiation"
    CONFLICT_RESOLUTION = "conflict_resolution"
    INTERVIEW = "interview"
    SALES = "sales"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"


@dataclass
class RoleplayScenario:
    """A roleplay scenario for practice."""
    id: str
    title: str
    category: ScenarioCategory
    description: str
    your_role: str
    monica_role: str
    objective: str
    techniques: List[str]  # Communication techniques to practice
    difficulty: str  # easy, medium, hard
    opening_line: str  # Monica's opening line
    tips: List[str] = field(default_factory=list)


# DEARMAN Technique Components
DEARMAN_COMPONENTS = {
    'D': {
        'name': 'Describe',
        'description': 'Describe the situation using facts only. Stick to what happened without judgments.',
        'example': '"When I asked for help with the project yesterday, I didn\'t receive a response."'
    },
    'E': {
        'name': 'Express',
        'description': 'Express your feelings about the situation using "I" statements.',
        'example': '"I felt frustrated and overwhelmed when I had to complete it alone."'
    },
    'A': {
        'name': 'Assert',
        'description': 'Assert what you want or need clearly and specifically.',
        'example': '"I would like us to set up a system for responding to help requests within 24 hours."'
    },
    'R': {
        'name': 'Reinforce',
        'description': 'Reinforce the benefits of getting what you want - reward the person.',
        'example': '"This would help our team work more efficiently and reduce stress for everyone."'
    },
    'M': {
        'name': 'Mindful',
        'description': 'Stay mindful and focused on your goal. Don\'t get distracted.',
        'example': 'Keep returning to your main point if the conversation goes off track.'
    },
    'A2': {
        'name': 'Appear Confident',
        'description': 'Use confident body language and tone, even if you don\'t feel it.',
        'example': 'Maintain eye contact, speak clearly, stand/sit up straight.'
    },
    'N': {
        'name': 'Negotiate',
        'description': 'Be willing to negotiate and find a compromise if needed.',
        'example': '"If daily check-ins don\'t work, could we try every other day?"'
    }
}

# Assertive Communication Principles
ASSERTIVE_PRINCIPLES = {
    'i_statements': {
        'name': 'Use "I" Statements',
        'description': 'Express your feelings without blaming others.',
        'wrong': '"You never listen to me!"',
        'right': '"I feel unheard when I\'m interrupted."'
    },
    'specific': {
        'name': 'Be Specific',
        'description': 'State exactly what you want or need.',
        'wrong': '"I need you to be better."',
        'right': '"I need you to arrive by 9 AM for our meetings."'
    },
    'respect': {
        'name': 'Maintain Respect',
        'description': 'Respect yourself and others throughout.',
        'wrong': '"That\'s a stupid idea."',
        'right': '"I see it differently. Here\'s my perspective..."'
    },
    'boundaries': {
        'name': 'Set Clear Boundaries',
        'description': 'Clearly state what is and isn\'t acceptable.',
        'wrong': '"I guess I could maybe try to do that..."',
        'right': '"I\'m not able to take on additional projects this week."'
    },
    'broken_record': {
        'name': 'Broken Record Technique',
        'description': 'Calmly repeat your point without getting defensive.',
        'example': 'Keep restating your position calmly when met with resistance.'
    },
    'fogging': {
        'name': 'Fogging',
        'description': 'Agree with any truth in criticism without getting defensive.',
        'example': '"You\'re right, I could have handled that better."'
    }
}

# Roleplay Scenarios
SCENARIOS = [
    # Workplace Scenarios
    RoleplayScenario(
        id="work_1",
        title="Asking for a Raise",
        category=ScenarioCategory.WORKPLACE,
        description="You've been at your job for 2 years and believe you deserve a raise based on your performance.",
        your_role="Employee requesting a raise",
        monica_role="Your manager who is budget-conscious but fair",
        objective="Successfully negotiate a raise or clear path to one",
        techniques=["DEARMAN", "assertive_communication"],
        difficulty="medium",
        opening_line="Hi, you wanted to see me? I have about 15 minutes before my next meeting.",
        tips=["Come prepared with specific accomplishments", "Know your market value", "Be ready to negotiate"]
    ),
    RoleplayScenario(
        id="work_2",
        title="Declining Extra Work",
        category=ScenarioCategory.WORKPLACE,
        description="Your coworker keeps asking you to help with their tasks, affecting your own work.",
        your_role="Employee who needs to set boundaries",
        monica_role="Coworker who frequently asks for help",
        objective="Politely but firmly decline while maintaining the relationship",
        techniques=["assertive_communication", "boundary_setting"],
        difficulty="easy",
        opening_line="Hey! I'm so swamped with this project. Could you help me out again? It'll only take an hour or two.",
        tips=["Use 'I' statements", "Offer alternatives if possible", "Stay firm but kind"]
    ),
    RoleplayScenario(
        id="work_3",
        title="Addressing a Difficult Coworker",
        category=ScenarioCategory.CONFLICT_RESOLUTION,
        description="A coworker has been taking credit for your ideas in meetings.",
        your_role="Employee addressing the issue directly",
        monica_role="Coworker who has been taking credit",
        objective="Address the behavior and establish better collaboration",
        techniques=["DEARMAN", "conflict_resolution"],
        difficulty="hard",
        opening_line="Oh hey, what's up? Did you need something?",
        tips=["Focus on specific incidents", "Avoid accusations", "Propose solutions"]
    ),
    
    # Personal Scenarios
    RoleplayScenario(
        id="personal_1",
        title="Setting Boundaries with Family",
        category=ScenarioCategory.PERSONAL,
        description="A family member keeps giving unsolicited advice about your life choices.",
        your_role="Adult child setting boundaries",
        monica_role="Well-meaning but overbearing parent/relative",
        objective="Establish boundaries while maintaining the relationship",
        techniques=["assertive_communication", "boundary_setting"],
        difficulty="medium",
        opening_line="I've been thinking about your situation, and I really think you should reconsider your career choice. Have you thought about going back to school?",
        tips=["Acknowledge their concern", "Be clear about your boundaries", "Redirect the conversation"]
    ),
    RoleplayScenario(
        id="personal_2",
        title="Expressing Needs in a Relationship",
        category=ScenarioCategory.PERSONAL,
        description="You need more quality time with your partner who has been working late.",
        your_role="Partner expressing emotional needs",
        monica_role="Busy partner who hasn't realized the impact",
        objective="Express your needs without blame and find a solution together",
        techniques=["DEARMAN", "i_statements"],
        difficulty="easy",
        opening_line="Hey, I just got home. What a long day! What's for dinner?",
        tips=["Choose the right time", "Focus on feelings, not accusations", "Propose specific solutions"]
    ),
    
    # Customer Service
    RoleplayScenario(
        id="customer_1",
        title="Handling a Complaint",
        category=ScenarioCategory.CUSTOMER_SERVICE,
        description="You're a customer service rep dealing with an upset customer.",
        your_role="Customer service representative",
        monica_role="Frustrated customer with a legitimate complaint",
        objective="De-escalate the situation and find a resolution",
        techniques=["active_listening", "empathy", "problem_solving"],
        difficulty="medium",
        opening_line="I've been on hold for 45 minutes! This is ridiculous! I want to speak to a manager right now!",
        tips=["Acknowledge their frustration", "Don't take it personally", "Focus on solutions"]
    ),
    
    # Interview
    RoleplayScenario(
        id="interview_1",
        title="Job Interview - Weakness Question",
        category=ScenarioCategory.INTERVIEW,
        description="You're in a job interview and asked about your greatest weakness.",
        your_role="Job candidate",
        monica_role="Interviewer",
        objective="Answer honestly while showing self-awareness and growth",
        techniques=["assertive_communication", "self_presentation"],
        difficulty="easy",
        opening_line="So, tell me about your greatest weakness.",
        tips=["Be genuine", "Show how you're working on it", "Don't give a fake weakness"]
    ),
    RoleplayScenario(
        id="interview_2",
        title="Salary Negotiation",
        category=ScenarioCategory.NEGOTIATION,
        description="You've received a job offer but the salary is lower than expected.",
        your_role="Job candidate negotiating salary",
        monica_role="HR representative",
        objective="Negotiate a better compensation package",
        techniques=["DEARMAN", "negotiation"],
        difficulty="hard",
        opening_line="We're pleased to offer you the position at $55,000 per year. When can you start?",
        tips=["Know your worth", "Consider total compensation", "Be prepared to walk away"]
    ),
    
    # Conflict Resolution
    RoleplayScenario(
        id="conflict_1",
        title="Roommate Conflict",
        category=ScenarioCategory.CONFLICT_RESOLUTION,
        description="Your roommate hasn't been doing their share of chores.",
        your_role="Roommate addressing the issue",
        monica_role="Roommate who's been slacking on chores",
        objective="Create a fair chore arrangement",
        techniques=["DEARMAN", "conflict_resolution"],
        difficulty="easy",
        opening_line="Oh hey, what's up? I was just about to watch a show.",
        tips=["Be specific about the issue", "Propose a solution", "Be willing to compromise"]
    ),
]


class RoleplayTrainer:
    """
    Interactive roleplay trainer for communication skills.
    """
    
    def __init__(self, ai_manager=None, tts_manager=None):
        self.ai_manager = ai_manager
        self.tts_manager = tts_manager
        
        # Current session state
        self.current_scenario: Optional[RoleplayScenario] = None
        self.conversation_history: List[Dict[str, str]] = []
        self.session_feedback: List[str] = []
        self.techniques_used: List[str] = []
        
        # Scenarios
        self.scenarios = {s.id: s for s in SCENARIOS}
        
        print("[ROLEPLAY] Roleplay Trainer initialized")
    
    def get_scenarios(self, category: ScenarioCategory = None) -> List[RoleplayScenario]:
        """Get available scenarios, optionally filtered by category."""
        if category:
            return [s for s in SCENARIOS if s.category == category]
        return SCENARIOS
    
    def get_categories(self) -> List[str]:
        """Get available scenario categories."""
        return [c.value for c in ScenarioCategory]
    
    def start_scenario(self, scenario_id: str) -> str:
        """Start a roleplay scenario."""
        if scenario_id not in self.scenarios:
            return f"Scenario '{scenario_id}' not found."
        
        self.current_scenario = self.scenarios[scenario_id]
        self.conversation_history = []
        self.session_feedback = []
        self.techniques_used = []
        
        # Build introduction
        intro = f"""[*] **Roleplay: {self.current_scenario.title}**

[*] **Scenario:** {self.current_scenario.description}

[*] **Your Role:** {self.current_scenario.your_role}
[*] **My Role:** {self.current_scenario.monica_role}

[Target] **Objective:** {self.current_scenario.objective}

[*] **Techniques to Practice:** {', '.join(self.current_scenario.techniques)}

[Idea] **Tips:**
"""
        for tip in self.current_scenario.tips:
            intro += f"• {tip}\n"
        
        intro += f"\n---\n\n**Monica (as {self.current_scenario.monica_role}):**\n\"{self.current_scenario.opening_line}\"\n\n*Your turn to respond...*"
        
        # Add Monica's opening to history
        self.conversation_history.append({
            'role': 'monica',
            'content': self.current_scenario.opening_line
        })
        
        return intro
    
    def respond(self, user_input: str) -> str:
        """Process user's response and continue the roleplay."""
        if not self.current_scenario:
            return "No scenario active. Start a scenario first!"
        
        # Add user input to history
        self.conversation_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Analyze user's communication
        feedback = self._analyze_communication(user_input)
        
        # Generate Monica's response using AI
        monica_response = self._generate_response(user_input)
        
        # Add Monica's response to history
        self.conversation_history.append({
            'role': 'monica',
            'content': monica_response
        })
        
        # Format output
        result = f"**Monica:** \"{monica_response}\"\n"
        
        if feedback:
            result += f"\n[Idea] *Feedback: {feedback}*"
        
        return result
    
    def _analyze_communication(self, text: str) -> str:
        """Analyze the user's communication style and provide feedback."""
        text_lower = text.lower()
        feedback_parts = []
        
        # Check for "I" statements
        if ' i feel ' in text_lower or ' i think ' in text_lower or ' i need ' in text_lower:
            feedback_parts.append("Good use of 'I' statements!")
            self.techniques_used.append("i_statements")
        
        # Check for aggressive language
        aggressive_words = ['you always', 'you never', 'you should', "that's stupid", "you're wrong"]
        if any(word in text_lower for word in aggressive_words):
            feedback_parts.append("Try to avoid accusatory language like 'you always/never'.")
        
        # Check for passive language
        passive_phrases = ['i guess', 'maybe', 'sort of', 'kind of', "i don't know", 'whatever']
        passive_count = sum(1 for phrase in passive_phrases if phrase in text_lower)
        if passive_count >= 2:
            feedback_parts.append("Your response seems a bit passive. Try being more direct.")
        
        # Check for assertive elements
        if 'i would like' in text_lower or 'i need' in text_lower or 'i expect' in text_lower:
            feedback_parts.append("Great assertive request!")
            self.techniques_used.append("assertive_request")
        
        # Check for DEARMAN elements
        if 'because' in text_lower or 'when' in text_lower:
            feedback_parts.append("Good job describing the situation.")
            self.techniques_used.append("describe")
        
        return ' '.join(feedback_parts) if feedback_parts else ""
    
    def _generate_response(self, user_input: str) -> str:
        """Generate Monica's response based on the scenario and conversation."""
        if not self.ai_manager:
            return self._get_fallback_response()
        
        # Build conversation context
        conv_text = ""
        for msg in self.conversation_history[-6:]:  # Last 6 messages
            role = "User" if msg['role'] == 'user' else "Monica"
            conv_text += f"{role}: {msg['content']}\n"
        
        prompt = f"""You are roleplaying as: {self.current_scenario.monica_role}

Scenario: {self.current_scenario.description}

The user is practicing: {', '.join(self.current_scenario.techniques)}

Conversation so far:
{conv_text}

Respond in character. Be realistic - don't make it too easy or too hard.
If the user is using good communication techniques, gradually become more cooperative.
If they're being aggressive or passive, respond naturally to that style.
Keep your response to 1-3 sentences. Stay in character.

Your response as {self.current_scenario.monica_role}:"""

        try:
            response = self.ai_manager.get_response(prompt)
            return response.strip().strip('"')
        except:
            return self._get_fallback_response()
    
    def _get_fallback_response(self) -> str:
        """Get a fallback response when AI is not available."""
        fallbacks = [
            "I hear what you're saying. Can you tell me more?",
            "That's an interesting point. What do you suggest we do?",
            "I understand your perspective. Let me think about that.",
            "Hmm, I hadn't considered that. Go on...",
            "I see. And how does that make you feel?",
        ]
        return random.choice(fallbacks)
    
    def end_scenario(self) -> str:
        """End the current scenario and provide summary feedback."""
        if not self.current_scenario:
            return "No scenario was active."
        
        # Generate summary
        summary = f"""[*] **Roleplay Complete: {self.current_scenario.title}**

[Stats] **Session Summary:**
• Exchanges: {len([m for m in self.conversation_history if m['role'] == 'user'])}
• Techniques practiced: {', '.join(set(self.techniques_used)) if self.techniques_used else 'None detected'}

"""
        
        # AI-generated feedback if available
        if self.ai_manager and len(self.conversation_history) > 2:
            feedback = self._generate_final_feedback()
            summary += f"[Note] **Feedback:**\n{feedback}\n"
        
        summary += "\n[*] Keep practicing! Communication skills improve with repetition."
        
        self.current_scenario = None
        return summary
    
    def _generate_final_feedback(self) -> str:
        """Generate final feedback using AI."""
        conv_text = "\n".join([f"{'User' if m['role'] == 'user' else 'Monica'}: {m['content']}" 
                              for m in self.conversation_history])
        
        prompt = f"""Analyze this roleplay conversation where the user was practicing {', '.join(self.current_scenario.techniques)}.

Scenario: {self.current_scenario.description}
Objective: {self.current_scenario.objective}

Conversation:
{conv_text}

Provide brief, constructive feedback (3-4 sentences) on:
1. What they did well
2. One area for improvement
3. A specific tip for next time

Be encouraging but honest."""

        try:
            return self.ai_manager.get_response(prompt)
        except:
            return "Great effort! Keep practicing these techniques in real situations."
    
    def get_technique_info(self, technique: str) -> str:
        """Get information about a communication technique."""
        technique_lower = technique.lower()
        
        if 'dearman' in technique_lower:
            result = "[*] **DEARMAN Technique**\n\nAn interpersonal effectiveness skill from DBT:\n\n"
            for key, info in DEARMAN_COMPONENTS.items():
                result += f"**{key} - {info['name']}:** {info['description']}\n"
                result += f"   *Example: {info['example']}*\n\n"
            return result
        
        elif 'assertive' in technique_lower:
            result = "[*] **Assertive Communication**\n\nKey principles:\n\n"
            for key, info in ASSERTIVE_PRINCIPLES.items():
                result += f"**{info['name']}:** {info['description']}\n"
                if 'wrong' in info:
                    result += f"   [ERROR] Instead of: {info['wrong']}\n"
                    result += f"   [OK] Try: {info['right']}\n"
                elif 'example' in info:
                    result += f"   *Example: {info['example']}*\n"
                result += "\n"
            return result
        
        return f"Technique '{technique}' not found. Available: DEARMAN, Assertive Communication"
    
    def quick_practice(self, technique: str) -> str:
        """Start a quick practice session for a specific technique."""
        technique_lower = technique.lower()
        
        # Find scenarios that use this technique
        matching = [s for s in SCENARIOS if any(technique_lower in t.lower() for t in s.techniques)]
        
        if not matching:
            return f"No scenarios found for '{technique}'. Try 'DEARMAN' or 'assertive'."
        
        # Pick a random matching scenario
        scenario = random.choice(matching)
        return self.start_scenario(scenario.id)


# Singleton instance
_trainer = None

def get_roleplay_trainer(ai_manager=None, tts_manager=None) -> RoleplayTrainer:
    """Get or create the roleplay trainer singleton."""
    global _trainer
    if _trainer is None:
        _trainer = RoleplayTrainer(ai_manager, tts_manager)
    elif ai_manager:
        _trainer.ai_manager = ai_manager
    elif tts_manager:
        _trainer.tts_manager = tts_manager
    return _trainer


# Test
if __name__ == "__main__":
    print("Roleplay Trainer Test")
    trainer = get_roleplay_trainer()
    
    print("\nCategories:", trainer.get_categories())
    print("\nScenarios:", [s.title for s in trainer.get_scenarios()])
    
    print("\n" + trainer.get_technique_info("dearman"))
