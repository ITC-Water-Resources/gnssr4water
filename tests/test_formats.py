from gnssr4water.gnssrlib import NMEAFile,nmea_type

import os
from datetime import datetime,timedelta

def test_NMEAFile():
    dir_path = os.path.dirname(os.path.realpath(__file__))

    nmeafile=os.path.join(dir_path,"testdata/lvicpi1_2024-02-17_00.gz")
    # nmeafile=os.path.join(dir_path,"testdata/lvicpi1_2024-02-17_00")
    # nmeafile=os.path.join(dir_path,"testdata/eoaf_ica_gnssr02_2024-06-21T000000.lz4")
    with NMEAFile(nmeafile) as nmeaid:
        for nmeacyc in nmeaid.readcycles():
            if nmeacyc['sats_in_view'] > 0:
                dtime=datetime(nmeacyc['year'],nmeacyc['month'],nmeacyc['day'],nmeacyc['hr'],nmeacyc['min'])+timedelta(seconds=nmeacyc['sec'])
                breakpoint()
            print(nmeacyc)

        # for i in range(40):
            # nmeacyc=nmeaid.read_cycle()
        # for m_t,nmea in nmeaid.readnmeas():
            # if m_t != nmea_type.NMEA_GSV:
                # breakpoint()
            # print(nmea)
    
