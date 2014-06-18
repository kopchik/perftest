//
//  tests.c
//  uSVM+DAG
//
//  Created by Aliaksei Severyn on 4/17/11.
//  Copyright 2011 UNITN. All rights reserved.
//
#include "svm_common.h"

long elem_counts;

void tree_kernel_vs_dag_size(DOC *X, double *Y, long totdoc, int SAMPLE_SIZE, KERNEL_PARM kernel_parm) {
    int i, j, k;
    int nsamples, num_nodes;
    long runtime_start;
    // get the dag over the full training set
    int dag_size[] = {1e+3, 5e+3, 10e+3, 20e+3, 30e+3, 40e+3, 50e+3};
    //    int dag_size[3] = {5e+3, 10e+3, 20e+3};
    long kernel_evals;
    
    for (j = 0; j< sizeof(dag_size)/sizeof(dag_size[0]); j++) {
        nsamples = dag_size[j]/SAMPLE_SIZE;
        printf("Number of examples: %d\n",dag_size[j]);
        
        /* uSVM */  
        printf("\nuSVM\n");
        printf("----\n");
        double value = 0;
        kernel_evals = 0;
        elem_counts = 0;
        runtime_start = get_runtime();
        for (i = 0; i<dag_size[j]; i++) {
             for (k = 0; k<SAMPLE_SIZE; k++) {
                value += Y[i]*kernel(&kernel_parm, &X[k], &X[i]);
            } 
        }        
        printf("kernel value: %.4f\n",value); 
        printf("time: %.4f\n", ((float)get_runtime() - (float)runtime_start)/100.0 );                        
                
        printf("================================\n");
        
        
    }
}


int main(int argc, char* argv[]) {
    DOC *X;
	double *Y;
	char trainfile[1024];
    int ntestfiles;
	char **testfiles=NULL;
    
	
	long totdoc;
	long kernel_cache_size;
	
	LEARN_PARM learn_parm;
	KERNEL_PARM kernel_parm;
    
	/* read input parameters */	
	
	read_input_parameters(argc,argv,trainfile, &testfiles, &ntestfiles ,&verbosity,
                          &kernel_cache_size,&learn_parm, &kernel_parm);
    
	//
	my_read_examples(trainfile, &X, &Y, &totdoc, kernel_parm);
    
    int SAMPLE_SIZE = 1000;
    
    tree_kernel_vs_dag_size(X, Y, totdoc, SAMPLE_SIZE, kernel_parm);
    
    return 0;
}
