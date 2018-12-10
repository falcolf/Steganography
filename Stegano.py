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
		self.gen_key_list()
		self.keyptr = 0
		self.height, self.width, self.channels = im.shape
		self.size = self.height*self.width
		self.capacity = (self.height-1) * self.width 							# row 0 for saving meta data.

		#current values
		self.row = 1
		self.col = 0
		self.chan = 0 															# 0 red : 1 green : 2 blue

	def gen_key_list(self): 													# function converts key into list with bit values.
		self.keyl=[]
		for c in self.key:
			bin_c = self.get_binary_value(ord(c),8)
			bin_c_list = list(bin_c)
			self.keyl+=bin_c_list
		print(' key list is ' + str(self.keyl))

	def next_key_bits(self): 													# function to get the next three bits for calculating next slot val
		self.key_nbits = [] 													# contains next three bits
		for i in range(3):
			bit_val = self.keyl.pop(0)
			self.key_nbits.append(bit_val)
			self.keyl.append(bit_val)

	def get_binary_value(self,val,bitsize): 									# returns binary value of any value according to required number of bits
		binval = bin(val)[2:]
		while len(binval)<bitsize:
			binval = '0'+binval
		return binval

	def get_modified_lsb(self,s,lsb): 											# helper function to modify the last bit in any string s to lsb PS required as strings are immutable
		lst = list(s)
		lst[-1] = lsb
		s = "".join(lst)
		return s

	def get_next_block(self):
		if self.row == self.height-1 and self.col == self.width-1:
			raise SteganographyException('Image slots filled.!')
		if self.row!=self.height-1 and self.col == self.width-1:
			self.row +=1
			self.col = 0
		else:
			self.col+=1

	def get_channel_value(self):
		key_bits = self.key_nbits[:2]
		key_bits = "".join(key_bits)
		print('in hereeeeee with '+key_bits)
		if key_bits == '00':
			return 0
		elif key_bits == '01':
			return 1
		elif key_bits == '10':
			return 2
		elif key_bits == '11':
			print('block skipped')
			self.get_next_block()
			self.next_key_bits()
			return self.get_channel_value()
		else:
			raise SteganographyException("Error while selecting channel")

	def get_mod_channel(self,cval,bcval):
		if cval == 0:
			if int(bcval[-1]) & int(self.key_nbits[-1]):
				return 1
			else:
				return 2
		elif cval == 1:
			if int(bcval[-1]) & int(self.key_nbits[-1]):
				return 2
			else:
				return 0
		elif cval == 2:
			if int(bcval[-1]) & int(self.key_nbits[-1]):
				return 0
			else:
				return 1
		else:
			raise SteganographyException('Error while getting mod channel')

	def get_mod_channel_space(self,cval):
		if cval == 1:
			return 0
		elif cval == 2:
			return 1
		elif cval ==0:
			return 2
		else:
			raise SteganographyException('Error while getting mod channel for space')

	def hide_bits(self,bits,space): 											# function to hide data
		bits = list(bits)	
		print('bits are '+str(bits))		
		for bit in bits:
			self.next_key_bits()
			print('for bit '+str(bit)+' we have next bits as '+ str(self.key_nbits))
			print('block being updated is  '+str(self.row)+','+str(self.col))
			chans = list(self.im[self.row,self.col])
			chan_val = self.get_channel_value()									# calculates the channel value to be checked
			print('channel value is '+str(chan_val))
			bin_chan_val = self.get_binary_value(chans[chan_val],8)				# binary value of the channel
			print('binary for the channel is '+str(bin_chan_val))
			mod_chan = self.get_mod_channel(chan_val,bin_chan_val)				# to get the channel where changes are to be made
			print('channel to be modified is '+str(mod_chan))
			modified_bin = self.get_modified_lsb(self.get_binary_value(chans[mod_chan],8),bit)	#channel modified
			chans[mod_chan] = int(modified_bin,2)								# update the value of the channel
			sp_mod_chan = self.get_mod_channel_space(mod_chan)					# get channel updated to save space value
			print('space embed channel is '+ str(sp_mod_chan))
			if space == 0:
				sp_cbval = self.get_binary_value(chans[sp_mod_chan],8)
				mod_sp_cval = self.get_modified_lsb(sp_cbval,'0')
				chans[sp_mod_chan] = int(mod_sp_cval,2)
			else:
				sp_cbval = self.get_binary_value(chans[sp_mod_chan],8)
				mod_sp_cval = self.get_modified_lsb(sp_cbval,'1')
				chans[sp_mod_chan] = int(mod_sp_cval,2)
			self.im[self.row,self.col] = tuple(chans)
			self.get_next_block()

	def store_data(self,data):
		data_len = len(data)
		next_space = 0
		for l in range(data_len):
			if next_space == 1:
				next_space = 0
				continue
			if l<data_len-1: 													# not the last charachter...so check next space value
				if data[l+1] == 32: 											# checks if next byte is for space
					next_space = 1
					l+=1
				self.hide_bits(self.get_binary_value(data[l],8),next_space)
			else:
				self.hide_bits(self.get_binary_value(data[l],8),0)

	def extract_data(self):
		pass

	def store_meta_data(self,l): 												# stores length in first row of the image. Length is stroed in 64 bit format.
		bin_len = self.get_binary_value(l,64) 
		for ptr in range(64):
			chans = list(self.im[0,ptr]) 										# chans now contains the three channel values as list
			bin_red_chan = self.get_binary_value(chans[0],8) 					# contains binary value for red channel ie 0th channel
			bin_red_chan_mod = self.get_modified_lsb(bin_red_chan,bin_len[ptr]) # contains modified value for red channel
			chans[0] = int(bin_red_chan_mod,2) 									# converts binary to decimal and stores modified value into channel list
			self.im[0,ptr] = tuple(chans) 										# updates image with modified values
		#print('meta data stored')

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
		self.store_meta_data(l)
		self.store_data(data)
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

		



