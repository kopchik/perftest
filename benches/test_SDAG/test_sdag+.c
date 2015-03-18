//
//  tests.c
//  uSVM+DAG
//
//  Created by Aliaksei Severyn on 4/17/11.
//  Copyright 2011 UNITN. All rights reserved.
//
#include "dag_tree_kernel.h"
#include "svm_common.h"

long elem_counts;


void compute_sdag_plus(DOC *X, dag_model_t *dag, int SAMPLE_SIZE, KERNEL_PARM kernel_parm) {
    double value = 0;
    long runtime_start;
    int i;
    // judy
    kernel_evals = 0;
    elem_counts = 0;
    runtime_start = get_runtime();
    
    
    for (i = 0; i<SAMPLE_SIZE; i++) {
        value += dag_tree_kernel(&kernel_parm,dag, &X[i]);
    } 
    printf("kernel value: %.4f\n",value); 
    printf("time: %.4f\n", ((float)get_runtime() - (float)runtime_start)/100.0 );
    printf("Number of kernel evaluations: %ld\n",kernel_evals);
    printf("Number of loop iterations inside JudySL: %ld\n",elem_counts);
}


void dag_tree_kernel_vs_dag_size(DOC *X, double *Y, long totdoc, int SAMPLE_SIZE, KERNEL_PARM kernel_parm) {
    int i, j, k;
    int nsamples, num_nodes;
    long runtime_start;
    // get the dag over the full training set
    int dag_size[] = {1e+3, 5e+3, 10e+3, 20e+3, 30e+3, 40e+3, 50e+3};
    //    int dag_size[3] = {5e+3, 10e+3, 20e+3};
    
    
    for (j = 0; j< sizeof(dag_size)/sizeof(dag_size[0]); j++) {
        nsamples = dag_size[j]/SAMPLE_SIZE;
        printf("Number of examples: %d\n",dag_size[j]);
        
        dag_model_t *dag;
        
        /* SDAG+ */
        printf("\nSDAG+\n");
        printf("-----\n");
        runtime_start = get_runtime();
        dag = dag_model_new();
        for (i = 0; i<dag_size[j]; i++) {
            dag_insert_tree(dag, &X[i], Y[i]);
        }
        printf("time to insert trees: %.4f\n", ((float)get_runtime() - (float)runtime_start)/100.0 );
        
        compute_sdag_plus(X, dag, SAMPLE_SIZE, kernel_parm);
        
        //        num_nodes = dag_model_stats(dag);
        //        printf("Total number of nodes in dag: %d\n",num_nodes);
        
        printf("\n");
        printf("Number of input trees: \t%d\n", dag->num_trees);	
        printf("Number of input nodes: \t%d\n", dag->num_nodes);
        
        dag_free_model(dag);
        
        printf("================================\n");
        
        
    }
}


int main(int argc, char* argv[]) {
    DOC *X;
	double *Y;
	char trainfile[1024];
    int ntestfiles;
	char **testfiles=NULL;
    int SAMPLE_SIZE = 1000;
    
	
	long totdoc;
	long kernel_cache_size;
	
	LEARN_PARM learn_parm;
	KERNEL_PARM kernel_parm;
    
	/* read input parameters */	
	
    read_input_parameters(argc,argv,trainfile, &testfiles, &ntestfiles ,&verbosity,
                          &kernel_cache_size,&learn_parm, &kernel_parm);
    //
    my_read_examples(trainfile, &X, &Y, &totdoc, kernel_parm);
    dag_tree_kernel_vs_dag_size(X, Y, totdoc, SAMPLE_SIZE, kernel_parm);

    execvp(argv[0], argv);
    return 0;
}
