/*# This file is part of gnssr4water*/
/*# gnssr4water is free software; you can redistribute it and/or*/
/*# modify it under the terms of the GNU Lesser General Public*/
/*# License as published by the Free Software Foundation; either*/
/*# version 3 of the License, or (at your option) any later version.*/

/*# gnssr4water is distributed in the hope that it will be useful,*/
/*# but WITHOUT ANY WARRANTY; without even the implied warranty of*/
/*# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU*/
/*# Lesser General Public License for more details.*/

/*# You should have received a copy of the GNU Lesser General Public*/
/*# License along with gnssr4water if not, write to the Free Software*/
/*# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA*/

/*# Author Roelof Rietbroek (r.rietbroek@utwente.nl), 2025*/

#include <string.h>
#include <stdio.h>


#ifndef GNSSRSTREAM_H
#define GNSSRSTREAM_H


#define GNSSR_IO_ERROR -1
#define GNSSR_EOF 2
#define GNSSR_SUCCESS 0

typedef enum { 
	UNCOMPRESSED,
#ifdef USE_GZIP
	GZIP,
#endif
#ifdef USE_LZ4
	LZ4
#endif
}stream_type;

struct gnssrstream{
	stream_type ftype;
	void *fid;
};

typedef struct gnssrstream gnssrstream;

int open_stream(const char *filename,gnssrstream* strid);
int readline(gnssrstream* strid, char *buffer,size_t slen);
void close_stream(gnssrstream* strid);
int eof(gnssrstream* strid);


#endif //GNSSRSTREAM_H

