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

#ifndef GNSSRLIB_H
#define GNSSRLIB_H

#define SPEED_OF_LIGHT 299792458.0

#define GNSS_BAND( FREQ, WMHZ, NAME )     \
	{                             \
	  .system=NAME,		      \
	  .frequency=FREQ,              \
	  .length=1e-6*SPEED_OF_LIGHT/FREQ,  \
	  .bandwidth=1e6*WMHZ           \
	};

#define GPSL1 GNSS_BAND(1575.42,15.345,"GPSL1");
#define GPSL2 GNSS_BAND(1227.6,11,"GPSL2");
#define GPSL5 GNSS_BAND(1176.45,12.5,"GPSL5");


#define QZSSL5  GNSS_BAND(1176.45,24,"QZSSL5");
#define QZSSL2C GNSS_BAND(1227.6,11,"QZSSL2");
#define QZSSE6 GNSS_BAND(1278.75,20,"QZSSE6");
#define QZSSL1 GNSS_BAND(1575.42,12,"QZSSL1")

#define GLONASSIL1 GNSS_BAND(1602,6.5,"GLONASSIL1");
#define GLONASSIL2  GNSS_BAND(1246,5,"GLONASSIL2");
#define GLONASSIIL1 GNSS_BAND(1575.42,6.5,"GLONASSIIL1");
#define GLONASSIIL2 GNSS_BAND(1248.06,8.75,"GLONASSIIL2");

#define GNSS_UNKNOWN GNSS_BAND(-1,-1,"UNKNOWN");
//possible other GNSS bands
//  GNSS frequencies (source https://www.rfwireless-world.com/Terminology/GPS-Frequency-Band-and-GNSS-Frequency-Band.html)
//# GLONASS II-L1 	1600.995MHz, 0.1874m,15.365MHz
//# GLONASS II-L3 	1202.025MHz, 0.2496m,20.46MHz
//# GLONASS II-L5 	1176.45MHz,0.255m,10.22MHz
//# GALILEO-E1 	1575.42MHz,0.1904m, 12MHz
//# GALILEO-E5b 	1207.14MHz, 0.248m, 12.5MHz
//# GALILEO-E5a 	1176.45MHz, 0.255m, 12.5MHz
//# GALILEO-E6 	1278.75MHz, 0.2346m, 20MHz
//# COMPASS CPII/Beidou-E2 	1561.098MHz,0.1921m,16MHz
//# COMPASS CPII/Beidou-E5 	1207.14MHz, 0.248m, 16MHz
//# COMPASS CPII/Beidou-E6 	1268.52MHz, 0.2364m, 16MHz
//# COMPASS CPII/Beidou-B1 	1561.098MHz, 0.1921m, 4.092MHz
//# COMPASS CPII/Beidou-B1-2 	1589.74MHz, 0.1887m, 4.092MHz
//# COMPASS CPII/Beidou-B2 	1207.14MHz, 0.248m, 24MHz
//# COMPASS CPII/Beidou-B3 	1268.52MHz, 0.2365m, 24MHz
//# COMPASS CPII/Beidou,B1-BOC 	1575.42MHz, 0.1904m, 16.368MHz
//# COMPASS CPII/Beidou,B2-BOC 	1207.14MHz, 0.248m, 5.115MHz
//# COMPASS CPII/Beidou,B3-BOC 	1268.52MHz, 0.2365m, 35.805MHz
//# COMPASS CPII/Beidou,L5 	1176.45MHz, 0.255m, 24MHz
//# IRNSS-1,L5 	1176.45MHz, 0.255m, 24MHz
//# IRNSS-1,S-Band 	2492.028MHz, 0.1204m, 16.5MHz 
//typedef enum gnss_system{ 
	//GPSL1=0,
	//GLONASSIIL1,
	//UNKNOWN
//}gnss_system;

struct gnss_system{
	const char system[12];
	double frequency;
	double length;
	double bandwidth;
};

typedef struct gnss_system gnss_system; 


extern const gnss_system gnss_gpsl1;
extern const gnss_system gnss_gpsl2;
extern const gnss_system gnss_glonassiil1;
extern const gnss_system gnss_unknown;
// ..
//
//
void copy_GNSS_as(gnss_system *sys, const gnss_system * sysfrom);

#endif //GNSSRLIB_H
