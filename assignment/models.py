from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.validators import MaxValueValidator, MinValueValidator
from course.models import ItemBase
from authentication.models import Student

class Assignment(ItemBase):
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    max_grade = models.IntegerField(validators=[MinValueValidator(0)], null=True, blank=True)
    active = models.BooleanField()
    duration = models.DurationField(default=timedelta(minutes=60))
    max_attempts = models.IntegerField(validators=[MinValueValidator(0)], null=True, blank=True)
    def is_valid(self):
        now = timezone.now()
        if now < self.valid_from or now > self.valid_to or not self.active:
            return False
        return True
    
    def __str__(self):
        return self.title
    
class Question(models.Model):
    class AnswerType(models.TextChoices):
        MCQ = 'mcq'
        WRITTEN = 'written'
        FILE = 'file' 
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    answer_type = models.CharField(choices=AnswerType.choices, default=AnswerType.MCQ)
    question_marks = models.IntegerField(validators=[MinValueValidator(0)],)
    
 
class MCQAnswer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='mcq_answers')
    answer = models.TextField()
    is_correct = models.BooleanField(default=False)



class AssignmentSubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending'
        SUBMITTED = 'submitted'
        EXPIRED = 'expired'
        CANCELED = 'canceled'
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assignment_submissions')
    submitted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    # grade = models.IntegerField(validators=[MinValueValidator(0)], null=True, blank=True)
    status = models.CharField(choices=Status.choices, default=Status.PENDING, max_length=20)
    # pending_grade = models.BooleanField(default=False)
    # pending_review = models.BooleanField(default=False)

    def grade(self):
        grade = 0
        for answer in self.answers.all():
            grade += answer.gained_marks or 0
        return grade
    


class SubmissionAnswer(models.Model):
    submission = models.ForeignKey(AssignmentSubmission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    
    gained_marks = models.IntegerField(validators=[MinValueValidator(0)], null=True, blank=True)
    text_answer = models.TextField(null=True, blank=True)
    
    # 2. For File Answers
    file_answer = models.FileField(upload_to='answers', null=True, blank=True)
    
    # 3. For MCQ Answers
    chosen_mcq = models.ForeignKey(MCQAnswer, on_delete=models.SET_NULL, null=True, blank=True)



