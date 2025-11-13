
import matplotlib.pyplot as plt
def plot_equity_curve(eq,title="Equity Curve"):
    plt.figure(figsize=(12,6))
    plt.plot(eq.index,eq.values)
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()
    return plt
