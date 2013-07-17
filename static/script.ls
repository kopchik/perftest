cursorX = 100
cursorY = 100

document.onmousemove = !(e) ->
  cursorX := e.pageX
  cursorY := e.pageY

export showpic = !(path) ->
  ($ \#image)[0].src = path
  ($ \#image).css {left:cursorX+15, top:cursorY+15, display: "block"}

export hidepic = ->
  ($ \#image).css {display: "none"}


# var cursorX;
#var cursorY;
#document.onmousemove = function(e){
#  cursorX = e.pageX;
#  cursorY = e.pageY;
#}
#
#function showpic(path){
#  $("#image")[0].src = path;
#  $("#image").css({left:cursorX+5, top:cursorY+5, display: "block"});
#}
#
#function hidepic() {
#  $("#image").css({display: "none"});
#}