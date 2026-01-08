/*# This file is part of gnssir*/
/*# gnssir is free software; you can redistribute it and/or*/
/*# modify it under the terms of the GNU Lesser General Public*/
/*# License as published by the Free Software Foundation; either*/
/*# version 3 of the License, or (at your option) any later version.*/

/*# gnssir is distributed in the hope that it will be useful,*/
/*# but WITHOUT ANY WARRANTY; without even the implied warranty of*/
/*# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU*/
/*# Lesser General Public License for more details.*/

/*# You should have received a copy of the GNU Lesser General Public*/
/*# License along with gnssr4water if not, write to the Free Software*/
/*# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA*/

/*# Author Roelof Rietbroek (r.rietbroek@utwente.nl), 2026*/

#include "gnssir.h"
#include "nmea.h"
#include "skymask.h"

#ifndef GNSSIR_ARCS_H
#define GNSSIR_ARCS_H

//reallocate data with steps of this chunk
#ifndef ARC_DATA_CHUNK
#define ARC_DATA_CHUNK 600
#endif

#ifndef ARC_FILL_VALUE
#define ARC_FILL_VALUE -9999
#endif


//Maximum number of arcs to hold simultaneously
#ifndef ARC_BUFFER_SIZE
#define ARC_BUFFER_SIZE 30
#endif

#define ARC_FULL_BUFFER -200

enum arc_state {FINAL=0, OPEN=1};
typedef enum arc_state arc_state;

struct arc{
	size_t len;
	size_t nreserve;
	arc_state state;	
	//GNSS SYSTEM	
	gnss_system system;
	int prn;
	//Observer position
	enu_position  site;
	//float lat;
	//float lon;
	//float ortho_height;
	//float geoid_height;
	double *mjd;
	float * elevation;
	float * azimuth;
	float * values;

};

typedef struct arc arc; 

int init_arc(arc *data);

int free_arc(arc *data);
int append_to_arc(arc *data,double mjd, float elevation,float azimuth,float cnr0);


///Stuff for the arc buffer interface

struct arc_buffer{
	arc * arcbuf[ARC_BUFFER_SIZE];
///states associated with the buffer
	//unsigned char state[ARC_BUFFER_SIZE];
	//expiry time delta in seconds
	int expiry_sec;
	int max_arclen_sec;
	size_t narcs;
	skymask * skymaskptr;
};

typedef struct arc_buffer arc_buffer; 

int init_arc_buffer(arc_buffer* arcbuf,int expiry_sec,int max_arclen_sec);
int free_arc_buffer(arc_buffer* arcbuf);


int append_cycle_data(const nmea_cycle * cyc, arc_buffer* arcbuf);

////extract a finsihed arc (and transfer ownership to caller)
//arc * pop_finished_arc(arc_buffer * arcbuf);

//int next_arc(gnssrstream * sid, arc * data);

int next_finalized_arc(const arc_buffer * abuf);
int purge_arc(arc_buffer * abuf,int itharc);
int insert_new_arc(arc_buffer * abuf,int itharc);



#endif //GNSSIR_ARCS_H
