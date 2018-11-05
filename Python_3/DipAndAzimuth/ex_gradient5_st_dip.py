#!/usr/bin/python
#
# Inline, Crossline, True dip, Dip Azimuth and Coherency/Saliency using the Gradient Structure Tensor
# Gradients calculated using Farid's 5 point derivative filter
#
import sys,os
import numpy as np
# Import the module with the I/O scaffolding of the External Attribute
#
sys.path.insert(0, os.path.join(sys.path[0], '..'))
import extattrib as xa
import extlib as xl
#
# These are the attribute parameters
#
xa.params = {
	'Inputs': ['Input'],
	'Output': ['Crl_dip', 'Inl_dip', 'True Dip', 'Dip Azimuth', 'Coherency'],
	'ZSampMargin' : {'Value':[-3,3], 'Minimum': [-3,3], 'Symmetric': True},
	'StepOut' : {'Value': [3,3], 'Minimum':[3,3], 'Symmetric': True},
	'Help': 'http://waynegm.github.io/OpendTect-Plugin-Docs/external_attributes/DipandAzimuth.html'
}
#
# Define the compute function
#
def doCompute():
	xs = xa.SI['nrinl']
	ys = xa.SI['nrcrl']
	zs = xa.params['ZSampMargin']['Value'][1] - xa.params['ZSampMargin']['Value'][0] + 1
	kernel = xl.getGaussian(xs-4, ys-4, zs-4)
	inlFactor = xa.SI['zstep']/xa.SI['inldist'] * xa.SI['dipFactor']
	crlFactor = xa.SI['zstep']/xa.SI['crldist'] * xa.SI['dipFactor']
	while True:
		xa.doInput()

		g = xa.Input['Input']
#
# Compute gradients
		gx = xl.farid5( g, axis=0 )
		gy = xl.farid5( g, axis=1 )
		gz = xl.farid5( g, axis=2 )
#
#	Inner product of  gradients
		gx2 = gx[2:xs-2,2:ys-2,:] * gx[2:xs-2,2:ys-2,:]
		gy2 = gy[2:xs-2,2:ys-2,:] * gy[2:xs-2,2:ys-2,:]
		gz2 = gz[2:xs-2,2:ys-2,:] * gz[2:xs-2,2:ys-2,:]
		gxgy = gx[2:xs-2,2:ys-2,:] * gy[2:xs-2,2:ys-2,:]
		gxgz = gx[2:xs-2,2:ys-2,:] * gz[2:xs-2,2:ys-2,:]
		gygz = gy[2:xs-2,2:ys-2,:] * gz[2:xs-2,2:ys-2,:]
#
#	Outer gaussian smoothing
		rgx2 = xl.sconvolve(gx2, kernel)
		rgy2 = xl.sconvolve(gy2, kernel)
		rgz2 = xl.sconvolve(gz2, kernel)
		rgxgy = xl.sconvolve(gxgy, kernel)
		rgxgz = xl.sconvolve(gxgz, kernel)
		rgygz = xl.sconvolve(gygz, kernel)
#
#	Form the structure tensor
		T = np.rollaxis(np.array([	[rgx2,  rgxgy, rgxgz],
									[rgxgy, rgy2,  rgygz],
									[rgxgz, rgygz, rgz2 ]]), 2)
#
#	Get the eigenvalues and eigen vectors and calculate the dips
		evals, evecs = np.linalg.eigh(T)
		ndx = evals.argsort()
		evecs = evecs[np.arange(0,T.shape[0],1),:,ndx[:,2]]
		e1 = evals[np.arange(0,T.shape[0],1),ndx[:,2]]
		e2 = evals[np.arange(0,T.shape[0],1),ndx[:,1]]
		xa.Output['Crl_dip'] = -evecs[:,1]/evecs[:,2]*crlFactor
		xa.Output['Inl_dip'] = -evecs[:,0]/evecs[:,2]*inlFactor
		xa.Output['True Dip'] = np.sqrt(xa.Output['Crl_dip']*xa.Output['Crl_dip']+xa.Output['Inl_dip']*xa.Output['Inl_dip'])
		xa.Output['Dip Azimuth'] = np.degrees(np.arctan2(xa.Output['Inl_dip'],xa.Output['Crl_dip']))
		coh = (e1-e2)/(e1+e2) 
		xa.Output['Coherency'] = coh * coh
		xa.doOutput()
	
#
# Assign the compute function to the attribute
#
xa.doCompute = doCompute
#
# Do it
#
xa.run(sys.argv[1:])
  
