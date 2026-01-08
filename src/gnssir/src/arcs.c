/*# gnssir4 is free software; you can redistribute it and/or*/
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

/*# Author Roelof Rietbroek (r.rietbroek@utwente.nl), 2025*/

#include <memory.h>
#include "arcs.h"
#include "position.h"

int init_arc(arc *data){
    const gnss_system system=GNSS_UNKNOWN;
    data->len=0;
    data->nreserve=0;
    data->state=OPEN;
    memcpy(&data->system,&system,sizeof(system));
    data->prn =-1;
    int err=init_enu_position(&data->site); 
    data->mjd=NULL;
    data->elevation=NULL;
    data->azimuth=NULL;
    data->values=NULL;

    return GNSSIR_SUCCESS; 
}


/*Free the dynamically allocated arrays in an arc struct*/
int free_arc(arc* data){

    

    if (data->mjd){
      FREEMEM(data->mjd);
      data->mjd=NULL;
    }
    
    if (data->elevation){
      FREEMEM(data->elevation);
      data->elevation=NULL;
    }
    
    if (data->azimuth){
      FREEMEM(data->azimuth);
      data->azimuth=NULL;
    }


    if (data->values){
      FREEMEM(data->values);
      data->values=NULL;
    }
    return GNSSIR_SUCCESS;
}


int realloc_and_copy(void ** dvec,size_t currentlen, size_t sz){
  
  //temporary copy pointer
  float * tmpstore=*dvec;

  //allocate new memory
  
  *dvec = ALLOC(sz*(ARC_DATA_CHUNK+currentlen));   

  if (!*dvec){
    return GNSSIR_MEMORY_ERROR;
  }

  if (tmpstore){
  //we need to copy old values in the new array
    memcpy(*dvec,tmpstore,currentlen*sz);
      
    FREEMEM(tmpstore);
    
  }

  return GNSSIR_SUCCESS;

}


int append_to_arc(arc *data, double mjd, float elevation, float azimuth, float value){
  
  if (data->nreserve < data->len+1){ 
    if ( GNSSIR_SUCCESS != realloc_and_copy((void**)&data->elevation,data->len,sizeof(float))){
      return GNSSIR_MEMORY_ERROR;
    }
    
    if ( GNSSIR_SUCCESS != realloc_and_copy((void**)&data->azimuth,data->len,sizeof(float))){
      return GNSSIR_MEMORY_ERROR;
    }
    
    if ( GNSSIR_SUCCESS != realloc_and_copy((void**)&data->values,data->len,sizeof(float))){
      return GNSSIR_MEMORY_ERROR;
    }
    
    if ( GNSSIR_SUCCESS != realloc_and_copy((void**)&data->mjd,data->len,sizeof(double))){
      return GNSSIR_MEMORY_ERROR;
    }

    data->nreserve+=ARC_DATA_CHUNK;

  }
  
  //actually append the data
  data->mjd[data->len]=mjd;
  data->elevation[data->len]=elevation;
  data->azimuth[data->len]=azimuth;
  data->values[data->len]=value;


  data->len++;

  return GNSSIR_SUCCESS;
}


int init_arc_buffer(arc_buffer* arcbuf,int expiry_sec,int max_arclen_sec){
  for (int i=0;i<ARC_BUFFER_SIZE;i++){
    arcbuf->arcbuf[i]=NULL;
    /*arcbuf->state[i]=0;*/
  }
  if (expiry_sec < 0){
    //set default of 5 min (finalize when a data gap of more than expiry_sec was encountered)
    expiry_sec=5*60;
  }
  
  if (max_arclen_sec < 0){
    //set default (1 hour maximum arc length)
    max_arclen_sec=1*3600;
  }
  
  arcbuf->expiry_sec=expiry_sec;
  arcbuf->max_arclen_sec=max_arclen_sec;
  arcbuf->narcs=0; 
  arcbuf->skymaskptr=NULL;
  return GNSSIR_SUCCESS;
}


int free_arc_buffer(arc_buffer* arcbuf){
  for (int i=0;i<ARC_BUFFER_SIZE;i++){
    arc * aptr=arcbuf->arcbuf[i];
    if (aptr != NULL){
      free_arc(aptr);
    }
  }
  return GNSSIR_SUCCESS;

}

arc* find_arcptr(arc_buffer * arcbuf, int prn){
  arc* aptr;
  for(int i=0;i< ARC_BUFFER_SIZE;i++){
    aptr=arcbuf->arcbuf[i];
      if (aptr){
        if (aptr->prn == prn && aptr->state == OPEN){
          return aptr;
        }
    }
  }
  
  return NULL;
}

int new_arc(arc** arcptr, arc_buffer *arcbuf,int prn, const gnss_system * sys,const enu_position * site){
    //find a free or oldest spot
    int islot=-1;
    //Make large enough so to initialize it on first encounter
    
    double rank=1e12;

    arc * aptr=NULL;
    int replace=1;

    for(int i=0;i< ARC_BUFFER_SIZE;i++){
      aptr=arcbuf->arcbuf[i];
      if (!aptr){
          //found an empty slot
          islot=i;
          //no replacement needed
          replace=0;
          break;
      }

      if (aptr->len ==0){
          
          islot=i;
          rank=0;
      }else{
        if ( aptr->mjd[aptr->len-1] < rank){
          islot=i;
          rank=aptr->mjd[aptr->len-1];
        }
      }

    }

    
    if (replace){
      warn_print("Warning: discarding oldest arc with prn %d\n",arcbuf->arcbuf[islot]->prn);
      if( purge_arc(arcbuf,islot) != GNSSR_SUCCESS){
        return GNSSIR_MEMORY_ERROR;
      }
    }


   ///allocate and initiate new arc 
    int err=insert_new_arc(arcbuf,islot);

    if (err != GNSSR_SUCCESS){
      return err;
    }
    aptr=arcbuf->arcbuf[islot];

    //set system, position and prn
    memcpy(&aptr->system,sys,sizeof(gnss_system));
    memcpy(&aptr->site,site,sizeof(enu_position));
    aptr->prn=prn;


    *arcptr=aptr;
    

    return GNSSR_SUCCESS;

    
}

int check_finalization(arc_buffer * arcbuf,double mjdcurrent){
    for(int i=0;i< ARC_BUFFER_SIZE;i++){
      arc * aptr=arcbuf->arcbuf[i];
      if (aptr){
          if (aptr->len > 0){
            double delta_sec=(int)(86400*(mjdcurrent-aptr->mjd[aptr->len-1]));
            if ((int)delta_sec > arcbuf->expiry_sec){
                aptr->state=FINAL;
                continue;
            }
          }
          
          if (aptr->len > 1){
            //also check arc length
            double delta_arc_sec=(int)(86400*(aptr->mjd[aptr->len-1]-aptr->mjd[0]));
            if ((int)delta_arc_sec > arcbuf->max_arclen_sec){
                aptr->state=FINAL;
                continue;
            }
      
          }
      }
    }
    

  return GNSSR_SUCCESS;
}

int append_cycle_data(const nmea_cycle * cyc, arc_buffer* arcbuf){
  int prn;
  int err;
  arc* aptr;

  //check for finalization of arcs
  err=check_finalization(arcbuf,cyc->mjd);


  for(int i=0;i < cyc->sats_in_view;i++){
    prn=cyc->prn[i];
    //check whether an arc with that prn already exists
    aptr=find_arcptr(arcbuf,prn);

    if(arcbuf->skymaskptr){
      int inmask=within_mask(arcbuf->skymaskptr,cyc->azimuth[i],cyc->elevation[i]);
      if (!inmask){
        if (aptr){
          //possibly trigger finalization when arc exists but exited skymask
          aptr->state=FINAL;
        }
        continue;
      }
    }

    if (!aptr){
      //try to create a new arc
      err=new_arc(&aptr,arcbuf,prn,&cyc->system[i],&cyc->site);
           
      if (!aptr){
        return GNSSIR_MEMORY_ERROR;
      }
    }
  
  //
  //append data to the relevant arc
   err=append_to_arc(aptr,cyc->mjd,cyc->elevation[i],cyc->azimuth[i],cyc->cnr0[i]);
  
  } 
  
  err=check_finalization(arcbuf,cyc->mjd);
  
  return GNSSR_SUCCESS;

}

int next_finalized_arc(const arc_buffer * abuf){
    for(int i=0;i< ARC_BUFFER_SIZE;i++){
      const arc * aptr=abuf->arcbuf[i];
      if (aptr){
          if(aptr->state == FINAL){
            return i;
          }
      }
    }
    //not found
    return -1;
}

int insert_new_arc(arc_buffer * abuf,int itharc){
   
      int err=GNSSR_SUCCESS;
      arc * aptr=abuf->arcbuf[itharc];
      if (aptr){
        err=purge_arc(abuf,itharc);
        if (err != GNSSR_SUCCESS){
          return err;
        }
      }

      aptr=ALLOC(sizeof(arc));
        

      if (!aptr){
      
        return GNSSIR_MEMORY_ERROR;
      }
    
      err=init_arc(aptr);

      if (err != GNSSR_SUCCESS){
        return err;
      }

      abuf->arcbuf[itharc]=aptr;
      abuf->narcs++;    
      return err;
}

int purge_arc(arc_buffer * abuf,int itharc){
   
      int err=GNSSR_SUCCESS;
      arc * aptr=abuf->arcbuf[itharc];
      if (aptr){
        err=free_arc(aptr);
        FREEMEM(aptr);
        abuf->narcs--; 
      }
      abuf->arcbuf[itharc]=NULL;
      return err;
}
