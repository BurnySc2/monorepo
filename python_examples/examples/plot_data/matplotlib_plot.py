from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

CURRENT_DIRECTORY = Path(__file__).parent


def plot_01():
    plt.plot([1, 2, 3, 4])
    plt.ylabel('some numbers')
    # Display plot in Pycharm or terminal
    # plt.show()
    plt.savefig(CURRENT_DIRECTORY / 'matplotlib_plot_01.png')


def plot_02():
    plt.plot([1, 2, 3, 4], [1, 4, 9, 16])
    plt.savefig(CURRENT_DIRECTORY / 'matplotlib_plot_02.png')


def plot_03():
    # evenly sampled time at 200ms intervals
    t = np.arange(0., 5., 0.2)

    # red dashes, blue squares and green triangles
    plt.plot(t, t, 'r--', t, t**2, 'bs', t, t**3, 'g^')
    plt.savefig(CURRENT_DIRECTORY / 'matplotlib_plot_03.png')


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
    plt.savefig(CURRENT_DIRECTORY / 'matplotlib_plot_04.png')


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
    plt.savefig(CURRENT_DIRECTORY / 'matplotlib_plot_05.png')


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
    plt.savefig(CURRENT_DIRECTORY / 'matplotlib_plot_06.png')


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
    plt.savefig(CURRENT_DIRECTORY / 'matplotlib_plot_07.png')


def plot_08():
    # Pie chart, where the slices will be ordered and plotted counter-clockwise:
    labels = 'Frogs', 'Hogs', 'Dogs', 'Logs'
    sizes = [15, 30, 45, 10]
    explode = (0, 0.1, 0, 0)  # only "explode" the 2nd slice (i.e. 'Hogs')

    _fig1, ax1 = plt.subplots()
    ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    plt.savefig(CURRENT_DIRECTORY / 'matplotlib_plot_08.png')


def plot_09():
    x = [10, 50, 30, 20]
    labels = ['Surfing', 'Soccer', 'Baseball', 'Lacrosse']

    _fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(x, labels=labels, autopct='%.1f%%')
    ax.set_title('Sport Popularity')
    plt.tight_layout()
    plt.savefig(CURRENT_DIRECTORY / 'matplotlib_plot_09.png')


def plot_10():
    labels = ['Surfing', 'Soccer', 'Baseball', 'Lacrosse']
    x = [0.1, 0.25, 0.15, 0.2]

    _fig, ax = plt.subplots(figsize=(6, 6))

    ax.pie(x, labels=labels, autopct='%.1f%%')
    ax.set_title('Sport Popularity')
    plt.tight_layout()
    plt.savefig(CURRENT_DIRECTORY / 'matplotlib_plot_10.png')


def plot_11():
    labels = ['Surfing', 'Soccer', 'Baseball', 'Lacrosse']
    x = [10, 50, 30, 20]

    _fig, ax = plt.subplots(figsize=(6, 6))

    ax.pie(
        x,
        labels=labels,
        autopct='%.1f%%',
        wedgeprops={
            'linewidth': 3.0,
            'edgecolor': 'white'
        },
        textprops={'size': 'x-large'}
    )
    ax.set_title('Sport Popularity', fontsize=18)
    plt.tight_layout()
    plt.savefig(CURRENT_DIRECTORY / 'matplotlib_plot_11.png')


def plot_12():
    ages = [17, 18, 19, 20, 21]
    total_population = [21217467, 27958147, 20859088, 28882735, 19978972]
    explode = [0, 0, 0, 0, 0.1]

    _fig, _ax = plt.subplots(figsize=(6, 6))
    plt.pie(total_population, labels=ages, explode=explode, wedgeprops={'edgecolor': 'black'})
    plt.title('A Simple Pie Chart')
    # plt.pie(
    #     total_population,
    #     labels=ages,
    #     explode=explode,
    #     shadow=True,
    #     autopct='%1.1f%%',
    #     wedgeprops={'edgecolor': 'black'}
    # )
    plt.savefig(CURRENT_DIRECTORY / 'matplotlib_plot_12.png')


def plot_13():
    ages = [17, 18, 19, 20, 21]
    total_population = [21217467, 27958147, 20859088, 28882735, 19978972]
    explode = [0, 0, 0, 0, 0.1]

    _fig, _ax = plt.subplots(figsize=(6, 6))

    plt.pie(
        total_population,
        labels=ages,
        explode=explode,
        shadow=True,
        autopct='%1.1f%%',
        wedgeprops={'edgecolor': 'black'}
    )
    plt.savefig(CURRENT_DIRECTORY / 'matplotlib_plot_13.png')


def plot_14():
    # https://matplotlib.org/stable/gallery/pie_and_polar_charts/pie_and_donut_labels.html
    _fig, ax = plt.subplots(figsize=(6, 3), subplot_kw=dict(aspect='equal'))

    recipe = ['375 g flour', '75 g sugar', '250 g butter', '300 g berries']

    data = [float(x.split()[0]) for x in recipe]
    ingredients = [x.split()[-1] for x in recipe]

    def func(pct, allvals):
        absolute = int(np.round(pct / 100. * np.sum(allvals)))
        return f'{pct:.1f}%\n({absolute} g)'

    wedges, _texts, autotexts = ax.pie(data, autopct=lambda pct: func(pct, data), textprops=dict(color='w'))

    ax.legend(wedges, ingredients, title='Ingredients', loc='center left', bbox_to_anchor=(1, 0, 0.5, 1))

    plt.setp(autotexts, size=8, weight='bold')

    ax.set_title('Matplotlib bakery: A pie')

    plt.savefig(CURRENT_DIRECTORY / 'matplotlib_plot_14.png')


def plot_15():
    # https://matplotlib.org/stable/gallery/pie_and_polar_charts/pie_and_donut_labels.html
    _fig, ax = plt.subplots(figsize=(6, 3), subplot_kw=dict(aspect='equal'))

    recipe = ['225 g flour', '90 g sugar', '1 egg', '60 g butter', '100 ml milk', '1/2 package of yeast']

    data = [225, 90, 50, 60, 100, 5]

    wedges, _texts = ax.pie(data, wedgeprops=dict(width=0.5), startangle=-40)

    bbox_props = dict(boxstyle='square,pad=0.3', fc='w', ec='k', lw=0.72)
    kw = dict(arrowprops=dict(arrowstyle='-'), bbox=bbox_props, zorder=0, va='center')

    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1) / 2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: 'right', 1: 'left'}[int(np.sign(x))]
        connectionstyle = f'angle,angleA=0,angleB={ang}'
        kw['arrowprops'].update({'connectionstyle': connectionstyle})
        ax.annotate(
            recipe[i], xy=(x, y), xytext=(1.35 * np.sign(x), 1.4 * y), horizontalalignment=horizontalalignment, **kw
        )

    ax.set_title('Matplotlib bakery: A donut')

    plt.savefig(CURRENT_DIRECTORY / 'matplotlib_plot_15.png')


def main():
    plot_01()
    plot_02()
    plot_03()
    plot_04()
    plot_05()
    plot_06()
    plot_07()
    plot_08()
    plot_09()
    plot_10()
    plot_11()
    plot_12()
    plot_13()
    plot_14()
    plot_15()


if __name__ == '__main__':
    main()
