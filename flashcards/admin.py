from flashcards.models import *
from django.contrib import admin

admin.site.register(Card)
admin.site.register(CardTagView)
admin.site.register(CardSourceView)
admin.site.register(Searchable)
