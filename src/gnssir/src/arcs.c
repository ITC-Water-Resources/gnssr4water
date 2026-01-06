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
