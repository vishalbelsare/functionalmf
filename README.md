# functionalmf: Bayesian factorization of functional matrices
This package implements a Bayesian tensor filtering (BTF), a method for factorizing matrices where each entry is an entire curve or function, rather than a scalar. Install with:
```
pip install functionalmf
```

Please open an issue if you have any trouble!

## Factorizing a functional matrix with `functionalmf`
The general problem that `functionalmf` solves is that you have data in a 4-dimensional array:
```python
import numpy as np
data = np.load('examples/data.npy')
print('Data shape is {}'.format(data.shape))
# Output: (10, 10, 10, 3)
```
And you want to factorize the matrix under the assumption:
- **dim 1:** rows with latent attributes that remain fixed
- **dim 2:** columns with latent attributes that change mostly-smoothly in **dim 3**
- **dim 4:** replicates. if you have only a 3-tensor, just make this dim size 1.

The specific class you should use depends on the likelihood function for your observations.

### Gaussian observations
If your observations are real-valued and generally assumed to follow a normal distribution for errors:
```python
from functionalmf.factor import GaussianBayesianTensorFiltering

def init_model(nembeds=3, tf_order=2, lam2=0.1, sigma2=0.5, nu2=1):
    # Setup the model
    return GaussianBayesianTensorFiltering(nrows, ncols, ndepth,
                                                          nembeds=nembeds, tf_order=tf_order,
                                                          sigma2_init=sigma2, nthreads=1,
                                                          lam2_init=lam2, nu2_init=nu2)

model = init_model()
```
You can then run the Gibbs sampler on the model with:
```python
results = model.run_gibbs(Y_missing, nburn=nburn, nthin=nthin, nsamples=nsamples, print_freq=50, verbose=True)
```
And you can get the sampler results along with the inferred means:
```python
Ws = results['W']
Vs = results['V']
Tau2s = results['Tau2']
lam2s = results['lam2']
sigma2s = results['sigma2']

# Get the Bayes estimate
Mu_hat = np.einsum('znk,zmtk->znmt', Ws, Vs)
Mu_hat_mean = Mu_hat.mean(axis=0)
```
See `examples/gaussian_tensor_filtering.py` for a full example. Results should look like:

![Visualization of the Binomial functional matrix factorization](https://github.com/tansey/functionalmf/raw/master/img/gaussian-tensor-filtering.png)

### Binomial, Bernoulli, or Negative Binomial observations
If your observations are binomial (or binary or negative binomial), you can use the Binomial sampler:
```python
from functionalmf.factor import BinomialBayesianTensorFiltering
def init_model(nembeds=3, tf_order=2, lam2=0.1, sigma2=0.5):
    # Setup the model
    return BinomialBayesianTensorFiltering(nrows, ncols, ndepth,
                                                          nembeds=nembeds, tf_order=tf_order,
                                                          sigma2_init=sigma2, nthreads=1,
                                                          lam2_init=lam2)

model = init_model()
```
The result follows the Gaussian example above, EXCEPT you need to pass the resulting means through the inverse logit transform:
```
from functionalmf.utils import ilogit
Mu_hat = ilogit(np.einsum('znk,zmtk->znmt', Ws, Vs))
Mu_hat_mean = Mu_hat.mean(axis=0)
```
See `examples/binomial_tensor_filtering.py` for a full example. Results should look like:

![Visualization of the Binomial functional matrix factorization](https://github.com/tansey/functionalmf/raw/master/img/binomial-tensor-filtering.png)


### Black box observations (Poisson example)
If you have a likelihood that is not in one of the conjugate or conditionally-conjugate categories above, you can use the non-conjugate sampler. This example focuses on a Poisson likelihood, common with count data, where the latent rate is constrained to be positive everywhere:
```python
from functionalmf.factor import ConstrainedNonconjugateBayesianTensorFiltering

def rowcol_loglikelihood(Y, WV, row=None, col=None):
    if row is not None:
        Y = Y[row]
    if col is not None:
        Y = Y[:,col]
    # missing = np.isnan(Y)
    if len(Y.shape) > len(WV.shape):
        WV = WV[...,None]
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        z = np.nansum(poisson.logpmf(Y, WV))
    return z

def init_model(tf_order=0, lam2=0.1, sigma2=0.5):
    # Constraints requiring positive means
    C_zero = np.concatenate([np.eye(ndepth), np.zeros((ndepth,1))], axis=1)
    
    # Setup the model
    return ConstrainedNonconjugateBayesianTensorFiltering(nrows, ncols, ndepth,
                                                          rowcol_loglikelihood,
                                                          C_zero,
                                                          nembeds=nembeds, tf_order=tf_order,
                                                          sigma2_true=sigma2, nthreads=1,
                                                          lam2_true=lam2)   
```
The code requires you provide it a log-likelihood function (`rowcol_loglikelihood`) that can optionally accept a `row` or `column` specifier. If those are specified, the corresponding `WV` matrix is limited to that specific row or column.

The rest of the code works the same as the above Gaussian sampler case. The results should look like this:

![Visualization of the Poisson functional matrix factorization](https://github.com/tansey/functionalmf/raw/master/img/poisson-tensor-filtering.png)

The blue bars show the NMF-based EP approximation that centers the sampler. The orange line is the fit.

See `examples/poisson_tensor_filtering.py` for the complete example code.

## Dose-Response Modeling
Dealing with dose-response modeling in multi-drug, multi-sample studies requires handling experimental technical error. An example dose-response model is not part of the `functionalmf` package, but is implemented on top of it. See `doseresponse/` for a complete example of dose-response modeling.

## Generalized analytic slice sampling
Included in the BTF code at `functionalmf/gass.py` is a standalone tool for sampling from posteriors with truncated multivariate normal priors. The model enables linear constraints and arbitrary likelihoods. The script includes a runnable example of a truncated, monotone GP. The result looks something like this:

![Visualization of the monotone GP](https://github.com/tansey/functionalmf/raw/master/img/gass.png)

Orange bands represent 90% Bayesian credible intervals.

# Installation issues
Known issues that come up installing and using the library are below.

- You may have trouble with `sksparse` on MacOSX using conda. A solution is to install suitesparse: `conda install -c conda-forge suitesparse`

# Citing this code
If you use this code, please cite the following:
```
Bayesian Tensor Filtering: Smooth, Locally-Adaptive Factorization of Functional Matrices
W. Tansey, C. Tosh, D.M. Blei
arXiv preprint arXiv:1906.?
```
Bibtex entry:
```
@article{tansey:etal:2019:btf,
  title={Bayesian Tensor Filtering: Smooth, Locally-Adaptive Factorization of Functional Matrices},
  author={Tansey, Wesley and Tosh, Christopher and Blei, David M.},
  journal={arXiv preprint arXiv:1906.?},
  year={2019}
}
```

