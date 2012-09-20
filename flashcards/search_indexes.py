import search
from search.core import porter_stemmer_non_stop
from flashcards.models import *

search.register(Card, ('front',), indexer=porter_stemmer_non_stop, search_index="front_search")
search.register(Card, ('back',), indexer=porter_stemmer_non_stop, search_index="back_search")
search.register(CardTagView, ('denormalized_searchable_name',), indexer=porter_stemmer_non_stop)
search.register(CardSourceView, ('denormalized_searchable_name'), indexer=porter_stemmer_non_stop, search_index='name_search')
search.register(CardSourceView, ('text'), indexer=porter_stemmer_non_stop, search_index='text_search')