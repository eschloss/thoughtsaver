from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.forms.formsets import formset_factory
from django.template  import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils import simplejson as json
import re, datetime, logging, random
from search.core import search
from flashcards.models import *
from flashcards.forms import *
from google.appengine.api import urlfetch
from accounts.models import Settings
from django.utils.http import urlquote
from django.core.urlresolvers import reverse
from google.appengine.api import urlfetch
from bs4 import BeautifulSoup

CARDS_PER_PAGE = 10 #TODO how many max cards per page?
MAX_NEW_CARDS = 10

#pklist for querysets, pklist2 for lists
def pklist2(modellist):
  return map(getpk, modellist)
def pklist(model):
  return innerList(model, 'pk')
#innerList for querysets, innerList2 for lists
def innerList(outerModel, innerModelField):
  return list(outerModel.values_list(innerModelField, flat=True))
def innerList2(outerModel, innerModelField):
  def getAttr(x):
    return getattr(x, innerModelField)
  return map(getAttr, outerModel)
def innerSet(outerModel, innerModelField):
  return set(outerModel.values_list(innerModelField, flat=True))


@login_required
def help(request):
  return render_to_response('help.html', {
    }, context_instance=RequestContext(request)
  )
  

#TODO split into smaller methods b/c this method will get overloaded eventually
#DEPRECATED
@login_required
def addCards(request):
  CardFormSet = formset_factory(CardForm, extra=MAX_NEW_CARDS)
  if request.method == 'POST':
    settings = request.user.get_profile()
    cardFormSet = CardFormSet(request.POST)
    if cardFormSet.is_valid():
      for cardForm in cardFormSet:
        cdata = cardForm.cleaned_data
        if cdata.__contains__('front') and cdata.__contains__('back'):
          front = cdata['front']
          back = cdata['back']
          card = Card.objects.create(front=front, back=back, settings=settings, nextTest=datetime.date.today())
          if cdata.__contains__('tagField'):
            tagField = cdata['tagField']
            tags = tagListClean(tagField)
            for t in tags:
              (tag, isNew) = Searchable.objects.get_or_create(type='t', name=t)
              CardTagView.objects.create(card=card, searchable=tag, denormalized_searchable_name=t, denormalized_card_settings=settings)
  else:
    cardFormSet = CardFormSet()
  return render_to_response('flashcards/addCards.html', {
      'cardFormSet': cardFormSet,
    }, context_instance=RequestContext(request)
  )

def createCard(settings, front, back, private, priority, donottest, tagField, sources, pk, copy):
  if back != '':
    if pk != None:
      card = get_object_or_404(Card, pk=pk)
      card.front = front
      card.back = back
      card.private = private
      card.priority = priority
      card.donottest = donottest
      card.save()
    else:
      card = Card.objects.create(original=not copy, front=front, back=back, settings=settings, nextTest=datetime.date.today(), private=private, priority=priority, donottest=donottest)
    tags = tagListClean(tagField)
    emptySearchablesForCard(card)
    for t in tags:
      createSearchable('t', CardTagView, t, card)
    for s in filter(lambda s: s != None and s.strip() != '', sources):
      createSearchable('s', CardSourceView, s, card)
    return card
  return None

def emptySearchablesForCard(card):
  CardTagView.objects.filter(card=card).delete()
  CardSourceView.objects.filter(card=card).delete()

def createSearchable(type, Model, name, card):
  (searchable, isNew) = Searchable.objects.get_or_create(name=name, type=type)
  Model.objects.create(card=card, searchable=searchable, denormalized_searchable_name=name, denormalized_card_settings=card.settings)

@login_required
def addTags(request):
  if request.method == 'POST' and request.POST.__contains__('id') and request.POST.__contains__('searchables'):
    tags = request.POST['searchables']
    id = request.POST['id']
    settings = request.user.get_profile()
    card = Card.objects.get(pk=id, settings=settings)
    for t in tagListClean(tags):
      (searchable, type) = Searchable.objects.get_or_create(type='t', name=t)
      CardTagView.objects.get_or_create(card=card, searchable=searchable, denormalized_searchable_name=t, denormalized_card_settings=card.settings)
  return HttpResponse('')
  
@login_required
def changeCard(request):
  if request.method == 'POST' and request.POST.__contains__('id'):
    id = request.POST['id']
    settings = request.user.get_profile()
    card = Card.objects.get(pk=id, settings=settings)
    if request.POST.__contains__('priority'):
      card.priority = request.POST['priority']
    if request.POST.__contains__('quizable'):
      card.donottest = request.POST['quizable'] != 'true';
    if request.POST.__contains__('isprivate'):
      card.private = request.POST['isprivate'] == 'true';
    card.save()
  return HttpResponse('')
  

'''def addSources(request):
  if request.method == 'POST' and request.POST.__contains__('id') and request.POST.__contains__('searchables'):
    tags = request.POST['searchables']
    id = request.POST['id']
    settings = request.user.get_profile()
    card = Card.objects.get(pk=id, settings=settings)
    for t in tagListClean(tags):
      (searchable, type) = Searchable.objects.get_or_create(type='s', name=t)
      CardSourceView.objects.get_or_create(card=card, searchable=searchable, denormalized_searchable_name=t, denormalized_card_settings=card.settings)
  return HttpResponse('')
'''

@login_required
def removeTags(request):
  if request.method == 'POST' and request.POST.__contains__('id') and request.POST.__contains__('searchables'):
    tags = request.POST['searchables']
    id = request.POST['id']
    settings = request.user.get_profile()
    card = Card.objects.get(pk=id, settings=settings)
    for t in tagListClean(tags):
      (searchable, type) = Searchable.objects.get_or_create(type='t', name=t)
      cardTagView = CardTagView.objects.filter(card=card, searchable=searchable, denormalized_searchable_name=t, denormalized_card_settings=card.settings)
      if len(cardTagView) > 0:
        cardTagView[0].delete()
  return HttpResponse('')

@login_required
def addCard(request):
  response = { 'success': False }
  if request.method == 'POST':
    POST = request.POST
    #response = { 'success': POST } #for testing purposes
    if POST.__contains__('front') and POST.__contains__('back') and POST.__contains__('tagField') and POST.__contains__('private')  and POST.__contains__('priority') and POST.__contains__('donottest'):
      settings = request.user.get_profile()
      front = POST['front']
      back = POST['back']
      tagField = POST['tagField']
      private = POST['private'] == 'true'
      donottest = POST['donottest'] == 'false'
      priority = POST['priority']
      sources = []
      if POST.__contains__('source1'):
        sources.append(POST['source1'])
      if POST.__contains__('source2'):
        sources.append(POST['source2'])
      pk = None
      if POST.__contains__('pk'):
        pk = POST['pk']
      copy = False
      if POST.__contains__('copy'):
        copy = True
      card = createCard(settings, front, back, private, priority, donottest, tagField, sources, pk, copy)
      if card != None:
        response['success'] = True
        response['pk'] = card.pk
  return HttpResponse(json.dumps(response), mimetype='applications/javascript') #should this be json


class WeightedSet():
  setDict = {}
  def __init__(self):
    self.setDict = {}
  def addSet(self, newSet, priority):
    for s in newSet:
      self.setDict[s[0]] = priority * int(s[1]) + self.setDict.get(s[0], 0)
  def getPkList(self):
    setList = self.setDict.items()
    setList = sorted(setList, key=lambda a: a[1], reverse=True)
    setList = map(lambda a: a[0], setList)
    return setList
  
def getCardSet(cardTagQuerySet):
  cardTagList = cardTagQuerySet.values_list('card', flat=True)
  return set(cardTagList)

PRIORITY_FRONT = 60
PRIORITY_BACK = 50
PRIORITY_TAG = 30
PRIORITY_SOURCE_STEM = 55
PRIORITY_SOURCE_TEXT = 5
PRIORITY_TAG_STEM = 70

MODEL_NAME_TO_MODEL = {
  'Card': Card,
  'CardTagView': CardTagView,
  'CardSourceView': CardSourceView,
  'CardTagView_Exact': CardTagView,
}

def asyncSearch(request):
  modelname = request.GET['model']
  model = MODEL_NAME_TO_MODEL[modelname]
  searchables = request.GET['searchables']
  search_index = request.GET['search_index']
  kwargs = json.loads(request.GET['kwargs'])
  logging.info("kwargs: "+str(kwargs))
  if modelname.find('_Exact') == -1:
    cards = search(model, searchables, search_index=search_index).filter(kwargs)
  else:
    cards = model.objects.filter(**kwargs)
  if len(cards) > 0:
    logging.info("cards: "+str(cards))
    if modelname != 'Card':
      cards = map(lambda a: a.card, list(cards))
    cards = set(map(lambda a: (a.pk, a.priority), list(cards)))
    logging.info('asyncsearch:' + str(cards))
  return HttpResponse(json.dumps(list(cards)), mimetype='applications/javascript')

ASYNC_URL = "http://thoughtsaver0.appspot.com/asyncSearch"
def setupAsyncSearch(modelName, searchables, search_index, **kwargs):
  rpc = urlfetch.create_rpc(deadline=10)
  kwargs = urlquote(json.dumps(kwargs))
  #kwargs = re.sub(r' ', '', json.dumps(kwargs))
  url = ASYNC_URL + "?model=" + modelName + "&searchables=" + searchables + "&search_index=" + search_index + "&kwargs=" +str(kwargs)
  logging.info("url: " +url)
  urlfetch.make_fetch_call(rpc, url)
  return rpc

#TODO I should cache this
# finds a weighted intersection of the cards
def filterCardsBySearchables(searchables, session):
  searchablesList = searchables.split(' ')
  weightedSet = WeightedSet()
  rpcs = []
  
  rpc = setupAsyncSearch('Card', searchables, "front_search", private=False, original=True)
  rpcs.append((PRIORITY_FRONT, rpc))

  rpc = setupAsyncSearch('Card', searchables, "back_search", private=False, original=True)
  rpcs.append((PRIORITY_BACK, rpc))
  
  for t in searchablesList:
    #TODO the Exact Tag Match is not asychronous....
    #Exact Tag Match
    tags = set(map(lambda a: (a.card.pk, a.card.priority), CardTagView.objects.filter(denormalized_searchable_name=t, denormalized_card_private=False, denormalized_card_original=True)))
    weightedSet.addSet(tags, PRIORITY_TAG)
    
    #Stem Tag Match
    rpc = setupAsyncSearch('CardTagView', t, "search_index", denormalized_card_private=False, denormalized_card_original=True)
    rpcs.append((PRIORITY_TAG_STEM, rpc))
    
    #Stem Source Match
    rpc = setupAsyncSearch('CardSourceView', t, "name_search", denormalized_card_private=False, denormalized_card_original=True)
    rpcs.append((PRIORITY_SOURCE_STEM, rpc))

    #Source Text search 
    rpc = setupAsyncSearch('CardSourceView', t, "text_search", denormalized_card_private=False, denormalized_card_original=True)
    rpcs.append((PRIORITY_SOURCE_TEXT, rpc))
    
  for r in rpcs:
    pks = json.loads(r[1].get_result().content)
    if len(pks) > 0:
      weightedSet.addSet(pks, r[0])
  return weightedSet

#TODO I should cache this
# TODO REMOVE DUPLICATION WITH ABOVE METHOD
# finds a weighted intersection of the cards
def filterCardsBySearchablesAndSettings(searchables, settings, session):
  searchablesList = searchables.split(' ')
  weightedSet = WeightedSet()
  rpcs = []
  
  rpc = setupAsyncSearch('Card', searchables, "front_search", settings=settings.pk, active=True)
  rpcs.append((PRIORITY_FRONT, rpc))

  rpc = setupAsyncSearch('Card', searchables, "back_search", settings=settings.pk, active=True)
  rpcs.append((PRIORITY_BACK, rpc))
  
  '''fronts = set(search(Card, searchables, search_index="front_search").filter(settings=settings))
  weightedSet.addSet(fronts, PRIORITY_FRONT)

  backs = set(search(Card, searchables, search_index="back_search").filter(settings=settings))
  weightedSet.addSet(backs, PRIORITY_BACK)
  '''
    
  for t in searchablesList:
    #Exact Tag Match #TODO this exact tag match is not asynchronous
    tags = CardTagView.objects.filter(denormalized_card_settings=settings, denormalized_searchable_name=t, denormalized_card_active=True)
    # Create a Search Log whenever for the tag matched in this search
    if tags.count() > 0:
      SearchLog.objects.create(searchable=tags[0].searchable, settings=settings)
    tags = set(map(lambda a: (a.card.pk, a.card.priority), tags))
    weightedSet.addSet(tags, PRIORITY_TAG)
    
    #Stem Tag Match
    rpc = setupAsyncSearch('CardTagView', t, "search_index", denormalized_card_settings=settings.pk, denormalized_card_active=True)
    rpcs.append((PRIORITY_TAG_STEM, rpc))
    
    #Stem Source Match
    rpc = setupAsyncSearch('CardSourceView', t, "name_search", denormalized_card_settings=settings.pk, denormalized_card_active=True)
    rpcs.append((PRIORITY_SOURCE_STEM, rpc))

    #Source Text search 
    rpc = setupAsyncSearch('CardSourceView', t, "text_search",  denormalized_card_settings=settings.pk, denormalized_card_active=True)
    rpcs.append((PRIORITY_SOURCE_TEXT, rpc))

    #Stem Tag Match
    '''searchCardTagView = search(CardTagView, t).filter(denormalized_card_settings=settings)
    tags = set(map(lambda a: a.card, searchCardTagView))
    weightedSet.addSet(tags, PRIORITY_TAG_STEM)
  
    #Stem Source Match
    sources = set(map(lambda a: a.card, search(CardSourceView, t).filter(denormalized_card_settings=settings)))
    weightedSet.addSet(sources, PRIORITY_SOURCE_STEM)'''
    
  for r in rpcs:
    pks = json.loads(r[1].get_result().content)
    if len(pks) > 0:
      logging.info("len pks > 0:"+str(pks))
      weightedSet.addSet(pks, r[0])
  return weightedSet

# Combines Card and Tags into easy-access data structure
class FullCard():
  tagList = []
  sourceList = []
  card = None
  def __init__(self, card):
    self.card = card.__as_dict__()
    tagPks = innerList(CardTagView.objects.filter(card=card), 'searchable')
    if len(tagPks) > 0:
      self.tagList = map(lambda x: x.name, Searchable.objects.in_bulk(tagPks).values())
    sourcePks = innerList(CardSourceView.objects.filter(card=card), 'searchable')
    if len(sourcePks) > 0:
      self.sourceList = map(lambda x: x.name, Searchable.objects.in_bulk(sourcePks).values())
  def __as_dict__(self):
    return {
      'tagList': self.tagList,
      'sourceList': self.sourceList,
      'card': self.card,
    }
def fullCardFromPk(pk):
  try:
    card = Card.objects.filter(pk=pk).only('front', 'back', 'settings')[0]
    fcard = FullCard(card)
    return fcard
  except:
    logging.error("card (pk=%s) does not exist" % (pk))
    

def generateFullCardListFromPkList(cardPkList):
  fullCardList = []
  for c in cardPkList:
    fc = fullCardFromPk(c)
    if fc != None:
      fullCardList.append(fc)
  return fullCardList

def generateFullCardListFromQueryset(cards):
  fullCardList = []
  for c in cards:
    fc = FullCard(c)
    if fc != None:
      fullCardList.append(fc)
  return fullCardList

def findCards(request, page):
  tagsString = ''
  mycardsonly = True
  settings = request.user.get_profile()
  if request.GET.__contains__('tags') and request.GET['tags'].strip() != '':
    tagsString = request.GET['tags'].strip()
    #tags = tagListClean(tagsString)
    if request.GET.__contains__('mycardsonly'):
      weightedSet = filterCardsBySearchablesAndSettings(tagsString, settings, request.session)
    else:
      mycardsonly = False
      weightedSet = filterCardsBySearchables(tagsString, request.session)
    cards = weightedSet.getPkList()
  else:
    if not request.GET.__contains__('mycardsonly') and request.GET.__contains__('tags'):
      mycardsonly = False
      cards = pklist(Card.objects.filter(private=False, original=True).only('pk'))
    else:
      cards = pklist(Card.objects.filter(settings=settings).only('pk'))
  return (cards[page*CARDS_PER_PAGE:(page+1)*CARDS_PER_PAGE], tagsString, mycardsonly)
  
@login_required
def myCardsAjax(request):
  cards = []
  if request.method == 'POST' and request.POST.__contains__('page'):
    page = int(request.POST['page'])
    (cards, tagsString, mycardsonly) = findCards(request, page)
    cards = map(lambda a: a.__as_dict__(), generateFullCardListFromPkList(cards))
  return HttpResponse(json.dumps(cards), mimetype='applications/javascript')
  
def copyCards(cards):
  newcards = []
  for pk in cards:
    fcard = fullCardFromPk(pk)
    card = fcard.card
    tagField = ",".join(fcard.tagList)
    newcard = createCard(None, card['front'], card['back'], card['private'], card['priority'], card['donottest'], tagField, fcard.sourceList, None, True)
    newcards.append(newcard.pk)
  return newcards
  
@login_required
def createShareSet(request):
  settings = request.user.get_profile()
  response = {}
  if request.POST.__contains__('cards[]'):
    cards = request.POST.getlist('cards[]')
    newcards = copyCards(cards)
    sset = ShareSet(cards=newcards, settings=settings)
    sset.save()
    response['url'] = '/viewSet/' + str(sset.pk)
  return HttpResponse(json.dumps(response), mimetype='applications/javascript')

def viewShareSet(request, pk):
  settings = None
  if request.user.is_authenticated():
    settings = request.user.get_profile()
  shareSet = ShareSet.objects.get(pk=pk)
  logging.info(shareSet.cards)
  cards = generateFullCardListFromPkList(shareSet.cards)
  cardForm = CardForm()
  request.session['viewSet'] = pk

  return render_to_response('flashcards/myCards.html', {
      'shareSet': shareSet,
      'cards': cards,
      'settings': settings,
      'cardform': cardForm,
      'mycardsonly': True,
      'suggestedTags': [],
      'tagsString': "",
      'selectedCards': [],
    }, context_instance=RequestContext(request)
  )
  
# TODO REMOVE DUPLICATION WITH ABOVE METHOD
@login_required
def myCards(request):
  settings = request.user.get_profile()
  (cards, tagsString, mycardsonly) = findCards(request, 0)
  
  # add already Selected Cards to this grouping
  selectedCards = []
  if request.session.__contains__('searchCards'):
    selectedCards = request.session['searchCards']
    cards.extend(set(selectedCards) - set(cards))
    request.session['searchCards'] = []
  cards = generateFullCardListFromPkList(cards)
  cardForm = CardForm()
  
  # calculate some Suggested Tags for this user
  suggestedTags = []
  searchLogs = SearchLog.objects.filter(settings=settings).order_by('-date')
  try:
    suggestedTags.append(searchLogs[0].searchable.name)
    suggestedTags.append(searchLogs[1].searchable.name)
    suggestedTags.append(searchLogs[2].searchable.name)
  except:
    pass
  try:
    sTags = SuggestedTags.objects.filter(settings=settings)[0]
    suggestedTags.append(sTags.highestOccuringTag.name)
  except:
    pass
  
  return render_to_response('flashcards/myCards.html', {
      'cards': cards,
      'settings': settings,
      'cardform': cardForm,
      'mycardsonly': mycardsonly,
      'suggestedTags': set(suggestedTags),
      'tagsString': tagsString,
      'selectedCards': selectedCards,
    }, context_instance=RequestContext(request)
  )
  
def sendSessionCards(request):
  if request.method == 'POST':
    post = request.POST
    request.session['searchCards'] = []
    session = request.session['searchCards']
    for card in post:
      session.append(int(card))
    logging.info(session)
  return HttpResponse('')
  
# non ajaxified for oldest browsers
#TODO AJAXIFY
@login_required
def copyCard(request, pk):
  settings = request.user.get_profile()
  card = get_object_or_404(Card, pk=pk)
  if card.settings == settings:
    return HttpResponse('Already have card') #TODO Fancify later on
  cardTags = CardTagView.objects.filter(card=card)
  newCard = Card.objects.create(original=False, front=card.front, back=card.back, settings=settings, nextTest=datetime.date.today()) #TODO - if theres time, make a method that copies all attrs
  for cardTag in cardTags:
    newCardTagView = CardTagView.objects.create(tag=cardTag.tag, card=newCard)
  return HttpResponse('Card successfully added to your collection')
  
# non ajaxified for oldest browsers
#TODO AJAXIFY
@login_required
def removeCard(request, pk):
  settings = request.user.get_profile()
  card = get_object_or_404(Card, pk=pk, settings=settings)
  card.delete()
  return HttpResponse('Card successfully removed from your collection')

@login_required
def myTags(request):
  settings = request.user.get_profile()
  tags = CardTagView.objects.filter(denormalized_card_settings=settings)
  return render_to_response('flashcards/myTags.html', {
      'tags': tags,
    }, context_instance=RequestContext(request)
  )
  
@login_required
def addCardBookmarklet(request):
  cardForm = CardForm()
  if request.method == 'GET':
    get = request.GET
    gcontains = get.__contains__
    if gcontains('back'):
      cardForm.setBack(get['back'])
    if gcontains('src'):
      cardForm.setSource(get['src'])
    if gcontains('title'):
      cardForm.setFront(get['title'])
    
  return render_to_response('flashcards/addCardBookmarklet.html', {
    'cardform': cardForm,
    }, context_instance=RequestContext(request)
  )
  
BYTE_LIMIT = 1000
  
def addHtmlForSource(request):
  logging.info("addHtmlForSource")
  if request.method == 'POST' and request.POST.__contains__('pk'):
    try:
      pk = request.POST['pk']
      source = get_object_or_404(CardSourceView, pk=pk)
      url = source.searchable.name.strip()
      if re.search(r'^https?:\/\/', url) == None:
        url = 'http://' + url
      rpc = urlfetch.create_rpc(deadline=10)
      urlfetch.make_fetch_call(rpc, url)
      data = rpc.get_result().content
      soup = BeautifulSoup(data).get_text(' ')
      source.text = re.sub(r'[^ \n\t\s].*[=+@#\$%\^&\*].*[^ \n\t\s]|[!@#\$%\^&\*\(\)\{\}\[\]\_+=:;\"\',<\.>?/`~]', '', soup)
      source.save()
      logging.info("Text found")
    except:
      pass
  return HttpResponse('')