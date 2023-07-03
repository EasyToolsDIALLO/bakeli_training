from operator import imod
from django.urls import path, include
from quizz import views
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    path('', views.home, name='home'),
    path('user-home/<int:id_domaine>/', views.user_home, name='user_home'),
    path('play/<int:id_parcours>/<str:completed>', views.play, name='play'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('submission-result/<int:attempted_question_pk>/',
         views.submission_result, name='submission_result'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('resume/<int:quiz_profile_id>', views.resume_test, name='resume'),
    path('parcours/<int:id_parcours>', views.affiche_categories, name='parcours'),
    path('add-question', views.add_questions_with_excel, name='add_with_excel'),
    path('recommandation', views.recommandation, name='recommandation'),
    path('error', views.error_404, name='not_found'),
    # path('api', include(router.urls)),
]
