import numpy as np
from empirical_bayes import estimate_likelihood
from utils import load_data_as_pandas


if __name__ == '__main__':
    import os
    import argparse
    import pandas as pd
    import matplotlib
    import matplotlib.pyplot as plt
    import seaborn as sns
    parser = argparse.ArgumentParser(description='Bayesian tensor filtering for dose-response modeling.')
    
    # General settings
    parser.add_argument('--basedir', default='doseresponse/data/sim/', help='Directory where all results will be saved.')
    parser.add_argument('--plotdir', default='doseresponse/plots/sim/', help='Directory where all results will be saved.')
    parser.add_argument('--big_plot', action='store_true', help='If true and plot is true, a single huge plot will be made.')
    parser.add_argument('--seed', type=int, default=4, help='The pseudo-random number generator seed.')
    parser.add_argument('--truth', action='store_true', help='If true, this is simulated data with ground truth known.')
    
    # tumors = [2, 4]
    # drugs = [0, 3, 7]
    

    # Get the arguments from the command line
    args = parser.parse_args()

    # Load the data
    df = load_data_as_pandas(os.path.join(args.basedir, 'data.csv'))

    print('Loading the model fit and true effects')
    resultsdir = os.path.join(args.basedir, 'seed{}'.format(args.seed))
    btf = np.load(os.path.join(resultsdir, 'btf.npy'))
    if args.truth:
        truth = np.load(os.path.join(args.basedir, 'truth.npy'))
    # held_out = np.load(os.path.join(resultsdir, 'held_out.npy'))
    # pairs = [tuple(x) for x in held_out.T]
    # paired_tumors = []
    # for tumor1 in range(held_out[0].max()+1):
    #     print(tumor1)
    #     for tumor2 in range(tumor1+1, held_out[0].max()+1):
    #         matches = []
    #         for drug in range(0,held_out[1].max()+1):
    #             if (tumor1, drug) in pairs and (tumor2, drug) in pairs:
    #                 matches.append(drug)
    #         if len(matches) >= 3:
    #             paired_tumors.append((tumor1, tumor2, matches))
    # for (tumor1, tumor2, matches) in paired_tumors:
    #     print(tumor1, tumor2, matches)

    print('Loading data and performing empirical Bayes likelihood estimate')
    Y, likelihood, cells, drugs, concentrations, control_obs = estimate_likelihood(df, tensor_outcomes=True, plot=False)

    print(Y.shape)
    # print('Getting real matches')
    # for (tumor1, tumor2, matches) in paired_tumors:
    #     present_matches = []
    #     for drug in matches:
    #         if np.all(np.isnan(Y[tumor1, drug])) or np.all(np.isnan(Y[tumor2, drug])):
    #             continue
    #         present_matches.append(drug)
    #     if len(present_matches) >= 3:
    #         print(tumor1, tumor2, matches)
    
    # tumors = [40, 238, 280]
    # drugs = [14, 48, 65]
    tumors = [46, 124]
    drugs = [4, 23, 40]

    print('Plotting results')
    with sns.axes_style('white'):
        plt.rc('font', weight='bold')
        plt.rc('grid', lw=3)
        plt.rc('lines', lw=3)
        matplotlib.rcParams['pdf.fonttype'] = 42
        matplotlib.rcParams['ps.fonttype'] = 42

        for i, ridx in enumerate(tumors):
            for j, cidx in enumerate(drugs):
                for k in range(Y.shape[2]):
                    plt.scatter(np.full(Y.shape[-1],concentrations[k]), Y[ridx,cidx,k], color='gray', label='Observations' if k == 0 else None)
                if args.truth:
                    plt.plot(concentrations, truth[ridx, cidx], color='black', label='Truth', lw=3)
                plt.plot(concentrations, btf[:,ridx,cidx].mean(axis=0), color='darkorange', label='BTF fit', lw=3)
                obs = likelihood.sample(1, size=(1000, len(concentrations)))
                obs *= btf[np.random.choice(btf.shape[0], size=1000), ridx, cidx]
                obs_lower = np.percentile(obs, 25, axis=0)
                obs_upper = np.percentile(obs, 75, axis=0)
                plt.fill_between(concentrations, obs_lower, obs_upper, color='orange', alpha=0.5)
                plt.ylim([0, np.nanmax(Y)+0.01])

                if args.truth and i == 0 and j == len(drugs) - 1:
                    handles, labels = plt.gca().get_legend_handles_labels()
                    order = [2,0,1]
                    legend_props = {'weight': 'bold', 'size': 14}
                    plt.legend([handles[idx] for idx in order],[labels[idx] for idx in order], loc='upper right', prop=legend_props)
                plt.xlabel('Log(concentration)', fontsize=18, weight='bold')
                plt.ylabel('Survival %', fontsize=18, weight='bold')
                plt.savefig(os.path.join(args.plotdir, 'example-tumor{}-drug{}.pdf'.format(i+4,j+4)), bbox_inches='tight') # TEMP +1 => +4
                plt.close()




