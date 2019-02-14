# -*- coding: utf-8 -*-
'''
Schema of analysis data.
'''
import re
import os
from datetime import datetime

import numpy as np
import scipy.io as sio
import datajoint as dj
import h5py as h5

from . import reference, utilities, acquisition

schema = dj.schema(dj.config.get('database.prefix', '') + 'analysis')


@schema
class TrialSegmentationSetting(dj.Lookup):
    definition = """ 
    trial_seg_setting: smallint
    ---
    -> reference.ExperimentalEvent
    pre_stim_duration: decimal(4,2)  # (s) pre-stimulus duration
    post_stim_duration: decimal(4,2)  # (s) post-stimulus duration
    """
    contents = [[0, 'delay_start', 1.5, 3]]
    

def perform_trial_segmentation(trial_key, event_name, pre_stim_dur, post_stim_dur, data, fs, first_time_point):
        # get event time
        try: 
            event_time_point = get_event_time(event_name, trial_key)
        except EventChoiceError as e:
            raise e
        #
        pre_stim_dur = float(pre_stim_dur)
        post_stim_dur = float(post_stim_dur)
        # check if pre/post stim dur is within start/stop time, if not, pad with NaNs
        trial_start, trial_stop = (acquisition.TrialSet.Trial & trial_key).fetch1('start_time', 'stop_time')

        pre_stim_nan_count = 0
        post_stim_nan_count = 0
        if trial_start and event_time_point - pre_stim_dur < trial_start:
            pre_stim_nan_count = int((trial_start - (event_time_point - pre_stim_dur)) * fs)
            pre_stim_dur = 0
            print(f'Warning: Out of bound prestimulus duration, pad {pre_stim_nan_count} NaNs')
        if trial_stop and event_time_point + post_stim_dur > trial_stop:
            post_stim_nan_count = int((event_time_point + post_stim_dur - trial_stop) * fs)
            post_stim_dur = trial_stop - event_time_point
            print(f'Warning: Out of bound poststimulus duration, pad {post_stim_nan_count} NaNs')

        event_sample_point = (event_time_point - first_time_point) * fs
        
        sample_points_to_extract = range((event_sample_point - pre_stim_dur * fs).astype(int),
                                             (event_sample_point + post_stim_dur * fs + 1).astype(int))
        segmented_data = data[sample_points_to_extract]    
        # pad with NaNs
        segmented_data = np.hstack((np.full(pre_stim_nan_count, np.nan), segmented_data,
                                    np.full(post_stim_nan_count, np.nan)))
        
        return segmented_data
       

def get_event_time(event_name, key):
    # get event time
    try:
        t = (acquisition.TrialSet.EventTime & key & {'trial_event': event_name}).fetch1('event_time')
    except:
        raise EventChoiceError(event_name, f'{event_name}: event not found')  
    if np.isnan(t):
        raise EventChoiceError(event_name, msg=f'{event_name}: event_time is nan')
    else:
        return t
    
    
class EventChoiceError(Exception):
    '''Raise when "event" does not exist or "event_type" is invalid (e.g. nan)'''
    def __init__(self, event_name, msg=None):
        if msg is None:
            msg = f'Invalid event type or time for: {event_name}'
        super().__init__(msg)
        self.event_name = event_name
    pass
