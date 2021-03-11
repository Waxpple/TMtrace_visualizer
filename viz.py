import numpy
import pandas as pd
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
import argparse
import time

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
                            
parser.add_argument('--compress', metavar='Boolean of compress operation', type= str2bool, default= False)
parser.add_argument('--path', metavar='Path to our trace file', default=None)
parser.add_argument('--debug', metavar='Debug flag', type= str2bool, default=False)
parser.add_argument('--csv', metavar='Boolean of store a csv file',type= str2bool , default= False)
parser.add_argument('--npy', metavar='Path to our trace numpy file', default=None)
parser.add_argument('--endpoint', metavar='Plot endpoint', type= int, default= 1000)
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
def encode_event2(event):
    if event == 'stm_start_entry':
        return 0
    elif event == 'stm_commit_exit__return':
        return 1
    elif event == 'stm_rollback_exit__return':
        print('rollback')
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
        df.event = df.event.map(lambda x: encode_event2(str(x).strip('probe_kmeans').strip(':')) )
    else:
        df.event = df.event.map(lambda x: encode_event(str(x).strip('probe_kmeans').strip(':')) )

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
    
def gatt(npy_path,debug=False,paint_event=False):
    
    # fetch timestamp
    t1 = time.time()


    # load array
    array = numpy.load(npy_path)
    array = array[0:args.endpoint,:]
    
    # figure size
    plt.figure(figsize=(50,20))

    # save first timestamp for base 
    time_offset = array[0,1]
    # create a record table
    record = np.zeros((max(array[:,0])+1,len(array[0,:])))
    if debug:
        print('create a record table with size{}'.format(record.shape))
    
    for j in range(len(array)):
        
        # fetch current transaction event
        thread = int(array[j,0])
        event = int(array[j,2])
        
        # Debug info
        if debug:
            print('{}:event and thread {} with event {}'.format(j,thread,event))
        
        # raise exception if there is any event which is not in our decoder
        if event==-1:
            raise Exception("Sorry, no numbers below zero in event")
        
        # if event type is start, save it and exit    
        if event==0:
            
            # save it to our record and wait for transaction end
            record[ thread,:] = array[j,:]
            
            # Debug info
            if debug:
                print('save record[{}]'.format(thread))
        
        # if event type is either commit or rollback, export the event
        else:
            
            # gatt char
            plt.barh(thread,array[j,1]-record[thread,1],left=record[thread,1]-time_offset, color = 'green' if event==1 else 'red' )
            
            # Debug info
            if paint_event:
                print('thread{}:{}'.format(thread,'green' if event==1 else 'red'))
            
            # if roll back event, save it to record
            if event==2:
                record[ thread,:] = array[j,:]
                
                # Debug info
                if debug:
                    print('rollback!save record[{}]'.format(thread))
    t2 = time.time()
    print('[Plot] time consume:{}'.format(t2-t1))
    if args.savefigure:
        plt.savefig(args.npy[:-3]+'jpg', bbox_inches='tight')
    plt.show()
if __name__=="__main__":
    
    # arg
    global args
    args = parser.parse_args()
    
    # conditional operation
    if args.compress:
        print('start to compress the original file and will save it as npy file format.')
        data_sort(args.path,args.encoder)
    print('start to plot the transactional event.')
    gatt(args.npy,debug=args.debug,paint_event=args.debug)
    