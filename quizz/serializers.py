from dataclasses import field
import imp
from rest_framework import serializers
from quizz import models
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'name', 'email']


class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Categorie
        fields = ['nom']


class ParcoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Parcours
        fields = ['name', 'categorie']


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Question
        fields = ['html', 'is_published', 'maximum_marks', 'categorie']


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Choice
        fields = ['html', 'is_correct', 'question']


class AttemptedQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AttemptedQuestion
        fields = ['question', 'quiz_profile', 'is_correct',
                  'selected_choice', 'marks_obtained']
