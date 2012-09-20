$(document).ready(function() {
  var tagDict = {};
  $('.tag').each(function() {
    if (tagDict[$(this).text()] == undefined) {
      tagDict[$(this).text()] = 1;
    } else {
      tagDict[$(this).text()] += 1;
    }
  });
  var tagcloud = $('#tagcloud');
  for (s in tagDict) {
    var a = $("<a></a>", {
      text: s +" ",
      href: '/myCards?tags=' +escape(s)+ '&mycardsonly=on'
    });
    a.css('font-size', 10+tagDict[s] +"pt");
    tagcloud.append(a);
  }
});