from django.http import HttpResponse
from flashcards.models import *
from django.template import loader, Context
from flashcards.views import generateFullCardListFromQueryset
import re

# THIS CURRENT SCHEME FOR CSV DOES NOT REQUIRE ANY EXTRA WORK HERE
def csvEscape(h):
  h = re.sub('\$', '', h)
  return h

def csv(request):
  csv_data = []
  if request.method == 'POST':
    items = request.POST.items()
    pks = filter(lambda (x, y): x.isdigit() and y == 'on', items)
    pks = map(lambda x: x[0], pks)
    cards = Card.objects.filter(pk__in=pks)
    cards = generateFullCardListFromQueryset(cards)
    
    header = ('front', 'back', 'priority', 'tags', 'sources')
    csv_data.append(header)
    for card in cards:
      csvList = []
      csvList.append(csvEscape(card.card['front']))
      csvList.append(csvEscape(card.card['back']))
      csvList.append("priority " + card.card['priority'])
      tags = csvEscape(', '.join(card.tagList))
      csvList.append(tags)
      sources = csvEscape(', '.join(card.sourceList))
      csvList.append(sources)
      csv_data.append(tuple(csvList))


    # The data is hard-coded here, but you could load it from a database or
    # some other source.
    """csv_data = (
        ('First row', 'Foo', 'Bar', 'Baz'),
        ('Second row', 'A', 'B', 'C', '"Testing"', "Here's a quote"),
    )"""
    
  response = HttpResponse(mimetype='text/csv')
  response['Content-Disposition'] = 'attachment; filename=cards.csv'

  t = loader.get_template('csv.txt')
  c = Context({
      'data': tuple(csv_data),
  })
  response.write(t.render(c))
  return response