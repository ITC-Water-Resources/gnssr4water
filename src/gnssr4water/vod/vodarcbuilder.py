# This file is part of gnssr4water
# gnssr4water is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.

# gnssr4water is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with gnssr4water if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

# Author Roelof Rietbroek (r.rietbroek@utwente.nl), 2025
import asyncio
from asyncio.exceptions import CancelledError
from asyncio.queues import QueueEmpty, QueueFull
from datetime import timedelta,datetime
from gnssr4water.core.logger import log
from gnssr4water.sites.arc import Arc
from gnssr4water.sites.skymask import SimpleMask
import numpy as np


class VODArcBuilder:
    def __init__(self,stream_clear,stream_obstr,mask,block=True,minLengthSec=1800,split=True,minElevationSpan=None):
        self.arccache={}
        self.maxarcs=10 
        # initialize a queue of finished satellite arcs
        self.arcqueue=asyncio.Queue(self.maxarcs)
        #set expiry when arcs will remain open for appending new values 
        self.expiry=timedelta(seconds=60)

        self.minlength=timedelta(seconds=minLengthSec) # minimum length of arc for it to be accepted
        self.block=block #block appending when the arc queue is full (discard earlier arcs in the queue when block=False)
        self.snrStream=snrStream
        self.isStreaming=False
        self.streamtask=None
        self.mask=mask

        self.mindb=10 #ignore values with very (likely erroneous) db values
        self.split=split

        self.minpoints=4
        self.minElevationSpan=minElevationSpan

    
    def attrs(self):
        """
        Get as list of attributes of the arcbuilder setting
        """
        return {"max_arc_gap_sec":self.expiry.seconds,"minimum DbHz":self.mindb,
                "min_segment_length_sec":self.minlength.seconds,
                "min_elevation_span_deg":self.minElevationSpan,
                "split_asc_desc":self.split,
                "mask_title":self.mask.title,
                "noisebandwidth_hz":self.mask.noiseBandwidth}

    def __len__(self) -> int: 
        """
        Return amount of arcs available
        """
        return self.arcqueue.qsize()
    
    def prepareArc(self,arc):
        arcs=[]
        if len(arc) < self.minpoints:
            #basic sanity check to exclude all arcs with less them minpoints
            return []

        if self.split and "-" in arc.direction:
            #split into ascending and descending arc before filtering and resubmit to this function
            a1,a2=arc.split()
            arcs=self.prepareArc(a1)
            arcs.extend(self.prepareArc(a2))
            return arcs

        if self.minElevationSpan is not None and (np.max(arc.elev) - np.min(arc.elev) < self.minElevationSpan):
            #possibly check for minimum elevation span
            return []

        if arc.deltaT < self.minlength:
            #check for minimum timelength
            # log.warning(f"arc is too short, {arc.deltaT}")
            return []

        return [arc]


    def append(self,sativ):
        """
        Process a cycle of SNR observations
        """
        if sativ.sats_in_view == 0: 
            #nothing to add
            return []
        tm=sativ.time
        arcsout=[]

        for i in range(sativ.sats_in_view):
            prn=sativ.prn[i] 
            el=sativ.elevation[i]
            az=sativ.azimuth[i]
            cnr0=sativ.cnr0[i]
            system=sativ.system[i]
            if cnr0 < self.mindb:
                continue

            masked=self.mask.masked(el,az)
    
            if prn in self.arccache:
                if masked:
                    # satellite moved out of view of the mask -> close the arc generate a new arc object ( or 2 if a split is requested)
                    arcsout.extend(self.prepareArc(Arc(**self.arccache.pop(prn))))
                    continue
                elif (tm-self.arccache[prn]["time"][-1]) > self.expiry:
                    arcsout.extend(self.prepareArc(Arc(**self.arccache.pop(prn))))
                    #satellite is within the mask but last point was too far in the past -> submit existing arc but allow the current values to start a new arc (do not continue the loop)
                else:
                    #append values to existing arc
                    self.arccache[prn]["time"].append(tm)
                    self.arccache[prn]["elev"].append(el)
                    self.arccache[prn]["az"].append(az)
                    self.arccache[prn]["cnr0"].append(cnr0)
                    continue 
            elif masked:
                #satellite is not in view of the mask, ignore
                continue

            #When we land here we should initialize a new arc
            self.arccache[prn]={"prn":prn,"system":system,"time":[tm],"elev":[el],"az":[az],"cnr0":[cnr0]}

        #check for expired arc (e.g. lost tracking) and submit
        expiredarcs=[prn for prn,val in self.arccache.items() if  (tm-val['time'][-1]) > self.expiry]
        for prn in expiredarcs:
            arcsout.extend(self.prepareArc(Arc(**self.arccache.pop(prn))))
        
        #return all arcs that are ready to be processed further
        return arcsout
    


    async def start(self):
        """
        Start streaming satellite vehicle messages
        """
        if self.isStreaming:
            log.warning("Arcbuilder is already in streaming mode, ignoreing")
            return
        
        
        self.isStreaming=True
        try: 
            for sv_snr in self.snrStream.readcycles():
                arcs_ready=self.append(sv_snr)
                for arc in arcs_ready:
                    
                    #add arcs to the async queue
                    if self.block:
                        await self.arcqueue.put(arc)
                    else:
                        try:
                            self.arcqueue.put_nowait(arc)
                        except QueueFull:
                            log.warning("Arc queue is full, deleting oldest entry, without using it")
                            # get rid of the oldest arc in the queue without using it
                            self.arcqueue.get_nowait()
                            self.arcqueue.task_done()
        except CancelledError:
                log.warning("canceling streaming task") 
                pass #ok, pass so to set the isStreaming status to False below
        
        
        self.isStreaming=False


    async def async_arcs(self):
        """
        Async generator to retrieve completed arcs
        """
        if self.streamtask is not None:
            #restart
            log.warning("stopping streaming task") 
            self.streamtask.cancel()

        self.streamtask=asyncio.create_task(self.start())

        while True:
            try:
                arc=await asyncio.wait_for(self.arcqueue.get(),timeout=10)
                yield arc
                self.arcqueue.task_done()
            except asyncio.TimeoutError:
                if self.streamtask.done():
                    break
                else: 
                    continue
            
        if not self.streamtask.done():
            #cancel (stop) streaming new messages into the arc builder
            self.streamtask.cancel()
        log.info("No more arcs in the async queue")
        return
        

    def arcs(self):
        """
            Generator to retrieve completed arcs from a stream
        """
        while True:
            for sv_snr in self.snrStream.readcycles():
                arcs=self.append(sv_snr)
                for arc in arcs:
                    yield arc

            log.info("No more arcs")
            return

