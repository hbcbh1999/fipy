#!/usr/bin/env python

## -*-Pyth-*-
 # ###################################################################
 #  FiPy - Python-based finite volume PDE solver
 # 
 #  FILE: "mayaviViewer.py"
 #
 #  Author: Jonathan Guyer <guyer@nist.gov>
 #  Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 #  Author: James Warren   <jwarren@nist.gov>
 #  Author: Daniel Stiles  <daniel.stiles@nist.gov>
 #    mail: NIST
 #     www: http://www.ctcms.nist.gov/fipy/
 #  
 # ========================================================================
 # This software was developed at the National Institute of Standards
 # and Technology by employees of the Federal Government in the course
 # of their official duties.  Pursuant to title 17 Section 105 of the
 # United States Code this software is not subject to copyright
 # protection and is in the public domain.  FiPy is an experimental
 # system.  NIST assumes no responsibility whatsoever for its use by
 # other parties, and makes no guarantees, expressed or implied, about
 # its quality, reliability, or any other characteristic.  We would
 # appreciate acknowledgement if the software is used.
 # 
 # This software can be redistributed and/or modified freely
 # provided that any derivative works bear some notice that they are
 # derived from it, and any modified versions bear some notice that
 # they have been modified.
 # ========================================================================
 #  See the file "license.terms" for information on usage and  redistribution
 #  of this file, and for a DISCLAIMER OF ALL WARRANTIES.
 #  
 # ###################################################################
 ##


__docformat__ = 'restructuredtext'

import os
import subprocess
import tempfile
import time

from fipy.viewers.viewer import _Viewer

class MayaviViewer(_Viewer):
    """
    .. attention:: This class is abstract. Always create one of its subclasses.

    The `_MayaviViewer` is the base class for the viewers that use the
    Mayavi_ python plotting package.

    .. Mayavi: http://code.enthought.com/projects/mayavi

    """

    def __init__(self, vars, title=None, **kwlimits):
        """
        Create a `_MayaviViewer`.
        
        :Parameters:
          vars
            a `CellVariable` or tuple of `CellVariable` objects to plot
          title
            displayed at the top of the `Viewer` window
          xmin, xmax, ymin, ymax, zmin, zmax, datamin, datamax
            displayed range of data. A 1D `Viewer` will only use `xmin` and
            `xmax`, a 2D viewer will also use `ymin` and `ymax`, and so on. All
            viewers will use `datamin` and `datamax`. Any limit set to a
            (default) value of `None` will autoscale.
        """
        self.vtkdir = tempfile.mkdtemp()
        self.vtkcellfname = os.path.join(self.vtkdir, "cell.vtk")
        self.vtkfacefname = os.path.join(self.vtkdir, "face.vtk")
        self.vtklockfname = os.path.join(self.vtkdir, "lock")

        from fipy.viewers.vtkViewer import VTKCellViewer, VTKFaceViewer

        try:
            self.vtkCellViewer = VTKCellViewer(vars=vars)
            cell_vars = self.vtkCellViewer.getVars()
        except TypeError:
            self.vtkCellViewer = None
            cell_vars = []

        try:
            self.vtkFaceViewer = VTKFaceViewer(vars=vars)
            face_vars = self.vtkFaceViewer.getVars()
        except TypeError:
            self.vtkFaceViewer = None
            face_vars = []

        _Viewer.__init__(self, vars=cell_vars + face_vars, title=title, **kwlimits)
        
        self.plot()

        cmd = ["python", 
               "/Users/guyer/Documents/research/FiPy/mayavi/fipy/viewers/mayaviViewer/mayaviDaemon.py",
               "--lock",
               self.vtklockfname]

        if self.vtkCellViewer is not None:
            cmd += ["--cell", self.vtkcellfname]
            
        if self.vtkFaceViewer is not None:
            cmd += ["--face", self.vtkfacefname]
            
                
        cmd += self._getLimit('xmin')
        cmd += self._getLimit('xmax')
        cmd += self._getLimit('ymin')
        cmd += self._getLimit('ymax')
        cmd += self._getLimit('zmin')
        cmd += self._getLimit('zmax')
        cmd += self._getLimit('datamin')
        cmd += self._getLimit('datamax')

        self.daemon = subprocess.Popen(cmd)
        
    def __del__(self):
        if os.path.isfile(self.vtkcellfname):
            os.unlink(self.vtkcellfname)
        if os.path.isfile(self.vtkfacefname):
            os.unlink(self.vtkfacefname)
        if os.path.isfile(self.vtklockfname):
            os.unlink(self.vtklockfname)
        os.rmdir(self.vtkdir)
        _Viewer.__del__(self)
        
    def _getLimit(self, key):
        """
        Return the limit associated with the key
        
        .. Note::
           
           `MayaviViewer` does not need the generality of multiple keys 
           because it is always 3D
        
        :Parameters:
          key
            a key string that identifies the limit of interest
            
        :Returns:
          the value of the limit or `None`
        """
        lim = _Viewer._getLimit(self, key)
        if lim is not None:
            return ["--%s" % key, str(lim)]
        else:
            return []

    def plot(self, filename=None):
        start = time.time()
        plotted = False
        while time.time() - start < 10. and not plotted:
            if not os.path.isfile(self.vtklockfname):
                if self.vtkCellViewer is not None:
                    self.vtkCellViewer.plot(filename=self.vtkcellfname)
                if self.vtkFaceViewer is not None:
                    self.vtkFaceViewer.plot(filename=self.vtkfacefname)
                lock = file(self.vtklockfname, 'w')
                if filename is not None:
                    lock.write(filename)
                lock.close()
                plotted = True
        if not plotted:
            print "viewer: NOT READY"
    
    def _validFileExtensions(self):
        return [".png",".jpg",".bmp",".tiff",".ps",".eps",".pdf",".rib",".oogl",".iv",".vrml",".obj"]
        
