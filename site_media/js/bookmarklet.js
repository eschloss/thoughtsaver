
function finalizeNewCard(newcard_div, front, back, tagField, priv, priority, donottest, pk, source1, source2) {
  window.close();
}

// block or replace existing functions
function setupAlreadySelectedCards() {}
function setupSearchForm() {}
function setupSuggestedTag() {}
function setupCopyCard() {}
function setupTrEllipses() {}
function setupSelectAllNone() {}
function setupRemoveCards() {}
function setupOldCard() {}
function setupToolbar() {}
function resetInitialValues(firstTime) {
  var newcard_div = $('.newcard');
  var front = newcard_div.find('input[name=front]');
  var back = newcard_div.find('textarea[name=back]');
  var source1 = newcard_div.find('input[name=source1]');
  var source2 = newcard_div.find('input[name=source2]');
  var tagField = newcard_div.find('input[name=tagField]');
  if (front.val() == '') front.val(MYCARDS.initial.front).addClass('example');
  if (back.val() == '') back.val(MYCARDS.initial.back).addClass('example');
  if (source1.val() == '') source1.val(MYCARDS.initial.source).addClass('example');
  if (source2.val() == '') source2.val(MYCARDS.initial.source).addClass('example');
  if (tagField.val() == '') tagField.val(MYCARDS.initial.tagField).addClass('example');
}
