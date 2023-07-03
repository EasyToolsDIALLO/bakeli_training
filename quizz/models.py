from re import A
from django.db import models

# Create your models here.
import random
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
NUMBER_OF_QUESTIONS = 5


class Domaine(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class Categorie(models.Model):
    nom = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.nom

    def questions_of_the_categorie(self):
        return self.categories.all()

    def questions_from_quizprofile(self, id_quizprofile):
        # Get attempts(tentatives) filter by quiz profil id
        attempts = AttemptedQuestion.objects.filter(
            quiz_profile=id_quizprofile)
        questions = []

        #
        for attempt in attempts:
            if attempt.question.categorie.id == self.id:
                tmp = Question.objects.get(id=attempt.question.id)
                questions.append(tmp)
        return questions


class Parcours(models.Model):
    name = models.CharField(max_length=255)
    categorie = models.ManyToManyField(Categorie, related_name='parcourss')
    domaine = models.ForeignKey(
        Domaine, on_delete=models.CASCADE, related_name='parcours', null=True)

    def __str__(self) -> str:
        return self.name

    def categories_of_parcours(self):
        return list(self.categorie.all())

    def questions_of_parcours(self):
        # Return all the categories
        categories = self.categories_of_parcours()
        questions = []

        # Stock each categorie's questions in the same list (questions)
        for categorie in categories:
            tmp = categorie.questions_of_the_categorie()
            questions.append(tmp)

        # Mix all questions together in one list
        questions = [
            item for list_question in questions for item in list_question]
        return questions

    def questions_from_quizprofile(self, id_quizprofile):
        # Return all the categories
        categories = self.categories_of_parcours()
        questions = []

        # Stock questions for all categories..
        for categorie in categories:
            tmp = categorie.questions_from_quizprofile(id_quizprofile)
            if len(tmp) != 0:
                questions.append(tmp)
        return questions


class Question(models.Model):
    ALLOWED_NUMBER_OF_CORRECT_CHOICES = 1

    # fields
    # The question itself
    html = models.TextField(_('Question Text'))

    is_published = models.BooleanField(
        _('Has been published?'), default=False, null=False)

    # The number of point you get if you are right
    maximum_marks = models.DecimalField(
        _('Maximum Marks'), default=4, decimal_places=2, max_digits=6)

    # The category which it is associated
    categorie = models.ForeignKey(
        Categorie, related_name="categories", on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.html

    def correct_choice(self):
        corr_choice = None
        # Search between the table the right answer associated to the question
        list_choice = Choice.objects.filter(question_id=self.id)
        for choice in list_choice:
            if choice.is_correct:
                corr_choice = choice
        return corr_choice


class Choice(models.Model):
    MAX_CHOICES_COUNT = 4

    question = models.ForeignKey(
        Question, related_name='choices', on_delete=models.CASCADE)
    is_correct = models.BooleanField(
        _('Is this answer correct?'), default=False, null=False)
    html = models.TextField(_('Choice Text'))

    def __str__(self):
        return self.html


class QuizProfile(models.Model):
    # The user passing the quizz
    user = models.ForeignKey(
        User, related_name='quizprofiles', on_delete=models.CASCADE)

    # His score
    total_score = models.DecimalField(
        _('Total Score'), default=0, decimal_places=2, max_digits=10)

    # His parcours
    parcours = models.ForeignKey(
        Parcours, null=True, on_delete=models.CASCADE, related_name='quizprofile')

    # Check if he has finished the quizz
    completed = models.BooleanField(
        _('Is the quizz is completed'), default=False, null=True)

    def __str__(self):
        return f'<QuizProfile: user={self.user}>'

    def get_new_question(self, id_categorie):
        # All the questions we have respond to a specific quizz linked to a parcours and a categorie
        # We filter the attemped question for the same quizz it is why we filter quiz_profile=self
        used_questions_pk = AttemptedQuestion.objects.filter(
            quiz_profile=self).values_list('question__pk', flat=True)

        # Exclude the precedents questions from the list of questions
        remaining_questions = Question.objects.exclude(
            pk__in=used_questions_pk).filter(categorie_id=id_categorie)

        # If the number of questions we respond during the quizz equals the number of questions
        # specify for the question, we have finished the quizz
        if len(used_questions_pk) == NUMBER_OF_QUESTIONS:
            self.complete_quizz()
            return

        # Choose the next question from the remaining questions not chosen yet
        return random.choice(remaining_questions)

    def create_attempt(self, question):
        # we create a attempt
        attempted_question = AttemptedQuestion(
            question=question, quiz_profile=self)

        # Save the attempted question
        attempted_question.save()

    def evaluate_attempt(self, attempted_question, selected_choice):
        # We check if the selected choice is for the question we have, if not we return nothing
        if attempted_question.question_id != selected_choice.question_id:
            return

        attempted_question.selected_choice = selected_choice
        if selected_choice.is_correct is True:
            attempted_question.is_correct = True
            # As the response is true we give the mark associated
            attempted_question.marks_obtained = attempted_question.question.maximum_marks

        # The response is right or not we save the attempted question
        attempted_question.save()
        self.update_score()

    def update_score(self):
        # We sum all the mark
        marks_sum = self.attempts.filter(is_correct=True).aggregate(
            models.Sum('marks_obtained'))['marks_obtained__sum']
        self.total_score = marks_sum or 0
        self.save()

    def calculation(self):
        # We get all the questions for the quizz in a list
        list_question = self.parcours.questions_from_quizprofile(self.id)
        result = []

        for questions in list_question:
            count = 0
            for question in questions:
                attempt = AttemptedQuestion.objects.get(
                    quiz_profile_id=self.id, question_id=question.id)
                if attempt.is_correct:
                    count += 1
            # Return a liste of tuple contains the category's name ,the number of questions et the number of correct answer
            result.append([questions[0].categorie.nom, len(questions), count])
        return result

    def success_rate(self):
        list_question = self.parcours.questions_from_quizprofile(self.id)
        count = 0
        number_question = 0
        rate = 0
        for questions in list_question:
            for question in questions:
                attempt = AttemptedQuestion.objects.get(
                    quiz_profile_id=self.id, question_id=question.id)
                if attempt.is_correct:
                    count += 1
                number_question += 1

        rate = round((count/number_question)*100)
        return rate

    def complete_quizz(self):
        self.completed = True
        self.save()


class AttemptedQuestion(models.Model):
    # the question
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    # The quizz
    quiz_profile = models.ForeignKey(
        QuizProfile, on_delete=models.CASCADE, related_name='attempts')

    # The selected answer of the question
    selected_choice = models.ForeignKey(
        Choice, on_delete=models.CASCADE, null=True)

    # If the selected answer of the question is correct or not
    is_correct = models.BooleanField(
        _('Was this attempt correct?'), default=False, null=False)

    # Mark obtained from the response
    marks_obtained = models.DecimalField(
        _('Marks Obtained'), default=0, decimal_places=2, max_digits=6)

    def get_absolute_url(self):
        return f'/submission-result/{self.pk}/'


class Tutorial(models.Model):
    categorie = models.ForeignKey(
        Categorie, on_delete=models.CASCADE, related_name='tutorials')
    contenu = models.TextField(_('Contenu video'), max_length=255)
    link = models.CharField(_('Link of video'), max_length=255)
