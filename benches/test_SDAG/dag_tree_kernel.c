//
//  Jdag_tree_kernel.c
//  perceptron+DAG
//
//  Created by Aliaksei Severyn on 4/12/11.
//  Copyright 2011 UNITN. All rights reserved.
//


#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <libgen.h>
#include "Judy.h"

#include "svm_common.h"

#include "dag_tree_kernel.h"

#define HASHSIZE (1<<8)

Pvoid_t PJcache[HASHSIZE];

extern long elem_counts;
//extern Pvoid_t PJcache[HASHSIZE]; // local cache used by sequential alg

//static HashTable *cache;
int NELEM = 1;
static double REMOVE_LEAVES = 0; 
/* struct for linked list implementation */
typedef struct dag_entry_s
{
	TreeNode *node;
	double freq;
    struct dag_entry_s *next;
} dag_entry_t;

typedef struct elem_s{
    double freq;
    TreeNode *node;	
} elem_t;

/* struct for array list implementation */
typedef struct dag_array_entry_s
{
	elem_t *elem;
    double linear_sum;
    int length;
    int maxsize;
} dag_array_entry_t;


/* forward declarations */

void arraylist_insert_node(dag_array_entry_t *list, TreeNode *node, double freq);
void my_read_examples(char *inputfile, DOC **X, double **Y, 
                      long *totdoc, KERNEL_PARM kernel_parm);

/* GSST kernel */
static double dag_tree_kernel_GSST(dag_model_t *dag_model, DOC *X);
static double dag_count_GSST(const TreeNode *Nx, const TreeNode *Nz);

/* SST kernel */
static double dag_tree_kernel_SST(dag_model_t *dag_model, DOC *X);
static double dag_count_SST(const TreeNode *Nx, const TreeNode *Nz);

/* PT kernel */
static double dag_tree_kernel_PT(dag_model_t *dag_model, DOC *X);
static double dag_Delta_PT( TreeNode * Nx, TreeNode * Nz);


static dag_entry_t* dag_entry_new()
{
	dag_entry_t *dag_entry;
	dag_entry = my_malloc(sizeof(dag_entry_t));
	dag_entry->freq = 1;
    dag_entry->next = NULL;
	return dag_entry;
}

static dag_array_entry_t* dag_array_entry_new()
{
	dag_array_entry_t *dag_array_entry;
	dag_array_entry = my_malloc(sizeof(dag_array_entry_t));
	dag_array_entry->elem = my_malloc(sizeof(elem_t)*NELEM);
    dag_array_entry->length = 0;
    dag_array_entry->maxsize = NELEM; 
    dag_array_entry->linear_sum = 0;
	return dag_array_entry;
}

/* Create a new key */
static unsigned long *new_key(unsigned long value)
{
	unsigned long *result;
	
	result = my_malloc(sizeof(unsigned long));
	*result = value;
	
	return result;
}

/* Create a new value */
static double *new_value(double value)
{
	double *result;
	
	result = my_malloc(sizeof(double));
	*result = value;
	
	return result;
}

static unsigned long my_hash(void *vlocation)
{
	unsigned long *location;
	
	location = (unsigned long *) vlocation;
	
	return (unsigned long) *location;
}

//static int my_equal(void *vlocation1, void *vlocation2)
//{
//	unsigned long *location1;
//	unsigned long *location2;
//	
//	location1 = (unsigned long *) vlocation1;
//	location2 = (unsigned long *) vlocation2;
//	
//	return *location1 == *location2;
//}
//
//const unsigned short int my_equal_arr(const void *a,const void *b)
//{
//	dag_entry_t *aa = (dag_entry_t*)a;
//	dag_entry_t *bb = (dag_entry_t*)b;
//	
//	return aa->node->hash == bb->node->hash;
//}

// =============================================================
dag_model_t* dag_model_new()
{
	dag_model_t* dag_model = my_malloc(sizeof(dag_model_t));
    
	HashTable* patterns = hash_table_new(string_hash,string_equal);
	hash_table_register_free_functions(patterns, NULL, NULL); // we keep pointers to the keys, but we still need to free the set stored in the value
	
	dag_model->patterns = patterns;
	dag_model->num_trees = 0;
	dag_model->num_nodes = 0;
	return dag_model;
}



//void _dag_free_model(dag_model_t *dag_model)
//{
//	HashTableIterator itr_patterns;
//	dag_entry_t **list, *ptr, *tmp;
//    KeyValuePair_t *bck;
//    
//	hash_table_iterate(dag_model->patterns, &itr_patterns);
//    
//	while (hash_table_iter_has_more(&itr_patterns)) {
//        bck = hash_table_iter_next(&itr_patterns);
//		list = bck->value;
//        ptr = *list;
//        while (ptr) {
//            tmp = ptr->next;
//            free(ptr);
//            ptr = tmp;
//        }
//	}
//	hash_table_free(dag_model->patterns);
//	free(dag_model);
//}

/* array */
void dag_free_model(dag_model_t *dag_model)
{
	HashTableIterator itr_patterns;
	dag_array_entry_t *list;
    KeyValuePair_t *bck;
    
	hash_table_iterate(dag_model->patterns, &itr_patterns);
    
	while (hash_table_iter_has_more(&itr_patterns)) {
        bck = hash_table_iter_next(&itr_patterns);
		list = (dag_array_entry_t*)bck->value;
        free(list->elem);
//        free(list->node_array);
//        free(list->freq_array);
        free(list);
    }
	hash_table_free(dag_model->patterns);
	free(dag_model);
}

static void dag_model_extend(dag_model_t *model, dag_model_t *model_ext, double alpha){
    int i, len_ext;
    elem_t *elem, *elem_ext;
    HashTableIterator itr_patterns;
    char *key_patterns_ext;
    KeyValuePair_t *bck;
    dag_array_entry_t *list, *list_ext;    
    
    // iterate through all the entries in model_ext->patterns
    hash_table_iterate(model_ext->patterns, &itr_patterns);
    while (hash_table_iter_has_more(&itr_patterns)) {
        bck = hash_table_iter_next(&itr_patterns);
        key_patterns_ext = (char*)bck->key;
		list_ext = (dag_array_entry_t*)bck->value;
        len_ext = list_ext->length;
        elem_ext = list_ext->elem;
        if ( (list = hash_table_lookup(model->patterns, key_patterns_ext)) == NULL ) { // add a missing entry to the model->patterns
            list = my_malloc(sizeof(dag_array_entry_t));            

            list->elem = my_malloc(sizeof(elem_t)*len_ext);
            list->length = len_ext;
            list->maxsize = len_ext; 
            
            elem = list->elem;
            for (i=0; i < len_ext; i++){
                elem[i].node = elem_ext[i].node;
                elem[i].freq = alpha * elem_ext[i].freq;
            }
            hash_table_insert(model->patterns, key_patterns_ext, list);
        }
        else {   
            for (i=0; i<len_ext; i++){
                arraylist_insert_node(list, elem_ext[i].node, alpha * elem_ext[i].freq);                
            }            
        } // if ( (list = hash_table_lookup(model->patterns, key_patterns_ext)) == NULL )
    } // while (hash_table_iter_has_more(&itr_patterns))
    
    model->num_nodes += model_ext->num_nodes;
    model->num_trees += model_ext->num_trees;
}


dag_model_t *dag_save_model(dag_model_t **S, double *alphas, int size_active){
    int j;
    dag_model_t *full_model = dag_model_new();
    
    for (j = 0; j<size_active; ++j)
        if (alphas[j] > 1e-8)
            dag_model_extend(full_model, S[j], alphas[j]);
    
    return full_model;
}

/* linked list */

//void _dag_insert_tree(dag_model_t *dag_model, DOC *X, double target)
//{	
//	int i,j;
//	dag_entry_t **list;
//	TreeNode *node;
//	FOREST *tree_forest;
//    dag_entry_t *node_dag, *ptr;
//	for (j=0; j<X->num_of_trees; j++) {
//		tree_forest = X->forest_vec[j];
//		for (i=0; i<tree_forest->listSize; i++) {
//            node = tree_forest->orderedNodeSet[i].node;
//            // insert the production of the node into patterns hashtable: dag_model->patterns[node->production] = node->hash
//			if ((list = hash_table_lookup(dag_model->patterns, node->production) ) == NULL) {                					
//                list = my_malloc(sizeof(dag_entry_t*));
//                node_dag = dag_entry_new();
//                node_dag->node = node;
//                node_dag->freq = target/sqrt(tree_forest->twonorm_PT);
//                *list = node_dag;
//                
//                hash_table_insert(dag_model->patterns, node->production, list);
//            }
//            else { // the same production is already in patterns
//                
//                for (ptr = *list; ptr!=NULL; ptr = ptr->next){
//                    if (ptr->node->hash == node->hash) {
//                        ptr->freq += target/sqrt(tree_forest->twonorm_PT);
//                        break;
//                    }                        
//                }
//                if (ptr==NULL) { // not found, insert this node into the list;
//                    node_dag = dag_entry_new();
//                    node_dag->node = node;
//                    node_dag->freq = target/sqrt(tree_forest->twonorm_PT);
//                    
//                    node_dag->next = *list;
//                    *list = node_dag;
//                }              
//            }
//            dag_model->num_nodes++;
//        } // for (i=0; i<tree_forest->listSize; i++)
//        dag_model->num_trees++;
//	} // for (j=0; j<X->num_of_trees; j++)
//}

void arraylist_insert_node(dag_array_entry_t *list, TreeNode *node, double freq){
    int k, len;
    elem_t *elem;
    
    len = list->length;
    elem = list->elem;
    for (k = 0; k<len; k++){ // search for a node in the list
        if (elem[k].node->hash == node->hash) {
            elem[k].freq += freq;
            break;
        }
    }
    if (k == len){ // no such node in the list
        if (k == list->maxsize){ // the list is full -> expand it
            //                        list->maxsize += (len >> 3) + (len < 9 ? 3 : 6);
            list->maxsize += NELEM;
            elem = realloc(elem, sizeof(elem_t)*list->maxsize);
            list->elem = elem;
        }
        elem[len].node = node;
        elem[len].freq = freq;
        list->length++;
    }
}

/* array */
void dag_insert_tree(dag_model_t *dag_model, DOC *X, double target)
{	
	int i,j;
	dag_array_entry_t *list;
	TreeNode *node;
	FOREST *tree_forest;
    elem_t *elem;
    
	for (j=0; j<X->num_of_trees; j++) {
		tree_forest = X->forest_vec[j];
		for (i=0; i<tree_forest->listSize; i++) {
            node = tree_forest->orderedNodeSet[i].node;
            // insert the production of the node into patterns hashtable: dag_model->patterns[node->production] = node->hash
			if ((list = hash_table_lookup(dag_model->patterns, node->production) ) == NULL) {                					
                list = dag_array_entry_new();
                elem = list->elem;
                elem[0].node = node;
                elem[0].freq = target/sqrt(tree_forest->twonorm_PT);
                list->linear_sum += target/sqrt(tree_forest->twonorm_PT);
                list->length++;
                hash_table_insert(dag_model->patterns, node->production, list);
            }
            else { // the same production is already in patterns
                list->linear_sum += target/sqrt(tree_forest->twonorm_PT);
                arraylist_insert_node(list, node, target/sqrt(tree_forest->twonorm_PT));
            }
            dag_model->num_nodes++;
        } // for (i=0; i<tree_forest->listSize; i++)
        dag_model->num_trees++;
	} // for (j=0; j<X->num_of_trees; j++)
}


double dag_tree_kernel(KERNEL_PARM* kernel_parm, dag_model_t *dag_model, DOC *X)
{
//	printf("%ld\n",kernel_parm->first_kernel);
	switch(kernel_parm->first_kernel) {			
		case  -1: 
			return dag_linear_kernel(dag_model, X); // productions kernel

		case  1: 
			SIGMA = 1;
			return dag_tree_kernel_SST(dag_model, X); // SST kernel (Collins and Duffy, 2002)
			
		case  2: 
			return dag_tree_kernel_GSST(dag_model, X); // SST kenel + bow kernel on leaves, 

        case  3: 
            REMOVE_LEAVES=0;
			return dag_tree_kernel_PT(dag_model, X); // PT kenel

        case  4: 
            REMOVE_LEAVES=MU*LAMBDA2;
			return dag_tree_kernel_PT(dag_model, X); // PT kenel    
            
		default:  
			printf("\nERROR: Tree Kernel number %ld not available \n\n",kernel_parm->first_kernel);
			fflush(stdout);
			exit(-1);
	}
	
	return 0;
}

double vector_linear_kernel(DOC *a, DOC *b) {
    return sprod_ss(a->vectors[0]->words,b->vectors[0]->words);
//    return sprod_ss(a->vectors[0]->words,b->vectors[0]->words)/sqrt(a->forest_vec[0]->twonorm_PT * b->forest_vec[0]->twonorm_PT);               
//                  /sqrt(a->vectors[0]->twonorm_STD * b->vectors[0]->twonorm_STD);
    
}

/*
double tree_linear_kernel(DOC *a, DOC *b) {
    return productions_kernel(a, b);
    
}
*/

//double _dag_tree_kernel(dag_model_t *dag_model, DOC *X)
///* uses local cache that is passed to dag_count to allow for thread-safety. */
///* use it only in the parallel version */
//{
//	int i,j,k;
//	TreeNode *node;
//	FOREST *tree_forest;
//    //	Pvoid_t *value_patterns;
//    dag_entry_t **value_patterns;
//	double sum = 0;
//	double kernel_value;
//    dag_entry_t **node_dag, *ptr;
//    Word_t Rc_int;
//    
//    /* init local cache */
//        
//	for (j=0; j<X->num_of_trees; j++) {
//		tree_forest = X->forest_vec[j];
//		
//        kernel_value = 0.0;
//		for (i=0; i<tree_forest->listSize; i++){
//            node = tree_forest->orderedNodeSet[i].node;
//			if ((value_patterns = hash_table_lookup(dag_model->patterns, node->production)) != NULL){
//                
//                elem_counts++;
//                
//                for (ptr = *value_patterns; ptr!=NULL; ptr = ptr->next){                
//                    //                    kernel_value += ptr->freq * Jdag_count_simple_cache(node, ptr->node); // use Judy
//                    kernel_value += ptr->freq * dag_count_no_cache(node, ptr->node); // use Judy
//                    kernel_evals++;                
//                }
//			}
//		}
//		sum += kernel_value/sqrt(tree_forest->twonorm_PT);
//	}
//	return sum;
//}


void dag_classify(dag_model_t *dag_model, KERNEL_PARM kernel_parm, char *testfile)
{
	long i;
	DOC *X_test;
	double *Y_test;
	double dist, doc_label;
	long totdoc_test;
	FILE *predfl;
	char predictionsfile[200];
    
	long correct=0,incorrect=0,no_accuracy=0;
	long res_a=0,res_b=0,res_c=0,res_d=0;
	double t1,runtime=0;
    
	printf("\n");
	printf("%s",SEP);
	printf("Testing...\n");
	printf("%s",SEP);
	
	my_read_examples(testfile, &X_test, &Y_test, &totdoc_test, kernel_parm);
	
    sprintf(predictionsfile, "%s.predictions", basename(testfile));
    
	if ((predfl = fopen(predictionsfile, "w")) == NULL){ 
		perror(predictionsfile); exit (1); 
	}
	printf("\nClassifying examples...\n");
	for (i=0; i<totdoc_test; i++) {
		if ((i % 100) == 0) {
			printf("%ld..",i);fflush(stdout);
		}
		doc_label = Y_test[i];
		t1 = get_runtime();
		dist = dag_tree_kernel(&kernel_parm, dag_model, &X_test[i]);
		runtime += (get_runtime()-t1);
		
		if(dist>0) {
			if(doc_label>0) correct++; else incorrect++;
			if(doc_label>0) res_a++; else res_b++;
		}
		else {
			if(doc_label<0) correct++; else incorrect++;
			if(doc_label>0) res_c++; else res_d++;
		}
		fprintf(predfl,"%.8g\n",dist);
		freeExample(&X_test[i]);
	}
	free(X_test);
	free(Y_test);
	
	fclose(predfl);
	printf("\n");
    printf("Test file: %s\n",testfile);
	printf("Runtime (without IO) in cpu-seconds: %.2f\n", (float)(runtime/100.0));
	
	if((!no_accuracy) && (verbosity>=1)) {
		float P, R, F1;
		P = (float)(res_a)*100.0/(res_a+res_b);
		R = (float)(res_a)*100.0/(res_a+res_c);
		F1 = (float)(2*P*R)/(P+R);
		printf("Accuracy on test set: %.2f%% (%ld correct, %ld incorrect, %ld total)\n",(float)(correct)*100.0/totdoc_test,correct,incorrect,totdoc_test);
		printf("Precision/recall on test set: %.2f%%/%.2f%%\n",P,R);
		printf("F1-measure on test set: %.2f%%\n",F1);
	}
	printf("\n");	
}

void dag_classify_sdag(dag_model_t **S, int size_active, double* alpha, KERNEL_PARM kernel_parm, char *testfile)
{
	int i,j;
	DOC *X_test;
	double *Y_test;
	double doc_label;
	long totdoc_test;
	FILE *predfl;
	char predictionsfile[200];
    
	long correct=0,incorrect=0,no_accuracy=0;
	long res_a=0,res_b=0,res_c=0,res_d=0;
	double t1,runtime=0;
    
	printf("\n");
	printf("%s",SEP);
	printf("Testing...\n");
	printf("%s",SEP);
	
	my_read_examples(testfile, &X_test, &Y_test, &totdoc_test, kernel_parm);
	
    double *dist = my_malloc(sizeof(double)*totdoc_test);
    
    printf("\nClassifying examples...\n");
    
    
    //    t1 = omp_get_wtime();
    t1 = get_runtime();
	for (i=0; i<totdoc_test; i++) {
        //        printf(".");fflush(stdout);
        dist[i] = 0;
        for (j=0; j<size_active; j++) {
            dist[i] += alpha[j]*dag_tree_kernel(&kernel_parm, S[j], &X_test[i]);
        }
    }
    runtime = get_runtime()-t1;
    //    runtime = omp_get_wtime()-t1;
    printf("Runtime (without IO) in cpu-seconds: %.2f\n", (float)(runtime/100.0));
    //    printf("Runtime (without IO) in cpu-seconds: %.2f\n", runtime);
    
    sprintf(predictionsfile, "%s.predictions", basename(testfile));
    
	if ((predfl = fopen(predictionsfile, "w")) == NULL){ 
		perror(predictionsfile); exit (1); 
	}
	for (i=0; i<totdoc_test; i++) {
		doc_label = Y_test[i];
		
		if(dist[i]>0) {
			if(doc_label>0) correct++; else incorrect++;
			if(doc_label>0) res_a++; else res_b++;
		}
		else {
			if(doc_label<0) correct++; else incorrect++;
			if(doc_label>0) res_c++; else res_d++;
		}
		fprintf(predfl,"%.8g\n",dist[i]);
		freeExample(&X_test[i]);
	}
    free(dist);
	free(X_test);
	free(Y_test);
	
	fclose(predfl);
	printf("\n");
    printf("Test file: %s\n",testfile);
	
	
	if((!no_accuracy) && (verbosity>=1)) {
		float P, R, F1;
		P = (float)(res_a)*100.0/(res_a+res_b);
		R = (float)(res_a)*100.0/(res_a+res_c);
		F1 = (float)(2*P*R)/(P+R);
		printf("Accuracy on test set: %.2f%% (%ld correct, %ld incorrect, %ld total)\n",(float)(correct)*100.0/totdoc_test,correct,incorrect,totdoc_test);
		printf("Precision/recall on test set: %.2f%%/%.2f%%\n",P,R);
		printf("F1-measure on test set: %.2f%%\n",F1);
	}
	printf("\n");	
}

// ---------------------------------
// Productions kernel kernel -F -1
// ---------------------------------

double dag_linear_kernel(dag_model_t *dag_model, DOC *X)
/* uses local cache that is passed to dag_count to allow for thread-safety. */
/* use it only in the parallel version */
{
	int i,j;
	TreeNode *node;
	FOREST *tree_forest;
    dag_array_entry_t *value_patterns;
	double sum = 0.0;
	double kernel_value;
    
	for (j=0; j<X->num_of_trees; j++) {        
		tree_forest = X->forest_vec[j];		
        kernel_value = 0.0;        
		for (i=0; i<tree_forest->listSize; i++){
            node = tree_forest->orderedNodeSet[i].node;
			if ((value_patterns = hash_table_lookup(dag_model->patterns, node->production)) != NULL)                
                kernel_value += value_patterns->linear_sum; // use Judy
		}
		sum += kernel_value/sqrt(tree_forest->twonorm_PT);
	}
    
	return sum;
}

// ---------------------------------
// Sub-set Tree kernel (SST) + leaves kernel -F 2
// ---------------------------------

static double dag_tree_kernel_GSST(dag_model_t *dag_model, DOC *X)
/* uses local cache that is passed to dag_count to allow for thread-safety. */
/* use it only in the parallel version */
{
	int i,j,k;
	TreeNode *node;
	FOREST *tree_forest;
    dag_array_entry_t *value_patterns;
	double sum = 0.0;
	double kernel_value;
    elem_t *elem;
    
	for (j=0; j<X->num_of_trees; j++) {        
		tree_forest = X->forest_vec[j];		
        kernel_value = 0.0;        
		for (i=0; i<tree_forest->listSize; i++){
            node = tree_forest->orderedNodeSet[i].node;
			if ((value_patterns = hash_table_lookup(dag_model->patterns, node->production)) != NULL){                
                elem_counts++;                
                
                elem = value_patterns->elem;
                for (k = 0; k<value_patterns->length; k++){ 
                    kernel_value += elem[k].freq * dag_count_GSST(elem[k].node, node); // use Judy
                    //                    kernel_value += value_patterns->freq_array[k] * dag_count_adv_cache(node, value_patterns->node_array[k]); // use Judy
                    kernel_evals++;                
                }
			}
		}
		sum += kernel_value/sqrt(tree_forest->twonorm_PT);
	}             
    
	return sum;
}

static double dag_count_GSST(const TreeNode *Nx, const TreeNode *Nz){
	int i;
	double prod = 1;
    for(i=0;i<Nx->iNoOfChildren && i<Nz->iNoOfChildren;i++)
        if (Nx->pChild[i]->production != NULL && Nz->pChild[i]->production != NULL &&
            strcmp(Nx->pChild[i]->production,Nz->pChild[i]->production)==0 
            && Nx->pChild[i]->pre_terminal != -1 && Nz->pChild[i]->pre_terminal != -1)
            prod*= (1 + dag_count_GSST( Nx->pChild[i], Nz->pChild[i])); // case 
    return LAMBDA*prod;
}

// ---------------------------------
// Sub-set Tree kernel (SST) kernel -F 1
// ---------------------------------

static double dag_tree_kernel_SST(dag_model_t *dag_model, DOC *X)
/* uses local cache that is passed to dag_count to allow for thread-safety. */
/* use it only in the parallel version */
{
	int i,j,k;
	TreeNode *node;
	FOREST *tree_forest;
    dag_array_entry_t *value_patterns;
	double sum = 0.0;
	double kernel_value;
    elem_t *elem;
    
//    /* init local adv cache */                
//    for (l = 0; l < HASHSIZE; l++) 
//        PJcache[l] = (Pvoid_t)NULL;
    
	for (j=0; j<X->num_of_trees; j++) {        
		tree_forest = X->forest_vec[j];		
        kernel_value = 0.0;        
		for (i=0; i<tree_forest->listSize; i++){
            node = tree_forest->orderedNodeSet[i].node;
			if ((value_patterns = hash_table_lookup(dag_model->patterns, node->production)) != NULL){                
                elem_counts++;                
                
                elem = value_patterns->elem;
                for (k = 0; k<value_patterns->length; k++){ 
                    kernel_value += elem[k].freq * dag_count_SST(elem[k].node, node); // use Judy
                    //                    kernel_value += value_patterns->freq_array[k] * dag_count_adv_cache(node, value_patterns->node_array[k]); // use Judy
                    kernel_evals++;                
                }
			}
		}
		sum += kernel_value/sqrt(tree_forest->twonorm_PT);
	}
    
//    /* init local adv cache */                
//    for (l = 0; l < HASHSIZE; l++) 
//        JLFA(Rc_int,PJcache[l]);                
    
	return sum;
}

static double dag_count_SST(const TreeNode *Nx, const TreeNode *Nz){
	int i;
	double prod = 1;
    
    if(Nx->pre_terminal || Nz->pre_terminal){			
        return LAMBDA;
    }
    else {
        for(i=0;i<Nx->iNoOfChildren;i++)
            if(Nx->pChild[i]->production!=NULL && Nz->pChild[i]->production!= NULL) {
                if(strcmp(Nx->pChild[i]->production, Nz->pChild[i]->production)==0)
                    prod*= (SIGMA + dag_count_SST( Nx->pChild[i], Nz->pChild[i])); // case 2
                else prod*=SIGMA; 
            }
        return LAMBDA*prod;
    }
}

static double dag_count_SST_cache(const TreeNode *Nx, const TreeNode *Nz){
	int i;
	double prod = 1;
	unsigned long key;
	double	*PValue;                    // pointer to array element value
	
	key = Nx->hash + Nz->hash;
    
	JLG(PValue, PJcache[key % HASHSIZE], key);
	if (PValue) {
		return *PValue;
	}
	else {
		if(Nx->pre_terminal || Nz->pre_terminal){			
			JLI(PValue, PJcache[key % HASHSIZE], key);
			return *PValue = LAMBDA;
		}
		else{
			for(i=0;i<Nx->iNoOfChildren;i++)
				if(Nx->pChild[i]->production!=NULL && Nz->pChild[i]->production!= NULL){
					if(strcmp(Nx->pChild[i]->production, Nz->pChild[i]->production)==0)
						prod*= (SIGMA + dag_count_SST_cache( Nx->pChild[i], Nz->pChild[i])); // case 2
					else prod*=SIGMA; 
				}
			JLI(PValue, PJcache[key % HASHSIZE], key);
			return *PValue = LAMBDA*prod;
		}
	}
}

// ---------------------------------
// Partial Tree (PT) kernel -F 3
// ---------------------------------

static double dag_tree_kernel_PT(dag_model_t *dag_model, DOC *X)
/* uses local cache that is passed to dag_count to allow for thread-safety. */
/* use it only in the parallel version */
{
	int i,j,k,l;
	TreeNode *node;
	FOREST *tree_forest;
    dag_array_entry_t *value_patterns;
	double sum = 0.0;
	double kernel_value;
    Word_t Rc_int;
    /* init local cache */
    elem_t *elem;
    
    /* init local adv cache */                
    for (l = 0; l < HASHSIZE; l++) 
        PJcache[l] = (Pvoid_t)NULL;
    
	for (j=0; j<X->num_of_trees; j++) {        
		tree_forest = X->forest_vec[j];		
        kernel_value = 0.0;        
		for (i=0; i<tree_forest->listSize; i++){
            node = tree_forest->orderedNodeSet[i].node;
			if ((value_patterns = hash_table_lookup(dag_model->patterns, node->production)) != NULL){                
                elem_counts++;                
                
                elem = value_patterns->elem;
                for (k = 0; k<value_patterns->length; k++){ 
                    kernel_value += elem[k].freq * dag_Delta_PT(elem[k].node, node); // use Judy
//                    kernel_value += elem[k].freq * dag_Delta_PT(elem[k].node, node) - REMOVE_LEAVES; // use Judy
//                    if(elem[k].node->iNoOfChildren!=0 || node->iNoOfChildren!=0)
//                        kernel_value -= REMOVE_LEAVES;
                    kernel_evals++;                
                }
			}
		}
		sum += kernel_value/sqrt(tree_forest->twonorm_PT);
	}
    
    /* init local adv cache */                
    for (l = 0; l < HASHSIZE; l++) 
        JLFA(Rc_int,PJcache[l]);                
    
	return sum;
}


#ifdef FAST

static double dag_Delta_SK(TreeNode **Sx, TreeNode ** Sz, int n, int m){
	
	double DPS[MAX_NUMBER_OF_CHILDREN_PT][MAX_NUMBER_OF_CHILDREN_PT];
	double DP[MAX_NUMBER_OF_CHILDREN_PT][MAX_NUMBER_OF_CHILDREN_PT];
	double kernel_mat[MAX_NUMBER_OF_CHILDREN_PT];
    
    int i,j,l,p;
    double K;
    
    
    p = n; if (m<n) p=m;if (p>MAX_CHILDREN) p=MAX_CHILDREN;
    
    
	//  if(n==0 || m==0 || m!=n) return 0;
    
    for (j=0; j<=m; j++)
		for (i=0; i<=n; i++)DPS[i][j]=DP[i][j]=0;
	
    kernel_mat[0]=0;
    for (i=1; i<=n; i++)
		for (j=1; j<=m; j++)
			if(strcmp((*(Sx+i-1))->sName,(*(Sz+j-1))->sName)==0) 
			{
				DPS[i][j]=dag_Delta_PT(*(Sx+i-1),*(Sz+j-1));
				kernel_mat[0]+=DPS[i][j];
			}
			else DPS[i][j]=0;
	
	
	//   printf("\nDPS\n"); stampa_math(DPS,n,m); printf("DP\n");  stampa_math(DP,n,m); 
	
	//   printf("kernel: n=%d m=%d, %s %s \n\n",n,m,(*(Sx))->sName,(*(Sz))->sName);
	
	for(l=1;l<p;l++){
		kernel_mat[l]=0;
		for (j=0; j<=m; j++)DP[l-1][j]=0;
		for (i=0; i<=n; i++)DP[i][l-1]=0;
		
		for (i=l; i<=n; i++)
			for (j=l; j<=m; j++){
				DP[i][j] = DPS[i][j]+LAMBDA*DP[i-1][j]
				+ LAMBDA*DP[i][j-1]
				- LAMBDA2*DP[i-1][j-1];
				
				if(strcmp((*(Sx+i-1))->sName,(*(Sz+j-1))->sName)==0){
					DPS[i][j] = dag_Delta_PT(*(Sx+i-1),*(Sz+j-1))* DP[i-1][j-1];
					kernel_mat[l] += DPS[i][j];
				}
				// else DPS[i][j] = 0;             
			}
		//      printf("\n----------------------------------\n"); printf("DPS i:%d, j:%d, l:%d\n",n,m,l+1);stampa_math(DPS,n,m);printf("DP\n");stampa_math(DP,n,m); 
	}
	//  K=kernel_mat[p-1];
	K=0;
	for(l=0;l<p;l++){K+=kernel_mat[l];
		//printf("String kernel of legnth %d: %1.7f \n\n",l+1,kernel_mat[l]);
	}
    return K;
}

#endif

#ifndef FAST


void stampa_math(double *DPS,int n,int m){
	int i,j;
	
	printf("\n");  
	for (i=0; i<=n; i++){
		for (j=0; j<=m; j++)
			printf("%1.8f\t",DPS(i,j));
		printf("\n");  
	}
    printf("\n");  
}

// SLOW SOLUTION BUT ABLE TO DEAL WITH MORE DATA 

static double dag_Delta_SK(TreeNode **Sx, TreeNode ** Sz, int n, int m){
	
	
    double *DPS =(double*) malloc((m+1)*(n+1)*sizeof(double));
    double *DP = (double*) malloc((m+1)*(n+1)*sizeof(double));
    double *kernel_mat = (double*) malloc((n+1)*sizeof(double));
    
    int i,j,l,p;
    double K;
	
    p = n; if (m<n) p=m;if (p>MAX_CHILDREN) p=MAX_CHILDREN;
	
	//  if(n==0 || m==0 || m!=n) return 0;
    
    for (j=0; j<=m; j++)
		for (i=0; i<=n; i++) DPS(i,j) = DP(i,j) =0;
	
    
	//printf("\nDPS(%d,%d)\n",n,m); fflush(stdout);
	//stampa_math(DPS,n,m); fflush(stdout);
	
    kernel_mat[0]=0;
    for (i=1; i<=n; i++)
		for (j=1; j<=m; j++)
			if(strcmp((*(Sx+i-1))->sName,(*(Sz+j-1))->sName)==0) 
			{
				DPS(i,j)=dag_Delta_PT(*(Sx+i-1),*(Sz+j-1));
				kernel_mat[0]+=DPS(i,j);
			}
			else DPS(i,j)=0;
	
	
	//  printf("\n\nDPS(%d,%d)\n",n,m); fflush(stdout);
	//  stampa_math(DPS,n,m); fflush(stdout);
	//  printf("\n\nDP(%d,%d)\n",n,m);  fflush(stdout);
	//  stampa_math(DPS,n,m); fflush(stdout);
	//  printf("\n\nKernel: n=%d m=%d, %s %s \n\n",n,m,(*(Sx))->sName,(*(Sz))->sName);fflush(stdout);
	
	for(l=1;l<p;l++){
		kernel_mat[l]=0;
		for (j=0; j<=m; j++)DP(l-1,j)=0;
		for (i=0; i<=n; i++)DP(i,l-1)=0;
		
		for (i=l; i<=n; i++)
			for (j=l; j<=m; j++){
				DP(i,j) = DPS(i,j)+LAMBDA*DP(i-1,j)
				+ LAMBDA*DP(i,j-1)
				- LAMBDA2*DP(i-1,j-1);
				
				if(strcmp((*(Sx+i-1))->sName,(*(Sz+j-1))->sName)==0){
					DPS(i,j) = dag_Delta_PT(*(Sx+i-1),*(Sz+j-1))* DP(i-1,j-1);
					kernel_mat[l] += DPS(i,j);
				}
				// else DPS[i][j] = 0;             
			}
		//      printf("\n----------------------------------\n"); printf("DPS i:%d, j:%d, l:%d\n",n,m,l+1);stampa_math(DPS,n,m);printf("DP\n");stampa_math(DP,n,m); 
	}
	//  K=kernel_mat[p-1];
	K=0;
	for(l=0;l<p;l++){K+=kernel_mat[l];
		//printf("String kernel of legnth %d: %1.7f \n\n",l+1,kernel_mat[l]);
	}
	
    
    free(kernel_mat);
    free(DPS);
    free(DP);
    
    return K;
}

#endif

static double dag_Delta_PT(TreeNode* Nx, TreeNode* Nz){
	double sum=0;
    double	*PValue;                    // pointer to array element value
    unsigned long key;
    
	key = Nx->hash + Nz->hash;
    
	JLG(PValue, PJcache[key % HASHSIZE], key);
	if (PValue) {
		return *PValue;
	}

//	if(delta_matrix[Nx->nodeID][Nz->nodeID]!=-1) 
//        return delta_matrix[Nx->nodeID][Nz->nodeID]; // already there
	
	if(strcmp(Nx->sName,Nz->sName)!=0) {
//		return (delta_matrix[Nx->nodeID][Nz->nodeID]=0);
        JLI(PValue, PJcache[key % HASHSIZE], key);
        return *PValue = 0;
//        return 0;
    }
	else if(Nx->iNoOfChildren==0 || Nz->iNoOfChildren==0) {
//		return (delta_matrix[Nx->nodeID][Nz->nodeID]=MU*LAMBDA2);
        JLI(PValue, PJcache[key % HASHSIZE], key);
        return *PValue = MU*LAMBDA2;
//        return MU*LAMBDA2;
    }
	else {
		sum = MU*(LAMBDA2 + dag_Delta_SK(Nx->pChild, Nz->pChild,Nx->iNoOfChildren, Nz->iNoOfChildren)); 
//		return (delta_matrix[Nx->nodeID][Nz->nodeID]=sum);
        JLI(PValue, PJcache[key % HASHSIZE], key);
        return *PValue = sum;
//        return sum;
	}
	return 0;
}

/* a version of dag_Delta_PT without cache */
static double _dag_Delta_PT(TreeNode* Nx, TreeNode* Nz){
	double sum=0;
	
	if(strcmp(Nx->sName,Nz->sName)!=0) {
        return 0;
    }
	else if(Nx->iNoOfChildren==0 || Nz->iNoOfChildren==0) {
        return MU*LAMBDA2;
    }
	else {
		sum = MU*(LAMBDA2 + dag_Delta_SK(Nx->pChild, Nz->pChild,Nx->iNoOfChildren, Nz->iNoOfChildren)); 
        return sum;
	}
	return 0;
}
