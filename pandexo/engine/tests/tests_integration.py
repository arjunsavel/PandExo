import warnings
warnings.filterwarnings('ignore')
import pandexo.engine.justdoit as jdi # THIS IS THE HOLY GRAIL OF PANDEXO
import numpy as np
import os

import pickle as pk

import urllib.request

import unittest

import zipfile


print(os.getcwd())


def download_folder(folder, path=None):
	"""
	Downloads a .zip file from this projects S3 testing bucket, unzips it, and deletes 
	the .zip file.

	Inputs:
		folder : (string) name of the folder to be downloaded.
	"""

	def retrieve_extract(path):
		with zipfile.ZipFile(folder + '.zip', 'r') as zip_ref:
			zip_ref.extractall(path)


	folder_url = f'https://pandexotesting.s3-us-west-1.amazonaws.com/{folder}.zip'
	urllib.request.urlretrieve(folder_url, folder + '.zip')
	if path:
		retrieve_extract(path)
	else: # we're running this in an arbitrary directory
		retrieve_extract('')
	if folder == 'pandeia_refdata':
		os.environ['pandeia_refdata'] = os.getcwd() + '/pandeia_data-1.4'
	elif folder == 'grp':
		os.environ['PYSYN_CDBS'] =  os.getcwd() + '/grp/hst/cdbs/'
	print(f'Downloaded {folder}')
	os.remove(folder + '.zip')

def delete_folder(folder):
	if os.listdir(folder):
		for f in os.listdir(folder):
			if folder[-1] == '/':
				path = folder + f
			else:
				path = folder + '/' + f
			if os.path.isfile(path):
				os.remove(path)
			else: # if it's a directory!
				delete_folder(path)
	os.rmdir(folder)


def run_test():
	try:
		os.environ['pandeia_refdata']
	except KeyError:
		download_folder('pandeia_data-1.4')
	try:
		os.environ['PYSYN_CDBS']
	except KeyError:
		download_folder('grp')
	print(os.listdir())
	print(os.environ['PYSYN_CDBS'])
	print(os.environ['pandeia_data-1.4'])
	exo_dict = jdi.load_exo_dict()
	exo_dict['observation']['sat_level'] = 80    #saturation level in percent of full well 
	exo_dict['observation']['sat_unit'] = '%' 
	exo_dict['observation']['noccultations'] = 2 #number of transits 
	exo_dict['observation']['R'] = None          #fixed binning. I usually suggest ZERO binning.. you can always bin later 
	                                 #without having to redo the calcualtion
	exo_dict['observation']['baseline'] = 1.0    #fraction of time in transit versus out = in/out
	exo_dict['observation']['baseline_unit'] = 'frac' 
	exo_dict['observation']['noise_floor'] = 0   #this can be a fixed level or it can be a filepath 
	exo_dict['star']['type'] = 'phoenix'        #phoenix or user (if you have your own)
	exo_dict['star']['mag'] = 8.0               #magnitude of the system
	exo_dict['star']['ref_wave'] = 1.25         #For J mag = 1.25, H = 1.6, K =2.22.. etc (all in micron)
	exo_dict['star']['temp'] = 5500             #in K 
	exo_dict['star']['metal'] = 0.0             # as log Fe/H
	exo_dict['star']['logg'] = 4.0
	exo_dict['star']['radius'] = 1
	exo_dict['star']['r_unit'] = 'R_sun'    
	exo_dict['planet']['type'] = 'constant'
	exo_dict['planet']['radius'] = 1                      #other options include "um","nm" ,"Angs", "secs" (for phase curves)
	exo_dict['planet']['r_unit'] = 'R_jup'  
	exo_dict['planet']['transit_duration'] = 2.0*60.0*60.0 
	exo_dict['planet']['td_unit'] = 's'
	exo_dict['planet']['f_unit'] = 'rp^2/r*^2'
	print('Starting TEST run')
	results = jdi.run_pandexo(exo_dict, ['NIRSpec G140H'], save_file=False)
	print('SUCCESS_test')

	return results

class TestNIRSpec_G140H(unittest.TestCase):
	results = run_test()

	def test_NIRSpec_G140H_output_spec(self):
		with open('pandexo/engine/tests/compare_run.p','rb') as f:
			compare_out = pk.load(f)
		compare_spectrum = compare_out['FinalSpectrum']['spectrum']
		spectrum = self.results['FinalSpectrum']['spectrum']
		val = np.array_equal(spectrum, compare_spectrum)
		self.assertTrue(val)
