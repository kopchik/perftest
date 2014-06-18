# Version: 1.10
# Date: 2010-09-28 16:55
# modified by: Aliaksei Severyn

# Makefile for SVM-light-TK with uniform sampling algorithm

# Modify the compiler and compiler flags to reflect your platform-specific configuration (set to gcc by default)
CC=gcc
CFLAGS=-Os -fomit-frame-pointer -ffast-math
LD=gcc
LDFLAGS=-Os

SFMTPATH=./SFMT-src-1.3.3

LIBS=-L. -lm                    # used libraries

# provide the path to your judy library location
JUDY_PATH=/home/aliaksei.severyn/opt/judy
JUDY_H=${JUDY_PATH}/include
JUDY_LIB_PATH=${JUDY_PATH}/lib
JUDY_LIB=Judy

CALG_H=${CALG_PATH}/include
CALG_LIB_PATH=${CALG_PATH}/lib
CALG_LIB=calg

SHRD_OBJS=svm_common.o tree_kernel.o tree_manager.o hash-table.o compare-string.o hash-string.o

all: test_sdag test_sdag+ test_usvm

clean: 
	rm -f *.o
	rm -f test_sdag
	rm -f test_sdag+
	rm -f test_usvm

### svm_uniform_sampling

# SDAG - compacts each cutting plane into a dag
test_sdag: ${SHRD_OBJS} dag_tree_kernel.o test_sdag.o 
	$(LD) $(LDFLAGS) $^ -o $@ $(LIBS) -L${JUDY_LIB_PATH} -l${JUDY_LIB}
	
test_sdag.o:
	$(CC) $(CFLAGS) -c test_sdag.c -o $@ -I ${JUDY_H}

test_sdag+: ${SHRD_OBJS} dag_tree_kernel.o test_sdag+.o 
	$(LD) $(LDFLAGS) $^ -o $@ $(LIBS) -L${JUDY_LIB_PATH} -l${JUDY_LIB}
	
test_sdag+.o:
	$(CC) $(CFLAGS) -c test_sdag+.c -o $@ -I ${JUDY_H}
	
test_usvm: ${SHRD_OBJS} test_usvm.o 
	$(LD) $(LDFLAGS) $^ -o $@ $(LIBS) 
	
test_usvm.o:
	$(CC) $(CFLAGS) -c test_usvm.c -o $@ 

dag_tree_kernel.o: dag_tree_kernel.c dag_tree_kernel.h
	$(CC) $(CFLAGS) -c dag_tree_kernel.c -o $@ -I ${JUDY_H}

svm_common.o: svm_common.c svm_common.h kernel.h
	$(CC) $(CFLAGS) -c svm_common.c -o $@
	
tree_manager.o: tree_manager.c svm_common.h kernel.h
	$(CC) $(CFLAGS) -c tree_manager.c -o $@

tree_kernel.o: tree_kernel.c svm_common.h kernel.h
	$(CC) $(CFLAGS) -c tree_kernel.c -o $@

hash-table.o: hash-table.c
	$(CC) $(CFLAGS) -c hash-table.c -o $@
	
compare-string.o: compare-string.c
	$(CC) $(CFLAGS) -c compare-string.c -o $@

hash-string.o: hash-string.c
	$(CC) $(CFLAGS) -c hash-string.c -o $@