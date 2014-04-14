cursorX = 100
cursorY = 100

document.onmousemove = !(e) ->
  cursorX := e.pageX
  cursorY := e.pageY

export showpic = !(path) ->
  img = ($ \#image)
  img.0.src = path
  ($ \#image).css {left: cursorX, \
                top: cursorY, \
                display: "block"}
  screen_sizeY = document.body.clientWidth

  cb = !->
    img_sizeY = img[0].clientHeight
    img_posX = cursorX+15
    img_posY = if cursorY + img_sizeY < screen_sizeY
      then cursorY
      else cursorY - img_sizeY
    #alert "OPA " + cursorY + " " + sizeY + " " + img_size_y
  #img.load(cb)

export hidepic = !->
  ($ \#image).css {display: "none"}