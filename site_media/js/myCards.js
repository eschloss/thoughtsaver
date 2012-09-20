var MYCARDS = {
  newForm: null,
  PROCESSING_ERROR_TEXT: 'Unable To Process this card.',
  INVALID_CARD_TEXT: 'Back may not be left blank',
  errorTD: $('<td></td>'),
  initial: {
    front: ' front of flashcard',
    back: ' back of flashcard',
    tagField: ' tag 1, tag 2, ...',
    source: ' source'
  },
  PIXELS_IN_DASH: 8,
  boxheight: 45,
  page: 0
};
MYCARDS.errorTD.addClass('errorTD');

function cloneErrorTD(newcard_div, text) {
  if (newcard_div.find('.errorTD').length == 0) {
    newcard_div.append(MYCARDS.errorTD.clone());
  }
  newcard_div.find('.errorTD').text(text);
}

function valueOrBlank(element) {
  if (element.hasClass('example')) {
    return '';
  }
  return element.val();
}

function newCardAjax(newcard_div) {
  var front = newcard_div.find('textarea[name=front]');
  var back = newcard_div.find('textarea[name=back]');
  var tagField = newcard_div.find('input[name=tagField]');
  var source1 = newcard_div.find('input[name=source1]');
  var source2 = newcard_div.find('input[name=source2]');
  var priv = newcard_div.find('input[name=private]');
  var donottest = newcard_div.find('input[name=donottest]');
  var priority = newcard_div.find('input[name=priority]:checked');
  if ($.trim(back.val()) == '') {
    cloneErrorTD(newcard_div, MYCARDS.INVALID_CARD_TEXT);
    return false;
  } else {
    cloneErrorTD(newcard_div, '');
  }
  
  if (newcard_div.data('tries') == null) {
    newcard_div.data('tries', 1);
  } else {
    newcard_div.data('tries', newcard_div.data('tries') + 1);
  }
  newcard_div.find('.newcard_add').text('Processing');
  
  var data = {
      'front': valueOrBlank(front),
      'back': valueOrBlank(back),
      'tagField': valueOrBlank(tagField),
      'source1': valueOrBlank(source1),
      'source2': valueOrBlank(source2),
      'private': priv.is(':checked'),
      'priority': valueOrBlank(priority),
      'donottest': donottest.is(':checked')
  };
  if (newcard_div.attr('id') != undefined) {
    data['pk'] = newcard_div.attr('id');
  }
  if (newcard_div.hasClass('copycard')) {
    newcard_div.removeClass('copycard');
    data['copy'] = true;
  }
  
  
  $.ajax({
    type: 'POST',
    url: "/addCard",
    success: function(response) {
      //alert(JSON.stringify(response));
      //TODO NESTED MESS OF IFELSES - FIX!!
      if (response.success == true) {
        finalizeNewCard(newcard_div, front, back, tagField, priv, priority, donottest, response.pk, source1, source2);
      } else {
        if (newcard_div.data('tries') > 2) {
          newcard_div.find('.newcard_add').text('Retry Add Card');
          var errorTD = cloneErrorTD(newcard_div, MYCARDS.PROCESSING_ERROR_TEXT);
          newcard_div.data('retry', true);
        } else {
          newCardAjax(newcard_div);
        }
      }
    },
    data: data,
    dataType: "json"
  });
  return true;
}

function addCardToTable(settings, prepend, front, back, tags, priv, priority, donottest, pk, source1, source2) {
  var li = $("#sampleLi").clone();
  var ul = $('ul');
  if (prepend) {
    ul.prepend(li);
  } else {
    ul.append(li);
  }
  li.attr('id', pk).removeClass('hide');
  li.find('input.pkInput').attr('name', pk);
  li.find('.front').text(front).attr('title', front);
  li.find('.back').text(back).attr('title', back);
  li.find('.tagfield').text(tags).attr('title', tags);
  li.find('.sourcefield').text(source1).append($('<br/>')).append(source2).attr('title', source1).attr('title2', source2);
  li.find('.td_priv').text(priv + "");
  if (priv) {
    li.find('.td_priv').after($("#lock").clone());
  }
  li.find('.td_dnt').text(donottest + "");
  li.find('.td_prior').text(priority).addClass('prior_'+priority);

  if (prepend) { //only show the NEW icon if you are prepending (a new card)
    spanclone = $('<img>', {
      src: '/site_media/img/new.jpg'
    });
    li.find('.extras').append(spanclone);
  }
  
  if (settings == $("#settingspk").val()) {
    li.find('.meta').append('<span class="removecard" name="/removeCard/' +pk+ '">REMOVE CARD</span>');
  } else {
    li.find('.meta').append('<span class="copyCard">ADD CARD</span>');
  }
  
  trEllipsisReset(li);
}

function finalizeNewCard(newcard_div, front, back, tagField, priv, priority, donottest, pk, source1, source2) {
  addCardToTable($("settingspk").val(), true, front.val(), back.val(), tagField.val(), priv.is(":checked"), priority.val(), donottest.is(":checked"), pk, source1.val(), source2.val());

  newcard_div.removeAttr('id');
  newcard_div.find('.newcard_add').text('save card');
  resetInitialValues(false);
}

function truncate(h, amount) {
  if (h.length > amount) {
    return h.substring(0, amount-3)+"..."
  }
  return h
}

function setupNewCard() {
  $('.example').live('focus', function() {
    $(this).empty().val('').removeClass('example');
  });
  
  $('.newcard_add').live('click', function() {
    var newcard_div = $(this).closest('.newcard');
    $('.example').focus();
    var validCard = newCardAjax(newcard_div);
    if (validCard) {
      if (newcard_div.data('retry') != true && newcard_div.attr('id') == undefined) {
        var cloned = MYCARDS.newForm.clone();
        newcard_div.before(cloned);
      
        var priority = cloned.find('input[name=priority]').filter('#id_priority_1').attr('checked', true);
      }
    }
  });
}

function addSearchablesToCard(inputField, id, searchables, url) {
  var text = inputField.attr('title');
  if (inputField.text() != '') {
    text += ', ';
  }
  text += searchables;
  inputField.attr('title', text);
  inputField.text(truncate(text, 25));
  var data = {
    id: id,
    searchables: searchables
  }
  
  $.ajax({
    type: 'POST',
    url: url,
    data: data,
    dataType: "json"
  });
}

function addSourcesToCard(li, sources) {
  var sourceField = li.find('.sourcefield');
  addSearchablesToCard(sourceField, li.attr('id'), sources, '/addSources');
}

function addTagsToCard(li, tags) {
  var tagField = li.find('.tagfield');
  addSearchablesToCard(tagField, li.attr('id'), tags, '/addTags');
}

function removeSearchablesToCard(inputField, id, searchables, url) {
  var text = inputField.attr('title');
  if (inputField.text() != '') {
    text = text.split(",");
    for (i in text) {
      text[i] = text[i].trim();
    }
    text = ","+text.join(",")+",";
    
    searchables2 = searchables.split(",");
    for (i in searchables2) {
      searchables2[i] = searchables2[i].trim();
      text = text.replace(","+searchables2[i]+",", ",");
    }
    text = text.substring(1, text.length-1);
    if (text == ',') text = "";
    
    inputField.attr('title', text);
    inputField.text(truncate(text, 25));
    var data = {
      id: id,
      searchables: searchables
    }
    
    $.ajax({
      type: 'POST',
      url: url,
      data: data,
      dataType: "json"
    });
  }
}

function removeSourcesToCard(li, sources) {
  var sourceField = li.find('.sourcefield');
  removeSearchablesToCard(sourceField, li.attr('id'), sources, '/removeSources');
}

function removeTagsToCard(li, tags) {
  var tagField = li.find('.tagfield');
  removeSearchablesToCard(tagField, li.attr('id'), tags, '/removeTags');
}

function addRemoveTagsSources(inputId, specificFunction) {
  var searchables = $(inputId);
  if (!searchables.hasClass('example') && searchables.val() != '' && searchables.val() != undefined) {
    searchables = searchables.val();
    $('ul input[type=checkbox]:checked').each(function() {
      var li = $(this).closest('li');
      specificFunction(li, searchables);
    });
  }
}

function saveEdits() {
  /* Add tags to selected cards */
  addRemoveTagsSources("#bulk-edit-add-tags", addTagsToCard);

  /* Add sources to selected cards */
  addRemoveTagsSources("#bulk-edit-add-sources", addSourcesToCard);

  /* Remove tags to selected cards */
  addRemoveTagsSources("#bulk-edit-remove-tags", removeTagsToCard);
  
  /* Remove sources to selected cards */
  addRemoveTagsSources("#bulk-edit-remove-sources", removeSourcesToCard);
  
  var selectedPriority = $("#bulk-edit-modify .selected");
  var quizable = $("#bulk-edit-modify input[name=quizable]:checked").val();
  var isprivate = $("#bulk-edit-modify input[name=isprivate]:checked").val();
  if (selectedPriority.size() > 0 || quizable != "" || isprivate != "") {
    priority = $("#bulk-edit-modify input[name=prioritybulk]:checked").val();
    changeCard(priority, quizable, isprivate);
  }
  
  /* change button to SAVED */
  $("#save-edits-text").show().fadeOut(3000);
  
  /* close the dialog box */
  setTimeout('$("#bulk-edit-toolbar").dialog("close");', 1000);
  
}

function changeCard(priority, quizable, isprivate) {
  var data = {};
  if (priority != undefined) data['priority'] = priority;
  if (quizable != '') data['quizable'] = quizable;
  if (isprivate != '') data['isprivate'] = isprivate;
  $('ul input[type=checkbox]:checked').each(function() {
    var li = $(this).closest('tr');
    changeCardAjax(li, data);
  });
}

function changeCardAjax(li, data) {
  data['id'] = li.attr('id');
  $.ajax({
    type: 'POST',
    url: '/changeCard',
    data: data,
    dataType: "json"
  });
}

function setupToolbar() {
  
  $("#save-edits").click(saveEdits);
  /*$('#bulk-tags').click(function() {
    var tags = $("#bulk-tags-input").val()
    $('table tbody input[type=checkbox]:checked').each(function() {
      var tr = $(this).closest('tr');
      addTagsToCard(tr, tags);
    });
  });*/

  $("#bulk-edit-toolbar").hide();
  $("#bulk-edit.activated").live('click', function() {
    $('.tagoptions').show();
    $("#bulk-edit-toolbar").dialog({ position: "center", width: 600, modal:true });
    resetBulkEdit();
  });

  $("#bulk-remove-toolbar").hide();
  $("#bulk-remove.activated").live('click', function() {
    $("#bulk-remove-toolbar").dialog({ position: "center", width: 600, modal:true });
  });
  $('#bulk-remove-button').click(function() {
    $('ul input[type=checkbox]:checked').each(function() {
      var li = $(this).closest('li');
      li.find('.removecard').click();
    });
    $("#bulk-remove-toolbar").dialog('close');
  });
  $('#bulk-remove-toolbar #close-button').click(function() {
    $("#bulk-remove-toolbar").dialog('close');
  });

  $("#bulk-share").hide();
  $("#share.activated").live('click', function() {
    $("#bulk-share").dialog({ position: "center", width: 600, modal:true });
  });
}

function moveOldCardToEditCard(li) {
  var front = li.find('.front').attr('title');
  var back = li.find('.back').attr('title');
  var tags = li.find('.tagfield').attr('title');
  var priority = li.find('.td_prior').text();
  var donottest = li.find('.td_dnt').text() == 'liue';
  var priv = li.find('.td_priv').text() == 'liue';
  var source1 = li.find('.sourcefield').attr('title');
  var source2 = li.find('.sourcefield').attr('title2');
  var newcard = $('.newcard');
  newcard.attr('id', li.attr('id'));
  li.remove();
  
  newcard.find('.example').focus();
  newcard.find('#id_front').val(front);
  newcard.find('#id_back').val(back);
  newcard.find('#id_tagField').val(tags);
  
  newcard.find("#sources-textarea").val(source1 + '\n' + source2);
  newcard.find('#id_source1').val(source1);
  newcard.find('#id_source2').val(source2);
  
  newcard.find('#id_private').prop("checked", priv);
  newcard.find('#id_donottest').prop("checked", donottest);
  newcard.find('.newcard_add').text('save card');
  newcard.find('input[name=priority]').filter('[value=' +priority+ ']').attr('checked', true);
  newcard.find('#priority-ui span:nth-child(' +(6-priority)+ ')').click();
}

/*
function copyCard(tr) {
  var tds = tr.find('td');
  var front = tds.eq(1).attr('title');
  var back = tds.eq(2).attr('title');
  var tags = tds.eq(3).attr('title');
  var priority = tds.eq(5).find('.td_prior').text();
  var donottest = tds.eq(5).find('.td_dnt').text() == 'true';
  var priv = tds.eq(5).find('.td_priv').text() == 'true';
  var source1 = tds.eq(4).attr('title');
  var source2 = tds.eq(4).attr('title2');
  var pk = tr.attr('id');
  tr.remove();
  
  addCardToTable($("#settingspk").val(), true, front, back, tags, priv, priority, donottest, pk, source1, source2);
}
*/

function setupOldCard() {
  $('.oldcard.mycard').live('dblclick', function() {
    $(this).css('position', 'absolute');
    $(this).css('top', $(this).offset().top);
    $(this).find('td').css('width', '200px');
    var li = $(this);
    if ($(this).hasClass('copycard')) {
      moveOldCardToEditCard(li);
      $('.newcard').addClass('copycard');
      $('.newcard').attr('id', '');
      $('.newcard_add').click();
    } else {
      $(this).animate({ top: "250px", opacity: 0.5, fontSize: "2em" }, 500, 'swing', function() {
        moveOldCardToEditCard(li);
      });
    }
  }).live('mousedown', function(e) {
    //if (e.shiftKey) {
    //} 
    if ($(this).hasClass('selectedCard')) {
      $(this).removeClass('selectedCard');
      $(this).find("input[type=checkbox]").attr('checked', false); 
    } else {
      $(this).addClass('selectedCard');
      $(this).find("input[type=checkbox]").attr('checked', true); 
    }
    var selectedCardCount = $(".selectedCard").size()
    var toolbar = $(".bulk-toolbar");
    if (selectedCardCount == 1) {
      toolbar.find(".plural").hide();
      toolbar.find(".singular").show();
    } else {
      $(".selectedCardCount").text(selectedCardCount);
      toolbar.find(".plural").show();
      toolbar.find(".singular").hide();
    }
    if (selectedCardCount > 0) {
      $('.tbutton.off').css('color', '#626262').css('cursor', 'inhereted');
      $('img.off').hide();
      $('img.on').show();
      $('.tbutton.off').addClass("activated");
    } else {
      $('.tbutton.off').css('color', '#d2d2d2').css('cursor', 'default');
      $('img.off').show();
      $('img.on').hide();
      $('.tbutton.off').removeClass("activated");
    }
    
    $('.oldcard.mycard').unbind('mouseover').bind('mouseover', function() {
      if (!$(this).hasClass('selectedCard')) {
        $(this).trigger('mousedown');
      }
    });
    
    $('html').bind('mouseup', function() {
      $('.oldcard.mycard').unbind('mouseover');
      $(this).unbind('mouseup');
    });
  });
  
  setupAlreadySelectedCards();
}

function removeCard(li, url) {
  $.ajax({
    type: 'POST',
    url: url,
    success: function(response) {
      li.remove();
    },
    dataType: "html"
  });
}

function setupRemoveCards() {
  $('.removecard').live('click', function() {
    removeCard($(this).closest('li'), $(this).attr('name'));
  });
}

$(document).ready(function () {
  MYCARDS.newForm = $("li.newcard").clone();
  setupNewCard();
  setupRemoveCards();
  setupOldCard();
  setupToolbar();
  setupButtons();
  setupExporting();
  resetInitialValues(true);
  setupPriorityButtons();
  setupCopyCard();
  setupSuggestedTag();
  setupSelectAllNone();
  setupSearchForm();
  setupMoreButtons();
  setupSharing();
  setupBulkEdit();
  setupSourceTextarea();
  setTimeout('setupTrEllipses();', 100);
});


function resetBulkEdit() {
  $('#bulk-edit-toolbar .tagoptions').show();
  $('[type=radio]').attr('checked', false);
  $('[type=text]').each(function() {
    $(this).blur().addClass('example');
    $(this).val($(this).attr('title'));
  });
}

function setupBulkEdit() {
  /* note. there is duplication to get rid of in the below functions */
  
  
  $(".modify-div [name=quizable][type=radio]").click(function() {
    if ($(this).data('alreadyChecked')) {
      $(this).attr('checked', false).data('alreadyChecked', false);
      $('[name=quizable][type=radio]:hidden').attr('checked', true);
    } else {
      $(this).data('alreadyChecked', true);
    }
  });
  $(".modify-div [name=isprivate][type=radio]").click(function() {
    if ($(this).data('alreadyChecked')) {
      $(this).attr('checked', false).data('alreadyChecked', false);
      $('[name=quizable][type=isprivate]:hidden').attr('checked', true);
    } else {
      $(this).data('alreadyChecked', true);
    }
  });
}

function setupSharing() {
  $("#share").click(function() {
    var cards = [];
    $('ul input[type=checkbox]:checked').each(function() {
      cards.push($(this).attr('name'));
    });
    if (cards.length > 0) {
      $.ajax({
        type: 'POST',
        url: "/createShareSet",
        data: {
          cards: cards
        },
        success: shareSetCreated,
        dataType: "json"
      });
    }
  });
}

TWITTER_URL = 'https://twitter.com/intent/tweet?text='

function shareSetCreated(response) {
  var text = 'I am sharing my flashcards with you on thoughtsaver: http://thoughtsaver0.appspot.com' + response['url'] + '&amp;lang=en';
  text = text.replace(/ /g, '%20').replace(/:/g, '%3A').replace(/\//g, '%2F');
  alert(text);
  $('#twitter-a').attr('href', TWITTER_URL + text);
}


function setupSelectAllNone() {
  $("#select-all-button").click(function() {
    $("li").each(function() {
      if (!$(this).hasClass('selectedCard')) {
        $(this).trigger('mousedown').trigger('mouseup');
      }
    });
    $(this).hide();
    $('#select-none-button').show();
  });
  $("#select-none-button").click(function() {
    $("li").each(function() {
      if ($(this).hasClass('selectedCard')) {
        $(this).trigger('mousedown').trigger('mouseup');
      }
    });
    $(this).hide();
    $('#select-all-button').show();
  });
}

function resetInitialValues(firstTime) {
  var newcard_div = $('.newcard');
  var front = newcard_div.find('textarea[name=front]');
  var back = newcard_div.find('textarea[name=back]');
  var source1 = newcard_div.find('input[name=source1]');
  var source2 = newcard_div.find('input[name=source2]');
  front.val(MYCARDS.initial.front).addClass('example');
  back.val(MYCARDS.initial.back).addClass('example');
  source1.val(MYCARDS.initial.source).addClass('example');
  source2.val(MYCARDS.initial.source).addClass('example');
  if (firstTime) {
    var tagField = newcard_div.find('input[name=tagField]');
    tagField.val(MYCARDS.initial.tagField).addClass('example');
  } else {
    front.focus().click();
  }
}

function setupButtons() {
  $('a.button').each(function() {
    $(this).click(function() {
      $(this).closest('form').submit();
    });
  });
}

$.fn.textHeight = function(){
  var html_org = $(this).html();
  var html_calc = '<span>' + html_org + '</span>'
  $(this).html(html_calc);
  var height = $(this).find('span:first').height();
  $(this).html(html_org);
  return height;
};

function setupTrEllipses() {
  $('li').each(function() {
    trEllipsisReset($(this));
  });
}

// TODO should refactor - sloppy code
function trEllipsisReset(li) {
  li.find('.front,.back,.tagfield,.sourcefield').each(function() {
    var txtheight = $(this).textHeight();
    var divheight = $(this).height();
    while (txtheight > divheight) {
      var text = $(this).text();
      $(this).text(text.substring(0, text.length-4) + '...');
      txtheight = $(this).textHeight();
    }
  });
}

function setupPriorityButtons() {
  $('#priority-ui span, #priority-ui2 span').click(function() {
    var selected = $(this).closest('#priority-ui, #priority-ui2').find('.selected');
    if (selected.size() > 0 && selected.eq(0).text() == $(this).text() && $(this).parent().attr('id') == 'priority-ui2') {
      selected.removeClass('selected');
      $(this).parent().parent().parent().find('input[name=priority], input[name=prioritybulk]').attr('checked', false);
    } else {
      selected.removeClass('selected');
      $(this).addClass('selected');
      var priority = $(this).text();
      $(this).parent().parent().parent().find('input[name=priority], input[name=prioritybulk]').attr('checked', false);
      $(this).parent().parent().parent().find('input[name=priority], input[name=prioritybulk]').filter('[value=' +priority+ ']').attr('checked', true);
    }
  });
  $('#priority-ui span').filter(':nth-child(3)').click();
}

function setupCopyCard() {
  $('.copyCard').live('click', function() {
    $(this).closest('li').addClass('mycard').addClass('copycard').dblclick();
  });
}

function setupSuggestedTag() {
  $('.suggestedTag').click(function() {
    $('input[name=tags]').val($(this).text());
    $('#searchbar_button').click();
  });
  $('.tagoptions').click(function() {
    var tagField = $(this).parent().parent().parent().find('.tagfield input')
    var currentTags = tagField.focus().val();
    if (currentTags == "") {
      tagField.val($(this).text());
    } else {
      tagField.val(currentTags + ", " +$(this).text());
    }
    $(this).hide();
  });
}

function setupSearchForm() {
  $('#searchform').submit(function() {
    var data = $('#cardform').serializeArray();
    
    $.ajax({
      type: 'POST',
      url: "/sendSessionCards",
      data: data,
      dataType: "json"
    });
  });
}

function setupAlreadySelectedCards() {
  var cards = $("#alreadySelectedCards").val().trim();
  if (cards != '') {
    cards = cards.split(' ');
    for (var c in cards) {
      $("#" + cards[c]).trigger('mousedown').trigger('mouseup');
    }
  }
}

function setupMoreButtons() {
  $(window).scroll(function(){
    if  ($(window).scrollTop() == $(document).height() - $(window).height()){
      var url = $("#fullpath").val();
      url = url.replace('myCards', 'myCardsAjax');
      MYCARDS.page++;
      var page = MYCARDS.page;
      
      $.ajax({
        type: 'POST',
        url: url,
        success: function(response) {
          //alert(JSON.stringify(response));
          for (var c in response) {
            var back = response[c].card.back;
            var front = response[c].card.front;
            var priv = response[c].card['private'];
            var priority = response[c].card.priority;
            var donottest = response[c].card.donottest;
            var pk = response[c].card.pk;
            var settings = response[c].card.settings;
            
            var source1 = "";
            var source2 = "";
            switch(response[c].sourceList.length) {
              case 0:
                break;
              case 1:
                source1 = response[c].sourceList[0];
              default:
                source2 = response[c].sourceList[1];
            }
            
            var tagList = response[c].tagList.join(", ");
            
            addCardToTable(settings, false, front, back, tagList, priv, priority, donottest, pk, source1, source2);
          }
        },
        data: {
          page: page
        },
        dataType: "json"
      });
    }
  });
}

function setupExporting() {
  $("#export").click(function() {
    var exportform = $("#export-form");
    var form = $("#cardform").clone();
    form.attr("action", "/export/csv")
    form.attr("target", "_blank");
    form.submit();
  });
}

function  setupSourceTextarea() {
  $('#sources-textarea').live('keyup', function() {
    var text = $(this).val();
    var newlineIndex = text.indexOf('\n');
    if (newlineIndex != -1) {
      $("#id_source1").removeClass('example').val(text.substring(0,newlineIndex));
      $("#id_source2").removeClass('example').val(text.substring(newlineIndex,text.length));
    } else {
      $("#id_source1").removeClass('example').val(text);
      $("#id_source2").removeClass('example').val('');
    }
  });
  
}