import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO


def plot_weekly_plan(**kwargs):
    fig = plt.figure(figsize=(3, 3), dpi=100)
    ax = fig.add_subplot('111')
    x = np.random.randn(500)
    y = np.random.randn(500)
    ax.plot(x, y, '.', color='r', markersize=10, alpha=0.2)
    ax.set_title('Behold')

    strIO = BytesIO()
    plt.savefig(strIO, dpi=fig.dpi)
    strIO.seek(0)
    return strIO
