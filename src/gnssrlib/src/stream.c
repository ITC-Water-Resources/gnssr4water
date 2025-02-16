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


#include <stdio.h>
#include <string.h>
#include "gnssrlib.h"
#include "stream.h"
#ifdef USE_GZIP
#include <zlib.h>
#endif

#ifdef USE_LZ4
#include "lz4stream.h"
#endif

int open_stream(const char *filename,gnssrstream* sid){
    size_t slen=strlen(filename);

    if (strncmp(filename+slen-3,".gz",3) == 0) {
#ifdef USE_GZIP
	sid->ftype = GZIP;
	sid->fid = (void*)gzopen(filename, "r");
	if (!sid->fid) {
	    fprintf(stderr, "Could not open file %s\n", filename);
	    return GNSSR_IO_ERROR;
	}else{
	    return GNSSR_SUCCESS;
	}
#else
	fprintf(stderr, "GZIP support not compiled in\n");
	return GNSSR_IO_ERROR;
#endif
    }

    if (strncmp(filename+slen-4,".lz4",4) == 0) {
#ifdef USE_LZ4
	sid->ftype = LZ4;
	sid->fid=(void*)open_lz4stream(filename);
	if (sid->fid== NULL) {
	    fprintf(stderr, "Could not open file %s\n", filename);
	    return GNSSR_IO_ERROR;
	}else{
	    return GNSSR_SUCCESS;
	}
#else
	fprintf(stderr, "LZ4 support not compiled in\n");
	return GNSSR_IO_ERROR;
#endif
    }

    sid->ftype = UNCOMPRESSED;
    sid->fid = (void*)fopen(filename, "r");
    if (sid->fid == NULL) {
	fprintf(stderr, "Could not open file %s\n", filename);
	return GNSSR_IO_ERROR;
    }else{
	return GNSSR_SUCCESS;
    }
}

void close_stream(gnssrstream * sid)
{
switch (sid->ftype) {
#ifdef USE_GZIP
    case GZIP: 
	gzclose(sid->fid);
	break;
#endif
#ifdef USE_LZ4
    case LZ4:
	close_lz4stream(sid->fid);
	break;

#endif
    case UNCOMPRESSED:
	fclose(sid->fid);
	break;

}
}

int readline(gnssrstream * sid, char *buffer,size_t slen)
{

switch (sid->ftype) {
#ifdef USE_GZIP
    case GZIP:
	{
	char* err= gzgets(sid->fid, buffer, slen);

	if (err == Z_NULL) {
	    //check for end of file
	    int eof = gzeof(sid->fid);
	    if (eof == 1) {
		buffer[0] = '\0';
		return GNSSR_EOF;
	    } else {
		return GNSSR_IO_ERROR;
	    }
	}

	return GNSSR_SUCCESS;
	}
	break;
#endif //USE_GZIP
       
#ifdef USE_LZ4
    case LZ4:
	{
	int err= readline_lz4(sid->fid, buffer, slen);
	if (err == LZ4_EOF) {
	    buffer[0] = '\0';
	    return GNSSR_EOF;
	} else if (err == LZ4_ERROR) {
	    return GNSSR_IO_ERROR;
	}else{
	    return GNSSR_SUCCESS;
	}}
	break;
#endif //USE_LZ4
    case UNCOMPRESSED:
	{
	char* err= fgets(buffer, slen, sid->fid);
	if (err == NULL) {
	    //check for end of file
	    if (feof(sid->fid)) {
		buffer[0] = '\0';
		return GNSSR_EOF;
	    } else {
		return GNSSR_IO_ERROR;
	    }
	}else{
	    return GNSSR_SUCCESS;
	}
	}
    break;
}
    //shouldn't get here
    return GNSSR_IO_ERROR;
    }
