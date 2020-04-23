import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def plot_events_cdf():
    df = pd.read_csv('num_events.csv')
    num_elems = len(df['Num_Events'])
    x = np.sort(df['Num_Events'])
    y = np.array(range(num_elems))/float(num_elems)
    plt.figure(figsize=(8,4))
    plt.xlabel('Number of Events', fontsize=18)
    plt.ylabel('CDF', fontsize=18)
    plt.plot(x, y, color='black')
    plt.xlim(-0.01, 400)
    plt.ylim(-0.01, 1.01)
    plt.tight_layout()
    plt.savefig('./events_cdf.png', bbox_inches='tight')

def plot_tasks_cdf():
    df = pd.read_csv('num_tasks.csv')
    num_elems = len(df['Num_Tasks'])
    x = np.sort(df['Num_Tasks'])
    y = np.array(range(num_elems))/float(num_elems)
    plt.figure(figsize=(8,4))
    plt.xlabel('Number of Tasks', fontsize=18)
    plt.ylabel('CDF', fontsize=18)
    plt.plot(x, y, color='black')
    plt.xlim(-0.01, 25)
    plt.ylim(-0.01, 1.01)
    plt.tight_layout()
    plt.savefig('./tasks_cdf.png', bbox_inches='tight')

def plot_summary_times_cdf():
    df = pd.read_csv('summary_time.csv')
    num_elems = len(df['Total_Time'])
    x1 = np.sort(df['Total_Time'])
    y = np.array(range(num_elems))/float(num_elems)
    x2 = np.sort(df['Load_Time'])
    x3 = np.sort(df['Gen_Time'])
    plt.figure(figsize=(8,4))
    plt.xlabel('Latency (s)', fontsize=20)
    plt.ylabel('CDF', fontsize=20)
    plt.plot(x2, y, color='red', label='Data Load Time')
    plt.plot(x3, y, color='blue', label='Generation Time')
    plt.plot(x1, y, color='black', label='Total Time')
    plt.legend( loc='lower right', ncol=1)
    plt.xlim(-0.01, 0.25)
    plt.ylim(-0.01, 1.01)
    plt.tight_layout()
    plt.savefig('./summary_cdf.png', bbox_inches='tight')

def main():
    plot_events_cdf()
    plot_tasks_cdf()
    plot_summary_times_cdf()

if __name__ == '__main__':
    main()