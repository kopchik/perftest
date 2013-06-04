library('lattice')


my.plot <- function(files, output="plots.pdf", breaks="FD") {
  pdf(output)
  for (fname in files) {
    data <- read.csv(fname, header=T)[[1]]
    h <- hist(data, breaks=breaks, col='red', main=fname)
    # fit
    xfit <- seq(min(data),max(data),length=40)
    yfit <- dnorm(xfit,mean=mean(data),sd=sd(data))
    yfit <- yfit*diff(h$mids[1:2])*length(data)
    lines(xfit, yfit, col="blue", lwd=2)
  }
  dev.off()
}

my.plot(files=list.files(pattern="s0_.*csv"), output="plots_00s.pdf", breaks=20)
my.plot(files=list.files(pattern="s03_.*csv"), output="plots_03s.pdf", breaks=20)


#postscript("hist.pdf", horizontal=FALSE)
