cursorX = 100
cursorY = 100

document.onmousemove = !(e) ->
  cursorX := e.pageX
  cursorY := e.pageY

export showpic = !(path) ->
  ($ \#image).0.src = path
  ($ \#image).css {left: cursorX+15, \
                  top: cursorY+15, \
                  display: "block"}

export hidepic = !->
  ($ \#image).css {display: "none"}