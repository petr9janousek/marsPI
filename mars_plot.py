from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas

class Plotter:
    def __init__(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.xlim = (0,4)
        self.ylim = (0,25)

    def resetplot(self):
        self.ax.cla()
        self.ax.set_xlim = self.xlim
        self.ax.set_ylim = self.ylim
        self.ax.grid(True)

    def plotpoints(self):
        self.resetplot()
        data = {'apples': 10, 'oranges': 15, 'lemons': 5, 'limes': 20}
        
        names = list(data.keys())
        values = list(data.values())
        self.ax.bar(names,values, color=['coral', 'orange', 'yellowgreen', 'skyblue'])
        self.fig.canvas.draw()