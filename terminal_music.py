""" based on code from arduino soundlight project """
import pyaudio
import numpy # for fft
import audioop
import sys
import math
import struct
import time
import curses
from socket import *

def list_devices():
    # List all audio input devices
    p = pyaudio.PyAudio()
    i = 0
    n = p.get_device_count()
    while i < n:
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            print str(i)+'. '+dev['name']
        i += 1
 
def analyze(data, width, sample_rate, bins):
    # Convert raw sound data to Numpy array
    fmt = "%dH"%(len(data)/2)
    data2 = struct.unpack(fmt, data)
    data2 = numpy.array(data2, dtype='h')
 
    # FFT black magic
    fourier = numpy.fft.fft(data2)
    ffty = numpy.abs(fourier[0:len(fourier)/2])/1000
    ffty1=ffty[:len(ffty)/2]
    ffty2=ffty[len(ffty)/2::]+2
    ffty2=ffty2[::-1]
    ffty=ffty1+ffty2
    ffty=numpy.log(ffty)-2
    
    fourier = list(ffty)[4:-4]
    fourier = fourier[:len(fourier)/2]
    
    size = len(fourier)
 
    # Split into desired number of frequency bins
    levels = [sum(fourier[i:(i+size/bins)]) for i in xrange(0, size, size/bins)][:bins]
    
    return levels

def visualize():
    
    chunk    = 2048 # Change if too fast/slow, never less than 1024
    scale    = 100   # Change if too dim/bright
    exponent = .5    # Change if too little/too much difference between loud and quiet sounds
    sample_rate = 44100 
    device   = 2  # Change to correct input device; use list_devices()
    
    p = pyaudio.PyAudio()
    stream = p.open(format = pyaudio.paInt16,
                    channels = 1,
                    rate = sample_rate,
                    input = True,
                    frames_per_buffer = chunk,
                    input_device_index = device)
    
    print "Starting, use Ctrl+C to stop"
    screen = curses.initscr()
    curses.start_color()
    curses.use_default_colors()

    term_height = screen.getmaxyx()[0]
    term_width = screen.getmaxyx()[1]

    min_bar_height = 1
    bar_width = 4
    bar_spacing = 2
    bins = term_width / (bar_width + bar_spacing) 

    bars = []
    
    for i in range(bins):
        xcoord = bar_spacing + i*(bar_width + bar_spacing) 
        bars.append(curses.newwin(min_bar_height, bar_width, 0, xcoord)) 

    #bars = [bar1, bar2, bar3, bar4, bar5, bar6, bar7]

    #colors
    curses.init_pair(1, -1, curses.COLOR_BLUE)
    curses.init_pair(2, -1, -1)
    #draw stuff
    #for i in range(len(bars)):
    #    bars[i].box()
        
    screen.refresh()
    for i in range(bins):
        bars[i].refresh()
    
  
    try:
        on = False
        while True:
            data = stream.read(chunk)
            levels = analyze(data, chunk, sample_rate, bins)
            # scale to [0,100]
            for i in range(bins):
                levels[i] = max(min((levels[i]*1.0)/scale, 1.0), 0.0)
                levels[i] = levels[i]**exponent
                levels[i] = int(levels[i]*term_height)
            
        

            for i in range(bins):
                height = levels[i]
                prev_coords = bars[i].getbegyx()
                bars[i].bkgd(' ', curses.color_pair(2))
                bars[i].erase()
                bars[i].refresh()
         
                bars[i] = curses.newwin( max(height, 2) , bar_width , 0  ,prev_coords[1])
                
                bars[i].bkgd(' ', curses.color_pair(1)) # set color     
                bars[i].refresh()

            #screen.refresh()
            for i in range(len(bars)):
                bars[i].refresh()
            
    except KeyboardInterrupt:
        pass
    finally:
        print "\nStopping"
        stream.close()
        p.terminate()
        curses.endwin()
        #ser.close()
 
if __name__ == '__main__':
    list_devices()
    visualize()
