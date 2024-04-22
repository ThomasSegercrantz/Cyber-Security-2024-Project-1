from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.db import connection
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import Choice, Question


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """
        Return the last five published questions (not including 
        those set to be published in the future).
        """
        #Flaw 2 Injection. All code in this method down to row 35.
        search_term = self.request.GET.get('search_term', '')
        raw_query = f"SELECT * FROM polls_question WHERE question_text LIKE '%{search_term}%' AND pub_date <= '{timezone.now()}' ORDER BY pub_date DESC LIMIT 5;"

        with connection.cursor() as cursor:
            cursor.execute(raw_query)
            results = cursor.fetchall()

        question_list = []
        for result in results:
            question_list.append(Question(*result))

        return question_list
        """
        The fix to Flaw 2 is:
        search_term = self.request.GET.get('q', '')

        queryset = Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]

        if search_term:
            queryset = queryset.filter(Q(question_text__icontains=search_term))

        return queryset
        """

class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"

#Flaw 1 CSRF - Cross Site Request Forgery. The fix to the flaw is by not including @csrf_exempt
@csrf_exempt
def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "polls/detail.html", 
            {"question": question, 
             "error_message": "You didn't select a choice"
             },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after succesfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))
    