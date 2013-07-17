var cursorX;
var cursorY;
document.onmousemove = function(e){
  cursorX = e.pageX;
  cursorY = e.pageY;
}

function showpic(path){
  $("#image")[0].src = path;
  $("#image").css({left:cursorX+10, top:cursorY+10, display: "block"});
}

function hidepic() {
  $("#image").css({display: "none"});
}