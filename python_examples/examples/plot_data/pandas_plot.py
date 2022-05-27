from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# plt.close("all")

CURRENT_DIRECTORY = Path(__file__).parent


def plot_01():
    ts = pd.Series(np.random.randn(1000), index=pd.date_range('1/1/2000', periods=1000))

    ts = ts.cumsum()

    ts.plot()
    # Display plot in Pycharm or terminal
    # plt.show()
    plt.savefig(CURRENT_DIRECTORY / 'pandas_plot_01.png')


def plot_02():
    ts = pd.Series(np.random.randn(1000), index=pd.date_range('1/1/2000', periods=1000))
    df = pd.DataFrame(np.random.randn(1000, 4), index=ts.index, columns=list('ABCD'))

    df = df.cumsum()

    df.plot()
    plt.savefig(CURRENT_DIRECTORY / 'pandas_plot_02.png')


def plot_03():
    ts = pd.Series(np.random.randn(1000), index=pd.date_range('1/1/2000', periods=1000))
    df = pd.DataFrame(np.random.randn(1000, 4), index=ts.index, columns=list('ABCD'))

    df3 = pd.DataFrame(np.random.randn(1000, 2), columns=['B', 'C']).cumsum()

    df3['A'] = pd.Series(list(range(len(df))))

    df3.plot(x='A', y='B')

    plt.savefig(CURRENT_DIRECTORY / 'pandas_plot_03.png')


def plot_04():
    ts = pd.Series(np.random.randn(1000), index=pd.date_range('1/1/2000', periods=1000))
    df = pd.DataFrame(np.random.randn(1000, 4), index=ts.index, columns=list('ABCD'))

    df.iloc[5].plot(kind='bar')

    plt.savefig(CURRENT_DIRECTORY / 'pandas_plot_04.png')


def plot_05():
    ts = pd.Series(np.random.randn(1000), index=pd.date_range('1/1/2000', periods=1000))
    df = pd.DataFrame(np.random.randn(1000, 4), index=ts.index, columns=list('ABCD'))

    plt.axhline(0, color='k')
    df.iloc[5].plot.bar()

    plt.savefig(CURRENT_DIRECTORY / 'pandas_plot_05.png')


def plot_06():
    df2 = pd.DataFrame(np.random.rand(10, 4), columns=['a', 'b', 'c', 'd'])

    df2.plot.bar()
    plt.savefig(CURRENT_DIRECTORY / 'pandas_plot_06.png')


def plot_07():
    df2 = pd.DataFrame(np.random.rand(10, 4), columns=['a', 'b', 'c', 'd'])
    df2.plot.bar(stacked=True)

    plt.savefig(CURRENT_DIRECTORY / 'pandas_plot_07.png')


def plot_08():

    df2 = pd.DataFrame(np.random.rand(10, 4), columns=['a', 'b', 'c', 'd'])
    df2.plot.barh(stacked=True)
    plt.savefig(CURRENT_DIRECTORY / 'pandas_plot_08.png')


def plot_09():

    df4 = pd.DataFrame(
        {
            'a': np.random.randn(1000) + 1,
            'b': np.random.randn(1000),
            'c': np.random.randn(1000) - 1,
        },
        columns=['a', 'b', 'c'],
    )

    df4.plot.hist(alpha=0.5)
    plt.savefig(CURRENT_DIRECTORY / 'pandas_plot_09.png')


def plot_10():
    df4 = pd.DataFrame(
        {
            'a': np.random.randn(1000) + 1,
            'b': np.random.randn(1000),
            'c': np.random.randn(1000) - 1,
        },
        columns=['a', 'b', 'c'],
    )

    df4.plot.hist(stacked=True, bins=20)
    plt.savefig(CURRENT_DIRECTORY / 'pandas_plot_10.png')


def plot_11():
    df = pd.DataFrame(np.random.rand(10, 4), columns=['a', 'b', 'c', 'd'])

    df.plot.area()
    plt.savefig(CURRENT_DIRECTORY / 'pandas_plot_11.png')


def plot_12():
    series = pd.Series(3 * np.random.rand(4), index=['a', 'b', 'c', 'd'], name='series')

    series.plot.pie(figsize=(6, 6))
    plt.savefig(CURRENT_DIRECTORY / 'pandas_plot_12.png')


def plot_13():
    df = pd.DataFrame(3 * np.random.rand(4, 2), index=['a', 'b', 'c', 'd'], columns=['x', 'y'])

    df.plot.pie(subplots=True, figsize=(8, 4))
    plt.savefig(CURRENT_DIRECTORY / 'pandas_plot_13.png')


def plot_14():
    series = pd.Series(3 * np.random.rand(4), index=['a', 'b', 'c', 'd'], name='series')
    series.plot.pie(
        labels=['AA', 'BB', 'CC', 'DD'],
        colors=['r', 'g', 'b', 'c'],
        autopct='%.2f',
        fontsize=20,
        figsize=(6, 6),
    )

    plt.savefig(CURRENT_DIRECTORY / 'pandas_plot_14.png')


def plot_15():
    series = pd.Series([0.1] * 4, index=['a', 'b', 'c', 'd'], name='series2')

    series.plot.pie(figsize=(6, 6))
    plt.savefig(CURRENT_DIRECTORY / 'pandas_plot_15.png')


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
