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

#include <stdio.h>
#include "stream.h"
#include "nmea.h"
#include "arcs.h"
#include "skymask.h"

void usage(char * message) {
    fprintf(stderr,"%s\n",message);
    fprintf(stdout,"arcxtract (GNSSIR library)\n"
		  "Extract arcs from NMEA files or serial ports\n"
		  "Usage:\n"
		  "arcxtract [OPTIONS] FILEORSERIAL\n"); 
}

/// Main program to continuously build GNSSIR arcs from a file or serial
int main(int argc, char **argv){

  if (argc != 2){
      usage("Wrong number of arguments");
      return 1;

  }

  gnssrstream gnss_sid;
  if ( open_stream(argv[1],&gnss_sid)!= GNSSR_SUCCESS){
    fprintf(stderr,"Failed to open GNSSIR source stream:%s\n",argv[1]);
    return -2;
  }

  
  nmea_cycle cyc;
  arc_buffer abuf;

  skymask skymsk;
  int err;
  err=setup_simple_skymask(&skymsk,20,270,5,40);

  err=init_arc_buffer(&abuf,-1,-1);
  
  //set the skymask
  abuf.skymaskptr=&skymsk;



  if (err != GNSSR_SUCCESS){
      fprintf(stderr,"ERROR initializing arc buffer. error: %d\n",err);
      return err;
  }
  
  do{
    err=read_nmea_cycle(&gnss_sid,&cyc);
    if (err == GNSSR_EOF){
      fprintf(stderr,"END of file reached%d\n",err);
    }else{
      //append cycle to Arc Buffer
      if (cyc.sats_in_view > 0){
	err=append_cycle_data(&cyc,&abuf); 
	fprintf(stdout,"Current allocated arcs %ld\n",abuf.narcs);
	/*fprintf(stdout,"satellite in view %d\n",cyc.sats_in_view);*/
      }
    }
      
    //check for next finalized arcs
    int itharg;
    do{

      itharg=next_finalized_arc(&abuf);
      if (itharg >= 0){
	arc * aptr=abuf.arcbuf[itharg];
	int arcdelta=(int)(86400*(aptr->mjd[aptr->len-1]-aptr->mjd[0]));
	fprintf(stdout,"Finished arc prn %d found with %ld data points over %d min\n",aptr->prn,aptr->len,arcdelta/60);
	err=purge_arc(&abuf,itharg);
      }
    }
    while(itharg >=0);



  }while (err == GNSSR_SUCCESS);



  return 0;
}

