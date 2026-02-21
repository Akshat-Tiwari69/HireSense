"""
Question bank for assessments
Provides MCQ questions, coding problems, and psychometric scenarios
"""

def get_mcq_questions(count=10):
    """Return sample MCQ questions"""
    questions = [
        {
            'id': 1,
            'question': 'What is the time complexity of binary search?',
            'options': ['O(n)', 'O(log n)', 'O(n^2)', 'O(1)'],
            'correct_answer': 'O(log n)',
            'category': 'algorithms',
            'difficulty': 'easy',
            'time_limit': 60
        },
        {
            'id': 2,
            'question': 'Which data structure uses LIFO?',
            'options': ['Queue', 'Stack', 'Array', 'Tree'],
            'correct_answer': 'Stack',
            'category': 'data-structures',
            'difficulty': 'easy',
            'time_limit': 60
        },
        {
            'id': 3,
            'question': 'What does REST stand for?',
            'options': [
                'Remote Execution Service Transfer',
                'Representational State Transfer',
                'Resource Execution State Transfer',
                'Remote State Transfer'
            ],
            'correct_answer': 'Representational State Transfer',
            'category': 'web-development',
            'difficulty': 'easy',
            'time_limit': 60
        }
    ]
    return questions[:count]

def get_coding_problem(difficulty="medium"):
    """Return a sample coding problem"""
    problems = {
        'easy': {
            'id': 1,
            'title': 'Two Sum',
            'description': 'Given an array of integers and a target, return indices of two numbers that add up to target.',
            'difficulty': 'easy',
            'starter_code': {
                'python': 'def two_sum(nums, target):\n    # Your code here\n    pass',
                'javascript': 'function twoSum(nums, target) {\n    // Your code here\n}',
                'java': 'public int[] twoSum(int[] nums, int target) {\n    // Your code here\n}'
            },
            'test_cases': [
                {'input': '[2,7,11,15], 9', 'expected': '[0,1]'},
                {'input': '[3,2,4], 6', 'expected': '[1,2]'}
            ]
        },
        'medium': {
            'id': 2,
            'title': 'Valid Parentheses',
            'description': 'Given a string containing just the characters \'(\', \')\', \'{\', \'}\', \'[\' and \']\', determine if the input string is valid.',
            'difficulty': 'medium',
            'starter_code': {
                'python': 'def is_valid(s):\n    # Your code here\n    pass',
                'javascript': 'function isValid(s) {\n    // Your code here\n}',
                'java': 'public boolean isValid(String s) {\n    // Your code here\n}'
            },
            'test_cases': [
                {'input': '"()"', 'expected': 'true'},
                {'input': '"()[]{}"', 'expected': 'true'},
                {'input': '"(]"', 'expected': 'false'}
            ]
        }
    }
    return problems.get(difficulty, problems['medium'])

def get_psychometric_scenarios(count=3):
    """Return sample psychometric scenarios"""
    scenarios = [
        {
            'id': 1,
            'scenario': 'Your teammate misses a critical deadline. How do you respond?',
            'options': [
                'Immediately escalate to management',
                'Have a private conversation to understand what happened',
                'Take over their work without discussing',
                'Ignore it and focus on your own tasks'
            ],
            'trait': 'teamwork'
        },
        {
            'id': 2,
            'scenario': 'You discover a potential security vulnerability in production code. What do you do?',
            'options': [
                'Fix it immediately without telling anyone',
                'Report it to the security team and your manager',
                'Wait until the next sprint to address it',
                'Ignore it if it seems minor'
            ],
            'trait': 'responsibility'
        },
        {
            'id': 3,
            'scenario': 'A client requests a feature that conflicts with best practices. How do you handle it?',
            'options': [
                'Implement exactly what they ask for',
                'Refuse to implement it',
                'Explain the concerns and suggest alternatives',
                'Implement it but make it hard to use'
            ],
            'trait': 'communication'
        }
    ]
    return scenarios[:count]
