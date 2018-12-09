#!/usr/bin/env python
# coding:UTF-8
"""Stegano.py

Usage:
  Stegano.py encode -i <input> -o <output> -k <key> -f <file>
  Stegano.py decode -i <input> -o <output> -k <key>

Options:
  -h, --help                Show this help
  --version                 Show the version
  -f,--file=<file>          File to hide
  -i,--in=<input>           Input image (carrier)
  -o,--out=<output>         Output image (or extracted file)
  -k,--key=<key>			Key for encoding
"""
import cv2
import docopt
import numpy as np

class SteganographyException(Exception):
	pass

class Stegano():

	def __init__(self,im,key):
		self.im = im
		self.key = key
		self.height, self.width, self.channels = im.shape
		self.size = self.height*self.width
		self.capacity = (self.height-1) * self.width # row 0 for saving meta data.

		#current values
		self.row = 0
		self.col = 0
		self.chan = 0 # 0 red : 1 green : 2 blue

	def get_binary_value(self,val,bitsize): #returns binary value of any value according to required number of bits
		binval = bin(val)[2:]
		while len(binval)<bitsize:
			binval = '0'+binval
		return binval

	def get_modified_lsb(self,s,lsb): #helper function to modify the last bit in any string s to lsb PS required as strings are immutable
		lst = list(s)
		lst[-1] = lsb
		s = "".join(lst)
		return s

	def store_meta_data(self,l): #stores length in first row of the image. Length is stroed in 64 bit format.
		bin_len = self.get_binary_value(l,64) 
		for ptr in range(64):
			chans = list(self.im[0,ptr]) #chans now contains the three channel values as list
			bin_red_chan = self.get_binary_value(chans[0],8) # contains binary value for red channel ie 0th channel
			bin_red_chan_mod = self.get_modified_lsb(bin_red_chan,bin_len[ptr]) #contains modified value for red channel
			chans[0] = int(bin_red_chan_mod,2) #converts binary to decimal and stores modified value into channel list
			self.im[0,ptr] = tuple(chans) # updates image with modified values
		print('meta data stored')

	def extract_meta_data(self):
		bin_len = ''
		for ptr in range(64):
			chans = list(self.im[0,ptr])
			bin_red_chan = self.get_binary_value(chans[0],8)
			bin_len += bin_red_chan[-1]
		l = int(bin_len,2)
		return l

	def encode_data(self,data):
		l = len(data)
		print('length of data stored is ' + str(l))
		self.store_meta_data(l)
		return self.im

	def decode_data(self):
		l = self.extract_meta_data()
		print('length of data to be extracted is ' + str(l))
		return

def main():
	args = docopt.docopt(__doc__, version="0.2")
	in_f = args["--in"]
	out_f = args["--out"]
	key = args["--key"]
	in_im = cv2.imread(in_f)
	steg = Stegano(in_im,key)

	if args["encode"]:
		data_file = args["--file"]
		data = open(data_file,'rb').read()
		res_im = steg.encode_data(data)
		cv2.imwrite(out_f,res_im)

	elif args["decode"]:
		steg.decode_data()

if __name__=="__main__":
	main()

		



