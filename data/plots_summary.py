import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def plot_preprocessing():
    df = pd.read_csv('./preprocess_scalability.csv')
    x = df['traces']
    y = df['real']
    plt.figure(figsize=(8,4))
    plt.xlabel('Number of Traces', fontsize=18)
    plt.ylabel('Time (s)')
    plt.plot(x,y)
    plt.savefig('./preprocessing.png', bbox_inches='tight')

def plot_micro():
    df_potara = pd.read_csv('./potara_microscalability.csv')
    df_summarizer = pd.read_csv('./graph_microscalability.csv')
    plt.figure(figsize=(8,4))
    plt.xlabel('Number of Documents', fontsize=18)
    plt.ylabel('Time (s)', fontsize=18)
    plt.plot(df_potara['tasks'],df_potara['real'], color='red', label='Potara')
    plt.plot(df_summarizer['tasks'], df_summarizer['real'], color='blue', label='Summarizer')
    #plt.ylim(-0.01, np.max(df_summarizer['real'] + 1))
    plt.legend( loc='lower right', ncol=1)
    plt.tight_layout()
    plt.savefig('./microscalability.png', bbox_inches='tight')

def plot_macro():
    df_potara = pd.read_csv('./potara_macroscalability.csv')
    df_summarizer = pd.read_csv('./graph_macroscalability.csv')
    plt.figure(figsize=(8,4))
    plt.xlabel('Number of Traces', fontsize=18)
    plt.ylabel('Time (s)', fontsize=18)
    plt.plot(df_potara['traces'],df_potara['real'], color='red', label='Potara')
    plt.plot(df_summarizer['traces'], df_summarizer['real'], color='blue', label='Summarizer')
    #plt.ylim(-0.01, np.max(df_summarizer['real'] + 1))
    plt.legend( loc='lower right', ncol=1)
    plt.tight_layout()
    plt.savefig('./macroscalability.png', bbox_inches='tight')

def main():
    plot_preprocessing()
    plot_micro()
    plot_macro()

if __name__ == '__main__':
    main()