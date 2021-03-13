import sys
import time
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pandas as pd
import argparse
# A arg type converter
def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

# Create a parser
parser = argparse.ArgumentParser(description='NTU 607 TMtrace visualizer',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
                            
parser.add_argument('--name', metavar='Benchmark name(very important)', default= 'ssca2')
parser.add_argument('--compress', metavar='Boolean of compress operation', type= str2bool, default= False)
parser.add_argument('--path', metavar='Path to our trace file', default=None)
parser.add_argument('--debug', metavar='Debug flag', type= str2bool, default=False)
parser.add_argument('--csv', metavar='Boolean of store a csv file',type= str2bool , default= False)
parser.add_argument('--npy', metavar='Path to our trace numpy file', default=None)
parser.add_argument('--endpoint', metavar='Plot endpoint', type= int, default= -1)
parser.add_argument('--startpoint', metavar='Plot startpoint', type= int, default= 0)
parser.add_argument('--encoder', metavar='Encoder for parse trace file', default= 'event2')
parser.add_argument('--savefigure', metavar='Boolean of store a png file.',type= str2bool , default= False)

# Data preprocessing for cleaning string
def encode_event(event):
    if event == 'stm_start_entry':
        return 0
    elif event == 'stm_commit_entry':
        return 1
    elif event == 'stm_rollback_entry':
        return 2
    else:
        return -1
    # if event == 'stm_start_entry':
    #     return 0
    # elif event == 'stm_commit_exit__return':
    #     return 1
    # elif event == 'stm_rollback_exit__return':
    #     return 2
    # else:
    #     return -1

def encode_event2(event):
    if event == args.name+'_stm_start_entry':
        return 0
    elif event == args.name+'_stm_commit_exit__return':
        return 1
    elif event == args.name+'_stm_rollback_exit__return':
        return 2
    else:
        return -1

def data_sort(path,encoder):
    
    # fetch timestamp
    t1 = time.time()
    # read file
    df = pd.read_csv(path,delimiter=r"\s+",header=None,names=["name", "pid","thread_name","time","event","memory_address"])
    

    # drop column
    df = df.drop(['name','pid'], axis=1)
    
    # clean file
    df.thread_name = df.thread_name.map(lambda x: int(str(x).strip('[').strip(']')))
    df.memory_address = df.memory_address.map(lambda x: int( str(x).strip('(').strip(')')[6:] ,16))
    if encoder =='event2':
        df.event = df.event.map(lambda x: encode_event2(str(x).strip('probe_'+args.name).strip(':')) )
    else:
        df.event = df.event.map(lambda x: encode_event(str(x).strip('probe_'+args.name).strip(':')) )

    df.time = df.time.map(lambda x: int(float(x.strip(':'))*1000000))
    
    # fetch timestamp
    t2 = time.time()


    # convert it to numpy
    array = df.to_numpy()
    if args.csv:
        df.to_csv(args.npy[:-3]+'csv')

    # save it
    numpy.save(args.npy,array)

    #fetch timestamp and print it
    t3 = time.time()
    print('[Compression] time consume:{}'.format(t2-t1))
    print('[Save I/O] time consume:{}'.format(t3-t2))

def fig2img(fig):
    """Convert a Matplotlib figure to a PIL Image and return it"""
    import io
    buf = io.BytesIO()
    fig.savefig(buf)
    buf.seek(0)
    img = Image.open(buf)
    return img

class RectItemR(pg.GraphicsObject):
    def __init__(self, rect,parent=None):
        super().__init__(parent)
        self._rect = rect
        self.picture = QtGui.QPicture()
        self._generate_picture()

    @property
    def rect(self):
        return self._rect

    def _generate_picture(self):
        painter = QtGui.QPainter(self.picture)
        painter.setPen(pg.mkPen("k"))
        painter.setBrush(pg.mkBrush('r'))
        painter.drawRect(self.rect)
        painter.end()

    def paint(self, painter, option, widget=None):
        painter.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())
class RectItemG(pg.GraphicsObject):
    def __init__(self, rect,parent=None):
        super().__init__(parent)
        self._rect = rect
        self.picture = QtGui.QPicture()
        self._generate_picture()

    @property
    def rect(self):
        return self._rect

    def _generate_picture(self):
        painter = QtGui.QPainter(self.picture)
        painter.setPen(pg.mkPen("k"))
        painter.setBrush(pg.mkBrush('g'))
        painter.drawRect(self.rect)
        painter.end()

    def paint(self, painter, option, widget=None):
        painter.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())

class App(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(App, self).__init__(parent)

        #### Create Gui Elements ###########
        self.mainbox = QtGui.QWidget()
        self.setCentralWidget(self.mainbox)
        self.mainbox.setLayout(QtGui.QVBoxLayout())

        self.canvas = pg.GraphicsLayoutWidget()
        self.mainbox.layout().addWidget(self.canvas)

        self.label = QtGui.QLabel()
        self.mainbox.layout().addWidget(self.label)


        self.analogPlot = self.canvas.addPlot(title='TMtrace real-time visualizer')
        self.analogPlot.setYRange(-1,20)                # set axis range
        self.analogPlot.setXRange(-1,1000)

        #### Set Data  #####################
        
        # load array
        self.array = np.load(args.npy)
        # get endpoint
        if int(args.endpoint)==-1:
            args.endpoint = self.array.shape[0]

        # slice array
        self.array = self.array[args.startpoint:args.endpoint,:]

        # save first timestamp for base 
        self.time_offset = self.array[0,1]
        # create a record table
        self.record = np.full((int(max(self.array[:,0]))+1,len(self.array[0,:])),-1)

        if args.debug:
            print('create a record table with size{}'.format(self.record.shape))


        

        self.counter = 0
        self.fps = 0.
        self.lastupdate = time.time()

        #### Start  #####################
        self._update()

    def _update(self):

        if args.debug:
            self.check_list = []
            if self.counter < len(self.array):
                self.check_list.append(self.counter)
            else:
                print(sum(self.check_list))
        if self.counter < self.array.shape[0]:

            #plot our log data
            
            # fetch current transaction event
            thread = int(self.array[self.counter,0])
            event = int(self.array[self.counter,2])

            # raise exception if there is any event which is not in our decoder
            if event==-1:
                raise Exception("Sorry, no numbers below zero in event")
            
            # if event type is start, save it and exit    
            if event==0:
                
                # save it to our record and wait for transaction end
                self.record[ thread,:] = self.array[self.counter,:]
            # if event type is either commit or rollback, export the event
            else:
                
                # gatt char
                if int(self.record[thread,2]) == -1:
                    #print('[Error] Attention! There is a event without entry point')
                    #print('[Error] Transaction event number:{}.'.format(j))
                    pass
                else:
                    #paint the plot
                    
                    # y x wy wx
                    if event ==1:
                        rect_item = RectItemG(QtCore.QRectF(self.record[thread,1]-self.time_offset,thread -0.5, self.array[self.counter,1]-self.record[thread,1],1 ))
                        #rect_item = RectItem(QtCore.QRectF(1,2,3,4))
                    else:
                        rect_item = RectItemR(QtCore.QRectF(self.record[thread,1]-self.time_offset,thread -0.5, self.array[self.counter,1]-self.record[thread,1],1 ))
                    self.analogPlot.addItem(rect_item)
                    
                    
                
                # if roll back event, save it to record
                if event==2:
                    self.record[ thread,:] = self.array[self.counter,:]

                # if commit event, clear the record
                if event==1:
                    self.record[ thread,:]= np.full(self.record[thread,:].shape,-1)
                    #print('clear the record successfully!')
        
        
        now = time.time()
        dt = (now-self.lastupdate)
        if dt <= 0:
            dt = 0.000000000001
        fps2 = 1.0 / dt
        self.lastupdate = now
        self.fps = self.fps * 0.9 + fps2 * 0.1
        tx = 'Mean Frame Rate:  {fps:.3f} FPS, index {counter}'.format(fps=self.fps,counter=(self.counter/self.array.shape[0])*100 )
        self.label.setText(tx)
        
        
        
        QtCore.QTimer.singleShot(1, self._update)
        self.counter += 1


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    # arg
    global args
    args = parser.parse_args()
    # conditional operation
    if args.compress:
        print('start to compress the original file and will save it as npy file format.')
        data_sort(args.path,args.encoder)
    print('start to plot the transactional event.')
    thisapp = App()
    thisapp.show()
    sys.exit(app.exec_())