from django.db.models import Count
from rest_framework import serializers
from django.apps import apps
from django.db import transaction
from education.redis_client import r
from .models import *



class MCQAnswerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False) 
    class Meta:
        model = MCQAnswer
        fields = ['id', 'answer', 'is_correct']


class AssignmentMCQAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MCQAnswer
        fields = ['id', 'answer']



class QuestionSerializer(serializers.ModelSerializer):
    question_marks = serializers.IntegerField(default=1, required=False, allow_null=True)
    mcq_answers = MCQAnswerSerializer(many=True, required=False)
    class Meta:
        model = Question
        fields = ['id', 'question', 'answer_type', 'question_marks', 'mcq_answers']
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.answer_type != Question.AnswerType.MCQ:
            representation.pop('mcq_answers', None)
        return representation
    @transaction.atomic
    def create(self, validated_data):
        mcq_answers_data = validated_data.pop('mcq_answers', [])
        question = Question.objects.create(**validated_data)
        answers = [MCQAnswer(question=question, **answer_data) for answer_data in mcq_answers_data]
        if answers:
            MCQAnswer.objects.bulk_create(answers)
        r.delete(f"assignment:{question.assignment_id}")
        return question
    
    @transaction.atomic
    def update(self, instance, validated_data):
        mcq_answers_data = validated_data.pop('mcq_answers', None)
        instance = super().update(instance, validated_data)

        if mcq_answers_data is not None:
            answers_to_update = []
            answers_to_create = []
            existing_answers = {ans.id: ans for ans in instance.mcq_answers.all()}

            for answer_data in mcq_answers_data:
                answer_id = answer_data.get('id')
                if answer_id and answer_id in existing_answers:
                    existing_answer = existing_answers.pop(answer_id)  # ✅ pop here
                    for attr, value in answer_data.items():
                        setattr(existing_answer, attr, value)
                    answers_to_update.append(existing_answer)
                else:
                    answers_to_create.append(MCQAnswer(question=instance, **answer_data))

            if existing_answers:
                MCQAnswer.objects.filter(id__in=existing_answers.keys()).delete()

            if answers_to_update:
                MCQAnswer.objects.bulk_update(answers_to_update, ['answer', 'is_correct'])

            if answers_to_create:
                MCQAnswer.objects.bulk_create(answers_to_create)
        r.delete(f"assignment:{instance.assignment_id}")
        return instance




        


class AssignmentQuestionSerializer(serializers.ModelSerializer):
    question_marks = serializers.IntegerField(default=1, required=False, allow_null=True)
    mcq_answers = AssignmentMCQAnswerSerializer(many=True, read_only=True)
    class Meta:
        model = Question
        fields = ['id', 'question', 'answer_type', 'question_marks', 'mcq_answers']
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.answer_type != Question.AnswerType.MCQ:
            representation.pop('mcq_answers', None)
        return representation


class AssignmentSerializer(serializers.ModelSerializer):
    questions = AssignmentQuestionSerializer(many=True, read_only=True)
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'created',
                   'updated',
                   'valid_from', 'valid_to', 'max_grade', 'active', "duration",
                     "max_attempts", 'questions']
        

class AnswerSubmissionSerializer(serializers.ModelSerializer):
    submission = serializers.PrimaryKeyRelatedField(queryset=AssignmentSubmission.objects.all(), required=False, allow_null=True)
    text_answer = serializers.CharField(required=False, allow_null=True)
    file_answer = serializers.FileField(required=False, allow_null=True)
    chosen_mcq = serializers.PrimaryKeyRelatedField(queryset=MCQAnswer.objects.all(), required=False, allow_null=True)
    question = serializers.PrimaryKeyRelatedField(read_only=True, required=False, allow_null=True)
    class Meta:
        model = SubmissionAnswer
        fields = ['id', 'question', 'text_answer', 'file_answer', 'chosen_mcq', 'submission']


class SubmissionInfoSerializer(serializers.ModelSerializer):
    grade = serializers.SerializerMethodField()
    def get_grade(self, obj):
        return obj.grade()
    class Meta:
        model = AssignmentSubmission
        fields = ['id', 'assignment', 'submitted_at', 'started_at', 'grade', 'status']


class AssignmentInfoSerializer(serializers.ModelSerializer):
    submissions = serializers.SerializerMethodField()
    def get_submissions(self, obj):
        return SubmissionInfoSerializer(obj.submissions.all(), many=True).data
    type = serializers.CharField(default='assignment', read_only=True)
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'created',
                   'updated', 'type',
                   'valid_from', 'valid_to', 'max_grade', 'active', "duration",
                     "max_attempts", 'submissions']
        

class AnswerReviewSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    class Meta:
        model = SubmissionAnswer
        fields = ['id', 'question', 'text_answer', 'file_answer', 'chosen_mcq', 'gained_marks']
class SubmissionSerializer(serializers.ModelSerializer):
    answers = AnswerReviewSerializer(many=True, read_only=True)
    grade = serializers.SerializerMethodField()
    def get_grade(self, obj):
        return obj.grade()
    class Meta:
        model = AssignmentSubmission
        fields = ['id', 'submitted_at', 'started_at', 'grade', 'status', 'answers']
