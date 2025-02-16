
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

#include "lz4stream.h"
#include <stdlib.h>
#include <string.h>


lz4stream* open_lz4stream(const char *filename){
    /*///initialize the struct*/
    lz4stream* lzid =malloc(sizeof(lz4stream));
    lzid->lz4_fid = NULL;
    //allocate memory for the chunk buffer
    lzid->chunkbuf = malloc(LZ4_CHUNK_SIZE);
    if (lzid->chunkbuf == NULL) {
	close_lz4stream(lzid);
	return NULL;
    }

    ///Open the (compressed) file for reading
    lzid->fid = fopen(filename, "r");

    if (lzid->fid == NULL) {
	//clean up and close shop
	close_lz4stream(lzid);
	fprintf(stderr, "Could not open file %s\n", filename);
	return NULL;
    }
    // open the lz4 decompressor
    LZ4F_errorCode_t ret = LZ4F_OK_NoError;
    ret = LZ4F_readOpen(&(lzid->lz4_fid), lzid->fid);
    if (LZ4F_isError(ret)) {
	printf("LZ4F_readOpen error: %s\n", LZ4F_getErrorName(ret));
	close_lz4stream(lzid);
        return NULL;
    }
    
    //decode the first chunk into the buffer
    int err = decompress_lz4_chunk(lzid);
    if (err != LZ4_SUCCESS) {
	//error decompressing the first chunkbuf
	//clean up and close shop
	close_lz4stream(lzid);
	return NULL;
    }
    return lzid;

}

int decompress_lz4_chunk(lz4stream* lzid){
    LZ4F_errorCode_t ret = LZ4F_read(lzid->lz4_fid, lzid->chunkbuf, LZ4_CHUNK_SIZE);
    if (LZ4F_isError(ret)) {
	printf("LZ4F_read error: %s\n", LZ4F_getErrorName(ret));
	close_lz4stream(lzid);
	return LZ4_ERROR;
    }
    lzid->buflen = ret; //store the amount of valid bytes in the buffer
    if (ret == 0) {
	//Nothing more to read-> end of file
	return LZ4_EOF;
    }
    ///let chunkptr point to beginning of the newly fed buffer
    lzid->chunkPtr = lzid->chunkbuf;
    ///add a null terminator to the buffer
    lzid->chunkbuf[ret] = '\0';
    return LZ4_SUCCESS;
}
int readline_lz4(lz4stream* lzid, char *buffer,size_t slen){
	
	if (lzid->buflen == 0) {
	    //no more data in the buffer
	    return LZ4_EOF;
	}

	char * bufPtr = buffer;

	//find the next newline character in the chunkbuffer
	char * ln = strchr(lzid->chunkPtr, '\n');
	
	
	// not found 
	if (ln == NULL ){
	    //copy the remaining bytes to the output buffer
	    
	    //remaining buffer does not fit in the buffer
	    if (lzid->buflen > lzid->chunkPtr + slen) {
		return LZ4_ERROR;
	    }
	    size_t bcopied = lzid->buflen - (lzid->chunkPtr - lzid->chunkbuf);
	    strncpy(bufPtr, lzid->chunkPtr,bcopied);
	    bufPtr += bcopied;
	    //add a null terminator
	    *bufPtr = '\0';
	    //decompress a chunk and try again
	    int err = decompress_lz4_chunk(lzid);
	    if (err == LZ4_EOF) {
		return LZ4_EOF;
	    }
	    ln = strchr(lzid->chunkPtr, '\n');
	    if ( ln == NULL){
		//no newline found after the second attempt
		return LZ4_ERROR;
	    }
	}
    
	//found string does not fit in the buffer
	if (ln > lzid->chunkPtr + slen) {
	    return LZ4_ERROR;
	}
	///check if data will fit
	//copy the data up to the newlin into to the buffer
	size_t bcopied = ln - lzid->chunkPtr+1;
	strncpy(bufPtr, lzid->chunkPtr, bcopied);
	
	bufPtr += bcopied;
	    //add a null terminator
	*bufPtr = '\0';
	//move the chunkPtr to the beginning of the next line
	lzid->chunkPtr = ln + 1;

	return LZ4_SUCCESS;
}


void close_lz4stream(lz4stream* lzid){
	if (lzid->lz4_fid != NULL) {
		LZ4F_readClose(lzid->lz4_fid);
	}

	if (lzid->fid != NULL) {
		fclose(lzid->fid);
	}
	
	if (lzid->chunkbuf != NULL) {
		free(lzid->chunkbuf);
	}

	free(lzid);
}
/*lz4stream* open_lz4stream(const char *filename){*/
    /*///initialize the struct*/
    /*lz4stream* lzid =malloc(sizeof(lz4stream));*/
    
    /*lzid->fid = fopen(filename, "r");*/
    /*if (lzid->fid == NULL) {*/
	/*fprintf(stderr, "Could not open file %s\n", filename);*/
	    /*return NULL;*/
    /*}else{*/
	/*lzid->dec_lz4 = LZ4_createStreamDecode();*/
	/*lzid->rbufPtr = lzid->rbuffer;*/
	/*lzid->mbufPtr = lzid->rbufPtr;*/

	/*int err = decompress_lz4_block(lzid);*/
	/*if (err != LZ4_SUCCESS) {*/
	    /*fprintf(stderr, "Error decompressing block\n");*/
	    /*return NULL;*/
	/*}*/
	/*return lzid;*/
    /*}*/
/*}*/

/*///Decompresses a block of the lz4 stream in the ring buffer*/
/*int decompress_lz4_block(lz4stream* lzid){*/
	
	/*uint16_t cmpbytes=0;*/
	/*//read the amount of compressed bytes in the next block*/
	/*size_t nread = fread(&cmpbytes, sizeof(uint16_t), 1,lzid->fid);*/
	/*if ( ( nread != 1) || (cmpbytes == 0) ) {*/
	    /*if (feof(lzid->fid)) {*/
		/*return LZ4_EOF;*/
	    /*} else {*/
		/*return LZ4_ERROR;*/
	    /*}*/
	/*}*/
	
	/*//read the compressed block*/
	/*nread = fread(lzid->compbuf, 1, cmpbytes, lzid->fid);*/


	/*if (nread != cmpbytes) {*/
	    /*if (feof(lzid->fid)) {*/
		/*return LZ4_EOF;*/
	    /*} else {*/
		/*return LZ4_ERROR;*/
	    /*}*/
	/*}*/
	
	/*//decompress the block into the ringbuffer*/
        /*int decBytes = LZ4_decompress_safe_continue(lzid->dec_lz4, lzid->compbuf, lzid->rbufPtr, cmpbytes, (int)LZ4_MAX_MESSAGE);*/

        /*if (decBytes <= 0) {*/
	    /*return LZ4_ERROR;*/
	/*}*/
	/*lzid->rbufPtr += decBytes;*/
	
	/*if (lzid->rbufPtr >= lzid->rbuffer + LZ4_RING_BUFFER - LZ4_MAX_MESSAGE) {*/
	    /*//reset to start of the ring buffer if the buffer is almost full*/
	    /*lzid->rbufPtr = lzid->rbuffer;*/
	/*}*/

	/*return LZ4_SUCCESS;*/
/*}*/

/*int readline_lz4(lz4stream* lzid, char *buffer,size_t slen){*/
	/*//find the next newline character in the ringbuffer*/
	
	/*char * ln = strchr(lzid->mbufPtr, '\n');*/
	/*// not found or  found in an older section of the ringbuffer*/
	/*if ((ln == NULL) || (ln > lzid->rbufPtr)){*/
	    /*//decompress a block and try again*/
	    /*decompress_lz4_block(lzid);*/
	    /*ln = strchr(lzid->mbufPtr, '\n');*/
	    /*if ( (ln == NULL) || (ln > lzid->rbufPtr)){*/
		/*//no newline found after the second attempt*/
		/*return LZ4_ERROR;*/
	    /*}*/
	/*}*/
	
	/*//copy the line to the buffer*/
	/*if (ln > lzid->mbufPtr +slen) {*/
	    /*// cannot fit the line in the buffer*/
	    /*return LZ4_ERROR;*/
	/*}*/
	/*strncpy(buffer, lzid->mbufPtr, ln - lzid->mbufPtr);*/
	/*lzid->mbufPtr = ln + 1;*/

	/*return LZ4_SUCCESS;*/
/*}*/


/*void close_lz4stream(lz4stream* lzid){*/
	/*LZ4_freeStreamDecode(lzid->dec_lz4);*/
	/*fclose(lzid->fid);*/
	/*free(lzid);*/
/*}*/
