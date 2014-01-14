(function(){
  var cursorX, cursorY, showpic, hidepic, out$ = typeof exports != 'undefined' && exports || this;
  cursorX = 100;
  cursorY = 100;
  document.onmousemove = function(e){
    cursorX = e.pageX;
    cursorY = e.pageY;
  };
  out$.showpic = showpic = function(path){
    var img, screen_sizeY, cb;
    img = $('#image');
    img[0].src = path;
    $('#image').css({
      left: cursorX,
      top: cursorY,
      display: "block"
    });
    screen_sizeY = document.body.clientWidth;
    cb = function(){
      var img_sizeY, img_posX, img_posY;
      img_sizeY = img[0].clientHeight;
      img_posX = cursorX + 15;
      img_posY = cursorY + img_sizeY < screen_sizeY
        ? cursorY
        : cursorY - img_sizeY;
    };
  };
  out$.hidepic = hidepic = function(){
    $('#image').css({
      display: "none"
    });
  };
}).call(this);
