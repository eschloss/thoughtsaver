from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
import urllib2
from google.appengine.api import urlfetch
from django.utils import simplejson as json
from django.template  import RequestContext
from importing.forms import CSVForm
import cgi
import os
import logging
import gdata.auth
import gdata.spreadsheets.client
import gdata.spreadsheets.data
from importing.models import *
from flashcards.views import createCard
import re
import models, copy

from django.http import HttpResponseRedirect
from google.appengine.api import users
from django.core.urlresolvers import reverse


CONSUMER_KEY = 'thoughtsaver0.appspot.com'
CONSUMER_SECRET = 'AOLa9jxPPIozxRRYDVHHztNZ'
SCOPES = ['https://spreadsheets.google.com/feeds/']

client = gdata.spreadsheets.client.SpreadsheetsClient()

@login_required
def importingOptions(request):
  return render_to_response('importing/importingOptions.html', {}, context_instance=RequestContext(request))
  
@login_required
def csv(request):
  settings = request.user.get_profile()
  if request.method == 'POST':
    csvForm = CSVForm(request.POST, request.FILES)
    if csvForm.is_valid():
      if csvForm.cleaned_data['file'] != None:
        Row.objects.filter(settings=settings).delete()
        commaString = csvForm.files['file'].read()
        commaList = map(lambda a: a.split(','), commaString.split('\n'))
        for row in commaList:
          row = map(lambda a: a.strip(), row)
          Row.objects.create(settings=settings, columns=row)
        return HttpResponseRedirect(reverse(choose_fields, args=['CSV', csvForm.cleaned_data['file']]))
  else:
    csvForm = CSVForm()
  return render_to_response('importing/csv.html', { 'csvForm': csvForm }, context_instance=RequestContext(request))

@login_required
def myGoogleDocs(request):
  settings = request.user.get_profile()
  Row.objects.filter(settings=settings).delete()
  
  access_token = gdata.gauth.AeLoad('ACCESS_TOKEN' + str(request.user.id))
  if not isinstance(access_token, gdata.gauth.OAuthHmacToken):
    return HttpResponseRedirect(reverse(get_oauth_token))


  setup_token(request.user.id)
  # Retrieve the spreadsheet options
  list_feed = 'https://spreadsheets.google.com/feeds/spreadsheets/private/full'
  feed = client.get_feed(list_feed,
                         desired_class=gdata.spreadsheets.data.SpreadsheetsFeed)
  sheets = {}
  for entry in feed.entry:
    sheets[entry.title.text] = re.search(r'spreadsheets/([^/]*)', entry.id.text).group(1)
  return render_to_response('importing/myGoogleDocs.html', { 'sheets': sheets}, context_instance=RequestContext(request))

@login_required
def select_worksheet(request, spreadsheet_id, spreadsheet_title):
  setup_token(request.user.id)
  # Retrieve the worksheet options
  list_feed = 'https://spreadsheets.google.com/feeds/worksheets/%s/private/full' % (spreadsheet_id)
  feed = client.get_feed(list_feed,
                         desired_class=gdata.spreadsheets.data.SpreadsheetsFeed)
  sheets = {}
  for entry in feed.entry:
    sheets[entry.title.text] = re.search(r'worksheets/[^/]*/([^/]*)', entry.id.text).group(1)
  if len(sheets.items()) == 1:
    key, value = sheets.items()[0]
    return HttpResponseRedirect(reverse(import_spreadsheet, args=[spreadsheet_id, value, spreadsheet_title, key]))
  return render_to_response('importing/select_worksheet.html', { 'sheets': sheets, 'spreadsheet_id': spreadsheet_id, 'spreadsheet_title': spreadsheet_title}, context_instance=RequestContext(request))

@login_required
def get_oauth_token(request):
  """Fetches a request token and redirects the user to the approval page."""

  # 1.) REQUEST TOKEN STEP. Provide the data scope(s) and the page we'll
  # be redirected back to after the user grants access on the approval page.
  oauth_callback_url = 'http://%s:%s%s' % (request.META.get('SERVER_NAME'), request.META.get('SERVER_PORT'), reverse(get_access_token))
  request_token = client.GetOAuthToken(SCOPES, oauth_callback_url, CONSUMER_KEY, consumer_secret=CONSUMER_SECRET)
  logging.debug(request_token)

  # When using HMAC, persist the token secret in order to re-create an
  # OAuthToken object coming back from the approval page.
  gdata.gauth.AeSave(request_token, 'REQUEST_TOKEN' + str(request.user.id))

  # Generate the URL to redirect the user to.
  authorization_url = request_token.generate_authorization_url()

  # 2.) APPROVAL STEP.  Redirect to user to Google's OAuth approval page.
  return HttpResponseRedirect(authorization_url)

@login_required
def get_access_token(request):
  """This handler is responsible for fetching an initial OAuth request token,
  redirecting the user to the approval page.  When the user grants access, they
  will be redirected back to this GET handler and their authorized request token
  will be exchanged for a long-lived access token."""
  saved_request_token = gdata.gauth.AeLoad('REQUEST_TOKEN' + str(request.user.id))
  request_token = gdata.gauth.AuthorizeRequestToken(saved_request_token,
                                                      request.build_absolute_uri())

  # 3.) Exchange the authorized request token for an access token
  access_token = client.GetAccessToken(request_token)
  gdata.gauth.AeSave(access_token, 'ACCESS_TOKEN' + str(request.user.id))

  return HttpResponseRedirect(reverse(myGoogleDocs))

def setup_token(id):
  access_token = gdata.gauth.AeLoad('ACCESS_TOKEN' + str(id))
  client.auth_token = gdata.gauth.OAuthHmacToken(
      CONSUMER_KEY, CONSUMER_SECRET,
      access_token.token, access_token.token_secret,
      access_token,
      next=None, verifier=None)

@login_required
def import_spreadsheet(request, spreadsheet_key, worksheet_id, spreadsheet_title, worksheet_title):

  setup_token(request.user.id)

  # Retrieve the "values" projection of the list feed, the most DB-like feed
  list_feed = 'https://spreadsheets.google.com/feeds/list/%s/%s/private/values' % (spreadsheet_key, worksheet_id)
  feed = client.get_feed(list_feed,
                         desired_class=gdata.spreadsheets.data.ListsFeed)

  settings = request.user.get_profile()
  Row.objects.filter(settings=settings).delete()

  # For each row, save it as a datastore entity
  colDict = {}
  for i, row in enumerate(feed.entry):
    rowd = row.to_dict()
    for col in rowd.keys():
      if not colDict.__contains__(col):
        colDict[col] = {}
      colDict[col][i] = rowd[col]
  logging.info("import Dictionary: \n%s" % (colDict))
  colDictKeys = colDict.keys()
  
  for i in range(len(feed.entry)):
    collist = []
    for k in colDictKeys:
      if colDict[k].__contains__(i) and colDict[k][i] != None:
        value = colDict[k][i]
      else:
        value = ''
      collist.append(value)
    Row.objects.create(settings=settings, columns=collist, order=i)
    logging.info("row object: \n%s" % (collist))
  request.session['colNames'] = colDictKeys

  return HttpResponseRedirect(reverse(choose_fields, args=[spreadsheet_title, worksheet_title]))
  
@login_required
def choose_fields(request, spreadsheet_title, worksheet_title):
  backrequired = request.session.__contains__('backrequired')
  if backrequired:
    del request.session['backrequired']
  settings = request.user.get_profile()
  rows = Row.objects.filter(settings=settings).order_by('order')
  max_cols = len(reduce(lambda x,y: x if len(x.columns) > len(y.columns) else y, rows).columns)
  titleTags = [spreadsheet_title,]
  if re.search(r'^Sheet.*', worksheet_title) == None:
    titleTags.append(worksheet_title)
  colNames = None
  if request.session.__contains__('colNames'):
    colNames = request.session['colNames']
  return render_to_response('importing/choose_fields.html', { 'titleTags': ", ".join(titleTags),
                                                             'colNames': colNames, 'rows': rows,
                                                             'max_cols': range(max_cols),
                                                             'spreadsheet_title': spreadsheet_title,
                                                             'worksheet_title': worksheet_title,
                                                             'backrequired': backrequired,
                                                             }, context_instance=RequestContext(request))
  
def removeRows(pklist, settings):
  for pk in pklist:
    try:
      Row.objects.get(settings=settings, pk=pk).delete()
    except:
      continue
  
@login_required
def generate_cards(request, spreadsheet_title, worksheet_title):
  settings = request.user.get_profile()
  fieldList = []
  titleTags = []
  if request.method == 'POST':
    postdata = request.POST
    while postdata.__contains__(str(len(fieldList))):
      fieldList.append(postdata[str(len(fieldList))])
    if not fieldList.__contains__('back'):
      request.session['backrequired'] = True
      return HttpResponseRedirect(reverse(choose_fields, args=[spreadsheet_title, worksheet_title]))
    titleTags = postdata['titleTags'].split(',')
    doNotImportList = postdata.getlist('donotimport')
    removeRows(doNotImportList, settings)
  rows = Row.objects.filter(settings=settings)
  for row in rows:
    front = ''
    back = ''
    tags = []
    tags.extend(titleTags)
    sources = []
    private = False
    donottest = False
    priority = '3'
    for i in range(len(fieldList)):
      # NASTY CODE SMELL - FIX UP TODO
      try:
        field = fieldList[i]
        col = row.columns[i]
        if field == 'front':
          front += col
        elif field == 'back':
          back += col
        elif field == 'tags':
          if col.strip() != '':
            tags.append(col)
        elif field == 'sources':
          if col.strip() != '':
            sources.append(col)
        elif field == 'private':
          private = (col.lower() == 'true' or col.lower() == 'x')
        elif field == 'donottest':
          donottest = (col.lower() == 'true' or col.lower() == 'x')
        elif field == 'priority':
          if col.lower() == '3' or col.lower() == 'average':
            priority = '3'
          elif col.lower() == 'l' or col.lower() == 'low':
            priority = '1'
          elif col.lower() == '5' or col.lower() == 'high':
            priority = '5'
      except:
        continue
    tagField = ", ".join(tags)
    card = createCard(settings, front, back, private, priority, donottest, tagField, sources, None, False)
  return HttpResponse("Saved %s new cards" % (len(rows)))
      
      
  max_cols = len(reduce(lambda x,y: x if len(x.columns) > len(y.columns) else y, rows).columns)
  return HttpResponse('success')
  