import numpy as np
from scipy.optimize import curve_fit
import matplotlib as mpl
mpl.rcParams.update({
    "text.usetex": True,
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica"]})

# mpl.rcParams.update({
#     "text.usetex": True,
#     "font.family": "serif",
#     "font.serif": ["Palatino"],
# })
import matplotlib.pyplot as pl

def fit_func(x, beta_1, beta_2) -> np.ndarray:
    return np.log(1 + beta_1 * x) / (1 + beta_2 * x)
    # return beta_1 * np.log(1 + beta_2 * x) / (1 + x)

def main() -> None:
    ydata = np.array([
        0.005717731546610594,
        0.033499978482723236,
        0.05529705435037613,
        0.07243339717388153,
        0.08747466653585434,
        0.0993848368525505,
        0.11006410419940948,
        0.12053751200437546,
        0.12830746173858643,
        0.13458271324634552,
        0.14003196358680725,
        0.1448056846857071,
        0.14875461161136627,
        0.15177837014198303,
        0.1544429063796997,
        0.1571042835712433,
        0.15915198624134064,
        0.16125325858592987,
        0.16271990537643433,
        0.1640692800283432,
        0.16541659832000732,
        0.1661401242017746,
        0.1669883131980896,
        0.16784413158893585,
        0.16737183928489685
    ])

    xdata = np.linspace(0, 12./25., 25)

    initial_guess = np.array([1., 1., 1.])
    p_opt, p_cov = curve_fit(fit_func, xdata, ydata)
    print(p_opt)

    # Plot
    fig, ax = pl.subplots(1, 1)
    ax.plot(xdata, ydata, 'ro')
    ax.plot(xdata, fit_func(xdata, *p_opt), 'g-')
    args = dict(transform=ax.transAxes, color='g')
    # ax.text(0.3, 0.5, r'$Z(x) = \frac{\beta_1 \log(1 + \beta_2 x)}{1 + x}$', fontsize=24, **args)
    ax.text(0.3, 0.5, r'$Z(x) = \frac{\log(1 + \beta_1 x)}{1 + \beta_2 x}$', fontsize=24, **args)
    ax.text(0.3, 0.35, r'$\beta_1 = {:0.4f}, \beta_2 = {:0.4f}$'.format(p_opt[0], p_opt[1]), fontsize=16, **args)
    ax.set_xlabel('normalized loop index')
    ax.set_ylabel('pillow height')
    pl.show()

if __name__ == '__main__':
    main()
