#!/usr/bin/env Rscript
suppressPackageStartupMessages(library("argparse"))
parser <- ArgumentParser()
parser$add_argument("files", metavar="N", nargs="+",
                    help="an integer for the accumulator")
args <- parser$parse_args()
print(args$files)

results = list()
for (name in args$files) {
  data <- read.csv(name, header=FALSE)
  data <- setNames(data$V1, data$V2)
  results = append(list(results), list(data))
}

# print(results[[2]])
# q()

names <- c()
benches <- c()
r <- c()
for (n in names(results[1])) {
  vref <- results[1][n]
  v2 <- results[2][n]
  #r <- c(r, v2/v1)
  if (vref == 0 && v2 == 0) {
    next }
  if (n == "task-clock") {
    next }
  r = append(r, v2/vref)
  print(v2/vref)
  names = append(names, n)
}

pdf(width=20, height=10)
par(las=2, mar=c(3,10,2,2))
barplot(r,
  #xlim=c(0,1.6),
  xlim=c(0,2),
  main="Fastests / Slowest ratio",
  width=c(3),
  names.arg=names,
  #space=1,
  #ylim=c(0,1.5),
  horiz=T,
  col=c("bisque", "green", "cyan4", "gray", "white"),
  cex.names=1.0)
abline(v=1)

