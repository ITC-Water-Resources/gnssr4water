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
#include <zlib.h>
#include <string.h>
#include "gnssrlib.h"
#include "stream.h"

#ifndef NMEA_H
#define NMEA_H

#define NMEA_BUFFER_SIZE 82

//maximum number of satellites in view to deal with
#ifndef NMEA_GSV_MAX_SATELLITES
#define NMEA_GSV_MAX_SATELLITES 40
#endif

#define NMEA_FILL -9999

typedef enum nmea_type { 
	NMEA_GGA,
	NMEA_GSV,
	NMEA_GLL,
	NMEA_GSA,
	NMEA_RMC,
	NMEA_VTG,
	NMEA_GNS,
	NMEA_UNSUPPORTED,
	NMEA_INVALID
}nmea_type;


///holds the information of all the GSV messages in a cycle
struct nmea_cycle{
	//RMC stuff
	int year;
	int month;
	int day;
	int hr;
	int min;
	float sec;
	char status;
	float lat;
	float lon;
	float ortho_height;
	float geoid_height;
	//GSV Stuff
	int sats_in_view;
	gnss_system system[NMEA_GSV_MAX_SATELLITES];
	int prn[NMEA_GSV_MAX_SATELLITES];
	float elevation[NMEA_GSV_MAX_SATELLITES];
	float azimuth[NMEA_GSV_MAX_SATELLITES];
	float cnr0[NMEA_GSV_MAX_SATELLITES];
};

typedef struct nmea_cycle nmea_cycle;

unsigned char calculate_checksum(const char * nmea);

int update_nmea_RMC(const char * nmea, nmea_cycle *data);

int update_nmea_GSV(const char * nmea, nmea_cycle *data);

int update_nmea_GGA(const char * nmea, nmea_cycle *data);

nmea_type check_nmea(char * nmea);

int init_nmea_cycle(nmea_cycle * data);

int read_nmea_cycle(gnssrstream *sid, nmea_cycle * data);

#endif //NMEA_H
