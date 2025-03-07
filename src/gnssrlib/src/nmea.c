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
#include <stdlib.h>
#include "gnssrlib.h"
#include "nmea.h"

unsigned char calculate_checksum(const char * nmea){
	size_t slen=strlen(nmea);
	unsigned char xorval=nmea[1];
	for (size_t i=2;i<slen-3;i++){
		xorval=xorval^nmea[i];
	}
	return xorval;
}

int shift_to_komma(const  char ** nmeaPtr,const char ** kommaPtr,int skip){
	
	for (int i=0;i<skip;i++){
	    //shift tothe next komma in the string
	    if (*kommaPtr!=NULL){
		*nmeaPtr=*kommaPtr+1;
	    }

	    *kommaPtr=strchr(*nmeaPtr,',');
	    if (*kommaPtr==NULL){
		return GNSSR_IO_ERROR;
	    }
	}
    return GNSSR_SUCCESS;
}

float convert_deg(const float deg){
	const float cconv=(1.0-100.0/60);
	return deg/60 + cconv*(int)(deg/100);
}

void extract_time(const char * nmeaPtr, int * hr, int * min, float * sec){
	
	float tstamp=atof(nmeaPtr);
	*hr=(int)(tstamp/10000);
	*min=(int)((tstamp-*hr*10000)/100);
	*sec=tstamp-*hr*10000-*min*100;
	
}

int init_nmea_cycle(nmea_cycle * data){
	const gnss_system system=GNSS_UNKNOWN;
	data->year=NMEA_FILL;
	data->month=NMEA_FILL;
	data->day=NMEA_FILL;
	data->hr=NMEA_FILL;
	data->min=NMEA_FILL;
	data->sec=NMEA_FILL;
	data->lon=NMEA_FILL;
	data->lat=NMEA_FILL;
	data->ortho_height=NMEA_FILL;
	data->geoid_height=NMEA_FILL;
	data->sats_in_view=0;
	for (int i=0;i<NMEA_GSV_MAX_SATELLITES;++i){
	    data->prn[i]=0;
	    data->elevation[i]=0;
	    data->azimuth[i]=0;
	    data->cnr0[i]=0;
	    memcpy(&data->system[i],&system,sizeof(system));
	}
	return GNSSR_SUCCESS;
}


nmea_type check_nmea(char * nmea){
    //remove possible line ends and carriage returns and determine the type of NMEA message

	if (nmea[0] != '$'){
		return NMEA_INVALID;
	}
	//possible remove carriage return and or newline
	size_t slen=strlen(nmea);
	if (nmea[slen-2]=='\r'){
		nmea[slen-2]='\0';
		nmea[slen-1]='\0';
		slen=slen-2;
	}else if (nmea[slen-1]=='\n'){
		nmea[slen-1]='\0';
		slen=slen-1;
	}
	//check if the checksum is correct
	int tmp;
	sscanf(nmea+slen-2,"%02x", &tmp);
	unsigned char check= (unsigned char) tmp;
	if ( calculate_checksum(nmea) != check){
		return NMEA_INVALID;
	}
	///Determines the type of NMEA message
	if (strncmp(nmea+3,"RMC",3)==0){
		return NMEA_RMC;
	}else if (strncmp(nmea+3,"GGA",3)==0){
	    return NMEA_GGA;
	}else if (strncmp(nmea+3,"GSV",3)==0){
	    return NMEA_GSV;
	}else if (strncmp(nmea+3,"GLL",3)==0){
	    return NMEA_GLL;
	}else if (strncmp(nmea+3,"GSA",3)==0){
	    return NMEA_GSA;
	}else if (strncmp(nmea+3,"VTG",3)==0){
	    return NMEA_VTG;
	}else if (strncmp(nmea+3,"GNS",3)==0){
	    return NMEA_GNS;
	}else{
	    return NMEA_UNSUPPORTED;
	}
}

int read_nmea_cycle(gnssrstream *sid, nmea_cycle * data){
    nmea_type m_type; 
    char buffer[NMEA_BUFFER_SIZE];
    int err=init_nmea_cycle(data);
    if (err != GNSSR_SUCCESS){
	return err;
    }
    int cycle_found=0;
    do{
	err=readline(sid,buffer,NMEA_BUFFER_SIZE);
	if (err != GNSSR_SUCCESS){
	    return err;
	}
	m_type=check_nmea(buffer);
	switch (m_type){
	    case NMEA_GSV:
		//Keep adding satellites in view until a RMC message is encountered
		err=update_nmea_GSV(buffer,data);
		break;
	    case NMEA_RMC:
		err=update_nmea_RMC(buffer,data);
		cycle_found=1;
		break;
	    case NMEA_GGA:
		//possibly adds orthometric and geoid height
		int erropt=update_nmea_GGA(buffer,data);
		if (erropt != GNSSR_SUCCESS){
		    err=GNSSR_SUCCESS;
		    //ok, as this is optional data
		}
		break;
	    default:
	}
	if (err != GNSSR_SUCCESS){
	    return err;
	}
    }while (! cycle_found);

    return GNSSR_SUCCESS;

}

int update_nmea_RMC(const char * nmea, nmea_cycle *data){
	const char * nmeaPtr=nmea;
	const char* kommaPtr=NULL;
	if (shift_to_komma(&nmeaPtr,&kommaPtr,2) == GNSSR_IO_ERROR){
	    return GNSSR_IO_ERROR;
	}
	
	//extract UTC time
	extract_time(nmeaPtr,&data->hr,&data->min,&data->sec);
	/*sscanf(nmeaPtr,"%02d%02d", &data->hr,&data->min);*/
	/*data->sec=atof(nmeaPtr+5);*/
	
	if (shift_to_komma(&nmeaPtr,&kommaPtr,1) == GNSSR_IO_ERROR){
	    return GNSSR_IO_ERROR;
	}


	data->status=*(nmeaPtr);
	

	if (shift_to_komma(&nmeaPtr,&kommaPtr,1) == GNSSR_IO_ERROR){
	    return GNSSR_IO_ERROR;
	}

	//extract latitude
	float deg=atof(nmeaPtr);
	deg=convert_deg(deg);
	
	if (shift_to_komma(&nmeaPtr,&kommaPtr,1) == GNSSR_IO_ERROR){
	    return GNSSR_IO_ERROR;
	}
	
	if (*(nmeaPtr)=='S'){
		data->lat=-deg;
	}else{
		data->lat=deg;
	}

	if (shift_to_komma(&nmeaPtr,&kommaPtr,1) == GNSSR_IO_ERROR){
	    return GNSSR_IO_ERROR;
	}
	deg=atof(nmeaPtr);

	deg=convert_deg(deg);

	if (shift_to_komma(&nmeaPtr,&kommaPtr,1) == GNSSR_IO_ERROR){
	    return GNSSR_IO_ERROR;
	}
	if (*(nmeaPtr)=='W'){
		data->lon=-deg;
	}else{
		data->lon=deg;
	}
	
	/*///skip the speed and course*/
	if (shift_to_komma(&nmeaPtr,&kommaPtr,3) == GNSSR_IO_ERROR){
	    return GNSSR_IO_ERROR;
	}
    
	//extract date
	sscanf(nmeaPtr,"%02d%02d%02d", &data->day,&data->month,&data->year);
	if (data->year < 80){
		data->year+=2000;
	}
	return GNSSR_SUCCESS;
}

void get_gnss_system(const char * nmea,gnss_system *system){
	if (strncmp(nmea+1,"GP",2)==0){
	    /*gnss_system gsystem=GPSL1;*/
	    memcpy(system,&gnss_gpsl1,sizeof(gnss_gpsl1));
	}else if (strncmp(nmea+1,"GL",2)==0){
	    memcpy(system,&gnss_glonassiil1,sizeof(gnss_glonassiil1));
	}else{
	    gnss_system gsystem=GNSS_UNKNOWN;
	    memcpy(system,&gnss_unknown,sizeof(gnss_unknown));
	}

}

int update_nmea_GSV(const char * nmea, nmea_cycle *data){
	const char * nmeaPtr=nmea;
	const char* kommaPtr=NULL;
	//check satellite system
	gnss_system system;
	get_gnss_system(nmeaPtr,&system);

	if (shift_to_komma(&nmeaPtr,&kommaPtr,4) == GNSSR_IO_ERROR){
	    return GNSSR_IO_ERROR;
	}

	//extract total number of messages in this cycle
	/*int total_messages=atoi(nmeaPtr);*/
	

	/*if (shift_to_komma(&nmeaPtr,&kommaPtr,1) == GNSSR_IO_ERROR){*/
	    /*return GNSSR_IO_ERROR;*/
	/*}*/
	//extract message id in this cycle
	/*int messageid=atoi(nmeaPtr)-1;*/
	
	/*if (shift_to_komma(&nmeaPtr,&kommaPtr,1) == GNSSR_IO_ERROR){*/
	    /*return GNSSR_IO_ERROR;*/
	/*}*/
	
	/*int satellites_in_view=atoi(nmeaPtr);*/

	/*if (shift_to_komma(&nmeaPtr,&kommaPtr,1) == GNSSR_IO_ERROR){*/
	    /*return GNSSR_IO_ERROR;*/
	/*}*/
	
	int prn;
	float elev;
	float az;
	float cnr0;
	int stop=0;
	for (int i=0 ;i<4;++i){
	    if (shift_to_komma(&nmeaPtr,&kommaPtr,1) == GNSSR_IO_ERROR){
		//possibly gracefully end the cycle
		return GNSSR_SUCCESS;
	    }
	    prn=atoi(nmeaPtr);
	    if (shift_to_komma(&nmeaPtr,&kommaPtr,1) == GNSSR_IO_ERROR){
		return GNSSR_IO_ERROR;
	    }
	    elev=atof(nmeaPtr);
	    if (shift_to_komma(&nmeaPtr,&kommaPtr,1) == GNSSR_IO_ERROR){
		return GNSSR_IO_ERROR;
	    }
	    az=atof(nmeaPtr);
	    if (shift_to_komma(&nmeaPtr,&kommaPtr,1) == GNSSR_IO_ERROR){
		//ok to have an error here (no komma found at the end)
		stop=1;
	    }

	    cnr0=atof(nmeaPtr);

	    int idx=data->sats_in_view;
	    data->prn[idx]=prn;
	    data->elevation[idx]=elev; 
	    data->azimuth[idx]=az;
	    data->cnr0[idx]=cnr0;
	    memcpy(&data->system[idx],&system,sizeof(system));
	    data->sats_in_view++;
	    if (data->sats_in_view >= NMEA_GSV_MAX_SATELLITES){
		//maximum number of satellites in view reached (start over)
		printf("Maximum number of satellites in view reached, resetting cycle\n");
		data->sats_in_view=0;
	    }
	    if (stop){
		return GNSSR_SUCCESS;

	    }
	}
	
    return GNSSR_SUCCESS;	
	

}


int update_nmea_GGA(const char * nmea, nmea_cycle *data){
	
	const char * nmeaPtr=nmea;
	const char* kommaPtr=NULL;
	//skip stuff which we already have from the RMC message
	if (shift_to_komma(&nmeaPtr,&kommaPtr,10) == GNSSR_IO_ERROR){
	    return GNSSR_IO_ERROR;
	}
    
	data->ortho_height=atof(nmeaPtr);


	if (shift_to_komma(&nmeaPtr,&kommaPtr,2) == GNSSR_IO_ERROR){
	    return GNSSR_IO_ERROR;
	}


	data->geoid_height=atof(nmeaPtr);

	return GNSSR_SUCCESS;

}
