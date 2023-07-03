from django.shortcuts import render
from cgitb import html
from multiprocessing import context
from random import choice
from traceback import print_tb
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from .models import Categorie, Domaine, QuizProfile, Question, AttemptedQuestion, Parcours, Choice, Tutorial
from .forms import UserLoginForm, RegistrationForm, AddWithExcel
from rest_framework.views import APIView
from rest_framework.response import Response
from quizz import serializers
import pandas as pd
from quizz.recommender import Recommender, SIM_OPTION

# created = False


def home(request):
    domaines = Domaine.objects.all()
    context = {'domaines': domaines}
    # print("Domaine: ", domaines)
    return render(request, 'quiz/home.html', context=context)


@login_required()
def user_home(request, id_domaine):
    parcours = Parcours.objects.filter(domaine_id=id_domaine)
    context = {'liste_parcours': parcours}
    # print("Parcours: ", parcours)
    return render(request, 'quiz/user_home.html', context=context)


def leaderboard(request):
    top_quiz_profiles = QuizProfile.objects.filter(
        user=request.user, completed=True).order_by('id')[:500]
    total_count = top_quiz_profiles.count()
    context = {
        'top_quiz_profiles': top_quiz_profiles,
        'total_count': total_count,
    }
    return render(request, 'quiz/leaderboard.html', context=context)


@login_required()
def play(request, id_parcours, completed):
    quiz_profile = None
    if completed == "False":
        quizprofiles = QuizProfile.objects.filter(
            user_id=request.user.id, parcours_id=id_parcours, completed=False)
        if len(quizprofiles) == 0:
            quiz_profile = QuizProfile.objects.create(
                user_id=request.user.id, parcours_id=id_parcours)
        else:
            quiz_profile = quizprofiles[0]

        print("quiz id ", quiz_profile.id)
        parcours = Parcours.objects.get(id=id_parcours)
        categories_parcours = list(parcours.categorie.all())

        if request.method == 'POST':
            '''list_quizprofile = list(
                QuizProfile.objects.filter(user=request.user))
            quiz_profile = list_quizprofile[-1]'''
            question_pk = request.POST['question__pk']
            attempted_question = quiz_profile.attempts.select_related(
                'question').get(question_id=question_pk)
            choice_pk = request.POST['choice_pk']
            print("********************************************************")
            print("Question: {} and Attempted: {} and Choice: {}".format(
                question_pk, attempted_question, choice_pk))
            try:
                selected_choice = attempted_question.question.choices.get(
                    pk=choice_pk)
            except ObjectDoesNotExist:
                return no_choice_selected(request, id_parcours)

            quiz_profile.evaluate_attempt(attempted_question, selected_choice)
            # return render(request, "quiz/test.html")
            return redirect(f'/play/{id_parcours}/{quiz_profile.completed}')
        else:

            categorie = choice(categories_parcours)
            print("categorie: ", categorie.id)
            question = quiz_profile.get_new_question(categorie.id)
            print("question: ", question)
            completed_quiz = str(quiz_profile.completed)
            print("completed_quiz: ", completed_quiz)
            number_answer = len(AttemptedQuestion.objects.filter(
                quiz_profile_id=quiz_profile.id))
            print("answer: ", number_answer)
            if question is not None:
                quiz_profile.create_attempt(question)
            else:
                print("completed quiz profile")

            context = {
                'question': question,
                'parcours': parcours,
                'completed': completed_quiz,
                'number_answer': number_answer,
                'max_question': Choice.MAX_CHOICES_COUNT
            }

            return render(request, 'quiz/play.html', context=context)
            # return render(request, "quiz/test.html")

    # return render(request, "quiz/test.html")


@login_required()
def submission_result(request, attempted_question_pk):
    attempted_question = get_object_or_404(
        AttemptedQuestion, pk=attempted_question_pk)
    context = {
        'attempted_question': attempted_question,
    }

    return render(request, 'quiz/submission_result.html', context=context)


def login_view(request):
    title = "Login"
    form = UserLoginForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(username=username, password=password)
        login(request, user)
        return redirect('home')
    return render(request, 'quiz/login.html', {"form": form, "title": title})


def register(request):
    title = "Create account"
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/login')
    else:
        form = RegistrationForm()

    context = {'form': form, 'title': title}
    return render(request, 'quiz/registration.html', context=context)


def logout_view(request):
    logout(request)
    return redirect('/')


def error_404(request):
    data = {}
    return render(request, 'quiz/error_404.html', data)


def error_500(request):
    data = {}
    return render(request, 'quiz/error_500.html', data)


# Create your views here.


def resume_test(request, quiz_profile_id,):
    attempts = AttemptedQuestion.objects.filter(quiz_profile=quiz_profile_id)
    quizprofile = QuizProfile.objects.get(id=quiz_profile_id)
    results = quizprofile.calculation() or []
    tresult = []
    percentage = []
    if results != []:
        for result in results:
            tmp = {
                'result': f'{result[0]},   {round(result[2]/result[1]*100)} %',
                'percent': str(result[2]/result[1]*100),
            }
            tresult.append(tmp)

    context = {
        'attempts': attempts,
        'results': tresult,
    }
    return render(request, 'quiz/resume.html', context)


def affiche_categories(request, id_parcours):
    parcours = Parcours.objects.get(id=id_parcours)
    categories = parcours.categorie.all() or []
    questions = []

    if categories != []:
        for categorie in categories:
            tmp = list(Question.objects.filter(categorie=categorie.id))
            questions.append((categorie, tmp))
    context = {
        'categories': categories,
        'questions': questions
    }
    return render(request, 'quiz/affiche.html', context)


def add_questions_with_excel(request):
    if request.method == 'POST':

        form = AddWithExcel(data=request.POST)

        print(form.is_valid())
        # path = form.cleaned_data['path_file']
        # questions = pd.read_excel(file_name, index_col=0)
        # questions = questions.head()
        # print(form.cleaned_data['path_file'])
        # for i in range(0, len(questions)):
        #     ques_excel = questions.loc[i]
        #     categorie = Categorie.objects.get(nom= ques_excel["Categories"])
        #     question = Question(html=ques_excel["Questions"], categorie= categorie)
        #     question.save()
        #     good_answer = int(ques_excel['Bonne_reponse'][-1])

        #     for j in range(4):
        #         if j == good_answer-1:
        #             choice = Choice(html=ques_excel[f"Opt{j+1}"],question=question,is_correct= True)
        #             choice.save()
        #         else:
        #             choice = Choice(html=ques_excel[f"Opt{j+1}"],question=question)
        #             choice.save()
        return redirect('home')

    else:
        form = AddWithExcel()
        context = {'form': form}
        return render(request, 'quiz/parametre.html', context)


def no_choice_selected(request, id_parcours):
    context = {
        'id': id_parcours
    }
    return render(request, 'quiz/not_selected_choice.html', context)


def recommandation(request):
    recommender_engine = Recommender(sim_options=SIM_OPTION)
    quiz = QuizProfile.objects.filter(
        user_id=request.user.id).distinct('parcours')
    last_quiz = []
    list_of_recommandation = {
        'amelioration': []
    }

    list_length = {
        'amelioration': 0
    }

    for elt in quiz:
        id_elt = elt.parcours.id
        tmp = QuizProfile.objects.filter(parcours=id_elt).latest('completed')
        last_quiz.append(tmp)

    recommender_engine.train_recommenders(request.user.id)

    for quizprofile in last_quiz:
        for categorie in quizprofile.parcours.categorie.all():
            tmp = round(recommender_engine.make_prediction(
                quizprofile.id, categorie.nom)*100)
            tuto = Tutorial.objects.get(categorie_id=categorie.id)
            print(f"tmp {tmp} categorie{categorie.nom}")
            if tmp < 80:
                list_of_recommandation['amelioration'].append(tuto)

    # list_length['critique'] = len(list_of_recommandation['critique'])
    list_length['amelioration'] = len(list_of_recommandation['amelioration'])

    context = {
        'recommandations': list_of_recommandation,
        'length': list_length,
    }
    return render(request, 'quiz/recommandation.html', context)

# API Views


class QuestionView(APIView):

    def get(self, request, format=None):
        questions = Question.objects.all()
        serializer = serializers.QuestionSerializer(questions, many=True)
        return Response(serializer.data)

    # def put(self, request, format = None):
