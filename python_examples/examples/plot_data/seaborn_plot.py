from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

# Apply the default theme
sns.set_theme()

CURRENT_DIRECTORY = Path(__file__).parent


def plot_01():
    # Load an example dataset
    tips = sns.load_dataset('tips')
    # Create a visualization
    sns.relplot(
        data=tips,
        x='total_bill',
        y='tip',
        col='time',
        hue='smoker',
        style='smoker',
        size='size',
    )

    # Save as image via
    plt.savefig(CURRENT_DIRECTORY / 'seaborn_plot_01.png')

    # Plotting in pycharm / terminal doesn't seem to work
    # plt.show()


def plot_02():
    dots = sns.load_dataset('dots')
    sns.relplot(
        data=dots,
        kind='line',
        x='time',
        y='firing_rate',
        col='align',
        hue='choice',
        size='coherence',
        style='choice',
        facet_kws=dict(sharex=False),
    )

    plt.savefig(CURRENT_DIRECTORY / 'seaborn_plot_02.png')


def plot_03():
    fmri = sns.load_dataset('fmri')
    sns.relplot(
        data=fmri,
        kind='line',
        x='timepoint',
        y='signal',
        col='region',
        hue='event',
        style='event',
    )

    plt.savefig(CURRENT_DIRECTORY / 'seaborn_plot_03.png')


def plot_04():
    penguins = sns.load_dataset('penguins')
    sns.jointplot(data=penguins, x='flipper_length_mm', y='bill_length_mm', hue='species')
    plt.savefig(CURRENT_DIRECTORY / 'seaborn_plot_04.png')


def plot_05():
    penguins = sns.load_dataset('penguins')
    g = sns.PairGrid(penguins, hue='species', corner=True)
    g.map_lower(sns.kdeplot, hue=None, levels=5, color='.2')
    g.map_lower(sns.scatterplot, marker='+')
    g.map_diag(sns.histplot, element='step', linewidth=0, kde=True)
    g.add_legend(frameon=True)
    g.legend.set_bbox_to_anchor((.61, .6))

    plt.savefig(CURRENT_DIRECTORY / 'seaborn_plot_05.png')


def main():
    plot_01()
    plot_02()
    plot_03()
    plot_04()
    plot_05()


if __name__ == '__main__':
    main()
