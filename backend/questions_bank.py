"""
MCQ Questions Bank for Assessment
"""

MCQ_QUESTIONS = [
    {
        "id": 1,
        "category": "programming",
        "difficulty": "easy",
        "question": "What does HTML stand for?",
        "options": [
            "Hyper Text Markup Language",
            "High Tech Modern Language",
            "Home Tool Markup Language",
            "Hyperlinks and Text Markup Language"
        ],
        "correct_answer": 0,
        "time_limit": 60
    },
    {
        "id": 2,
        "category": "programming",
        "difficulty": "medium",
        "question": "Which of the following is NOT a JavaScript data type?",
        "options": [
            "String",
            "Boolean",
            "Float",
            "Undefined"
        ],
        "correct_answer": 2,
        "time_limit": 60
    },
    {
        "id": 3,
        "category": "programming",
        "difficulty": "medium",
        "question": "What is the time complexity of binary search?",
        "options": [
            "O(n)",
            "O(log n)",
            "O(n log n)",
            "O(1)"
        ],
        "correct_answer": 1,
        "time_limit": 90
    },
    {
        "id": 4,
        "category": "database",
        "difficulty": "easy",
        "question": "What does SQL stand for?",
        "options": [
            "Structured Query Language",
            "Simple Question Language",
            "Structured Question Language",
            "Simple Query Language"
        ],
        "correct_answer": 0,
        "time_limit": 60
    },
    {
        "id": 5,
        "category": "database",
        "difficulty": "medium",
        "question": "Which SQL command is used to retrieve data from a database?",
        "options": [
            "GET",
            "SELECT",
            "RETRIEVE",
            "FETCH"
        ],
        "correct_answer": 1,
        "time_limit": 60
    },
    {
        "id": 6,
        "category": "web",
        "difficulty": "medium",
        "question": "What is the purpose of the CSS box model?",
        "options": [
            "To create animations",
            "To define layout and spacing of elements",
            "To style text",
            "To create responsive images"
        ],
        "correct_answer": 1,
        "time_limit": 75
    },
    {
        "id": 7,
        "category": "programming",
        "difficulty": "hard",
        "question": "What design pattern ensures a class has only one instance?",
        "options": [
            "Factory Pattern",
            "Singleton Pattern",
            "Observer Pattern",
            "Strategy Pattern"
        ],
        "correct_answer": 1,
        "time_limit": 90
    },
    {
        "id": 8,
        "category": "algorithms",
        "difficulty": "hard",
        "question": "Which sorting algorithm has the best average-case time complexity?",
        "options": [
            "Bubble Sort",
            "Insertion Sort",
            "Quick Sort",
            "Selection Sort"
        ],
        "correct_answer": 2,
        "time_limit": 90
    },
    {
        "id": 9,
        "category": "web",
        "difficulty": "easy",
        "question": "What does API stand for?",
        "options": [
            "Application Programming Interface",
            "Automated Programming Interface",
            "Application Process Integration",
            "Advanced Programming Interface"
        ],
        "correct_answer": 0,
        "time_limit": 60
    },
    {
        "id": 10,
        "category": "programming",
        "difficulty": "medium",
        "question": "What is the purpose of version control systems like Git?",
        "options": [
            "To compile code",
            "To track changes in code over time",
            "To debug programs",
            "To deploy applications"
        ],
        "correct_answer": 1,
        "time_limit": 75
    }
]

CODING_PROBLEMS = [
    {
        "id": 1,
        "title": "Two Sum",
        "difficulty": "easy",
        "description": "Given an array of integers nums and an integer target, return indices of the two numbers that add up to target.",
        "example": "Input: nums = [2,7,11,15], target = 9\nOutput: [0,1]",
        "test_cases": [
            {"input": {"nums": [2, 7, 11, 15], "target": 9}, "output": [0, 1]},
            {"input": {"nums": [3, 2, 4], "target": 6}, "output": [1, 2]},
            {"input": {"nums": [3, 3], "target": 6}, "output": [0, 1]}
        ]
    },
    {
        "id": 2,
        "title": "Reverse String",
        "difficulty": "easy",
        "description": "Write a function that reverses a string.",
        "example": "Input: 'hello'\nOutput: 'olleh'",
        "test_cases": [
            {"input": "hello", "output": "olleh"},
            {"input": "world", "output": "dlrow"},
            {"input": "python", "output": "nohtyp"}
        ]
    },
    {
        "id": 3,
        "title": "Palindrome Check",
        "difficulty": "easy",
        "description": "Check if a given string is a palindrome (reads the same forward and backward).",
        "example": "Input: 'racecar'\nOutput: True",
        "test_cases": [
            {"input": "racecar", "output": True},
            {"input": "hello", "output": False},
            {"input": "madam", "output": True}
        ]
    }
]

PSYCHOMETRIC_SCENARIOS = [
    {
        "id": 1,
        "scenario": "You are leading a project with a tight deadline. A team member consistently misses deadlines, affecting the entire team's progress. How would you handle this situation?",
        "traits": ["leadership", "communication", "problem_solving"]
    },
    {
        "id": 2,
        "scenario": "You discover a significant bug in production that was caused by your code. The fix will take several hours. What do you do?",
        "traits": ["accountability", "stress_management", "decision_making"]
    },
    {
        "id": 3,
        "scenario": "A colleague takes credit for your idea in a meeting. How do you respond?",
        "traits": ["assertiveness", "conflict_resolution", "professionalism"]
    },
    {
        "id": 4,
        "scenario": "You're asked to work on a technology you've never used before with a short learning curve. How do you approach this?",
        "traits": ["adaptability", "learning_agility", "resilience"]
    },
    {
        "id": 5,
        "scenario": "Your team is divided on a technical decision. How do you help reach a consensus?",
        "traits": ["collaboration", "communication", "leadership"]
    }
]


def get_mcq_questions(count=10):
    """Get a set of MCQ questions"""
    import random
    return random.sample(MCQ_QUESTIONS, min(count, len(MCQ_QUESTIONS)))


def get_coding_problem(difficulty="easy"):
    """Get a coding problem by difficulty"""
    problems = [p for p in CODING_PROBLEMS if p['difficulty'] == difficulty]
    import random
    return random.choice(problems) if problems else CODING_PROBLEMS[0]


def get_psychometric_scenarios(count=3):
    """Get psychometric scenarios"""
    import random
    return random.sample(PSYCHOMETRIC_SCENARIOS, min(count, len(PSYCHOMETRIC_SCENARIOS)))
