#!/usr/bin/env Rscript
good <- read.csv("good", header=FALSE)
good <- setNames(good$V1, good$V2)
bad <- read.csv("bad", header=FALSE)
bad <- setNames(bad$V1, bad$V2)

ns <- c()
r <- c()
for (n in names(good)) {
  v1 <- good[[n]]
  v2 <- bad[[n]]
  #r <- c(r, v2/v1)
  if (v1 == 0 && v2 == 0) {
  next }
  if (n == "task-clock") {
    next }
  r = append(r, v2/v1)
  ns = append(ns, n)
}

pdf(width=20, height=10)
par(las=2, mar=c(3,10,2,2))
barplot(r,
  #xlim=c(0,1.6),
  xlim=c(0,2),
  main="Fastests / Slowest ratio",
  width=c(3),
  names.arg=ns,
  #space=1,
  #ylim=c(0,1.5),
  horiz=T,
  col=c("bisque", "green", "cyan4", "gray", "white"),
  cex.names=1.0)
abline(v=1)

