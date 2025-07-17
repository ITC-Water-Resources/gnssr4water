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

gnssr_darkblue="#003247"
gnssr_yellow='#bcd42f'
gnssr_green='#39b24b'
gnssr_blue='#297ab9'
gnssr_red='#e15989'
gnssr_lightgreen='#6cc6ac'


def add_alpha(hxcol,alpha):
    """
    Add an alpha channel to a hex color code.
    Parameters:
    ----------
    hxcol: str
        Hex color code (e.g., '#FF5733').
    alpha: float
        Alpha value between 0 (transparent) and 1 (opaque).
    """
    return hxcol+hex(int(alpha*255))[-2:]

