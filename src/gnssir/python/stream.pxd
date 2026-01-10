cdef extern from "../src/stream.h" nogil:
    cdef const int _GNSSR_SUCCESS "GNSSR_SUCCESS"
    cdef const int _GNSSR_IO_ERROR "GNSSR_IO_ERROR"
    cdef const int _GNSSR_EOF "GNSSR_EOF"
    struct gnssrstream:
        pass
    int open_stream(const char * filename, gnssrstream* gz)
    void close_stream(gnssrstream *gz)
    int readline(gnssrstream *gz, char * line,size_t slen)

