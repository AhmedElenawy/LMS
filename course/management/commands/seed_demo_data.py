import requests
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django.db import transaction

# --- ADJUST THESE IMPORTS TO MATCH YOUR EXACT APP NAMES ---
from course.models import Category, Course, Module, Content, Video, Text
from assignment.models import Assignment, Question, MCQAnswer
from authentication.models import Instructor

class Command(BaseCommand):
    help = 'Populates the database with real course data, high-quality images, and assignments without deleting existing data.'
    @transaction.atomic
    def handle(self, *args, **kwargs):
        real_data = [
            {
                "category": "Web Development",
                "title": "Complete Python & Django Masterclass",
                "overview": "Learn Python and Django by building real-world applications.",
                "base_price": "59.99",
                "image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80", 
                "modules": [
                    {
                        "title": "Module 1: Python Fundamentals",
                        "contents": [
                            {"type": "video", "title": "Welcome to the Course", "url": "https://www.youtube.com/watch?v=kqtD5dpn9C8"},
                            {"type": "text", "title": "Environment Setup", "body": "Please install Python 3.10 and VS Code to get started."},
                            {
                                "type": "assignment", 
                                "title": "Python Basics Quiz",
                                "max_grade": 20,
                                "active": True,
                                "duration_minutes": 30,
                                "max_attempts": 3,
                                "questions": [
                                    {
                                        "question": "Which of the following is used to define a function in Python?",
                                        "answer_type": "mcq",
                                        "question_marks": 10,
                                        "choices": [
                                            {"text": "func", "is_correct": False},
                                            {"text": "def", "is_correct": True},
                                            {"text": "function", "is_correct": False}
                                        ]
                                    },
                                    {
                                        "question": "Write a brief explanation of what a dictionary is in Python.",
                                        "answer_type": "written",
                                        "question_marks": 10
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "category": "Frontend Development",
                "title": "React JS for Beginners",
                "overview": "Master React, Hooks, and Redux in this comprehensive bootcamp.",
                "base_price": "49.99",
                "image_url": "https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=800&q=80", 
                "modules": [
                    {
                        "title": "Module 1: Introduction to React",
                        "contents": [
                            {"type": "video", "title": "What is React?", "url": "https://www.youtube.com/watch?v=Tn6-PIqc4UM"},
                            {
                                "type": "assignment", 
                                "title": "React Core Concepts",
                                "max_grade": 10,
                                "active": True,
                                "duration_minutes": 15,
                                "max_attempts": 2,
                                "questions": [
                                    {
                                        "question": "What hook is used to manage state in a functional component?",
                                        "answer_type": "mcq",
                                        "question_marks": 10,
                                        "choices": [
                                            {"text": "useEffect", "is_correct": False},
                                            {"text": "useState", "is_correct": True},
                                            {"text": "useReducer", "is_correct": False}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]

        now = timezone.now()

        # 1. Safely grab Instructor ID 10
        instructor, created = Instructor.objects.get_or_create(id=10)
        if created:
            self.stdout.write(self.style.WARNING("Instructor with ID 10 did not exist, so a placeholder was created."))

        for data in real_data:
            self.stdout.write(f"Processing course: {data['title']}...")

            # 2. Get or Create Category
            category, _ = Category.objects.get_or_create(
                title=data['category'],
                defaults={'slug': slugify(data['category'])}
            )

            # 3. Get or Create Course (Added slug generation to defaults just in case)
            course, course_created = Course.objects.get_or_create(
                title=data['title'],
                defaults={
                    'slug': slugify(data['title']),
                    'instructor': instructor,
                    'category': category,
                    'overview': data['overview'],
                    'base_price': data['base_price'],
                }
            )

            # 4. Image Handling (Only runs once when course is first created)
            if course_created and data.get('image_url'):
                try:
                    self.stdout.write("Downloading high-quality image...")
                    response = requests.get(data['image_url'], timeout=10)
                    if response.status_code == 200:
                        file_name = f"{slugify(course.title)}.jpg"
                        course.image.save(file_name, ContentFile(response.content), save=True)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Could not download image: {e}"))

            # 5. Build the Curriculum
            if course_created:
                for mod_data in data['modules']:
                    module = Module.objects.create(course=course, title=mod_data['title'])
                    
                    for content_data in mod_data['contents']:
                        # NOTE: Added `owner=instructor` below to prevent ItemBase IntegrityErrors
                        
                        if content_data['type'] == 'video':
                            # Removed owner=instructor
                            item = Video.objects.create(title=content_data['title'], url=content_data['url'])
                            Content.objects.create(module=module, item=item)
                        
                        elif content_data['type'] == 'text':
                            # Removed owner=instructor
                            item = Text.objects.create(title=content_data['title'], body=content_data['body'])
                            Content.objects.create(module=module, item=item)
                        
                        elif content_data['type'] == 'assignment':
                            # Removed owner=instructor
                            item = Assignment.objects.create(
                                title=content_data['title'],
                                valid_from=now,
                                valid_to=now + timedelta(days=365),
                                max_grade=content_data.get('max_grade', 100),
                                active=content_data.get('active', True),
                                duration=timedelta(minutes=content_data.get('duration_minutes', 60)),
                                max_attempts=content_data.get('max_attempts', 1)
                            )
                            Content.objects.create(module=module, item=item)

                            for q_data in content_data.get('questions', []):
                                question = Question.objects.create(
                                    assignment=item,
                                    question=q_data['question'],
                                    answer_type=q_data['answer_type'],
                                    question_marks=q_data['question_marks']
                                )

                                if question.answer_type == Question.AnswerType.MCQ:
                                    for choice_data in q_data.get('choices', []):
                                        MCQAnswer.objects.create(
                                            question=question,
                                            answer=choice_data['text'],
                                            is_correct=choice_data['is_correct']
                                        )

        self.stdout.write(self.style.SUCCESS('Successfully populated LMS data!'))