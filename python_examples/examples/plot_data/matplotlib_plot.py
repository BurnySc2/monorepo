import matplotlib.pyplot as plt
import numpy as np


def plot_01():
    plt.plot([1, 2, 3, 4])
    plt.ylabel('some numbers')
    # Display plot in Pycharm or terminal
    # plt.show()
    plt.savefig('matplotlib_plot_01.png')


def plot_02():
    plt.plot([1, 2, 3, 4], [1, 4, 9, 16])
    plt.savefig('matplotlib_plot_02.png')


def plot_03():
    # evenly sampled time at 200ms intervals
    t = np.arange(0., 5., 0.2)

    # red dashes, blue squares and green triangles
    plt.plot(t, t, 'r--', t, t**2, 'bs', t, t**3, 'g^')
    plt.savefig('matplotlib_plot_03.png')


def plot_04():
    data = {
        'a': np.arange(50),
        'c': np.random.randint(0, 50, 50),
        'd': np.random.randn(50),
    }
    data['b'] = data['a'] + 10 * np.random.randn(50)
    data['d'] = np.abs(data['d']) * 100

    plt.scatter('a', 'b', c='c', s='d', data=data)
    plt.xlabel('entry a')
    plt.ylabel('entry b')
    plt.savefig('matplotlib_plot_04.png')


def plot_05():
    mu, sigma = 100, 15
    x = mu + sigma * np.random.randn(10000)

    # the histogram of the data
    _n, _bins, _patches = plt.hist(x, 50, density=1, facecolor='g', alpha=0.75)

    plt.xlabel('Smarts')
    plt.ylabel('Probability')
    plt.title('Histogram of IQ')
    plt.text(60, .025, r'$\mu=100,\ \sigma=15$')
    plt.axis([40, 160, 0, 0.03])
    plt.grid(True)
    plt.savefig('matplotlib_plot_05.png')


def plot_06():
    _ax = plt.subplot()

    t = np.arange(0.0, 5.0, 0.01)
    s = np.cos(2 * np.pi * t)
    _line, = plt.plot(t, s, lw=2)

    plt.annotate(
        'local max',
        xy=(2, 1),
        xytext=(3, 1.5),
        arrowprops=dict(facecolor='black', shrink=0.05),
    )

    plt.ylim(-2, 2)
    plt.savefig('matplotlib_plot_06.png')


def plot_07():
    # Fixing random state for reproducibility
    np.random.seed(19680801)

    # make up some data in the open interval (0, 1)
    y = np.random.normal(loc=0.5, scale=0.4, size=1000)
    y = y[(y > 0) & (y < 1)]
    y.sort()
    x = np.arange(len(y))

    # plot with various axes scales
    plt.figure()

    # linear
    plt.subplot(221)
    plt.plot(x, y)
    plt.yscale('linear')
    plt.title('linear')
    plt.grid(True)

    # log
    plt.subplot(222)
    plt.plot(x, y)
    plt.yscale('log')
    plt.title('log')
    plt.grid(True)

    # symmetric log
    plt.subplot(223)
    plt.plot(x, y - y.mean())
    plt.yscale('symlog', linthresh=0.01)
    plt.title('symlog')
    plt.grid(True)

    # logit
    plt.subplot(224)
    plt.plot(x, y)
    plt.yscale('logit')
    plt.title('logit')
    plt.grid(True)
    # Adjust the subplot layout, because the logit one may take more space
    # than usual, due to y-tick labels like "1 - 10^{-3}"
    plt.subplots_adjust(
        top=0.92,
        bottom=0.08,
        left=0.10,
        right=0.95,
        hspace=0.25,
        wspace=0.35,
    )
    plt.savefig('matplotlib_plot_07.png')


def plot_08():
    # Pie chart, where the slices will be ordered and plotted counter-clockwise:
    labels = 'Frogs', 'Hogs', 'Dogs', 'Logs'
    sizes = [15, 30, 45, 10]
    explode = (0, 0.1, 0, 0)  # only "explode" the 2nd slice (i.e. 'Hogs')

    _fig1, ax1 = plt.subplots()
    ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    plt.savefig('matplotlib_plot_08.png')


def main():
    plot_01()
    plot_02()
    plot_03()
    plot_04()
    plot_05()
    plot_06()
    plot_07()
    plot_08()


if __name__ == '__main__':
    main()
