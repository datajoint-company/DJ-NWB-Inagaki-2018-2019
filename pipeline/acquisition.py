'''
Schema of aquisition information.
'''
import re
import os
import sys
from datetime import datetime

import numpy as np
import scipy.io as sio
import datajoint as dj
import h5py as h5

from . import reference, subject, utilities

schema = dj.schema(dj.config.get('database.prefix', '') + 'acquisition')


@schema
class ExperimentType(dj.Lookup):
    definition = """
    experiment_type: varchar(64)
    """
    contents = zip(['behavior', 'extracellular', 'photostim', 'Auditory task', 'Tactile task'
                    'intracellular', 'EPSP', 'regular'])  # regular: no current injection, EPSP: negative current injection


@schema
class Session(dj.Manual):
    definition = """
    -> subject.Subject
    session_time: datetime    # session time
    session_id: varchar(24)
    ---
    session_directory = "": varchar(256)
    session_note = "": varchar(256) 
    """

    class Experimenter(dj.Part):
        definition = """
        -> master
        -> reference.Experimenter
        """

    class ExperimentType(dj.Part):
        definition = """
        -> master
        -> ExperimentType
        """  
    

@schema
class TrialSet(dj.Imported):
    definition = """
    -> Session
    ---
    trial_counts: int # total number of trials
    """
    
    class Trial(dj.Part):
        definition = """
        -> master
        trial_id: smallint           # id of this trial in this trial set
        ---
        start_time=null: float               # start time of this trial, with respect to starting point of this session
        stop_time=null: float                # end time of this trial, with respect to starting point of this session
        -> reference.TrialType
        -> reference.TrialResponse
        trial_stim_present: bool  # is this a stim or no-stim trial
        trial_is_good: bool  # good/bad status of trial (bad trials are not analyzed)
        delay_duration=null: decimal(6,2)  # (s) duration of the delay period
        """
        
    class EventTime(dj.Part):
        definition = """ # experimental paradigm event timing marker(s) for this trial
        -> master.Trial
        -> reference.ExperimentalEvent.proj(trial_event="event")
        ---
        event_time = null: float   # (in second) event time with respect to this session's start time
        """

    def make(self, key):
        # this function implements the ingestion of Trial data into the pipeline
        return NotImplementedError
    