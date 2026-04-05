#!/usr/bin/env python3
"""Generate 5000 diverse training phrases for STT"""
import random

# Tongue twisters
TWISTERS = [
    "She sells seashells by the seashore",
    "Peter Piper picked a peck of pickled peppers",
    "How much wood would a woodchuck chuck if a woodchuck could chuck wood",
    "Red lorry yellow lorry",
    "Unique New York",
    "Toy boat toy boat toy boat",
    "Irish wristwatch",
    "Rubber baby buggy bumpers",
    "Six slippery snails slid slowly seaward",
    "Betty Botter bought some butter",
    "A proper copper coffee pot",
    "Greek grapes grow in Greece",
    "Fresh French fried fish",
    "Black background brown background",
    "The sixth sick sheik's sixth sheep's sick",
    "Pad kid poured curd pulled cod",
    "Imagine an imaginary menagerie manager managing an imaginary menagerie",
    "Fred fed Ted bread and Ted fed Fred bread",
    "Lesser leather never weathered wetter weather better",
    "Which witch switched the Swiss wristwatches",
]

# Common phrases
COMMON = [
    "Good morning how are you today",
    "What time is it right now",
    "Can you help me with something",
    "I need to schedule a meeting",
    "Please send me that email",
    "Turn on the lights in the living room",
    "What's the weather like outside",
    "Play some music for me",
    "Set a reminder for tomorrow",
    "Call my friend John",
    "Open the calendar application",
    "Search for restaurants nearby",
    "Navigate to the nearest gas station",
    "Read my latest messages",
    "What's on my schedule today",
    "Remind me to buy groceries",
    "How do I get to the airport",
    "Book a flight to New York",
    "Order some food for delivery",
    "Check my bank account balance",
]

# Questions
QUESTIONS = [
    "What is the capital of France",
    "How many planets are in the solar system",
    "Who wrote Romeo and Juliet",
    "What year did World War Two end",
    "How tall is Mount Everest",
    "What is the speed of light",
    "Who invented the telephone",
    "What is the largest ocean on Earth",
    "How many bones are in the human body",
    "What is the chemical symbol for gold",
    "Who painted the Mona Lisa",
    "What is the square root of one hundred forty four",
    "How many continents are there",
    "What is the longest river in the world",
    "Who was the first president of the United States",
    "What is the boiling point of water in Fahrenheit",
    "How many days are in a leap year",
    "What is the largest mammal on Earth",
    "Who discovered penicillin",
    "What is the distance from Earth to the Moon",
]

# Technical phrases
TECHNICAL = [
    "Initialize the neural network parameters",
    "Run the machine learning algorithm",
    "Debug the software application",
    "Compile the source code",
    "Deploy to production server",
    "Configure the database settings",
    "Update the system dependencies",
    "Execute the python script",
    "Analyze the data visualization",
    "Optimize the query performance",
    "Implement the API endpoint",
    "Test the user interface",
    "Review the pull request",
    "Merge the feature branch",
    "Rollback the deployment",
    "Monitor the system metrics",
    "Scale the cloud infrastructure",
    "Encrypt the sensitive data",
    "Authenticate the user credentials",
    "Validate the input parameters",
]

# Story starters
STORIES = [
    "Once upon a time in a faraway kingdom there lived a brave knight",
    "The old man sat quietly by the window watching the rain fall gently",
    "She opened the mysterious letter and couldn't believe what she read",
    "The spaceship landed softly on the surface of the unknown planet",
    "Deep in the forest there was a cottage where nobody had lived for years",
    "The detective examined the clues carefully trying to solve the mystery",
    "As the sun set over the mountains the travelers made camp for the night",
    "The scientist made an incredible discovery that would change everything",
    "In the busy city streets people hurried past without noticing each other",
    "The young artist painted her dreams onto the large empty canvas",
]

# Numbers and dates
NUMBERS = [
    "The total amount is three hundred forty seven dollars and fifty cents",
    "My phone number is five five five one two three four five six seven",
    "The year nineteen eighty four was very significant",
    "She turned twenty five years old yesterday",
    "The meeting is scheduled for two thirty in the afternoon",
    "We need exactly forty two units of the product",
    "The temperature today is seventy three degrees Fahrenheit",
    "I have been waiting for approximately fifteen minutes",
    "The building has one hundred twenty floors",
    "There are seven billion people on Earth",
]

# Names and places
NAMES = [
    "My name is Michael and I live in California",
    "Sarah went to visit her grandmother in Texas",
    "The company headquarters is located in Seattle Washington",
    "Dr. Johnson will see you at three o'clock",
    "Please contact Elizabeth at the front desk",
    "The package was shipped from Chicago Illinois",
    "Professor Williams teaches advanced mathematics",
    "Jennifer and Robert are getting married next month",
    "The restaurant on Main Street is called Giuseppe's",
    "Alexander the Great conquered many territories",
]

# Actions and commands
COMMANDS = [
    "Please close the door behind you",
    "Turn off the computer when you leave",
    "Put the documents on my desk",
    "Send this message to everyone on the team",
    "Schedule the appointment for next Tuesday",
    "Cancel my subscription immediately",
    "Forward this email to the marketing department",
    "Print twenty copies of this report",
    "Delete all the temporary files",
    "Save the changes before closing",
]

# Emotions and expressions
EMOTIONS = [
    "I am so happy to see you again after all this time",
    "This is absolutely wonderful news congratulations",
    "I'm feeling a bit tired today need some coffee",
    "That movie was incredibly sad I cried at the end",
    "What an amazing surprise I wasn't expecting this",
    "I'm really frustrated with this situation",
    "Thank you so much for your help I really appreciate it",
    "I'm nervous about the presentation tomorrow",
    "This is the best day of my life everything is perfect",
    "I'm sorry to hear about what happened",
]

# Wake-phrase focused phrases for robust activation training
WAKE_VARIANTS = [
    "Monica initialize",
    "Hey Monica initialize",
    "Monica initialise",
    "Monica system online",
    "Monica start up",
    "Monica startup",
    "Monica wake up",
    "Monica activate",
    "Monika initialize",
    "Omega initialize",
    "Monica interlaced",
    "Monica in itialize",
]

# Generate variations
def generate_phrases():
    phrases = set()
    
    # Add base phrases
    for lst in [TWISTERS, COMMON, QUESTIONS, TECHNICAL, STORIES, NUMBERS, NAMES, COMMANDS, EMOTIONS]:
        phrases.update(lst)
    phrases.update(WAKE_VARIANTS)

    # Extra wake phrase coverage with realistic speaking contexts.
    wake_prefixes = ["", "hey ", "okay ", "yo "]
    wake_suffixes = ["", " please", " now", " right now", " let's begin"]
    wake_conditions = ["", " in a noisy room", " from far away", " with background TV", " from the other side of the room"]
    for base in WAKE_VARIANTS:
        b = base.lower()
        for p in wake_prefixes:
            for s in wake_suffixes:
                for c in wake_conditions:
                    phrases.add(f"{p}{b}{s}{c}".strip())
    
    # Generate variations with prefixes
    prefixes = ["Hey Monica ", "Monica ", "Please ", "Can you ", "I want to ", "I need to ", 
                "Could you please ", "Would you mind ", "I'd like to ", "Let's "]
    
    for phrase in list(COMMON + COMMANDS)[:50]:
        for prefix in prefixes:
            phrases.add(f"{prefix}{phrase.lower()}")
    
    # Generate sentences with different subjects
    subjects = ["I", "You", "We", "They", "He", "She", "The team", "Everyone", "Nobody", "Someone"]
    verbs = ["want", "need", "have", "should", "could", "would", "will", "must", "might", "can"]
    objects = ["help with this project", "finish the report", "attend the meeting", "review the document",
               "call the client", "send the email", "update the system", "fix the problem",
               "complete the task", "start the process", "check the results", "analyze the data"]
    
    for subj in subjects:
        for verb in verbs:
            for obj in objects:
                phrases.add(f"{subj} {verb} {obj}")
    
    # Generate counting phrases
    for i in range(1, 101):
        phrases.add(f"The number is {i}")
        phrases.add(f"I count {i} items")
    
    # Days and months
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    months = ["January", "February", "March", "April", "May", "June", 
              "July", "August", "September", "October", "November", "December"]
    
    for day in days:
        phrases.add(f"Today is {day}")
        phrases.add(f"The meeting is on {day}")
        phrases.add(f"I have an appointment on {day}")
    
    for month in months:
        phrases.add(f"My birthday is in {month}")
        phrases.add(f"The event is scheduled for {month}")
        phrases.add(f"We're going on vacation in {month}")
    
    # Colors and objects
    colors = ["red", "blue", "green", "yellow", "orange", "purple", "black", "white", "pink", "brown"]
    objects2 = ["car", "house", "shirt", "book", "phone", "computer", "chair", "table", "door", "window"]
    
    for color in colors:
        for obj in objects2:
            phrases.add(f"The {color} {obj} is over there")
            phrases.add(f"I want the {color} {obj}")
    
    # Alphabet sentences
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    for letter in alphabet:
        phrases.add(f"The letter {letter.upper()} is the {ord(letter)-96} letter of the alphabet")
    
    # Weather phrases
    weather = ["sunny", "cloudy", "rainy", "snowy", "windy", "foggy", "stormy", "humid", "cold", "hot"]
    for w in weather:
        phrases.add(f"The weather today is {w}")
        phrases.add(f"It looks like it will be {w} tomorrow")
        phrases.add(f"I hope it's not too {w} outside")
    
    # Food and drink
    foods = ["pizza", "hamburger", "salad", "pasta", "sushi", "tacos", "sandwich", "soup", "steak", "chicken"]
    drinks = ["coffee", "tea", "water", "juice", "soda", "milk", "wine", "beer", "smoothie", "lemonade"]
    
    for food in foods:
        phrases.add(f"I would like to order {food} please")
        phrases.add(f"The {food} here is excellent")
        phrases.add(f"Do you have any {food} on the menu")
    
    for drink in drinks:
        phrases.add(f"Can I have a glass of {drink}")
        phrases.add(f"I'll take a {drink} please")
    
    # More technical
    techs = ["artificial intelligence", "machine learning", "deep learning", "neural networks",
             "natural language processing", "computer vision", "speech recognition", "data science"]
    for tech in techs:
        phrases.add(f"I'm studying {tech}")
        phrases.add(f"The future of {tech} is exciting")
        phrases.add(f"How does {tech} work")
    
    # Pangrams
    pangrams = [
        "The quick brown fox jumps over the lazy dog",
        "Pack my box with five dozen liquor jugs",
        "How vexingly quick daft zebras jump",
        "The five boxing wizards jump quickly",
        "Sphinx of black quartz judge my vow",
        "Two driven jacks help fax my big quiz",
        "The jay pig fox dwelt on zebra and my squab",
        "Waltz nymph for quick jigs vex bud",
        "Quick zephyrs blow vexing daft Jim",
        "Crazy Frederick bought many very exquisite opal jewels",
    ]
    phrases.update(pangrams)
    
    # Long sentences
    long_sents = [
        "The magnificent sunset painted the sky with brilliant shades of orange pink and purple as we watched from the hilltop",
        "After spending three weeks preparing for the presentation the team finally felt confident about their proposal",
        "The ancient library contained thousands of books manuscripts and scrolls dating back hundreds of years",
        "She carefully arranged the flowers in the vase making sure each one was perfectly positioned",
        "The children ran through the park laughing and playing without a care in the world",
        "Despite the challenges we faced throughout the project we managed to deliver everything on time",
        "The symphony orchestra performed beautifully receiving a standing ovation from the audience",
        "He walked slowly down the empty street thinking about everything that had happened that day",
        "The chef prepared an exquisite meal using only the freshest ingredients from the local market",
        "We stayed up late talking about our dreams and plans for the future",
    ]
    phrases.update(long_sents)
    
    # Fill to 5000
    templates = [
        "I think {} is very important",
        "We should consider {} more carefully",
        "The problem with {} is that it takes too long",
        "Have you ever thought about {}",
        "Let me tell you about {}",
        "What do you think about {}",
        "I believe {} will change everything",
        "The best thing about {} is the quality",
        "I've been working on {} for a while now",
        "Everyone should know about {}",
    ]
    
    topics = ["technology", "education", "health", "business", "science", "art", "music", "sports",
              "travel", "food", "environment", "politics", "culture", "history", "philosophy",
              "psychology", "economics", "medicine", "engineering", "mathematics"]
    
    for template in templates:
        for topic in topics:
            phrases.add(template.format(topic))
    
    # Add more until we hit 5000
    adjectives = ["great", "small", "large", "beautiful", "ugly", "fast", "slow", "bright", "dark", "new", "old"]
    nouns = ["idea", "plan", "project", "system", "process", "method", "approach", "solution", "strategy", "concept"]
    
    for adj in adjectives:
        for noun in nouns:
            phrases.add(f"That's a {adj} {noun}")
            phrases.add(f"We need a more {adj} {noun}")
            phrases.add(f"I have a {adj} {noun} to share")
    
    # More diverse fillers
    actions = ["running", "walking", "reading", "writing", "cooking", "driving", "swimming", "dancing", "singing", "painting"]
    places = ["park", "beach", "mountain", "city", "forest", "desert", "island", "village", "river", "lake"]
    times = ["morning", "afternoon", "evening", "night", "dawn", "dusk", "midnight", "noon"]
    
    for action in actions:
        for place in places:
            phrases.add(f"I enjoy {action} at the {place}")
            phrases.add(f"We went {action} near the {place}")
        for time in times:
            phrases.add(f"I like {action} in the {time}")
    
    # Conversational
    convos = [
        "How have you been lately",
        "It's been a while since we talked",
        "What are your plans for the weekend",
        "Did you watch the game last night",
        "I heard there's a new restaurant downtown",
        "The traffic was terrible this morning",
        "I can't believe how fast time flies",
        "Remember when we used to hang out more",
        "Things have been pretty busy at work",
        "I'm thinking about learning something new",
        "Have you read any good books recently",
        "The news has been crazy lately",
        "I really need a vacation soon",
        "My phone battery dies so quickly",
        "I should probably go to bed earlier",
        "Exercise really does make you feel better",
        "I'm trying to eat healthier these days",
        "Technology changes so fast nowadays",
        "I miss the way things used to be",
        "Sometimes I wonder what the future holds",
    ]
    phrases.update(convos)
    
    # Opinions
    opinions = [
        "I strongly believe that education is the key to success",
        "In my opinion we should focus more on renewable energy",
        "I think social media has both positive and negative effects",
        "From my perspective the economy is improving slowly",
        "I feel that people should be more kind to each other",
        "It seems to me that technology is advancing too quickly",
        "I would argue that reading is still important in the digital age",
        "My view is that we need to protect the environment",
        "I'm convinced that hard work pays off eventually",
        "I suspect that things will get better with time",
    ]
    phrases.update(opinions)
    
    # Instructions
    instructions = [
        "First you need to open the application and sign in",
        "Make sure to save your work before closing the program",
        "Click on the settings icon in the top right corner",
        "Enter your password and then press the submit button",
        "Scroll down to find the option you're looking for",
        "Double click on the file to open it",
        "Right click to see the context menu",
        "Drag and drop the item into the folder",
        "Press control and c to copy the selected text",
        "Use the search bar to find what you need",
    ]
    phrases.update(instructions)
    
    # Descriptive
    descriptive = [
        "The tall building cast a long shadow across the street",
        "Her voice was soft and gentle like a summer breeze",
        "The old oak tree stood proudly in the center of the garden",
        "His eyes sparkled with excitement when he heard the news",
        "The room was filled with the sweet aroma of fresh flowers",
        "The waves crashed against the rocky shore with tremendous force",
        "A gentle rain began to fall as we walked through the park",
        "The mountains in the distance were covered with snow",
        "The busy marketplace was full of colorful fruits and vegetables",
        "The ancient castle stood on top of the hill overlooking the valley",
    ]
    phrases.update(descriptive)
    
    # Fill remaining with varied sentences
    sentence_starts = ["Actually", "Honestly", "Basically", "Obviously", "Clearly", "Apparently", "Surprisingly", "Unfortunately", "Fortunately", "Interestingly"]
    sentence_middles = [
        "I think we should reconsider our approach",
        "the situation is more complicated than expected",
        "we need to work together on this",
        "that's not what I meant at all",
        "things turned out better than anticipated",
        "we have to make a decision soon",
        "there are many factors to consider",
        "I didn't realize how difficult it would be",
        "everyone has their own perspective",
        "we can learn from this experience",
    ]
    
    for start in sentence_starts:
        for middle in sentence_middles:
            phrases.add(f"{start} {middle}")
    
    # More essays and stories
    essays = [
        "The importance of time management cannot be overstated in today's fast-paced world",
        "Climate change is one of the most pressing issues facing humanity today",
        "The digital revolution has fundamentally transformed how we communicate with each other",
        "Education plays a crucial role in shaping the future of society",
        "Mental health awareness has become increasingly important in recent years",
        "The rise of artificial intelligence raises important ethical questions",
        "Globalization has connected people across the world like never before",
        "The preservation of cultural heritage is essential for future generations",
        "Economic inequality continues to be a major challenge in many countries",
        "The role of government in healthcare remains a topic of debate",
        "Social media has changed the way we consume news and information",
        "The importance of biodiversity in maintaining healthy ecosystems",
        "Technological advancement has both benefits and drawbacks for society",
        "The impact of urbanization on rural communities is significant",
        "Renewable energy sources are key to a sustainable future",
        "The ethics of genetic engineering require careful consideration",
        "Access to clean water remains a challenge in many parts of the world",
        "The gig economy is reshaping traditional employment patterns",
        "Privacy concerns in the digital age are increasingly relevant",
        "The relationship between art and society has always been complex",
    ]
    phrases.update(essays)
    
    # More tongue twisters
    more_twisters = [
        "A big black bug bit a big black bear",
        "Can you can a can as a canner can can a can",
        "I scream you scream we all scream for ice cream",
        "Whether the weather be fine or whether the weather be not",
        "She stood on the balcony inexplicably mimicking him hiccupping",
        "Six sick hicks nick six slick bricks with picks and sticks",
        "Susie works in a shoeshine shop where she shines she sits",
        "Near an ear a nearer ear a nearly eerie ear",
        "On a lazy laser raiser lies a laser ray eraser",
        "Rory the warrior and Roger the worrier were reared wrongly",
        "The great Greek grape growers grow great Greek grapes",
        "Through three cheese trees three free fleas flew",
        "Eleven benevolent elephants held eleven yellow umbrellas",
        "A skunk sat on a stump and thunk the stump stunk",
        "If two witches were watching two watches which witch would watch which watch",
        "I saw Susie sitting in a shoe shine shop",
        "How can a clam cram in a clean cream can",
        "I wish to wish the wish you wish to wish",
        "Send toast to ten tense stout saints ten tall tents",
        "Top chopstick shops stock top chopsticks",
    ]
    phrases.update(more_twisters)
    
    # Daily life phrases
    daily = [
        "I woke up early this morning feeling refreshed and ready for the day",
        "After breakfast I decided to go for a walk around the neighborhood",
        "The coffee shop on the corner makes the best cappuccino in town",
        "I need to pick up some groceries on my way home from work",
        "The kids have soccer practice at four o'clock this afternoon",
        "My car needs an oil change and the tires are getting worn",
        "I forgot to pay the electricity bill and now it's overdue",
        "The dentist appointment is scheduled for next Monday morning",
        "We should clean the garage this weekend it's getting cluttered",
        "I promised to help my friend move into their new apartment",
        "The dog needs to go to the vet for his annual checkup",
        "I'm thinking about repainting the living room a different color",
        "The washing machine has been making a strange noise lately",
        "We ran out of milk so I'll stop by the store later",
        "The neighbors are having a barbecue and invited us over",
        "I need to renew my driver's license before it expires",
        "The garden needs watering the plants are looking a bit dry",
        "I should start exercising more regularly to stay healthy",
        "The internet has been really slow all day today",
        "I'm looking forward to the weekend I could use some rest",
    ]
    phrases.update(daily)
    
    # More questions
    more_questions = [
        "What time does the movie start tonight",
        "Where did you put the car keys",
        "How long have you been waiting here",
        "Why didn't you call me back yesterday",
        "When is the project deadline",
        "Who is responsible for this decision",
        "Which restaurant should we go to for dinner",
        "How much does this item cost",
        "What happened at the meeting today",
        "Where are we supposed to meet them",
        "Why is the traffic so bad today",
        "When will you be finished with that",
        "Who told you about this",
        "Which option do you prefer",
        "How often do you go to the gym",
        "What do you think we should do",
        "Where can I find more information",
        "Why hasn't anyone responded yet",
        "When did this problem start",
        "How did they solve the issue",
    ]
    phrases.update(more_questions)
    
    # Professional phrases
    professional = [
        "I'd like to schedule a conference call with the stakeholders",
        "Please review the attached document and provide your feedback",
        "The quarterly report shows significant growth in revenue",
        "We need to align our strategy with the company's objectives",
        "The client has requested a meeting to discuss the proposal",
        "I'll follow up with you next week regarding the project status",
        "Please ensure all team members are informed of the changes",
        "The budget has been approved by the finance department",
        "We should conduct a thorough analysis before making a decision",
        "The presentation has been scheduled for Thursday afternoon",
        "I appreciate your prompt response to my earlier email",
        "Could you provide an update on the implementation timeline",
        "The contract terms need to be reviewed by legal",
        "We've received positive feedback from the customer survey",
        "Please prioritize the tasks according to their urgency",
        "The new policy will take effect starting next month",
        "I recommend we explore alternative solutions to this problem",
        "The team has successfully completed the first phase of development",
        "We need to improve our communication with remote employees",
        "The performance metrics indicate room for improvement",
    ]
    phrases.update(professional)
    
    # Emotional expressions
    more_emotions = [
        "I can't express how grateful I am for your support",
        "This situation is really stressing me out",
        "I'm so proud of everything you've accomplished",
        "It breaks my heart to see you going through this",
        "I've never been more excited about anything in my life",
        "The disappointment I felt was overwhelming",
        "Your kindness means the world to me",
        "I'm feeling overwhelmed by all these responsibilities",
        "Nothing makes me happier than spending time with family",
        "I regret not taking that opportunity when I had the chance",
        "The joy on their faces made it all worthwhile",
        "I'm worried about what might happen next",
        "Your words of encouragement really lifted my spirits",
        "I feel so blessed to have such amazing friends",
        "The uncertainty is making me anxious",
        "I couldn't be more pleased with the results",
        "It hurts to know that I let you down",
        "I'm hopeful that things will work out in the end",
        "The relief I felt when I heard the news was immense",
        "I treasure every moment we spend together",
    ]
    phrases.update(more_emotions)
    
    # Travel phrases
    travel = [
        "The flight departs at seven thirty in the morning",
        "We need to check in at least two hours before departure",
        "The hotel room has a beautiful view of the ocean",
        "I'd like to book a round trip ticket to Los Angeles",
        "The tour guide showed us all the historic landmarks",
        "We got lost trying to find the museum",
        "The local cuisine was absolutely delicious",
        "I forgot to pack my toothbrush and had to buy a new one",
        "The train station is about fifteen minutes from here",
        "We should exchange some currency before we leave",
        "The passport control line was extremely long",
        "Our luggage got delayed but arrived the next day",
        "The sunset from the beach was breathtaking",
        "I took hundreds of photos during the trip",
        "The language barrier made communication difficult",
        "We rented a car to explore the countryside",
        "The souvenir shop had some unique items",
        "I'm still jet-lagged from the long flight",
        "The weather was perfect for sightseeing",
        "I can't wait to plan our next vacation",
    ]
    phrases.update(travel)
    
    # Numbers spelled out
    for i in range(100, 1000, 7):
        phrases.add(f"The total comes to {i} dollars")
    
    for i in range(1, 32):
        phrases.add(f"The appointment is on the {i}th of the month")
    
    # Years
    for year in range(1990, 2026):
        phrases.add(f"That happened in the year {year}")
    
    # Percentages
    for pct in range(0, 101, 5):
        phrases.add(f"The completion rate is {pct} percent")
    
    # Book and movie quotes
    quotes = [
        "To be or not to be that is the question",
        "It was the best of times it was the worst of times",
        "All that glitters is not gold",
        "The only thing we have to fear is fear itself",
        "I think therefore I am",
        "To infinity and beyond",
        "May the force be with you",
        "Here's looking at you kid",
        "You can't handle the truth",
        "Life is like a box of chocolates you never know what you're gonna get",
        "I'll be back",
        "Why so serious",
        "Elementary my dear Watson",
        "Houston we have a problem",
        "There's no place like home",
        "After all tomorrow is another day",
        "I see dead people",
        "You talking to me",
        "Frankly my dear I don't give a damn",
        "I'm going to make him an offer he can't refuse",
    ]
    phrases.update(quotes)
    
    # Science phrases
    science = [
        "The speed of light is approximately three hundred thousand kilometers per second",
        "Water molecules consist of two hydrogen atoms and one oxygen atom",
        "The theory of relativity was developed by Albert Einstein",
        "Photosynthesis converts sunlight into chemical energy",
        "The periodic table organizes elements by atomic number",
        "DNA contains the genetic instructions for all living organisms",
        "Gravity is the force that attracts objects toward each other",
        "The human brain contains approximately eighty six billion neurons",
        "Plate tectonics explains the movement of Earth's continents",
        "Black holes are regions where gravity is so strong that nothing can escape",
        "Evolution occurs through natural selection over many generations",
        "Atoms are the basic building blocks of matter",
        "The mitochondria is the powerhouse of the cell",
        "Sound travels faster through water than through air",
        "The universe is approximately thirteen point eight billion years old",
    ]
    phrases.update(science)
    
    # Health and fitness
    health = [
        "Regular exercise can help reduce the risk of heart disease",
        "It's recommended to drink eight glasses of water per day",
        "Getting enough sleep is essential for good health",
        "A balanced diet includes fruits vegetables and whole grains",
        "Stress can have negative effects on both physical and mental health",
        "Stretching before exercise helps prevent injuries",
        "Cardiovascular exercise strengthens the heart and lungs",
        "Meditation can help reduce anxiety and improve focus",
        "Vitamin D is important for bone health",
        "High blood pressure is often called the silent killer",
    ]
    phrases.update(health)
    
    # Technology descriptions
    tech_desc = [
        "The smartphone has revolutionized the way we communicate",
        "Cloud computing allows data to be stored on remote servers",
        "Virtual reality creates immersive digital experiences",
        "Blockchain technology enables secure decentralized transactions",
        "The internet of things connects everyday devices to the network",
        "Machine learning algorithms improve with more data",
        "Cybersecurity protects systems from digital attacks",
        "Autonomous vehicles use sensors to navigate without human input",
        "Quantum computers can solve problems faster than traditional computers",
        "Five G networks provide faster wireless connectivity",
    ]
    phrases.update(tech_desc)
    
    # Hobbies
    hobbies = [
        "I've been learning to play the guitar for about six months now",
        "Photography is a great way to capture special moments",
        "Gardening can be very relaxing and rewarding",
        "I enjoy baking homemade bread on the weekends",
        "Knitting is a skill that takes patience to master",
        "Chess requires strategic thinking and planning ahead",
        "Bird watching is a peaceful outdoor activity",
        "I started collecting stamps when I was a child",
        "Woodworking allows you to create beautiful furniture",
        "Hiking is a great way to explore nature and stay fit",
    ]
    phrases.update(hobbies)
    
    # Comparisons
    comparisons = [
        "This year's sales are higher than last year's",
        "The new model is faster and more efficient",
        "Quality is more important than quantity",
        "The second option seems better than the first",
        "Today was hotter than yesterday",
        "This version is an improvement over the previous one",
        "The benefits outweigh the risks",
        "Experience matters more than education in this field",
        "Prevention is better than cure",
        "Actions speak louder than words",
    ]
    phrases.update(comparisons)
    
    # Conditional sentences
    conditionals = [
        "If it rains tomorrow we will cancel the picnic",
        "I would help you if I had more time",
        "Unless we leave now we will miss the train",
        "If I had known earlier I would have done things differently",
        "We can go out for dinner if you finish your work on time",
        "If the price is right I might consider buying it",
        "Should you need any assistance please don't hesitate to ask",
        "If everything goes according to plan we should be done by Friday",
        "I wouldn't have believed it if I hadn't seen it myself",
        "If you want to succeed you have to work hard",
    ]
    phrases.update(conditionals)
    
    # Reporting speech
    reporting = [
        "She said that she would be here by noon",
        "He mentioned that the meeting was postponed",
        "They told me they had already finished the project",
        "The report states that sales increased by twenty percent",
        "According to the news the weather will improve tomorrow",
        "The doctor advised me to get more rest",
        "My friend suggested that we try a new restaurant",
        "The teacher explained how to solve the problem",
        "He promised that he would call back later",
        "She admitted that she had made a mistake",
    ]
    phrases.update(reporting)
    
    # Sequencing
    sequences = [
        "First wash your hands then prepare the ingredients",
        "After that you need to mix everything together",
        "Next add the spices and stir well",
        "Finally bake in the oven for thirty minutes",
        "Before you begin make sure you have all the materials",
        "Once you're done let it cool for a few minutes",
        "Following that step you should see results immediately",
        "To start with let me give you some background information",
        "Subsequently the situation improved dramatically",
        "In conclusion I believe this is the best approach",
    ]
    phrases.update(sequences)
    
    # More varied sentences
    varied = [
        "The library is open from nine in the morning until eight at night",
        "Please submit your application before the deadline",
        "The concert has been sold out for weeks",
        "I accidentally deleted all my files and had to recover them",
        "The new employee is adjusting well to the team",
        "We celebrated our anniversary at a fancy restaurant",
        "The construction project is behind schedule",
        "I need to charge my phone the battery is almost dead",
        "The recipe calls for two cups of flour and one cup of sugar",
        "She has been promoted to senior manager",
        "The movie received excellent reviews from critics",
        "I prefer working from home to commuting every day",
        "The package should arrive within three to five business days",
        "He apologized for being late to the meeting",
        "The store is having a big sale this weekend",
        "I've been meaning to read that book for months",
        "The museum has an impressive collection of modern art",
        "We need to reschedule our appointment",
        "The restaurant has a no reservation policy",
        "I'm considering switching to a different phone carrier",
    ]
    phrases.update(varied)
    
    # Sports phrases
    sports = [
        "The team won the championship after an incredible season",
        "The score is currently three to two with ten minutes remaining",
        "The athlete broke the world record by two seconds",
        "The coach decided to substitute the injured player",
        "The referee made a controversial call",
        "The game went into overtime after a tied score",
        "Training camp starts next week for the new season",
        "The playoffs begin on Friday night",
        "He scored the winning goal in the final minute",
        "The defense played exceptionally well throughout the match",
    ]
    phrases.update(sports)
    
    # Music phrases
    music = [
        "The concert was absolutely amazing from start to finish",
        "This song has been stuck in my head all day",
        "The album reached number one on the charts",
        "She has a beautiful voice and great stage presence",
        "The band is going on tour next summer",
        "I learned to play this piece on the piano",
        "The lyrics are really meaningful and touching",
        "Classical music helps me concentrate when I'm working",
        "The drummer kept perfect time throughout the performance",
        "They released a new single that's already gone viral",
    ]
    phrases.update(music)
    
    # More combinations
    verbs2 = ["believe", "understand", "remember", "forget", "realize", "recognize", "appreciate", "consider", "imagine", "suppose"]
    clauses = [
        "that this is the right decision",
        "how difficult it must have been",
        "what you're going through",
        "why things turned out this way",
        "how much effort was involved",
        "that mistakes can happen",
        "the importance of this matter",
        "how quickly time passes",
        "what needs to be done",
        "that we all make errors sometimes",
    ]
    
    for verb in verbs2:
        for clause in clauses:
            phrases.add(f"I {verb} {clause}")
    
    # Add unique fillers to reach 5000
    filler_subjects = ["The manager", "My colleague", "The customer", "Our team", "The client", "The supervisor", "The consultant"]
    filler_actions = ["requested", "suggested", "recommended", "proposed", "mentioned", "indicated", "confirmed"]
    filler_objects = [
        "a meeting for next week",
        "some changes to the document",
        "a different approach",
        "additional resources",
        "a revised timeline",
        "better communication",
        "more detailed analysis",
    ]
    
    for subj in filler_subjects:
        for action in filler_actions:
            for obj in filler_objects:
                phrases.add(f"{subj} {action} {obj}")
    
    # More diverse fillers to reach 5000
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
    activities = ["visiting", "exploring", "touring", "discovering", "experiencing"]
    for city in cities:
        for act in activities:
            phrases.add(f"I'm thinking about {act} {city} next summer")
            phrases.add(f"Have you ever been to {city}")
            phrases.add(f"The weather in {city} is different from here")
    
    # Amounts and measurements
    for amount in range(1, 51):
        phrases.add(f"We need {amount} units of this product")
        phrases.add(f"The project will take approximately {amount} days")
        phrases.add(f"There are {amount} people waiting in line")
    
    # Time expressions
    hours = list(range(1, 13))
    for hour in hours:
        phrases.add(f"The meeting starts at {hour} o'clock")
        phrases.add(f"I'll be there by {hour} thirty")
        phrases.add(f"Let's meet at {hour} fifteen")
    
    # Adjective noun combinations
    more_adj = ["incredible", "remarkable", "outstanding", "exceptional", "impressive", "extraordinary", "magnificent", "wonderful", "fantastic", "superb"]
    more_nouns = ["opportunity", "achievement", "performance", "experience", "result", "outcome", "contribution", "effort", "work", "presentation"]
    for adj in more_adj:
        for noun in more_nouns:
            phrases.add(f"That was an {adj} {noun}")
            phrases.add(f"What an {adj} {noun}")
    
    # Cause and effect
    causes = ["the delay", "the problem", "the issue", "the mistake", "the error", "the confusion", "the misunderstanding"]
    effects = ["we missed the deadline", "the project was postponed", "we had to start over", "everything was affected", "the schedule changed"]
    for cause in causes:
        for effect in effects:
            phrases.add(f"Because of {cause} {effect}")
    
    # Preferences
    items = ["coffee", "tea", "movies", "books", "music", "sports", "travel", "cooking", "technology", "art"]
    for item in items:
        phrases.add(f"I really enjoy {item}")
        phrases.add(f"I'm not a big fan of {item}")
        phrases.add(f"I prefer {item} over anything else")
        phrases.add(f"I've always been interested in {item}")
    
    # More numbers spelled out
    for n in range(50, 200):
        phrases.add(f"The quantity ordered was {n}")
    
    # Countries
    countries = ["Japan", "France", "Germany", "Italy", "Spain", "Brazil", "Canada", "Australia", "India", "China"]
    for country in countries:
        phrases.add(f"I would love to visit {country} someday")
        phrases.add(f"The culture in {country} is fascinating")
        phrases.add(f"Products from {country} are known for quality")
        phrases.add(f"I met someone from {country} recently")
    
    # Animals
    animals = ["dog", "cat", "bird", "fish", "rabbit", "horse", "elephant", "lion", "tiger", "bear"]
    for animal in animals:
        phrases.add(f"My favorite animal is the {animal}")
        phrases.add(f"I saw a {animal} at the zoo yesterday")
        phrases.add(f"The {animal} is known for being intelligent")
    
    # More professional
    departments = ["marketing", "sales", "engineering", "finance", "human resources", "operations", "legal", "research"]
    for dept in departments:
        phrases.add(f"The {dept} department needs more resources")
        phrases.add(f"I have a meeting with the {dept} team")
        phrases.add(f"The {dept} budget was approved last week")
        phrases.add(f"We need to coordinate with {dept}")
    
    # Final fillers
    feelings = ["happy", "sad", "excited", "worried", "confident", "uncertain", "optimistic", "pessimistic"]
    reasons = ["the results", "the news", "the decision", "the outcome", "the progress", "the situation"]
    for feel in feelings:
        for reason in reasons:
            phrases.add(f"I'm feeling {feel} about {reason}")
    
    for i in range(200, 300):
        phrases.add(f"The order number is {i}")
    
    return list(phrases)[:5000]

if __name__ == "__main__":
    phrases = generate_phrases()
    random.shuffle(phrases)
    
    with open("stt_training_phrases.txt", "w", encoding="utf-8") as f:
        for i, phrase in enumerate(phrases, 1):
            f.write(f"{phrase}\n")
    
    print(f"Generated {len(phrases)} unique phrases")
    print("Saved to stt_training_phrases.txt")
