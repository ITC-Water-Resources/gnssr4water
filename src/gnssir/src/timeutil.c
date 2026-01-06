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

/*# Author Roelof Rietbroek (r.rietbroek@utwente.nl), 2025*/


double mjd(const int year, const int month,const int day, const int hour, const int minute, const double second){
  
  int jd= day-32075+1461*(year+4800+((month-14)/12))/4+367*(month-2-((month-14)/12)*12)/12-3*((year+4900+((month-14)/12))/100)/4;
/*int jd= day-32075+1461*(yr+4800+(month-14)/12)/4+367*(month-2-(month-14)/12*12)/12-3*((yr+4900+(month-14)/12)/100)/4;*/

  return (double)jd - 2400000.5 + ((double)(hour-12)+(double)minute/60+(double)second/3600)/24.0;



}


void mjd_to_datetime(double mjd, int *year,int * month, int * day, int * hour,int * minute, double * second){
  
  
  double dayfrac=mjd-(int)mjd;

  int jd=mjd+2400000.5;
  
  //constants for the algoiithm
  int y=4716;
  int v=3;
  int j=1401;
  int u=5;
  int m=2;
  int s=153;
  int n =12;
  int w = 2;
  int r =4;   
  int B =274277;
  int p=1461;
  int C=-38;   
  

  int f = jd + j + (((4 * jd + B)/146097) * 3)/4 + C;

  int e = r * f + v;
  int g = (e%p)/r;
  int h = u * g + w;
  *day = (h%s)/u + 1;
  *month = (h/s + m)%n + 1;
  *year = (e/p) - y + (n + m - *month)/ n;

/*int p=(jd+0.5); int s1=p+68569;*/
  /*int n=(4*s1)/146097;*/
  /*int s2=s1-(146097*n+3)/4;*/
  /*int i=(4000*(s2 + 1))/1461001;*/
  /*int s3=s2 - (1461*i)/4 + 31;*/
  /*int q=(80*s3)/2447;*/
  /*int e = s3 - (2447*q)/80;*/
  /*int s4 = q/11;*/
  /**month = q + 2 - 12*s4; */
  /**yr = 100*(n - 49) + i + s4; */
  /**day= (e + jd - p + 0.5);*/

  /*double dayfrac=((e + jd - p +0.5 )- *day);*/
  
  *hour=(dayfrac*24);
  dayfrac-=(double)(*hour)/24;
  *minute=(dayfrac*24*60);
  dayfrac-=(double)(*minute)/(24*60);
  *second=dayfrac*86400;



} 
