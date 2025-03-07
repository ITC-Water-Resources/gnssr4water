# This file is part of gnssr4water
# gnssr4water is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.

# geoslurp is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with Frommle; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

# Author Roelof Rietbroek (r.rietbroek@utwente.nl), 2024

import logging

logging.basicConfig()
log=logging.getLogger("gnssr4water")

def setInfoLevel():
    """Set logging level to INFO severity"""
    log.setLevel(logging.INFO)

def setDebugLevel():
    """Set logging level to DEBUG severity"""
    log.setLevel(logging.DEBUG)


def setWarningLevel():
    """Set logging level to WARNING severity"""
    log.setLevel(logging.WARNING)

def setErrorLevel():
    """Set logging level to ERROR severity"""
    log.setLevel(logging.ERROR)


