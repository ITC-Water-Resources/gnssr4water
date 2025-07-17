# This file is part of gnssr4water
# gnssr4water is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.

# gnssr4water is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with gnssr4water if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

# Author Roelof Rietbroek (r.rietbroek@utwente.nl), 2025

from gnssr4water.sites.arc import Arc
from gnssr4water.core.logger import logging
import os
import pickle

class ArcStore:
    """
    A class to store and retrieve arcs using pickle serialization.
    can be used as an intermediate store for arcs
    """
    def __init__(self,picklestore,mode='r'):
        self.file=picklestore
        self.mode=mode
         
        if self.mode == 'r' and not os.path.exists(self.file):
            raise FileNotFoundError(f"File {self.file} does not exist for reading arcs")

        if self.mode == 'r':
            self.fid=open(self.file,'rb')
        

        elif self.mode == 'w':
            self.fid=open(self.file,'wb')
        elif self.mode == 'a':
            self.fid=open(self.file,'ab')
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fid.close()
    

    def write(self,arc):
        """
        Append an arc to the store
        """
        if self.mode == 'r':
            raise ValueError("ArcStore is not writable")
        pickle.dump(arc, self.fid)

    def arcs(self):
        """Get the currently loaded arcs"""     
        
        try:
            while True:
                arc=pickle.load(self.fid)
                yield arc
        except EOFError:
                return


