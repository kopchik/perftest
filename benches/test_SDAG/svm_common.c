/************************************************************************/
/*                                                                      */
/*   svm_common.c                                                       */
/*                                                                      */
/*   Definitions and functions used in both svm_learn and svm_classify. */
/*                                                                      */
/*   Author: Thorsten Joachims                                          */
/*   Date: 02.07.02                                                     */
/*                                                                      */
/*                                                                      */
/*                                                                      */
/*   Modified by Alessandro Moschitti for adding the Tree Kernels	*/
/*   Date: 21.10.04 							*/
/*                                                                      */
/*                                                                      */
/*   Copyright (c) 2002  Thorsten Joachims - All rights reserved        */
/*                                                                      */
/*   This software is available for non-commercial use only. It must    */
/*   not be modified and distributed without prior permission of the    */
/*   author. The author is not responsible for implications from the    */
/*   use of this software.                                              */
/*                                                                      */
/************************************************************************/

# include "ctype.h"
# include "svm_common.h"
# include "kernel.h"           /* this contains a user supplied kernel */
//# include "Judy.h"

long   verbosity;              /* verbosity level (0-4) */
long   kernel_cache_statistic;

void print_help();
void wait_any_key();

CFLOAT kernel(KERNEL_PARM *kernel_parm, DOC *a, DOC *b) 
/* calculate the kernel function */
{
    // double k1;
    kernel_cache_statistic++;
    switch(kernel_parm->kernel_type) {
        case 0: /* linear */ 
            return(CFLOAT)sprod(a, b); 
        case 1: /* polynomial */   
            return ((CFLOAT)pow(kernel_parm->coef_lin*sprod(a, b)
                                +kernel_parm->coef_const,(double)kernel_parm->poly_degree));
        case 2: /* radial basis function */
            return((CFLOAT)exp(-kernel_parm->rbf_gamma*(a->vectors[0]->twonorm_sq-2*sprod(a,b)+b->vectors[0]->twonorm_sq)));
        case 3: /* sigmoid neural net */
            return((CFLOAT)tanh(kernel_parm->coef_lin*sprod(a,b)+kernel_parm->coef_const)); 
        case 4: /* custom-kernel supplied in file kernel.h */
            return((CFLOAT)custom_kernel(kernel_parm,a,b));
        case 5: /* combine kernels */
            return ((CFLOAT)advanced_kernels(kernel_parm,a,b));
            
        case 6: /* Tree kernels on u*/
            return tree_kernel(kernel_parm, a, b, atoi(kernel_parm->custom), atoi(kernel_parm->custom));
            
        case 11: /* Re-ranking of predicate argument structures only trees, i.e. re-ranking using trees */
            return((CFLOAT)SRL_re_ranking_CoNLL2006(kernel_parm,a,b));           
        case 12: /* Re-ranking of predicate argument structures only trees + vectors */
            return((CFLOAT)SRL_re_ranking_CoNLL2006(kernel_parm,a,b));            
        case 13: /* Re-ranking of predicate argument structures only vectors */
            return((CFLOAT)SRL_re_ranking_CoNLL2006(kernel_parm,a,b)); 
        case 14: /* Classification of Entailment pairs */
            return((CFLOAT)ACL2006_Entailment_kernel(kernel_parm,a,b)); 
        case 15: /* Classification of Entailment pairs */
            return (CFLOAT)JHU_KERNELS(kernel_parm, a, b);
        case 16: /* Classification of Entailment pairs */
            return((CFLOAT)ACL2008_Entailment_kernel(kernel_parm,a,b));
        case 17: return (CFLOAT)ACL2008(kernel_parm, a, b);
            
        case 30: /* Classification of Entailment pairs */
            return (CFLOAT)Question_Answer_Classification(kernel_parm, a, b);      
            
        case 51: /* Re-ranking of predicate argument structures only trees, i.e. re-ranking using trees */
            return((CFLOAT) SRL_re_ranking_ACL2009(kernel_parm, a, b));
        case 52: /* Re-ranking of predicate argument structures only trees + vectors */
            return((CFLOAT) SRL_re_ranking_ACL2009(kernel_parm, a, b));
        case 53: /* Re-ranking of predicate argument structures only vectors */
            return((CFLOAT) SRL_re_ranking_ACL2009(kernel_parm, a, b));  
        case 100: /* Use only the tree whose index is specified in the custom parameter */
            return((CFLOAT) tree_kernel(kernel_parm, a, b, atoi(kernel_parm->custom),atoi(kernel_parm->custom)));  
			
        default: /* Advanced vectorial kernels*/
            printf("\nNo kernel corresponding to -t = %ld option \n",kernel_parm->kernel_type);
            exit(-1);
            
            /*if (b->num_of_trees > 0 && a->num_of_trees>0) {
             printf("\n tree 1: <"); writeTreeString(a->forest_vec[0]->root);
             printf(">\n tree 2: <"); writeTreeString(b->forest_vec[0]->root);printf(">\n");
             printf("Kernel :%1.20lf \n",k1);  
             }*/
    }
}

double sprod(DOC *a, DOC *b){ // compatibility with standard svm-light
    if(a->num_of_vectors>0 && b->num_of_vectors>0 ){
        if(a->vectors[0]==NULL || b->vectors[0]==NULL){
            printf("ERROR: first vector not defined (with a traditional kernel it must be defined)\n");
            exit(-1);
        }
        else return sprod_ss(a->vectors[0]->words,b->vectors[0]->words);
    }      
    return 0;
}

double sprod_i(DOC *a, DOC *b, int i, int j){ // compatibility with standard svm-light
    if(a->num_of_vectors>0 && b->num_of_vectors>0 ){
        if(a->vectors[i]==NULL || b->vectors[j]==NULL){
            printf("ERROR: first vector not defined (with a traditional kernel it must be defined)\n");
            exit(-1);
        }
        else return sprod_ss(a->vectors[i]->words,b->vectors[j]->words);
    }      
    return 0;
}


double sprod_ss(WORD *a, WORD *b)
/* compute the inner product of two sparse vectors */
{
    register FVAL sum=0;
    register WORD *ai,*bj;
    ai=a;
    bj=b;
    while (ai->wnum && bj->wnum) {
        if(ai->wnum > bj->wnum) {
            bj++;
        }
        else if (ai->wnum < bj->wnum) {
            ai++;
        }
        else {
            sum+=ai->weight * bj->weight;
            ai++;
            bj++;
        }
    }
    return((double)sum);
}

WORD* sub_ss(WORD *a, WORD *b) 
/* compute the difference a-b of two sparse vectors */
{
    register WORD *sum,*sumi;
    register WORD *ai,*bj;
    long veclength;
    
    ai=a;
    bj=b;
    veclength=0;
    while (ai->wnum && bj->wnum) {
        if(ai->wnum > bj->wnum) {
            veclength++;
            bj++;
        }
        else if (ai->wnum < bj->wnum) {
            veclength++;
            ai++;
        }
        else {
            veclength++;
            ai++;
            bj++;
        }
    }
    while (bj->wnum) {
        veclength++;
        bj++;
    }
    while (ai->wnum) {
        veclength++;
        ai++;
    }
    veclength++;
    
    sum=(WORD *)my_malloc(sizeof(WORD)*veclength);
    sumi=sum;
    ai=a;
    bj=b;
    while (ai->wnum && bj->wnum) {
        if(ai->wnum > bj->wnum) {
            (*sumi)=(*bj);
            sumi->weight*=(-1);
            sumi++;
            bj++;
        }
        else if (ai->wnum < bj->wnum) {
            (*sumi)=(*ai);
            sumi++;
            ai++;
        }
        else {
            (*sumi)=(*ai);
            sumi->weight-=bj->weight;
            sumi++;
            ai++;
            bj++;
        }
    }
    while (bj->wnum) {
        (*sumi)=(*bj);
        sumi->weight*=(-1);
        sumi++;
        bj++;
    }
    while (ai->wnum) {
        (*sumi)=(*ai);
        sumi++;
        ai++;
    }
    sumi->wnum=0;
    return(sum);
}

double model_length_s(MODEL *model, KERNEL_PARM *kernel_parm) 
/* compute length of weight vector */
{
    register long i,j;
    register double sum=0,alphai;
    register DOC *supveci;
    
    for(i=1;i<model->sv_num;i++) {  
        alphai=model->alpha[i];
        supveci=model->supvec[i];
        for(j=1;j<model->sv_num;j++) {
            sum+=alphai*model->alpha[j]
            *kernel(kernel_parm,supveci,model->supvec[j]);
        }
    }
    return(sqrt(sum));
}

void clear_vector_n(double *vec, long int n)
{
    register long i;
    for(i=0;i<=n;i++) vec[i]=0;
}

void add_vector_ns(double *vec_n, WORD *vec_s, double faktor)
{
    register WORD *ai;
    ai=vec_s;
    while (ai->wnum) {
        vec_n[ai->wnum]+=(faktor*ai->weight);
        ai++;
    }
}

double sprod_ns(double *vec_n, WORD *vec_s)
{
    register double sum=0;
    register WORD *ai;
    ai=vec_s;
    while (ai->wnum) {
        sum+=(vec_n[ai->wnum]*ai->weight);
        ai++;
    }
    return(sum);
}

void add_weight_vector_to_linear_model(MODEL *model)
/* compute weight vector in linear case and add to model */
{
    long i;
    
    model->lin_weights=(double *)my_malloc(sizeof(double)*(model->totwords+1));
    clear_vector_n(model->lin_weights,model->totwords);
    for(i=1;i<model->sv_num;i++) {
        add_vector_ns(model->lin_weights,(model->supvec[i]->vectors[0])->words,
                      model->alpha[i]);
    }
}


/*
 struct tree_kernel_parameters{
 short kernel_type;
 short TKGENERALITY;
 double lambda;
 double mu;
 double weight;
 short normalization;
 }
 */

void read_input_tree_kernel_param(){
    FILE *params;
    int j,i=0;
    params=fopen("tree_kernels.param","r");
    if(params!=NULL){
		printf("\nLoading tree kernel parameters from file\n");fflush(stdin);
		do {
            fscanf(params,"%hd,",&tree_kernel_params[i].kernel_type);
            fscanf(params,"%hd,",&tree_kernel_params[i].TKGENERALITY);
            fscanf(params,"%lf,",&tree_kernel_params[i].lambda);
            fscanf(params,"%lf,",&tree_kernel_params[i].mu);
            fscanf(params,"%lf,",&tree_kernel_params[i].weight);
            fscanf(params,"%hd%*[^\n]\n",&tree_kernel_params[i].normalization);
            /*           printf("tree number %d: %d,",i,tree_kernel_params[i].kernel_type);
             printf("%d,",tree_kernel_params[i].TKGENERALITY);
             printf("%f,",tree_kernel_params[i].lambda);
             printf("%f,",tree_kernel_params[i].mu);
             printf("%f,",tree_kernel_params[i].weight);
             printf("%d\n",tree_kernel_params[i].normalization);
             */
            i++;
		} while(!feof(params)&&tree_kernel_params[i].kernel_type!=END_OF_TREE_KERNELS);
		fclose(params);
        for(j=0;j<i;j++){
            if(tree_kernel_params[j].kernel_type != NOKERNEL){
                printf("tree number %d: %d,",j,tree_kernel_params[j].kernel_type);
                printf("%d,",tree_kernel_params[j].TKGENERALITY);
                printf("%f,",tree_kernel_params[j].lambda);
                printf("%f,",tree_kernel_params[j].mu);
                printf("%f,",tree_kernel_params[j].weight);
                printf("%d\n",tree_kernel_params[j].normalization);
            }
        }
        printf("\n");
    }
}



void read_model(char *modelfile, MODEL *model, long  max_words_doc, long int ll)
{
    FILE *modelfl;
    int i;
    int pos;
    char *line;
    char version_buffer[100];
    long int fake_totwords;
    
    if(verbosity>=1) {
        printf("Reading model..."); fflush(stdout);
    }
    
    line = (char *)my_malloc(sizeof(char)*ll);
    
    if ((modelfl = fopen (modelfile, "r")) == NULL)
    { perror (modelfile); exit (1); }
    
    fscanf(modelfl,"SVM-light Version %s\n",version_buffer);
    
    //printf("Version file %s --- version label %s \n",version_buffer,VERSION);
    
    
    if(strcmp(version_buffer,VERSION)) {
        perror ("Version of model-file does not match version of svm_classify!"); 
        exit (1); 
    }
    fscanf(modelfl,"%ld%*[^\n]\n", &model->kernel_parm.kernel_type);  
    fscanf(modelfl,"%ld%*[^\n]\n", &model->kernel_parm.poly_degree);
    fscanf(modelfl,"%lf%*[^\n]\n", &model->kernel_parm.rbf_gamma);
    fscanf(modelfl,"%lf%*[^\n]\n", &model->kernel_parm.coef_lin);
    fscanf(modelfl,"%lf%*[^\n]\n", &model->kernel_parm.coef_const);
    fscanf(modelfl,"%[^#]%*[^\n]\n", model->kernel_parm.custom);
    fscanf(modelfl,"%lf%*[^\n]\n", &model->kernel_parm.lambda);
    fscanf(modelfl,"%lf%*[^\n]\n", &model->kernel_parm.tree_constant);
    fscanf(modelfl,"%c%*[^\n]\n", &model->kernel_parm.combination_type);
    fscanf(modelfl,"%ld%*[^\n]\n", &model->kernel_parm.first_kernel);
    fscanf(modelfl,"%ld%*[^\n]\n", &model->kernel_parm.second_kernel);
    fscanf(modelfl,"%f%*[^\n]\n", &model->kernel_parm.mu);
    fscanf(modelfl,"%ld%*[^\n]\n", &model->kernel_parm.normalization);
    
    fscanf(modelfl,"%c%*[^\n]\n", &model->kernel_parm.vectorial_approach_standard_kernel);
    fscanf(modelfl,"%c%*[^\n]\n", &model->kernel_parm.vectorial_approach_tree_kernel);
    fscanf(modelfl,"%hd%*[^\n]\n", &model->kernel_parm.tree_kernel_params);
    
    fscanf(modelfl,"%ld%*[^\n]\n", &model->totwords);
    fscanf(modelfl,"%ld%*[^\n]\n", &model->totdoc);
    fscanf(modelfl,"%ld%*[^\n]\n", &model->sv_num);
    fscanf(modelfl,"%lf%*[^\n]\n", &model->b);
    
    
    LAMBDA = model->kernel_parm.lambda; // to make faster the kernel evaluation 
    LAMBDA2 = LAMBDA*LAMBDA;
    MU=model->kernel_parm.mu;
    TKGENERALITY=model->kernel_parm.first_kernel;
    PARAM_VECT=model->kernel_parm.tree_kernel_params;
    if(PARAM_VECT == 1) read_input_tree_kernel_param(); // if there is the file tree_kernel.param load paramters
    
    for(i=1;i<model->sv_num;i++) {
        fgets(line,(int)ll,modelfl);
        pos=0;
        while(strlen(line)<3){
            printf("\nWARNING: empty line for the support vector %d\n\n",i);    
            fgets(line,(int)ll,modelfl);
        }
        sscanf(line,"%lf",&model->alpha[i]);
        model->supvec[i] = (DOC *)my_malloc(sizeof(DOC));
        
        //   printf("--->%d--><%s>\n",i,line+pos);fflush(stdout);
        //   printf("Go after alpha\n");fflush(stdout);
        
        while(!isspace((int)line[pos]) && line[pos]!=0)pos++; //go after alpha
        
        //   printf("--->%d--><%s>\n",i,line+pos);fflush(stdout);
        //   printf("Go after spaces\n");fflush(stdout);
        
        while(isspace((int)line[pos])) pos++;// go after spaces
        //   printf("--->%d--><%s>\n",i,line+pos);fflush(stdout);
        
        read_tree_forest(line, model->supvec[i], &pos);// read the tree forest: set PARAM_VECT to 0 if less paramaters than vector entries
        PARAM_VECT = model->kernel_parm.tree_kernel_params; // restore parameter file flag
        
        /* Look for Standard Features */
        // writeTreeString((model->supvec[i])->root);
        
        //printf("LINE:%s\n",line+pos);fflush(stdout);
        while(isspace((int)line[pos])&& line[pos]!=0) pos++;//remove spaces
        //while((!isspace((int)line[pos])) && line[pos]) pos++;
        // if vectors exists
        if(line[pos]!=0) read_vector_set(line+pos, model->supvec[i],max_words_doc,&fake_totwords);// read the set of vectors 
        else {model->supvec[i]->vectors=NULL;model->supvec[i]->num_of_vectors=0;}
        
        evaluateNorma(&(model->kernel_parm), model->supvec[i]);
        PARAM_VECT=model->kernel_parm.tree_kernel_params;
        
        (model->supvec[i])->docnum = -1;
    }
    fclose(modelfl);
    free(line);
    if(verbosity>=1) {
        fprintf(stdout, "OK. (%d support vectors read)\n",(int)(model->sv_num-1));
    }
}

void read_documents(char *docfile, DOC *docs, double *label, 
                    long int max_words_doc, long int ll, 
                    long int *totwords, long int *totdoc, KERNEL_PARM *kernel_parm)
{
    char *line;
    DOC doc;
    long dnum=0,dpos=0,dneg=0,dunlab=0;
    double doc_label;
    FILE *docfl;
    
    line = (char *)my_malloc(sizeof(char)*ll);
    
    if ((docfl = fopen (docfile, "r")) == NULL)
    { perror (docfile); exit (1); }
    
    if(verbosity>=1) {
        printf("Reading examples into memory..."); fflush(stdout);
    }
    dnum=0;
    (*totwords)=0;
    
    while((!feof(docfl)) && fgets(line,(int)ll,docfl)) {
        
        doc.docnum=dnum+1;
        if(strlen(line)==0){
            printf("\nERROR: empty line, missing end of line before end of file\n");
            exit(1);
        }
        
        
        if(!parse_document(line, &doc, &doc_label, totwords, max_words_doc, kernel_parm)) {
            printf("\nParsing error in line %ld!\n%s",dnum,line);
            exit(1);
        }
        
        label[dnum]=doc_label;
        /*  printf("Class=%ld ",doc_label);  */
        if (doc_label > 0) dpos++;
        if (doc_label < 0) dneg++;
        if (doc_label == 0) dunlab++;
        
        docs[dnum].queryid = doc.queryid;
        docs[dnum].costfactor = doc.costfactor;
        
        docs[dnum].forest_vec = doc.forest_vec;
        docs[dnum].num_of_trees = doc.num_of_trees;
        docs[dnum].vectors = doc.vectors;
        docs[dnum].num_of_vectors = doc.num_of_vectors;
        
        // less than 5 basic kernels and greater than 50 only vectors (to save memory)
        if (kernel_parm->kernel_type<4) { // from 0 to 3 are original kernels => no trees
            freeForest(&doc); // save memory by freeing trees
            docs[dnum].num_of_trees = 0;
            docs[dnum].forest_vec =NULL;
            kernel_parm->second_kernel=kernel_parm->kernel_type;
        }   
        
        // establish some interval to free vectors
        
        //    if(kernel_parm->kernel_type>20){
        //	     docs[dnum].vectors = NULL;
        //         docs[dnum].num_of_vectors = 0;
        //         freeVectorSet(&doc); // save memory by freeing vectors
        //     }
        
        docs[dnum].docnum=dnum;
        
        /* printf("\nNorm=%f\n",docs[dnum].twonorm_sq);  */
        
        /*printf("parse tree number %d: ",dnum);
         writeTreeString(doc.root);
         */
        /*    printf("%d\t",(int)doc_label);  
         */ 
        dnum++;  
        if(verbosity>=1) {
            if((dnum % 1000) == 0) {
                printf("%ld..",dnum); fflush(stdout);
            }
        }
    } 
    
    fclose(docfl);
    free(line);
    
    if(verbosity>=1) {
        fprintf(stdout, "OK. (%ld examples read)\n", dnum);
    }
    
    fflush(stdout);
    
    (*totdoc)=dnum;
}

//unsigned long string_hash(void *string)
//{
//	/* This is the djb2 string hash function */
//	
//	unsigned long result = 5381;
//	unsigned char *p;
//	
//	p = (unsigned char *) string;
//	
//	while (*p != '\0') {
//		result = ((result << 5) ^ result ) ^ (*p);
//		++p;
//	}
//	
//	return result;
//}

int compare_words(const void* item1, const void* item2)
{
	const WORD *it1 = (WORD*)item1;
	const WORD *it2 = (WORD*)item2;
	if (it1->wnum > it2->wnum)
        return 1;
    else if (it1->wnum < it2->wnum)
        return -1;
        else
            return 0;
}

//void _read_vector_from_tree_nodes(DOC *doc){
//    int i, j, num_nodes, num_trees;
//    FOREST *tree_forest;
//    OrderedTreeNode *tree_node_list;
//    VECTOR_SET *tmp_vector_set;
//    WORD *tmp_words;
//    
//    num_trees = doc->num_of_trees;
//    doc->num_of_vectors = num_trees;
//    doc->vectors = (VECTOR_SET **)my_malloc(sizeof(VECTOR_SET*)*num_trees);
//    
//    for (i=0; i<num_trees; i++) {
//        tree_forest = doc->forest_vec[i];
//        tree_node_list = tree_forest->orderedNodeSet;
//        tmp_vector_set = (VECTOR_SET*)my_malloc(sizeof(VECTOR_SET));
//        
//        num_nodes = tree_forest->listSize;
//        
//        tmp_words = my_malloc(sizeof(WORD)*(num_nodes+1));
//        
//        // go through all the nodes and hash their production rules
//        for (j = 0; j<num_nodes; j++) {
//            tmp_words[j].wnum = string_hash(tree_node_list[j].sName);
//            tmp_words[j].weight = 1.0;
//        }
//        
//        qsort(tmp_words, num_nodes, sizeof(WORD), &compare_words);
//        
//        tmp_words[j].wnum = 0;
//        
//        tmp_vector_set->words = tmp_words;
//        doc->vectors[i] = tmp_vector_set;
//    }
//    
////    /* DEBUG */
////    for (i=0; i<doc->num_of_vectors; i++) {
////        tmp_words = doc->vectors[i]->words;
////        j = 0;
////        while (tmp_words[j].wnum) {
////            printf("%lu %.2f\n",tmp_words[j].wnum,tmp_words[j].weight);
////            j++;
////        }
////        printf("\n");
////    }
//}

void writeTreeString(TreeNode *node){
    
    int i;
    
    if(node==NULL) return;
    
	if(node->iNoOfChildren>0){
        printf("(%s ",node->sName); 
        for(i=0;i<node->iNoOfChildren;i++){
            writeTreeString(node->pChild[i]);
        }
        printf(")"); 
	}
	else printf("(%s)",node->sName);
}

//void read_vector_from_tree_nodes(DOC *doc){
//    int i, j, num_nodes, num_trees;
//    FOREST *tree_forest;
//    OrderedTreeNode *tree_node_list;
//    VECTOR_SET *tmp_vector_set;
//    WORD *tmp_words;
//    Pvoid_t tmp_hash_array;
//    FVAL *Pvalue;
//    Word_t key;
//    Word_t Rc_int;
//    
//    num_trees = doc->num_of_trees;
//    doc->num_of_vectors = num_trees;
//    doc->vectors = (VECTOR_SET **)my_malloc(sizeof(VECTOR_SET*)*num_trees);
//
////    printf("--------------------\n");
//    
//    for (i=0; i<num_trees; i++) {
//        tree_forest = doc->forest_vec[i];
//        tree_node_list = tree_forest->orderedNodeSet;
//        tmp_vector_set = (VECTOR_SET*)my_malloc(sizeof(VECTOR_SET));
//        
//        num_nodes = tree_forest->listSize;
//        
////        writeTreeString(doc->forest_vec[i]->root); printf("\n");
//        
//        tmp_hash_array = (Pvoid_t)NULL;
//        // go through all the nodes and hash their production rules
//        for (j = 0; j<num_nodes; j++) {
//            key = string_hash(tree_node_list[j].sName);
//            JLI(Pvalue, tmp_hash_array, key);
//            *Pvalue += 1.0;
////            printf("%lu %.2f %s\n",key, *Pvalue, tree_node_list[j].sName);
////            printf("%s\n",tree_node_list[j].sName);
//        }
////        printf("\n");
//        
//        // allocate memory for words array
//        JLC(Rc_int, tmp_hash_array, 0, -1);        
//        tmp_words = my_malloc(sizeof(WORD)*(Rc_int+1));
//        
//        // fill up the words array
//        key = 0;
//        j = 0;
//        // go through all the key/value pairs in tmp_hash_array
//        JLF(Pvalue, tmp_hash_array, key);
//        while (Pvalue != NULL) {
//            tmp_words[j].wnum = key;
//            tmp_words[j].weight = *Pvalue;
////            if (*Pvalue > 1)
////                printf("%lu %.4f\n",key, *Pvalue);
//            j++;
//            JLN(Pvalue, tmp_hash_array, key);
//        }
//        tmp_words[j].wnum = 0;
//        
//        JLFA(Rc_int, tmp_hash_array);
//        tmp_vector_set->words = tmp_words;
//        doc->vectors[i] = tmp_vector_set;
//    }
//    
////    /* DEBUG */
////    printf("\n");
////    for (i=0; i<doc->num_of_vectors; i++) {
////        tmp_words = doc->vectors[i]->words;
////        j = 0;
////        
////        while (tmp_words[j].wnum) {
////            printf("%lu %.2f\n",tmp_words[j].wnum,tmp_words[j].weight);
////            j++;
////        }
////        printf("\n");
////    }
////    printf("Sprod: %.2f\n", sprod_ss(tmp_words, tmp_words));
//}

int parse_document(char *line, DOC *doc, double *label, 
                   long int *totwords, long int max_words_doc, KERNEL_PARM *kernel_parm)
{
    int pos;
    
    doc->queryid=0;
    doc->costfactor=1;
    //printf("\n\n---------------------------------------------------------\n\n");fflush(stdout);
    pos=0;
    
    // while((isspace((int)line[pos])||line[pos]=='\n') && line[pos]!=0) 
    //    {printf("%c\t",line[pos]);pos++;}
    
    if(sscanf(line+pos,"%lf",label) == EOF) return(0);
    // printf("LINE:%s\n\n\n",line);fflush(stdout);
    
    while(!isspace((int)line[pos]))pos++;// go after label 
    
    read_tree_forest(line, doc, &pos);// read the tree forest: set PARAM_VECT to 0 if less paramaters than vector entries
    PARAM_VECT = kernel_parm->tree_kernel_params; // restore parameter file flag
    
    /* Look for Standard Features, pos returns the end of the last tree*/
    //  printf("LINE:%s\n",line+pos);fflush(stdout);
    
    /* enable this to create linear vector from production rules*/
//    read_vector_from_tree_nodes(doc);
    
    
    while(isspace((int)line[pos])&& line[pos]!=0) pos++;// go to "|BV|" marker or to the first number
    /*while((!isspace((int)line[pos])) && line[pos]) pos++;*/
    if(line[pos]!=0) read_vector_set(line+pos, doc, max_words_doc, totwords);// read the tree forest 
    else {doc->vectors=NULL;doc->num_of_vectors=0;}
    
    doc->docnum=-1;
    
    evaluateNorma(kernel_parm,doc);
    PARAM_VECT = kernel_parm->tree_kernel_params; // restore parameter file flag
//    printf("Norm STD: %.2f\n", doc->vectors[0]->twonorm_STD);
//    doc->vectors[0]->twonorm_STD = sprod_ss(doc->vectors[0]->words, doc->vectors[0]->words);
    return(1);
}

/*void free_example(DOC *example, long deep)
 {
 if(example) {
 if(deep) {
 if(example->vectors[0]->words)
 free_vector(example->vectors[0]->words);
 }
 free(example);
 }
 }*/

/*extern void freeExample(DOC *example){
 free(example);
 }*/


/*void go_after_STD_mark(FILE *f1, long int *ll){
 char mark[1000];
 *mark=0;
 while(strstr(mark,"|ET|")!=NULL && !feof(f1)){
 //printf("%s\n",mark);
 fscanf(f1,"%s",mark);
 (*ll)+=strlen(mark)+4; // count some spaces more
 *mark=0;
 }
 // ...no problem if the program will double the memory it is just for a line;
 }
 */

void nol_ll(char *file, long int *nol, long int *wol, long int *ll) 
/* Grep through file and count number of lines, maximum number of
 spaces per line, and longest line. */
{
    FILE *fl;
    int ic;
    char c;
    long current_length,current_wol;
    
    if ((fl = fopen (file, "r")) == NULL)
    { perror (file); exit (1); }
    current_length=0;
    current_wol=0;
    (*ll)=0;
    (*nol)=1;
    (*wol)=0;
    // go_after_STD_mark(fl,ll);
    while((ic=getc(fl)) != EOF) {
        c=(char)ic;
        current_length++;
        if(isspace((int)c)) {
            current_wol++;
        }
        if(c == '\n') {
            (*nol)++;
            if(current_length>(*ll)) {
                (*ll)=current_length;
            }
            if(current_wol>(*wol)) {
                (*wol)=current_wol;
            }
            // printf ("%d %d\n",current_wol,current_length);
            current_length=0;
            current_wol=0;
        }
    }
    fclose(fl);
    
    if(current_length>(*ll)) {
        (*ll)=current_length;
    }
}

long minl(long int a, long int b)
{
    if(a<b)
        return(a);
    else
        return(b);
}

long maxl(long int a, long int b)
{
    if(a>b)
        return(a);
    else
        return(b);
}

long get_runtime(void)
{
    clock_t start;
    start = clock();
    return((long)((double)start*100.0/(double)CLOCKS_PER_SEC));
}


# ifdef MICROSOFT

int isnan(double a)
{
    return(_isnan(a));
}

# endif


void *my_malloc(size_t size)
{
    void *ptr;
    ptr=(void *)malloc(size);
    if(!ptr) { 
        perror ("Out of memory!\n"); 
        exit (1); 
    }
    return(ptr);
}

void copyright_notice(void)
{
    printf("\nCopyright: Thorsten Joachims, thorsten@ls8.cs.uni-dortmund.de\n\n");
    printf("This software is available for non-commercial use only. It must not\n");
    printf("be modified and distributed without prior permission of the author.\n");
    printf("The author is not responsible for implications from the use of this\n");
    printf("software.\n\n");
}

/* DEBUG
 
 double k1;  WORD *pippo;   
 
 printf("doc IDs :%d %d  ",a->docnum,b->docnum);
 if(a->vectors!=NULL && b->vectors!=NULL){
 pippo=a->vectors[0]->words;
 while(pippo->wnum!=0){printf ("%ld:%lf ",pippo->wnum,pippo->weight);pippo++;};fflush(stdout);
 pippo=b->vectors[0]->words;printf("\t");
 while(pippo->wnum!=0){printf ("%ld:%lf ",pippo->wnum,pippo->weight);pippo++;};fflush(stdout);
 printf("  KERNEL %lf\n",k1);
 }
 
 return k1; 
 */
/****************************** IO-handling **********************************/

void write_model(char *modelfile, MODEL *model)
{
    FILE *modelfl;
    long j,i;
    char temp[MAX_PARSE_TREE_LENGTH];
    WORD *index;
	
    if(verbosity>=1) {
        printf("Writing model file..."); fflush(stdout);
    }
    if ((modelfl = fopen (modelfile, "w")) == NULL)
    { perror (modelfile); exit (1); }
    fprintf(modelfl,"SVM-light Version %s\n",VERSION);
    fprintf(modelfl,"%ld # kernel type\n",
            model->kernel_parm.kernel_type);
    fprintf(modelfl,"%ld # kernel parameter -d \n",
            model->kernel_parm.poly_degree);
    fprintf(modelfl,"%.8g # kernel parameter -g \n",
            model->kernel_parm.rbf_gamma);
    fprintf(modelfl,"%.8g # kernel parameter -s \n",
            model->kernel_parm.coef_lin);
    fprintf(modelfl,"%.8g # kernel parameter -r \n",
            model->kernel_parm.coef_const);
    fprintf(modelfl,"%s# kernel parameter -u \n",model->kernel_parm.custom);
	
    fprintf(modelfl,"%.8g # kernel parameter -L \n", model->kernel_parm.lambda);
    fprintf(modelfl,"%.8g # kernel parameter -T \n",model->kernel_parm.tree_constant);
    fprintf(modelfl,"%c # kernel parameter -C \n",model->kernel_parm.combination_type);
    fprintf(modelfl,"%ld # kernel parameter -F \n",model->kernel_parm.first_kernel);
    fprintf(modelfl,"%ld # kernel parameter -S \n",model->kernel_parm.second_kernel);
    fprintf(modelfl,"%f # kernel parameter -M \n",model->kernel_parm.mu);
    fprintf(modelfl,"%ld # kernel parameter -N \n",model->kernel_parm.normalization);
	
    fprintf(modelfl,"%c # kernel parameter -V \n", model->kernel_parm.vectorial_approach_standard_kernel);
    fprintf(modelfl,"%c # kernel parameter -W \n", model->kernel_parm.vectorial_approach_tree_kernel); //forest
    fprintf(modelfl,"%d # kernel parameter -U \n", model->kernel_parm.tree_kernel_params); 
	
    fprintf(modelfl,"%ld # highest feature index \n",model->totwords);
    fprintf(modelfl,"%ld # number of training documents \n",model->totdoc);
	
    fprintf(modelfl,"%ld # number of support vectors plus 1 \n",model->sv_num);
    fprintf(modelfl,"%.8g # threshold b, each following line is a SV (starting with alpha*y)\n",model->b);
	
    for(i=1;i<model->sv_num;i++) {
        fprintf(modelfl,"%.32g ",model->alpha[i]);
        
        
        for(j=0; j < model->supvec[i]->num_of_trees;j++) {
			fprintf(modelfl," |BT| ");      
			strcpy(temp,"");
			getStringTree(model->supvec[i]->forest_vec[j]->root,temp);
			fprintf(modelfl,"%s",temp);
		}
        if(model->supvec[i]->num_of_trees)fprintf(modelfl," |ET| ");
		
        for (j=0; j<(model->supvec[i])->num_of_vectors; j++) {
			index=(model->supvec[i]->vectors[j])->words;
			while ((index)->wnum){
                fprintf(modelfl,"%ld:%.8g ",
                        (long)(index->wnum),
                        (double)(index->weight));index++;
			}
			if(j+1<(model->supvec[i])->num_of_vectors) fprintf(modelfl," |BV| "); 
        }
        if(model->supvec[i]->num_of_vectors)fprintf(modelfl," |EV| ");
        fprintf(modelfl,"\n");
		
    }
	
    fclose(modelfl);
    if(verbosity>=1) {
        printf("done\n");
    }
}


void write_prediction(char *predfile, MODEL *model, double *lin, 
                      double *a, long int *unlabeled, 
                      long int *label, long int totdoc, 
                      LEARN_PARM *learn_parm)
{
    FILE *predfl;
    long i;
    double dist,a_max;
	
    if(verbosity>=1) {
        printf("Writing prediction file..."); fflush(stdout);
    }
    if ((predfl = fopen (predfile, "w")) == NULL)
    { perror (predfile); exit (1); }
    a_max=learn_parm->epsilon_a;
    for(i=0;i<totdoc;i++) {
        if((unlabeled[i]) && (a[i]>a_max)) {
            a_max=a[i];
        }
    }
    for(i=0;i<totdoc;i++) {
        if(unlabeled[i]) {
            if((a[i]>(learn_parm->epsilon_a))) {
				dist=(double)label[i]*(1.0-learn_parm->epsilon_crit-a[i]/(a_max*2.0));
            }
            else {
				dist=(lin[i]-model->b);
            }
            if(dist>0) {
				fprintf(predfl,"%.8g:+1 %.8g:-1\n",dist,-dist);
            }
            else {
				fprintf(predfl,"%.8g:-1 %.8g:+1\n",-dist,dist);
            }
        }
    }
    fclose(predfl);
    if(verbosity>=1) {
        printf("done\n");
    }
}

void write_alphas(char *alphafile, double *a, 
                  long int *label, long int totdoc)
{
    FILE *alphafl;
    long i;
	
    if(verbosity>=1) {
        printf("Writing alpha file..."); fflush(stdout);
    }
    if ((alphafl = fopen (alphafile, "w")) == NULL)
    { perror (alphafile); exit (1); }
    for(i=0;i<totdoc;i++) {
        fprintf(alphafl,"%.8g\n",a[i]*(double)label[i]);
    }
    fclose(alphafl);
    if(verbosity>=1) {
        printf("done\n");
    }
}

void my_read_examples(char *inputfile, DOC **X, double **Y, long *totdoc, KERNEL_PARM kernel_parm)
{
	long max_docs, max_words_doc;
	long totwords, ll;
	
	printf("Scanning examples..."); fflush(stdout);
	nol_ll(inputfile,&max_docs,&max_words_doc,&ll); /* scan size of input file */
	printf("done\n"); fflush(stdout);
	
	max_words_doc+=10;
	ll+=10;
	max_docs+=2;
	
	*X = (DOC *)my_malloc(sizeof(DOC)*max_docs);         /* feature vectors */
	*Y = (double *)my_malloc(sizeof(double)*max_docs); /* target values */
	
	/* input in svm^light format */
	read_documents(inputfile,*X,*Y,max_words_doc,ll,&totwords,totdoc,&kernel_parm);
}

void read_input_parameters(int argc,char *argv[],char *docfile,char ***testfiles, int *ntestfiles,
						   long *verbosity,long *kernel_cache_size,
						   LEARN_PARM *learn_parm,KERNEL_PARM *kernel_parm)
{
	int i;
	char type[100];
	
	/* set default */
	//strcpy (modelfile, "svm_model");
	strcpy (learn_parm->predfile, "trans_predictions");
	strcpy (learn_parm->alphafile, "");
	(*verbosity)=1;
	
	
	/* set default */
	learn_parm->maxiter=300;
	learn_parm->svm_maxqpsize=100;
	learn_parm->svm_c=1.0;
	learn_parm->eps=0.001;
	learn_parm->biased_hyperplane=12345; /* store random seed */
	learn_parm->remove_inconsistent=4; 
	
	learn_parm->skip_final_opt_check=0;
	learn_parm->svm_newvarsinqp=0;
	learn_parm->svm_iter_to_shrink=-9999;
	(*kernel_cache_size)=40;
	learn_parm->transduction_posratio=-1.0;
	learn_parm->svm_costratio=1.0;
	learn_parm->svm_costratio_unlab=1.0;
	learn_parm->svm_unlabbound=1E-5;
	learn_parm->epsilon_crit=0.001;
	learn_parm->epsilon_a=1E-15;
	learn_parm->compute_loo=0;
	learn_parm->rho=1.0;
	learn_parm->xa_depth=0;
	kernel_parm->kernel_type=0;
	kernel_parm->poly_degree=3;
	kernel_parm->rbf_gamma=1.0;
	kernel_parm->coef_lin=1;
	kernel_parm->coef_const=1;
	kernel_parm->lambda=.4;
	kernel_parm->tree_constant=1;
	kernel_parm->second_kernel=1;
	kernel_parm->first_kernel=1; 
	kernel_parm->normalization=3;
	kernel_parm->combination_type='T'; //no combination
	kernel_parm->vectorial_approach_standard_kernel='S';
	kernel_parm->vectorial_approach_tree_kernel='S';
	kernel_parm->mu=.4; // Default Duffy and Collins Kernel 
	kernel_parm->tree_kernel_params=0; // Default no params
	strcpy(kernel_parm->custom,"empty");
	strcpy(type,"c");
	
	for(i=1;(i<argc) && ((argv[i])[0] == '-');i++) {
		switch ((argv[i])[1]) 
		{ 
			case '?': print_help(); exit(0);
			case 'z': i++; strcpy(type,argv[i]); break;
			case 'v': i++; (*verbosity)=atol(argv[i]); break;
			case 'b': i++; learn_parm->biased_hyperplane=atol(argv[i]); break;
			case 'i': i++; learn_parm->remove_inconsistent=atol(argv[i]); break;
			case 'f': i++; learn_parm->skip_final_opt_check=!atol(argv[i]); break;
			case 'q': i++; learn_parm->svm_maxqpsize=atol(argv[i]); break;
			case 'n': i++; learn_parm->maxiter=atol(argv[i]); break;
			case 'h': i++; learn_parm->svm_iter_to_shrink=atol(argv[i]); break;
			case 'm': i++; (*kernel_cache_size)=atol(argv[i]); break;
			case 'c': i++; learn_parm->svm_c=atof(argv[i]); break;
			case 'w': i++; learn_parm->eps=atof(argv[i]); break;
			case 'p': i++; learn_parm->transduction_posratio=atof(argv[i]); break;
			case 'j': i++; learn_parm->svm_costratio=atof(argv[i]); break;
			case 'e': i++; learn_parm->epsilon_crit=atof(argv[i]); break;
			case 'o': i++; learn_parm->rho=atof(argv[i]); break;
			case 'k': i++; learn_parm->xa_depth=atol(argv[i]); break;
			case 'x': i++; learn_parm->compute_loo=atol(argv[i]); break;
			case 't': i++; kernel_parm->kernel_type=atol(argv[i]); break;
			case 'd': i++; kernel_parm->poly_degree=atol(argv[i]); break;
			case 'g': i++; kernel_parm->rbf_gamma=atof(argv[i]); break;
			case 's': i++; kernel_parm->coef_lin=atof(argv[i]); break;
			case 'r': i++; kernel_parm->coef_const=atof(argv[i]); break;
			case 'u': i++; strcpy(kernel_parm->custom,argv[i]); break;
			case 'l': i++; strcpy(learn_parm->predfile,argv[i]); break;
			case 'a': i++; strcpy(learn_parm->alphafile,argv[i]); break;
			case 'L': i++; kernel_parm->lambda=atof(argv[i]); break;
			case 'T': i++; kernel_parm->tree_constant=atof(argv[i]); break;
			case 'C': i++; kernel_parm->combination_type=*argv[i]; break;
			case 'F': i++; kernel_parm->first_kernel=atoi(argv[i]); break;
			case 'S': i++; kernel_parm->second_kernel=atoi(argv[i]); break;
			case 'V': i++; kernel_parm->vectorial_approach_standard_kernel=*argv[i]; break;
			case 'W': i++; kernel_parm->vectorial_approach_tree_kernel=*argv[i]; break;
			case 'M': i++; kernel_parm->mu=atof(argv[i]); break; 
			case 'N': i++; kernel_parm->normalization=atoi(argv[i]); break; 
			case 'U': i++; kernel_parm->tree_kernel_params=atoi(argv[i]); break; // user defined parameters 
				
				
			default: printf("\nUnrecognized option %s!\n\n",argv[i]);
				print_help();
				exit(0);
		}
	}
	
	LAMBDA = kernel_parm->lambda; // to make faster the kernel evaluation 
	LAMBDA2 = LAMBDA*LAMBDA;
	MU= kernel_parm->mu;
	TKGENERALITY=kernel_parm->first_kernel;
	PARAM_VECT=kernel_parm->tree_kernel_params;
	if(PARAM_VECT == 1) read_input_tree_kernel_param(); // if there is the file tree_kernel.param load paramters
	
	
	if(i>=argc) {
		printf("\nNot enough input parameters!\n\n");
		wait_any_key();
		print_help();
		exit(0);
	}
	
	strcpy (docfile, argv[i]);
    i++;
    *ntestfiles = 0;
    
    int arg_pos = i;
    (*ntestfiles) = argc-i;
    if (*ntestfiles >= 0) {
        *testfiles = (char**)my_malloc(sizeof(char*)*(*ntestfiles));
        i = 0;
        while ( arg_pos+i<argc ) {  
            (*testfiles)[i] = (char*)my_malloc(sizeof(char)*strlen(argv[arg_pos+i]));
            strcpy((*testfiles)[i], argv[arg_pos+i]);
            i++;        
        }
    }
    
    
	if(learn_parm->svm_iter_to_shrink == -9999) {
		if(kernel_parm->kernel_type == LINEAR) 
			learn_parm->svm_iter_to_shrink=2;
		else
			learn_parm->svm_iter_to_shrink=100;
	}
	if(strcmp(type,"c")==0) {
		learn_parm->type=CLASSIFICATION;
	}
	else if(strcmp(type,"r")==0) {
		learn_parm->type=REGRESSION;
	}
	else if(strcmp(type,"p")==0) {
		learn_parm->type=RANKING;
	}
	else if(strcmp(type,"P")==0) {
		learn_parm->type=PERCEPTRON;
	}    
	else if(strcmp(type,"B")==0) {
		learn_parm->type=PERCEPTRON_BATCH;
	}
	
	
	else {
		printf("\nUnknown type '%s': Valid types are 'c' (classification), 'r' regession, and 'p' preference ranking.\n",type);
		wait_any_key();
		print_help();
		exit(0);
	}    
	if((learn_parm->skip_final_opt_check) 
	   && (kernel_parm->kernel_type == LINEAR)) {
		printf("\nIt does not make sense to skip the final optimality check for linear kernels.\n\n");
		learn_parm->skip_final_opt_check=0;
	}    
	if((learn_parm->skip_final_opt_check) 
	   && (learn_parm->remove_inconsistent)) {
		printf("\nIt is necessary to do the final optimality check when removing inconsistent \nexamples.\n");
		wait_any_key();
		print_help();
		exit(0);
	}    
	if((learn_parm->svm_maxqpsize<2)) {
		printf("\nMaximum size of QP-subproblems not in valid range: %ld [2..]\n",learn_parm->svm_maxqpsize); 
		wait_any_key();
		print_help();
		exit(0);
	}
	if((learn_parm->svm_maxqpsize<learn_parm->svm_newvarsinqp)) {
		printf("\nMaximum size of QP-subproblems [%ld] must be larger than the number of\n",learn_parm->svm_maxqpsize); 
		printf("new variables [%ld] entering the working set in each iteration.\n",learn_parm->svm_newvarsinqp); 
		wait_any_key();
		print_help();
		exit(0);
	}
	/*  if(learn_parm->svm_iter_to_shrink<1) {
	 printf("\nMaximum number of iterations for shrinking not in valid range: %ld [1,..]\n",learn_parm->svm_iter_to_shrink);
	 wait_any_key();
	 print_help();
	 exit(0);
	 }*/
	if(learn_parm->svm_c<0) {
		printf("\nThe C parameter must be greater than zero!\n\n");
		wait_any_key();
		print_help();
		exit(0);
	}
	if(learn_parm->transduction_posratio>1) {
		printf("\nThe fraction of unlabeled examples to classify as positives must\n");
		printf("be less than 1.0 !!!\n\n");
		wait_any_key();
		print_help();
		exit(0);
	}
	if(learn_parm->svm_costratio<=0) {
		printf("\nThe COSTRATIO parameter must be greater than zero!\n\n");
		wait_any_key();
		print_help();
		exit(0);
	}
	if(learn_parm->epsilon_crit<=0) {
		printf("\nThe epsilon parameter must be greater than zero!\n\n");
		wait_any_key();
		print_help();
		exit(0);
	}
	if(learn_parm->rho<0) {
		printf("\nThe parameter rho for xi/alpha-estimates and leave-one-out pruning must\n");
		printf("be greater than zero (typically 1.0 or 2.0, see T. Joachims, Estimating the\n");
		printf("Generalization Performance of an SVM Efficiently, ICML, 2000.)!\n\n");
		wait_any_key();
		print_help();
		exit(0);
	}
	if((learn_parm->xa_depth<0) || (learn_parm->xa_depth>100)) {
		printf("\nThe parameter depth for ext. xi/alpha-estimates must be in [0..100] (zero\n");
		printf("for switching to the conventional xa/estimates described in T. Joachims,\n");
		printf("Estimating the Generalization Performance of an SVM Efficiently, ICML, 2000.)\n");
		wait_any_key();
		print_help();
		exit(0);
	}
}

void wait_any_key()
{
	printf("\n(more)\n");
	(void)getc(stdin);
}

// from SVM-light-TK (svm_learn_main.c)
void print_help()
{
	printf("\nTree Kernels in SVM-light %s : SVM Learning module %s\n",VERSION,VERSION_DATE);
	printf("by Alessandro Moschitti, moschitti@info.uniroma2.it\n");
	printf("University of Rome \"Tor Vergata\"\n\n");
	
	copyright_notice();
	printf("   usage: svm_learn [options] example_file model_file\n\n");
	printf("Arguments:\n");
	printf("         example_file-> file with training data\n");
	printf("         model_file  -> file to store learned decision rule in\n");
	
	printf("General options:\n");
	printf("         -?          -> this help\n");
	printf("         -v [0..3]   -> verbosity level (default 1)\n");
	printf("Learning options:\n");
	printf("         -z {c,r,p}  -> select between classification (c), regression (r),\n");
	printf("                        and preference ranking (p) (default classification)\n");
	printf("         -c float    -> C: trade-off between training error\n");
	printf("                        and margin (default [avg. x*x]^-1)\n");
	printf("         -w [0..]    -> epsilon width of tube for regression\n");
	printf("                        (default 0.1)\n");
	printf("         -j float    -> Cost: cost-factor, by which training errors on\n");
	printf("                        positive examples outweight errors on negative\n");
	printf("                        examples (default 1) (see [4])\n");
	printf("         -b [0,1]    -> use biased hyperplane (i.e. x*w+b>0) instead\n");
	printf("                        of unbiased hyperplane (i.e. x*w>0) (default 1)\n");
	printf("         -i [0,1]    -> remove inconsistent training examples\n");
	printf("                        and retrain (default 0)\n");
	printf("Performance estimation options:\n");
	printf("         -x [0,1]    -> compute leave-one-out estimates (default 0)\n");
	printf("                        (see [5])\n");
	printf("         -o ]0..2]   -> value of rho for XiAlpha-estimator and for pruning\n");
	printf("                        leave-one-out computation (default 1.0) (see [2])\n");
	printf("         -k [0..100] -> search depth for extended XiAlpha-estimator \n");
	printf("                        (default 0)\n");
	printf("Transduction options (see [3]):\n");
	printf("         -p [0..1]   -> fraction of unlabeled examples to be classified\n");
	printf("                        into the positive class (default is the ratio of\n");
	printf("                        positive and negative examples in the training data)\n");
	
	printf("Kernel options:\n");
	printf("         -t int      -> type of kernel function:\n");
	printf("                        0: linear (default)\n");
	printf("                        1: polynomial (s a*b+c)^d\n");
	printf("                        2: radial basis function exp(-gamma ||a-b||^2)\n");
	printf("                        3: sigmoid tanh(s a*b + c)\n");
	printf("                        4: user defined kernel from kernel.h\n");
	
	printf("                        5: combination of forest and vector sets according to W, V, S, C options\n");
	printf("                        11: re-ranking based on trees (each instance must have two trees),\n");
	printf("                        12: re-ranking based on vectors (each instance must have two vectors)\n");
	printf("                        13: re-ranking based on both tree and vectors (each instance must have\n");
	printf("                            two trees and two vectors)  \n");
	printf("         -W [S,A]    -> with an 'S', a tree kernel is applied to the sequence of trees of two input\n");
	printf("                        forests and the results are summed;  \n");
	printf("                     -> with an 'A', a tree kernel is applied to all tree pairs from the two forests\n");
	printf("                        (default 'S')\n");
	printf("         -V [S,A]    -> same as before but regarding sequences of vectors are used (default 'S' and\n");
	printf("                        the type of vector-based kernel is specified by the option -S)\n");
	printf("         -S [0,4]    -> kernel to be used with vectors (default polynomial of degree 3,\n");
	printf("                        i.e. -S = 1 and -d = 3)\n");
	printf("         -C [*,+,T,V]-> combination operator between forests and vectors (default 'T')\n");
	printf("                     -> 'T' only the contribution from trees is used (specified by option -W)\n");
	printf("                     -> 'V' only the contribution from vectors is used (specified by option -V)\n");
	printf("                     -> '+' or '*' sum or multiplication of the contributions from vectors and \n");
	printf("                            trees (default T) \n");
	printf("         -F [0,1,2,3]-> 0 = ST kernel, 1 = SST kernel, 2 = SST-bow, 3 = PT kernel (default 1)\n");
	printf("         -M float    -> Mu decay factor for PT kernel (default 0.4)\n");
	printf("         -L float    -> decay factor in tree kernel (default 0.4)\n");
	printf("         -S [0,4]    -> kernel to be used with vectors (default polynomial of degree 3, \n");
	printf("                        i.e. -S = 1 and -d = 3)\n");
	printf("         -T float    -> multiplicative constant for the contribution of tree kernels when -C = '+'\n");
	printf("         -N float    -> 0 = no normalization, 1 = tree normalization, 2 = vector normalization and \n");
	printf("                        3 = tree normalization of both trees and vectors. The normalization is applied \n");
	printf("                        to each individual tree or vector (default 3).\n");
	
	printf("         -u string   -> parameter of user defined kernel\n");
	printf("         -d int      -> parameter d in polynomial kernel\n");
	printf("         -g float    -> parameter gamma in rbf kernel\n");
	printf("         -s float    -> parameter s in sigmoid/poly kernel\n");
	printf("         -r float    -> parameter c in sigmoid/poly kernel\n");
	printf("         -u string   -> parameter of user defined kernel\n");
	
	printf("Optimization options (see [1]):\n");
	printf("         -q [2..]    -> maximum size of QP-subproblems (default 10)\n");
	printf("         -n [2..q]   -> number of new variables entering the working set\n");
	printf("                        in each iteration (default n = q). Set n<q to prevent\n");
	printf("                        zig-zagging.\n");
	printf("         -m [5..]    -> size of cache for kernel evaluations in MB (default 40)\n");
	printf("                        The larger the faster...\n");
	printf("         -e float    -> eps: Allow that error for termination criterion\n");
	printf("                        [y [w*x+b] - 1] >= eps (default 0.001)\n");
	printf("         -h [5..]    -> number of iterations a variable needs to be\n"); 
	printf("                        optimal before considered for shrinking (default 100)\n");
	printf("         -f [0,1]    -> do final optimality check for variables removed\n");
	printf("                        by shrinking. Although this test is usually \n");
	printf("                        positive, there is no guarantee that the optimum\n");
	printf("                        was found if the test is omitted. (default 1)\n");
	printf("Output options:\n");
	printf("         -l string   -> file to write predicted labels of unlabeled\n");
	printf("                        examples into after transductive learning\n");
	printf("         -a string   -> write all alphas to this file after learning\n");
	printf("                        (in the same order as in the training set)\n");
	wait_any_key();
	printf("\nMore details in:\n");
	printf("[1] T. Joachims, Making Large-Scale SVM Learning Practical. Advances in\n");
	printf("    Kernel Methods - Support Vector Learning, B. Schˆlkopf and C. Burges and\n");
	printf("    A. Smola (ed.), MIT Press, 1999.\n");
	printf("[2] T. Joachims, Estimating the Generalization performance of an SVM\n");
	printf("    Efficiently. International Conference on Machine Learning (ICML), 2000.\n");
	printf("[3] T. Joachims, Transductive Inference for Text Classification using Support\n");
	printf("    Vector Machines. International Conference on Machine Learning (ICML),\n");
	printf("    1999.\n");
	printf("[4] K. Morik, P. Brockhausen, and T. Joachims, Combining statistical learning\n");
	printf("    with a knowledge-based approach - A case study in intensive care  \n");
	printf("    monitoring. International Conference on Machine Learning (ICML), 1999.\n");
	printf("[5] T. Joachims, Learning to Classify Text Using Support Vector\n");
	printf("    Machines: Methods, Theory, and Algorithms. Dissertation, Kluwer,\n");
	printf("    2002.\n\n");
	printf("\nFor Tree-Kernel details:\n");
	printf("[6] A. Moschitti, A study on Convolution Kernels for Shallow Semantic Parsing.\n");
	printf("    In proceedings of the 42-th Conference on Association for Computational\n");
	printf("    Linguistic, (ACL-2004), Barcelona, Spain, 2004.\n\n");
	printf("[7] A. Moschitti, Making tree kernels practical for natural language learning.\n");
	printf("    In Proceedings of the Eleventh International Conference for Computational\n");
	printf("    Linguistics, (EACL-2006), Trento, Italy, 2006.\n\n");
	
}

