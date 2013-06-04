library('lattice')


my.plot <- function(files, output="plots.pdf", breaks="FD") {
  pdf(output)
  for (fname in files) {
    data <- read.csv(fname, header=T)[[1]]
    hist(data, breaks=breaks, col='red', main=fname)
    #xfit <- seq(min(data),max(data),length=40)
    #yfit <- dnorm(xfit,mean=mean(data),sd=sd(data))
    #yfit <- yfit*diff(h$mids[1:2])*length(data)
    #lines(xfit, yfit, col="blue", lwd=2)
  }
}

my.plot(list.files(pattern="*s00*csv"), output="plots_00s.pdf")
my.plot(list.files(pattern="*s03*csv"), output="plots_03s.pdf")


#postscript("hist.pdf", horizontal=FALSE)
#dev.off()
