(function(){
  var cursorX, cursorY, showpic, hidepic, out$ = typeof exports != 'undefined' && exports || this;
  cursorX = 100;
  cursorY = 100;
  document.onmousemove = function(e){
    cursorX = e.pageX;
    cursorY = e.pageY;
  };
  out$.showpic = showpic = function(path){
    $('#image')[0].src = path;
    $('#image').css({
      left: cursorX + 15,
      top: cursorY + 15,
      display: "block"
    });
  };
  out$.hidepic = hidepic = function(){
    return $('#image').css({
      display: "none"
    });
  };
}).call(this);
