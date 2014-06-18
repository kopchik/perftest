/*
 *  dag_tree_kernel.h
 *  testing_c_algs
 *
 *  Created by Aliaksei Severyn on 3/28/11.
 *  Copyright 2011 UNITN. All rights reserved.
 *
 */

#ifndef _DAG_TREE_KERNEL_H
#define _DAG_TREE_KERNEL_H

#include <Judy.h>
#include "hash-table.h"                                                                                                               
#include "hash-string.h"
#include "compare-string.h"

#include "svm_common.h"

#define HASHSIZE (1<<8)

long kernel_evals;

typedef	struct dag_model_s
{
	HashTable *patterns;
	int num_trees;
	int num_nodes;
} dag_model_t;

/* interface to Judy eff functions */

dag_model_t*	dag_model_new();
void			dag_free_model(dag_model_t *dag_model);
int             dag_model_stats(dag_model_t *dag_model);
dag_model_t     *dag_save_model(dag_model_t **S, double *alphas, int size_active);

void			dag_insert_tree(dag_model_t *dag_model, DOC *X, double target);
void			dag_classify(dag_model_t *dag_model, KERNEL_PARM kernel_parm, char *testfile);
void            dag_classify_sdag(dag_model_t **S, int size_active, double* alpha, KERNEL_PARM kernel_parm, char *testfile);

double          dag_tree_kernel(KERNEL_PARM * kernel_parm, dag_model_t *dag_model, DOC *X);
double          vector_linear_kernel(DOC *a, DOC *b);
double          tree_linear_kernel(DOC *a, DOC *b);
double          dag_linear_kernel(dag_model_t *dag_model,    DOC *X);

#endif
