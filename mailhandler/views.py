from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
import logging
from django.views.decorators.csrf import csrf_exempt
from google.appengine.api import mail
from google.appengine.api import taskqueue
from django.core.mail import EmailMultiAlternatives
import re, logging, datetime
from flashcards.models import *
from accounts.models import Settings
from django.template.loader import render_to_string
from flashcards.testViews import getDailyCards
from flashcards.views import createCard
from django.contrib.auth.models import User

@csrf_exempt    
def emailToCard(request):
  if request.POST:
    message = mail.InboundEmailMessage(request.raw_post_data)
    logging.info("Email To Card from " + message.sender)
    (front, back, settings, fields) = parseEmail(message)
    if settings != None:
      createCardFromEmail(front, back, settings, fields)
  return HttpResponse('ok')

# TODO - lots of duplication btw tags & sources, consolidate these
def parseTags(tags):
  tags = tags[2:len(tags)]
  tags = tags.split(',')
  return map(lambda x: x.strip(), tags)

#TODO - this depends on how to deal with sources
def parseSources(sources):
  sources = sources[2:len(sources)]
  sources = sources.split(',')
  return map(lambda x: x.strip(), sources)
  
LINE_HANDLER = {
  's:': parseSources,
  't:': parseTags,
}

def parseEmail(message):
  sender = re.sub(r'^.*<|>.*$', '', message.sender)
  users = User.objects.filter(email=sender)
  if users.count() > 0:
    settings = users[0].get_profile()
    front = message.subject
    plaintext_bodies = message.bodies('text/plain')
    #bodyLines = plaintext_bodies.split('\n')
    back = []
    fields = {
      't': [], #tags
      's': [], #sources
    }
    for l in plaintext_bodies: #bodyLines:
      lines = l[1].decode().split('\n')
      for l in lines:
        l = l.strip()
        if LINE_HANDLER.__contains__(l[0:1]):
          fields[l[0]] = LINE_HANDLER[l[0:1]](l)
        else:
          back.append(l)
      return (front, "\n".join(back), settings, fields)
  return (None, None, None, None)

def createCardFromEmail(front, back, settings, fields):
  tagField = ", ".join(fields['t'])
  sourceField = ", ".join(fields['s'])
  card = createCard(settings, front, back, False, 'a', False, tagField, sourceField, None)

#Cron job to run once a day
def sendDailyTests(request):
  settings = Settings.objects.filter(denormalized_nextTest__lte=datetime.date.today(), receiveEmail=True)
  logging.info("Daily Email Reminders: %s sent" % (str(len(settings))))
  
  for setting in settings:
    taskqueue.add(url="/mailhandler/sendDailyTest", params={'settings': setting.pk })
  return HttpResponse('success')

#task queue
def sendDailyTest(request):
  if request.method == 'POST' and request.POST.__contains__('settings'):
    settings = Settings.objects.get(pk=request.POST['settings'])
    user = settings.user
    subject, from_email, to = 'ThoughtSaver Daily Test', 'thoughtsaver9@gmail.com', user.email
    text_content = "To take today's test go to http://thoughtsaver0.appspot.com/dailyTest"
    cards = getDailyCards(settings)
    if len(cards) > 0:
      html_content = render_to_string('test/innerTest.html', { 'cards': cards, 'extraBreaks': True, })
      msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
      msg.attach_alternative(html_content, "text/html")
      try:
        msg.send()
        logging.info("Daily Email: %s" % (from_email))
      except:
        logging.error("Invalid Email for user %s (pk=%s)" % (user.username, user.pk))
  return HttpResponse('success')
    
