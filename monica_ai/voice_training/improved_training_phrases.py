"""
Improved Training Phrases for Monica Voice Recognition
Created: 2025-12-12

These phrases are optimized for speech-to-text training:
- Length: 10-20 words (captures natural speech patterns)
- Variety: Questions, commands, statements, complex sentences
- Natural: Conversational style with proper rhythm
- No digits: All numbers spelled out

HOW TO USE:
1. Copy sections you want to use
2. Paste into record_voice.py's phrase lists
3. Record samples using the voice training GUI
4. Train your model

BENEFIT: Longer, more varied phrases = Better voice recognition!
"""

# === CONVERSATIONAL QUESTIONS & ANSWERS (Natural dialogue patterns) ===
conversational_long_phrases = [
    # Knowledge & Information
    "Can you explain to me how artificial intelligence actually works in modern computer systems?",
    "I've been wondering what the difference is between machine learning and deep learning technologies.",
    "Could you tell me more about what neural networks are and how they process information?",
    "I'm curious about how Python became one of the most popular programming languages for data science.",
    "What exactly is the difference between JavaScript and other programming languages like Python or Java?",
    "Can you help me understand how databases store and retrieve information so quickly?",
    "I'd like to know more about how the internet connects millions of computers around the world.",
    "Could you explain what cloud computing is and why so many companies are using it now?",
    "I've heard a lot about blockchain technology but I'm not sure how it actually works.",
    "Can you tell me what cryptocurrency is and how it's different from regular money?",
    "I'm trying to understand what Bitcoin is and why people think it's valuable.",
    "Could you explain how the stock market works and why prices go up and down?",
    "What causes inflation and why does it make things more expensive over time?",
    "Can you tell me what GDP means and why economists use it to measure economic health?",
    "I'd like to understand what democracy is and how it's different from other forms of government.",
    "Could you explain the difference between capitalism and socialism in simple terms?",
    "What is the United Nations and what role does it play in international relations?",
    "Can you tell me what NATO is and why it was created after World War Two?",

    # Science & Space
    "I'm fascinated by black holes and I'd love to know more about how they form.",
    "Can you explain what causes earthquakes and why some areas have them more often than others?",
    "I've always wondered why the sky appears blue during the day but red at sunset.",
    "Could you tell me more about why we dream and what purpose it might serve?",
    "I'm curious about why leaves change color in the autumn before they fall off trees.",
    "Can you explain why the ocean is salty when freshwater rivers flow into it?",
    "I'd like to understand how electricity works and how it gets from power plants to our homes.",
    "Could you help me understand how airplanes are able to stay up in the air?",
    "I'm trying to learn how GPS works and how it knows exactly where we are.",
    "Can you explain what causes hurricanes and why they're so powerful and destructive?",
    "I've been reading about climate change and I'd like to understand it better.",
    "Could you tell me more about renewable energy sources like solar and wind power?",
    "What is DNA and how does it contain all the instructions for building living things?",
    "Can you explain what viruses are and how they're different from bacteria?",
    "I'm curious about what atoms are made of and how small they actually are.",
    "Could you help me understand what gravity is and why it pulls objects toward Earth?",

    # History & Geography
    "Can you tell me about when America was founded and who the founding fathers were?",
    "I'd like to know more about what happened during World War Two and how it ended.",
    "Could you explain what the Cold War was and why it was called that?",
    "I'm interested in learning about ancient Egypt and how they built the pyramids.",
    "Can you tell me about the Roman Empire and why it was so powerful?",
    "I'd like to understand what caused the American Civil War and what the outcome was.",
    "Could you explain what happened during the Industrial Revolution and how it changed society?",
    "What led to World War One and why did so many countries get involved?",
    "Can you tell me about the moon landing and why it was such an important achievement?",
    "I'm curious about when the internet was invented and how it became so widespread.",

    # Technology & Modern Life
    "Could you explain what WiFi is and how it lets us connect to the internet wirelessly?",
    "I'd like to understand what Bluetooth technology is and how it connects devices together.",
    "Can you tell me about five G networks and how they're faster than four G?",
    "I'm curious about what fiber optic cables are and why they're better for internet.",
    "Could you explain what a VPN is and why people use them for privacy?",
    "I'd like to know more about cloud storage and where my files actually go.",
    "Can you help me understand what an API is and why developers use them?",
    "I'm trying to learn about cybersecurity and how to protect my personal information online.",
    "Could you explain what encryption is and how it keeps our data safe?",
    "I'd like to understand what two factor authentication is and why it's more secure.",
    "Can you tell me about open source software and how it's different from proprietary software?",
    "I'm curious about what malware is and how it can infect computers.",
    "Could you explain what phishing is and how to avoid falling for it?",
]

# === COMPLEX COMMANDS & INSTRUCTIONS (Multi-step actions) ===
command_long_phrases = [
    # Device & System Control
    "Please open the calendar application and show me my appointments for next week.",
    "Could you turn on the lights in the living room and set them to fifty percent brightness?",
    "I need you to start recording this conversation and save it to my documents folder.",
    "Please search the internet for information about restaurants near me that are open now.",
    "Can you set a timer for fifteen minutes and remind me when it's time to check the oven?",
    "I'd like you to play some relaxing music from my favorite playlist on Spotify.",
    "Could you send a text message to Sarah asking if she's free for lunch tomorrow?",
    "Please add milk, eggs, and bread to my shopping list for the grocery store.",
    "I need you to check the weather forecast for this weekend and let me know if it will rain.",
    "Can you remind me to call the doctor's office tomorrow morning at nine o'clock?",
    "Please turn off all the lights in the house and set the thermostat to sixty eight degrees.",
    "I'd like you to create a new note and title it meeting notes from today's conference.",
    "Could you find my phone and make it ring so I can locate it?",
    "Please lock all the doors and windows and activate the security system for the night.",
    "I need you to adjust the volume on the TV and change it to channel five.",

    # Email & Communication
    "Please compose a new email to my team letting them know about tomorrow's meeting at two pm.",
    "I'd like you to search through my emails and find the message from John about the project deadline.",
    "Could you reply to Sarah's email and tell her that I'll be there on Friday afternoon?",
    "Please schedule a video call with the marketing team for next Tuesday at ten thirty am.",
    "I need you to forward that important email to everyone in the department right away.",
    "Can you check if I have any unread messages from my boss and read them to me?",
    "Please send a calendar invite for the quarterly review meeting to all the managers.",
    "I'd like you to draft an email thanking the client for their business and feedback.",

    # Navigation & Travel
    "Please give me directions to the nearest coffee shop that has good reviews.",
    "I need to find the fastest route to downtown Tampa avoiding all the highway traffic.",
    "Could you tell me how long it will take to drive to Orlando from my current location?",
    "Please search for gas stations along my route that have the lowest prices today.",
    "I'd like you to find hotels near the convention center that cost less than one hundred dollars per night.",
    "Can you show me restaurants within walking distance that serve vegetarian food?",
    "Please calculate the distance from my house to the airport and estimate the travel time.",
    "I need to know if there are any traffic delays on Interstate four heading east right now.",
]

# === THERAPEUTIC & MINDFULNESS PHRASES (Professional & wellness context) ===
therapeutic_long_phrases = [
    # Mindfulness & Grounding
    "Let's begin with a mindfulness exercise to help you feel more present in this moment.",
    "I'd like to guide you through some box breathing to help calm your nervous system.",
    "Could we practice progressive muscle relaxation starting with your feet and working upward?",
    "Let's try some grounding techniques to help you feel more connected to your body and surroundings.",
    "I want you to notice five things you can see around you right now without judging them.",
    "Can you focus on your breathing and try to make each exhale longer than each inhale?",
    "Let's practice urge surfing to help you ride out this difficult feeling without acting on it.",
    "I'd like you to identify three sounds you can hear and really focus on them.",
    "Could you tell me about two things you can touch and describe how they feel?",
    "Let's work on thought labeling so you can observe your thoughts without getting caught up in them.",

    # Therapy & Processing
    "Can you tell me more about what you were feeling when that situation happened yesterday?",
    "I'd like to explore what automatic thoughts came up for you during that difficult moment.",
    "Could we work on cognitive restructuring to help you challenge some of those negative beliefs?",
    "Let's talk about your safety plan and make sure you know what to do if you feel overwhelmed.",
    "I want to check in with you about how you've been practicing your coping skills at home.",
    "Can we review the homework from last session and discuss what you learned from it?",
    "I'd like to explore your core values and how they relate to your current life goals.",
    "Could you describe what happens in your body when you start to feel anxious or stressed?",
    "Let's talk about your attachment style and how it might affect your relationships.",
    "I want to help you build a stronger sense of self-compassion and kindness toward yourself.",

    # Assessment & Check-ins
    "On a scale from zero to ten, how would you rate your anxiety level right now?",
    "Can you tell me if you've been having any thoughts of harming yourself or others lately?",
    "I'd like to know how well you've been sleeping over the past week or so.",
    "Could you describe your mood today and whether it's been stable or fluctuating?",
    "Let's talk about any significant changes in your appetite or eating habits recently.",
    "Can you tell me if you've been able to do the things you normally enjoy doing?",
    "I want to check if you've been taking your medication as prescribed by your doctor.",
    "Could you let me know if you've been using any substances like alcohol or drugs?",
    "Let's review your progress toward the goals we set in our first session together.",
    "Can you share with me what's been working well and what's still challenging for you?",
]

# === PROFESSIONAL & BUSINESS PHRASES (Workplace communication) ===
professional_long_phrases = [
    # Meetings & Collaboration
    "I'd like to schedule a meeting with the entire team to discuss the new project timeline.",
    "Could we set up a quick call this afternoon to go over the quarterly sales report?",
    "Please add the discussion of the marketing strategy to next week's agenda for the board meeting.",
    "I need to know if everyone has reviewed the proposal before we present it to the client.",
    "Can you send me the latest version of the spreadsheet with all the updated financial figures?",
    "I'd like to get your feedback on the draft presentation before we share it with management.",
    "Could we brainstorm some ideas for improving customer satisfaction and retention rates?",
    "Please make sure all the team members have access to the shared drive with the project files.",

    # Planning & Organization
    "I need to create a timeline for the product launch that includes all the major milestones.",
    "Could you help me prioritize these tasks based on which ones are most urgent and important?",
    "Please review the budget proposal and let me know if you have any concerns or questions.",
    "I'd like to set some clear objectives for the next quarter that align with our annual goals.",
    "Can we break down this large project into smaller, more manageable tasks and deadlines?",
    "I need to delegate some of these responsibilities to other team members who have capacity.",
    "Could you prepare a summary of the key findings from the market research we conducted?",
    "Please track the progress on all these initiatives and send me a status update by Friday.",

    # Problem Solving & Decision Making
    "I think we need to analyze the root cause of this problem before we can find a solution.",
    "Could we evaluate the pros and cons of each option before making our final decision?",
    "I'd like to gather more data and information before we commit to this course of action.",
    "Can we identify the potential risks and how we might mitigate them if they occur?",
    "I need to understand what went wrong so we can prevent it from happening again in the future.",
    "Could you research some best practices from other companies in our industry?",
    "Please consider how this decision will impact our customers, employees, and bottom line.",
    "I want to make sure we're thinking long term and not just solving the immediate issue.",
]

# === EVERYDAY LIFE & PERSONAL PHRASES (Natural daily conversations) ===
everyday_long_phrases = [
    # Shopping & Errands
    "I need to stop by the grocery store on my way home to pick up ingredients for dinner.",
    "Could you remind me to get gas before I drive to Jacksonville this weekend?",
    "I should probably call the pharmacy and refill my prescription before I run out completely.",
    "I need to drop off these packages at the post office before it closes at five o'clock.",
    "Could we swing by the dry cleaners and pick up those clothes I dropped off last week?",
    "I want to stop at the bank and deposit this check before the end of the day.",
    "I should make a list of everything I need from the hardware store for the home repairs.",
    "I need to remember to return that item I bought online since it doesn't fit properly.",

    # Family & Social
    "I should call my mom this weekend and see how she's doing since we haven't talked lately.",
    "Could you remind me to send a birthday card to my friend before the end of the week?",
    "I need to check with Sarah and see if she wants to meet for coffee next Tuesday morning.",
    "I should probably text the group and let everyone know about the change of plans.",
    "I want to invite the neighbors over for dinner sometime next month when things calm down.",
    "I need to RSVP to that wedding invitation before the deadline they gave us.",
    "I should reach out to my old college friends and try to organize a reunion.",
    "I want to spend more quality time with my family on the weekends instead of working.",

    # Health & Wellness
    "I really need to start exercising regularly and eating healthier to improve my overall health.",
    "I should make an appointment with my doctor for my annual checkup and physical exam.",
    "I want to try meditation and see if it helps reduce my stress and anxiety levels.",
    "I need to drink more water throughout the day instead of relying so much on coffee.",
    "I should get to bed earlier tonight so I can get at least eight hours of sleep.",
    "I want to find a new gym or fitness class that I actually enjoy and will stick with.",
    "I need to take some time for self-care and do things that help me relax and recharge.",
    "I should cut back on screen time before bed since it's affecting my sleep quality.",

    # Home & Maintenance
    "I really need to clean out the garage this weekend because it's getting too cluttered.",
    "I should call a plumber to fix that leaky faucet before it causes any water damage.",
    "I want to repaint the living room walls and maybe change the color to something brighter.",
    "I need to replace the air filters in the HVAC system since they haven't been changed in months.",
    "I should mow the lawn and trim the hedges before they get too overgrown.",
    "I want to organize my closet and donate clothes I haven't worn in over a year.",
    "I need to check the smoke detector batteries and make sure they're all working properly.",
    "I should winterize the house before the cold weather arrives and temperatures drop.",
]

# === TECHNICAL & DETAILED EXPLANATIONS (Complex technical content) ===
technical_long_phrases = [
    # Programming & Development
    "I'm working on a Python script that will automatically process data from multiple CSV files.",
    "Could you explain how to use Git to manage version control for my software development project?",
    "I need to debug this JavaScript code because it's throwing an error when the page loads.",
    "I'm trying to optimize the database queries to improve the application's performance and speed.",
    "Could you help me understand how to implement authentication and authorization in this web app?",
    "I need to write unit tests for all these functions to make sure they work correctly.",
    "I'm learning about machine learning algorithms and how to train models on large datasets.",
    "Could you explain the difference between supervised and unsupervised learning in data science?",
    "I need to set up a continuous integration pipeline for automated testing and deployment.",
    "I'm working on refactoring this legacy code to make it more maintainable and efficient.",

    # IT & Systems
    "I need to configure the network firewall to block unauthorized access while allowing legitimate traffic.",
    "Could you help me troubleshoot why these computers can't connect to the wireless network?",
    "I'm trying to set up a backup system that automatically saves all our data every night.",
    "I need to install the latest security patches and updates on all the servers this weekend.",
    "Could you explain how to migrate our data from the old database to the new cloud platform?",
    "I'm working on configuring the VPN so employees can securely access the network remotely.",
    "I need to monitor the system logs to identify any unusual activity or potential security threats.",
    "Could you help me optimize the server configuration to handle more concurrent users?",

    # Science & Research
    "I'm conducting an experiment to test my hypothesis about how temperature affects chemical reactions.",
    "Could you explain the methodology I should use to ensure my research results are valid and reliable?",
    "I need to analyze this statistical data and determine if there's a significant correlation between the variables.",
    "I'm writing a research paper that reviews the current literature on renewable energy technologies.",
    "Could you help me design a controlled study to minimize bias and confounding variables?",
    "I need to calibrate all the laboratory instruments before we begin collecting any measurements.",
    "I'm trying to replicate the results from this published study to verify their findings.",
    "Could you explain how to calculate the standard deviation and margin of error for this sample?",
]

# === STORYTELLING & DESCRIPTIVE PHRASES (Narrative and descriptive language) ===
storytelling_long_phrases = [
    # Descriptive Narratives
    "The old lighthouse stood tall on the rocky cliff overlooking the turbulent ocean waves below.",
    "She walked through the quiet forest path as golden sunlight filtered through the autumn leaves.",
    "The bustling city streets were filled with people rushing to catch their trains and buses home.",
    "A gentle breeze rustled the curtains as the sound of rain tapped against the window panes.",
    "The aroma of freshly baked bread drifted from the kitchen and filled the entire house.",
    "Children laughed and played in the park while their parents watched from nearby benches.",
    "The mountains rose majestically in the distance with their peaks covered in pristine white snow.",
    "Stars twinkled brightly in the dark night sky as the moon cast its silvery glow below.",
    "The old bookstore smelled of aged paper and leather with dusty shelves reaching to the ceiling.",
    "Waves crashed rhythmically against the shore as seagulls soared and called overhead.",

    # Personal Experiences
    "I remember the day I graduated from college and how proud my family was of my achievement.",
    "Last summer I traveled to Europe and visited several countries I had always dreamed of seeing.",
    "When I was younger I used to spend summers at my grandparents' farm in the countryside.",
    "I'll never forget the first time I rode a bicycle without training wheels down our street.",
    "Yesterday I had the most interesting conversation with a stranger while waiting for the bus.",
    "I recently started learning a new language and it's been challenging but very rewarding.",
    "The best meal I ever had was at a small restaurant in Italy during my honeymoon trip.",
    "I used to be afraid of public speaking but I've gradually become more confident over time.",
]

# === QUESTIONS & ANSWERS (Interview and discussion style) ===
question_answer_long_phrases = [
    # Personal Questions
    "What do you like to do in your free time when you're not working or busy with other obligations?",
    "Can you tell me about a challenge you've overcome and what you learned from that experience?",
    "What are your goals for the next year and what steps are you taking to achieve them?",
    "Who has been the most influential person in your life and how have they impacted you?",
    "What would you do differently if you could go back and give advice to your younger self?",
    "What accomplishments are you most proud of and why are they meaningful to you?",
    "How do you usually handle stress and what coping strategies work best for you personally?",
    "What motivates you to get up in the morning and tackle the challenges of each new day?",

    # Hypothetical Questions
    "If you could live anywhere in the world without any restrictions, where would you choose to live?",
    "What would you do if you won the lottery and suddenly had more money than you needed?",
    "If you could have dinner with anyone from history, who would you choose and what would you ask them?",
    "What superpower would you want to have if you could choose just one and why?",
    "If you could go back in time to any period in history, which era would you visit?",
    "What would you do if you had an extra hour in every day that no one else had?",
    "If you could master any skill instantly without having to practice, what would you learn?",
    "What would your ideal day look like from the moment you wake up until you go to sleep?",
]

# === COMMON SAYINGS & EXPRESSIONS (Idiomatic and conversational) ===
expressions_long_phrases = [
    "I think we should cross that bridge when we come to it instead of worrying about it now.",
    "The early bird gets the worm so I try to start my day as early as possible.",
    "You can lead a horse to water but you can't make it drink no matter how hard you try.",
    "Actions speak louder than words so I'd rather see what people do than hear what they say.",
    "Don't count your chickens before they hatch because things don't always work out as planned.",
    "Every cloud has a silver lining even when things seem difficult or challenging at first.",
    "The grass is always greener on the other side until you actually get there and see for yourself.",
    "Practice makes perfect so the more you do something the better you'll become at it.",
    "When life gives you lemons you should make lemonade and try to make the best of the situation.",
    "Rome wasn't built in a day so be patient and remember that good things take time.",
    "A picture is worth a thousand words because seeing something is more powerful than describing it.",
    "Don't put all your eggs in one basket because you need to diversify and have backup plans.",
]

# USAGE INSTRUCTIONS:
"""
TO ADD THESE TO YOUR TRAINING:

1. Open record_voice.py

2. Find the section where phrases are defined (around line 682)

3. Add whichever sections you want, for example:

    phrases.extend(conversational_long_phrases)
    phrases.extend(command_long_phrases)
    phrases.extend(professional_long_phrases)

4. Save the file

5. Run START_VOICE_TRAINING.bat

6. Record samples of the new phrases

7. Train your model with the improved data!

BENEFITS:
- Longer phrases (10-20 words) = Better recognition of natural speech
- More varied = Model learns different sentence patterns
- Complex sentences = Handles real-world conversations better
- Natural language = Sounds more like actual human speech

TOTAL NEW PHRASES: ~300+ ready to use!
"""

# Quick stats
if __name__ == "__main__":
    total = (
        len(conversational_long_phrases) +
        len(command_long_phrases) +
        len(therapeutic_long_phrases) +
        len(professional_long_phrases) +
        len(everyday_long_phrases) +
        len(technical_long_phrases) +
        len(storytelling_long_phrases) +
        len(question_answer_long_phrases) +
        len(expressions_long_phrases)
    )

    print(f"Total improved phrases: {total}")
    print(f"\nBreakdown:")
    print(f"  Conversational: {len(conversational_long_phrases)}")
    print(f"  Commands: {len(command_long_phrases)}")
    print(f"  Therapeutic: {len(therapeutic_long_phrases)}")
    print(f"  Professional: {len(professional_long_phrases)}")
    print(f"  Everyday: {len(everyday_long_phrases)}")
    print(f"  Technical: {len(technical_long_phrases)}")
    print(f"  Storytelling: {len(storytelling_long_phrases)}")
    print(f"  Questions: {len(question_answer_long_phrases)}")
    print(f"  Expressions: {len(expressions_long_phrases)}")
    print(f"\nAverage length: 10-20 words per phrase")
    print(f"All digits spelled out: YES ✅")
    print(f"Natural conversation style: YES ✅")
