from .models import QuizProfile
import pandas as pd
from surprise import Dataset
from surprise import Reader
from surprise import KNNWithMeans
SIM_OPTION = {
    "name": "cosine",
    "user_based": False,  # Compute  similarities between items
}


def convert_quizprofile_to_liste(quiz_liste):
    categories = []
    quiz = []
    ratings = []

    for quiz_profile in quiz_liste:
        elt = quiz_profile.calculation()
        for result in elt:
            rate = 1-(result[2]/result[1])*1
            categories.append(result[0])
            quiz.append(quiz_profile.id)
            ratings.append(rate)
    return categories, quiz, ratings


class Recommender(KNNWithMeans):
    def __init__(self, k=40, min_k=1, sim_options=..., verbose=True, **kwargs):
        super().__init__(k, min_k, sim_options, verbose, **kwargs)

    def get_quizprofile(self, id_user):
        quizprofiles = QuizProfile.objects.filter(
            user_id=id_user, completed=True)
        # List of quizprofile don't reach 100%
        list_of_not_success_quiz = []
        for quizprofile in quizprofiles:
            if quizprofile.success_rate() < 100:
                list_of_not_success_quiz.append(quizprofile)
        return list_of_not_success_quiz

    def interaction_table(self, id_user):
        quiz_liste = self.get_quizprofile(id_user)
        interact = {}
        interact["categories"], interact["quiz"], interact["ratings"] = convert_quizprofile_to_liste(
            quiz_liste)
        df = pd.DataFrame(interact)
        # print(df)
        reader = Reader(rating_scale=(0, 1))
        data = Dataset.load_from_df(
            df[["quiz", "categories", "ratings"]], reader)
        return data

    def train_recommenders(self, id_user):
        data = self.interaction_table(id_user)
        self.fit(data.build_full_trainset())

    def make_prediction(self, quiz, categorie):
        prediction = self.predict(quiz, categorie)
        return prediction.est
