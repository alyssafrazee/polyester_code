#!/usr/bin/python

### code to extract specific error calculations from a GemErr error model
### http://www.biomedcentral.com/1471-2164/13/74

import gzip
import cPickle
import numpy as np

def get_matrices(gzipFile, paired):
    f = gzip.open(gzipFile)
    if paired:
        readLen = cPickle.load(f)
        mx1 = cPickle.load(f)
        mx2 = cPickle.load(f)
        f.close()
        return mx1, mx2
    else:
        readLen = cPickle.load(f)
        mx = cPickle.load(f)
        f.close()
        return mx

def get_model(m):
    """m is a 7-D matrix generated by GemErr.py"""
    for dim in [2,3,4,5]:
        m = np.add.reduce(m, 2) 
        # we will not address preceding / following bases
    
    inds={'A':0, 'T':1, 'G':2, 'C':3, 'N':4}
    ret = np.zeros((101,5,5))
    for pos in xrange(len(ret)):
        for refBase in ['A', 'T', 'G', 'C', 'N']:
            for readBase in ['A', 'T', 'G', 'C', 'N']:
                refi = inds[refBase]
                readi = inds[readBase]
                if m[pos][refi][5] == 0:
                    # there were no reference bases with this nucleotide at this position
                    # so we will just sequence this base as is and not worry about errors.
                    ret[pos][refi][readi] = 1 if refi==readi else 0
                elif refi == readi:
                    num_errors = sum(m[pos][refi][j] for j in range(5) if j != refi)
                    num_correct = m[pos][refi][5] - num_errors
                    correct_prob = 1 - (float(num_errors) / num_correct)
                    ret[pos][refi][readi] = correct_prob
                else:
                    # nucleotide-specific error probability
                    transition_prob = float(m[pos][refi][readi]) / m[pos][refi][5]
                    ret[pos][refi][readi] = transition_prob

    return ret

def save_model(array, outf):
    """write text file to disk containing this error model specification
    to be read into R later"""
    inds={'A':0, 'T':1, 'G':2, 'C':3, 'N':4}
    with open(outf, 'w') as f:
        f.write('errmodel\treadA\treadT\treadG\treadC\treadN\tpos\n')
        for pos in xrange(len(array)):
            for refBase in ['A', 'T', 'G', 'C', 'N']:
                f.write('ref'+refBase+'\t')
                for readBase in ['A', 'T', 'G', 'C', 'N']:
                    f.write(str(array[pos][inds[refBase]][inds[readBase]])+'\t')
                    if readBase == 'N':
                        f.write(str(int(pos))+'\n')

def release_models(modelpath, modelname, outfolder, paired):
    if paired:
        mx1, mx2 = get_matrices(modelpath+'/'+modelname+'_p.gzip', True)
        mate1 = get_model(mx1)
        mate2 = get_model(mx2)
        save_model(mate1, outfolder+'/'+modelname+'_mate1')
        save_model(mate2, outfolder+'/'+modelname+'_mate2')
    else:
        mx = get_matrices(modelpath+'/'+modelname+'_s.gzip', False)
        model = get_model(mx)
        save_model(model, outfolder+'/'+modelname+'_single')

### create error model files for release
model_path = 'GemSIM_v1.6/models'
outfolder = './error_models'
for model in ['ill100v4', 'ill100v5', 'r454ti']:
    release_models(model_path, model, outfolder, False)
    if model != 'r454ti':
        release_models(model_path, model, outfolder, True)
