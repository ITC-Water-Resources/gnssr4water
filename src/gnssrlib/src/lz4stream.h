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

#include "lz4static/lz4.h"
#include "lz4static/lz4file.h"
#include <stdio.h>

#define LZ4_MAX_MESSAGE 1024
#define LZ4_RING_BUFFER 256*1024
#define LZ4_CHUNK_SIZE 1024*16 
#define LZ4_ERROR -1
#define LZ4_EOF -2
#define LZ4_SUCCESS 0



#ifndef LZ4STREAM_H
#define LZ4STREAM_H

struct lz4stream{
    //LZ4_streamDecode_t* dec_lz4;
    LZ4_readFile_t* lz4_fid;
    FILE* fid;
    //char rbuffer[LZ4_RING_BUFFER];
    //char * rbufPtr;
    char *mbufPtr;
    //char compbuf[LZ4_COMPRESSBOUND(LZ4_MAX_MESSAGE)];
    char * chunkbuf;
    char *chunkPtr;
   size_t buflen;
};

typedef struct lz4stream lz4stream;

lz4stream* open_lz4stream(const char *filename);
void close_lz4stream(lz4stream* lzid);
int readline_lz4(lz4stream* lzid, char *buffer,size_t slen);
int decompress_lz4_chunk(lz4stream* lzid);


#endif //LZ4STREAM_H
