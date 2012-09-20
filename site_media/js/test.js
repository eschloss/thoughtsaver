var DISPLAY_ANSWER = $('<div></div>', {
  text: 'Show Answer',
  id: 'nextButton'
});

$(document).ready(function () {
  $('input[type=submit]').hide();
  var testcards = $('.testcard');
  testcards.hide();
  testcards.eq(0).show();
  beginTestCard(testcards, 0);
});

function beginTestCard(testcards, i) {
  var card = testcards.eq(i);
  var back = card.find('.back');
  back.hide().before(DISPLAY_ANSWER);
  DISPLAY_ANSWER.click(function() {
    DISPLAY_ANSWER.remove();
    back.show();
  });
  
  card.show().find('input[type=radio]').click(function() { //TODO try .select instead - may be cleaner
    if (testcards.length == i + 1) {
      $('form').submit();
    } else {
      card.hide();
      beginTestCard(testcards, i + 1);
    }
  });
  
  
  
}