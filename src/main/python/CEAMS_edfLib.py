#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A basic library to read, modify and write edf file.  
Only specific fields of the edf header can be modified.

Created on Thu Oct 29 14:34:43 2020

@author: Karine Lacourse (karine.lacourse.cnmtl@ssss.gouv.qc.ca)
"""

import numpy as np
import sys
import os
import re

def read_edf_header(fname, message_win):
    """Read header information from EDF+ based on https://www.edfplus.info/specs/edf.html
    
    Parameters
    -----------
    fname : str
        Path to the EDF or EDF+ file.
   
    Returns
    -----------
    edf_info : dict 
        each field of the edf header are saved in edf_info
        
    Usage : edf_info = read_edf_header(your_file.edf, message_win)


    Additional information:

    HEADER RECORD (we suggest to also adopt the 12 simple additional EDF+ specs)
        8 ascii : version of this data format (0)
        80 ascii : local patient identification (mind item 3 of the additional EDF+ specs)
        80 ascii : local recording identification (mind item 4 of the additional EDF+ specs)
        8 ascii : startdate of recording (dd.mm.yy) (mind item 2 of the additional EDF+ specs)
        8 ascii : starttime of recording (hh.mm.ss)
        8 ascii : number of bytes in header record
        44 ascii : reserved
        8 ascii : number of data records (-1 if unknown, obey item 10 of the additional EDF+ specs)
        8 ascii : duration of a data record, in seconds
        4 ascii : number of signals (ns) in data record
        -> bytes = 256 bytes
        ns * 16 ascii : ns * label (e.g. EEG Fpz-Cz or Body temp) (mind item 9 of the additional EDF+ specs)
        ns * 80 ascii : ns * transducer type (e.g. AgAgCl electrode)
        ns * 8 ascii : ns * physical dimension (e.g. uV or degreeC)
        ns * 8 ascii : ns * physical minimum (e.g. -500 or 34)
        ns * 8 ascii : ns * physical maximum (e.g. 500 or 40)
        ns * 8 ascii : ns * digital minimum (e.g. -2048)
        ns * 8 ascii : ns * digital maximum (e.g. 2047)
        ns * 80 ascii : ns * prefiltering (e.g. HP:0.1Hz LP:75Hz)
        ns * 8 ascii : ns * nr of samples in each data record
        ns * 32 ascii : ns * reserved
        -> bytes = 256 bytes X ns = 256 x 36 = 9216
        -> total number of bytes =  256 + 9216 = 9472

    DATA RECORD
        nr of samples[1] * integer : first signal in the data record
        nr of samples[2] * integer : second signal
        ..
        ..
        nr of samples[ns] * integer : last signal
        ex) 36 * 

    
    """
    
    # General chec
    [file_name, file_ext] = os.path.splitext(fname)
    if file_ext.lower() != '.edf' and file_ext.lower() != '.rec':    
        err_message = '{} must be .edf or .rec format'.format(fname)
        message_win.append(err_message)
        print(err_message)
        sys.exit()
    else:
        try:
            with open(fname, 'rb') as fid:
                message_win.append('... opening {}'.format(fname))
                edf_info = {}
                
                # 8 ascii : version of this data format (0)
                fid.seek(8,0)  # version (unused here)
                
                # 80 ascii : local patient identification
                edf_info['patient_id'] = fid.read(80).decode('latin-1')
                
                # 80 ascii : local recording identification
                # edf_info['rec_id'] = 'Startdate xx-XXX-xxxx X X X  
                edf_info['rec_id'] = fid.read(80).decode('latin-1')

                # in NATUS the local recording identification is missing (when the data is not anonymized)
                # it starts with the startdate, starttime and number of bytes in header record concatenated
                # '09.04.2421.46.169472    EDF+C                                       -1      1   '
                # Pattern to detect the missing field
                pattern = r'^\d{2}.\d{2}.\d{4}.\d{2}.\d+'
                match = re.match(pattern, edf_info['rec_id'])
                
                # The field local recording identification is missing
                if match:
                    # The following fields are extracted from the local recording identification reading

                    # 8 ascii : startdate of recording (dd.mm.yy)
                    edf_info['startdate'] = edf_info['rec_id'][0:8]
                    
                    # 8 ascii : starttime of recording (hh.mm.ss)
                    edf_info['starttime'] = edf_info['rec_id'][8:16]
                    
                    # 8 ascii : number of bytes in header record 
                    hdr_nbytes = edf_info['rec_id'][16:24]
                    try: 
                        edf_info['hdr_nbytes'] = int(hdr_nbytes)
                    except ValueError:
                        edf_info['hdr_nbytes'] = hdr_nbytes
                        message_win.append('hdr_nbytes not an integer')
                    
                    # 44 ascii : reserved
                    edf_info['comment_44rsv'] = edf_info['rec_id'][24:68]

                    # 8 ascii : number of data records
                    # if -1 change it lower at the end
                    n_records = edf_info['rec_id'][68:76]
                    try:
                        edf_info['n_records'] = int(n_records)
                    except ValueError:
                        edf_info['n_records'] = n_records
                        message_win.append('n_records not an integer')
                    
                    # 8 ascii : duration of a data record, in seconds
                    end_of_rec =fid.read(4)
                    end_of_rec=end_of_rec.decode('latin-1')
                    edf_info['record_length_sec'] = edf_info['rec_id'][76:80]+end_of_rec
                    try : 
                        edf_info['record_length_sec'] = float(edf_info['record_length_sec'])
                    except ValueError:
                        message_win.append('record_length_sec not a float')

                    # Create a valid edf_info['rec_id'] of 80 characters
                    edf_info['rec_id'] =  "Startdate X X X X                                                               "
                else:
                    # 8 ascii : startdate of recording (dd.mm.yy)
                    edf_info['startdate'] = fid.read(8).decode('latin-1')
                    
                    # 8 ascii : starttime of recording (hh.mm.ss)
                    edf_info['starttime'] = fid.read(8).decode('latin-1')
                    
                    # 8 ascii : number of bytes in header record
                    hdr_nbytes = fid.read(8)
                    try: 
                        edf_info['hdr_nbytes'] = int(hdr_nbytes) 
                    except ValueError:
                        edf_info['hdr_nbytes'] = hdr_nbytes
                        message_win.append('hdr_nbytes not an integer')
                    
                    # 44 ascii : reserved
                    edf_info['comment_44rsv'] = fid.read(44).decode('latin-1')
                
                    # 8 ascii : number of data records
                    # if -1 change it !!!
                    n_records = fid.read(8)
                    try:
                        edf_info['n_records'] = int(n_records)
                    except ValueError:
                        edf_info['n_records'] = n_records
                        message_win.append('n_records not an integer')
                    
                    # 8 ascii : duration of a data record, in seconds
                    edf_info['record_length_sec'] = float(fid.read(8))
                
                # 4 ascii : number of signals (ns) in data record
                nchan = fid.read(4)
                try:
                    edf_info['nchan'] = int(nchan)
                except ValueError:
                    edf_info['nchan'] = nchan
                    message_win.append('nchan not an integer')
                
                header_size_before_chan = fid.tell()
                if not (header_size_before_chan==256):
                    message_win.append(f'The first part of the header is not the expected 256 bytes, it is {header_size_before_chan} bytes')

                # ns * 16 ascii : ns * label
                # e.g. EEG Fpz-Cz or Body temp
                if isinstance(edf_info['nchan'], int):
                    channels = list(range(edf_info.get('nchan')))
                    edf_info['ch_labels'] = [fid.read(16).decode('latin-1') for ch in channels]
                    
                    # ns * 80 ascii : ns * transducer type
                    # e.g. AgAgCl electrode
                    edf_info['transducer'] = [fid.read(80).decode('latin-1') for ch in channels]
                    
                    # ns * 8 ascii : ns * physical dimension
                    # e.g. uV or degreeC
                    edf_info['units'] = [fid.read(8).decode('latin-1') for ch in channels]
                
                    # ns * 8 ascii : ns * physical minimum 
                    # e.g. -500 or 34
                    edf_info['physical_min'] = np.array([float(fid.read(8))
                                            for ch in channels])
                    # e.g. 500 or 40
                    edf_info['physical_max'] = np.array([float(fid.read(8))
                                            for ch in channels])
                    # e.g. -2048
                    digital_min = np.array([float(fid.read(8)) for ch in channels])
                    digital_min = np.rint(digital_min).astype(int)
                    edf_info['digital_min'] = digital_min
                    
                    # e.g. 2047
                    digital_max = np.array([float(fid.read(8)) for ch in channels])
                    edf_info['digital_max'] = np.rint(digital_max).astype(int)
                    
                    # ns * 80 ascii : ns * prefiltering
                    # e.g. HP:0.1Hz LP:75Hz
                    edf_info['prefiltering'] = [fid.read(80).decode('latin-1') for ch in channels][:]
                
                    # number of samples per record
                    edf_info['n_samps_record'] = np.array([int(fid.read(8)) for ch in channels])
                    
                    # Last access of the edf header
                    # 32 reserved for each chan
                    comment_32rsv = []
                    for ch in channels:
                        comment_32rsv.append(fid.read(32).decode('latin-1'))
                    edf_info['comment_32rsv'] = comment_32rsv
                    
                    # The 'hdr_nbytes' is used to read the data in the original file in order to write a new version of the file.
                    # The write function will use the hdr_nbytes_real to make valid the new header of the file
                    # The hdr_nbytes is automatically updated to reflect where the data is saved in the original file  
                    edf_info['hdr_nbytes'] = fid.tell()
                                        
                    # Save the real number of bytes in the header in order to correct the edf header
                    if match:
                        edf_info['hdr_nbytes_real'] = fid.tell()+80
                    else:
                        edf_info['hdr_nbytes_real'] = fid.tell()

                    # Verify the file size written in the edf header
                    header_size_after_chan = fid.tell()-header_size_before_chan
                    if not header_size_after_chan==(256*edf_info.get('nchan')):
                        message_win.append(f'The second part of the header is not the expected {256*edf_info.get("nchan")} bytes, it is {header_size_after_chan} bytes')
                    
                    fid.seek(0, 2) # 0 offset from the end of the file
                    n_bytes = fid.tell()
                    n_data_bytes = n_bytes - edf_info.get('hdr_nbytes')
                    total_samps = n_data_bytes // 2 # why 2 !!!!
                    read_records = total_samps // np.sum(edf_info.get('n_samps_record'))
                    edf_info['n_records_real'] = read_records
                    
                    if edf_info['n_records'] == -1:
                        edf_info['n_records'] = read_records

                    if edf_info.get('n_records') != read_records:
                        err_message = 'Number of records from the header ({}) ' \
                        'does not match the file size ({})' .format(edf_info.get('n_records'), \
                            read_records)
                        message_win.append(err_message)
                    
                #fid.close()
                
            return edf_info            
            
        except OSError:
            err_message = '{} could not open/read'.format(fname)
            message_win.append(err_message)


def read_edf_data(fname, hdr_nbytes, message_win):
    """Read the data chunk from EDF+, read and return all the bytes from 
    the last byte in the edf header until EOF 
    
    Parameters
    -----------
    fname : str
        Path to the EDF or EDF+ file.
    hdr_nbytes : int
        Number of bytes in the edf header
   
    Returns
    -----------
    edf_data : bytes
        the whole chunk of data in binary format
        
    Usage : edf_data = read_edf_data(your_file.edf, 7424, message_win)    
    
    """
    try:
        fid = open(fname, 'rb')
    except OSError:
        # Eventually all the message will be report in a text file
        # especially in batch with many files
        err_message = '{} could not open/read'.format(fname)
        message_win.append(err_message)
        sys.exit()
    
    if fid.seekable():
        fid.seek(hdr_nbytes,0)
        edf_data = fid.read()
    else:
        err_message = '{} not seekable, data is null'.format(fname)
        message_win.append(err_message)   
        edf_data = 0
    return edf_data


# Internal function to create or erase the file with the filename "fname".
# Only the encoding is set. 
def _erase_file(fname, message_win):
    # Erase the file
    with open(fname, 'wb') as fid:
        try:
            # 8 ascii : version of this data format (0)
            fid.write(bytes(str(0).ljust(8),encoding='latin-1'))
            fid.close()
        except OSError:
            # Eventually all the message will be report in a text file
            # especially in batch with many files
            err_message = '{} could not open/write'.format(fname)
            message_win.append(err_message)
            sys.exit()     


def write_edf_hdr(fname, edf_info, message_win):
    """Create or erase the file with the filename "fname" and write the edf 
    header "edf_info".
    
    Parameters
    -----------
    fname : str
        Path to the EDF or EDF+ file.
    edf_info : dict 
        each field of the edf header are saved in edf_info
        
    Usage : write_edf_hdr('fname.edf', edf_info, message_win)
    """
    
    # Open the file in write mode to fix the encoding and clode it
    _erase_file(fname, message_win)
    
    with open(fname, 'ab') as fid:      
        with fid:
            
            # 80 ascii : local patient identification
            fid.write(bytes(edf_info.get('patient_id').ljust(80),encoding='latin-1'))
            
            # 80 ascii : local recording identification
            fid.write(bytes(edf_info.get('rec_id').ljust(80),encoding='latin-1'))
            
            # 8 ascii : startdate of recording (dd.mm.yy)
            fid.write(bytes(edf_info.get('startdate').ljust(8),encoding='latin-1'))
            
            # 8 ascii : starttime of recording (hh.mm.ss)
            fid.write(bytes(edf_info.get('starttime').ljust(8),encoding='latin-1'))
            
            # 8 ascii : number of bytes in header record
            fid.write(bytes(str(edf_info.get('hdr_nbytes_real')).ljust(8),encoding='latin-1'))
            #fid.write(bytes(str(edf_info.get('hdr_nbytes')).ljust(8),encoding='latin-1'))
            
            # 44 ascii : reserved
            fid.write(bytes(edf_info.get('comment_44rsv').ljust(44),encoding='latin-1'))
            
            # 8 ascii : number of data records
            # if -1 change it !!!
            fid.write(bytes(str(edf_info.get('n_records')).ljust(8),encoding='latin-1'))
            
            # 8 ascii : duration of a data record, in seconds
            fid.write(bytes(str(edf_info.get('record_length_sec')).ljust(8),encoding='latin-1'))
            
            # 4 ascii : number of signals (ns) in data record
            fid.write(bytes(str(edf_info.get('nchan')).ljust(4),encoding='latin-1'))
            
            # ns * 16 ascii : ns * label
            # e.g. EEG Fpz-Cz or Body temp
            channels = list(range(edf_info.get('nchan')))
            for ch in channels:
                fid.write(bytes(edf_info.get('ch_labels')[ch].ljust(16),encoding='latin-1'))
            
            # ns * 80 ascii : ns * transducer type
            # e.g. AgAgCl electrode
            for ch in channels:
                fid.write(bytes(edf_info.get('transducer')[ch].ljust(80),encoding='latin-1'))
            
            # ns * 8 ascii : ns * physical dimension
            # e.g. uV or degreeC
            for ch in channels:
                fid.write(bytes(edf_info.get('units')[ch].ljust(8),encoding='latin-1'))       
        
            # ns * 8 ascii : ns * physical minimum 
            # e.g. -500 or 34
            for ch in channels:
                fid.write(bytes(str(edf_info.get('physical_min')[ch]).ljust(8),encoding='latin-1'))
    
            # e.g. 500 or 40
            for ch in channels:
                fid.write(bytes(str(edf_info.get('physical_max')[ch]).ljust(8),encoding='latin-1'))
    
            # e.g. -2048
            for ch in channels:
                fid.write(bytes(str(edf_info.get('digital_min')[ch]).ljust(8),encoding='latin-1'))   
    
            # e.g. 2047
            for ch in channels:
                fid.write(bytes(str(edf_info.get('digital_max')[ch]).ljust(8),encoding='latin-1'))    
    
            # ns * 80 ascii : ns * prefiltering
            # e.g. HP:0.1Hz LP:75Hz
            for ch in channels:
                fid.write(bytes(edf_info.get('prefiltering')[ch].ljust(80),encoding='latin-1'))            
        
            # number of samples per record
            for ch in channels:
                fid.write(bytes(str(edf_info.get('n_samps_record')[ch]).ljust(8),encoding='latin-1')) 
            
            # 32 ascii x nchan: reserved
            for ch in channels:
                fid.write(bytes(edf_info.get('comment_32rsv')[ch].ljust(32),encoding='latin-1'))  
                
            fid.close()
                
            
def write_edf_data(fname, edf_info, edf_data, message_win):
    """Write the edf data chunk (already organized as data records) into the 
    edf file with the filename "fname".  The file has to exist and have a valid 
    edf header that matches the edf data chunk.  This function needs to be called
    after write_edf_hdr.
    
    Parameters
    -----------
    fname : str
        Path to the EDF or EDF+ file.
    edf_info : dict 
        each field of the edf header are saved in edf_info
    edf_data : bytes
        chunk of edf data to write into an edf file
        data needs to be packed per data records as specified in 
        https://www.edfplus.info/specs/edf.html
        
    Usage : write_edf_data('fname.edf', edf_info, edf_data, message_win)
    """    
    with open(fname, 'ab') as fid:      
        with fid:
            
            # Write the data
            fid.write(bytes(edf_data))
            
            # Verify the file size written in the edf header
            fid.seek(0, 2)
            n_bytes_eof = fid.tell()
            n_data_bytes = n_bytes_eof - edf_info.get('hdr_nbytes')
            
            # why 2 ? -> precision header = 8, and precision TS = 16 ? 
            total_samps = n_data_bytes // 2 
            
            read_records = total_samps // np.sum(edf_info.get('n_samps_record'))
            if edf_info.get('n_records') != read_records:
                err_message = 'Number of records from the header ({}) ' \
                'does not match the file size ({})' .format(edf_info.get('n_records'), \
                    read_records)
                message_win.append(err_message)     
                
            fid.close()


def write_edf_file(fname, edf_info, edf_data, message_win):
    """Write the edf header and the edf data chunk in an EDF+ file.
    
    Parameters
    -----------
    fname : str
        Path to the EDF or EDF+ file.
    edf_info : dict
        dict of each edf header field
    edf_data : bytes
        chunk of edf data to write into an edf file
        data needs to be packed per data records as specified in 
        https://www.edfplus.info/specs/edf.html
        
    Usage : write_edf_file(your_file.edf, edf_info, edf_data ,message_win)    
    
    """    
    # open the file in dump mode, write the edf header and close it
    write_edf_hdr(fname, edf_info, message_win)
    # open the file in dump mode, write the edf data and close it 
    write_edf_data(fname, edf_info, edf_data, message_win)
    

def _modify_patient_id(val_to_mod, message_win):
    """Modify the local patient identification from the edf header.
        
        Parameters
        -----------
        val_to_mod : str or int or float or array
            The new field value.
       
        Returns
        -----------
        True if the field can be modified False otherwise 
        
    """
    message_win.append("You want to modify patient_id field to :'{}'\n".format(val_to_mod))
    # Print the specification info from 
    #   https://www.edfplus.info/specs/edfplus.html#additionalspecs
    message_win.append("-------------------------------------------------------------------\n"\
          " Information from edf specification\n"
          "-------------------------------------------------------------------\n"\
          "The 'local patient identification' field must start with the "\
          "subfields\n(subfields do not contain, but are separated by, spaces):\n"\
          "- the code by which the patient is known in the hospital "\
              "administration. ex. MCH-0234567\n"\
          "- sex (English, so F or M).\n"\
          "- birthdate in dd-MMM-yyyy format using the English 3-character "\
              "abbreviations of the month in capitals. 02-AUG-1951 is OK, "\
                  "while 2-AUG-1951 is not.\n"\
          "- the patients name.\n\n"\
          " notes : \n -Any space inside the hospital code or patient name "\
              "must be replaced by a different character, for instance an _."\
          " ex: MCH-0234567 F 02-MAY-1951 Haagse_Harry\n"\
          " -Subfields whose contents are unknown, not applicable "\
              "or must be made anonymous are replaced by a single character 'X'."\
               " So, if everything is unknown then the 'local patient "\
                   "identification' field would start with: 'X X X X'.\n\n"\
          " MAKE SURE YOU RESPECT THE EDF SPECT TO USE EDFbrowser\n"\
          "-------------------------------------------------------------------\n")  
    # Any edits are accepted for the patient id, but a warning is printed if it
    # does not respect the edf+ spect
    field_mod = False        
    # Look for the right separator and the right number of fields
    if val_to_mod.count(' ')>=3:
        patient_id_val = val_to_mod.split(' ')
        # make sure the second field is the sex
        sex = patient_id_val[1]
        if sex == 'F' or sex == 'M' or sex == 'X':
            # make sure the third field is the birthdate with some verif
            bd_val = patient_id_val[2].split('-')
            # make sure it is 3 fields
            if len(bd_val)==3: 
                # make sure the day is numbers
                if all(bd_val[0])>0 and all(bd_val[0])<9:
                    # make sure the format is dd MMM YYYY
                    if len(bd_val[0])==2 and len(bd_val[1])==3 and len(bd_val[2])==4:
                        # make sure the MMM is capital
                        if bd_val[1].isupper():
                            # Make sure YYYY is numbers
                            if all(bd_val[2])>0 and all(bd_val[2])<9:
                                field_mod = True     
            elif len(bd_val)==1: 
                if bd_val[0]=='X':
                    field_mod = True             
                    
    return field_mod

def _modify_rec_id(val_to_mod, message_win):
    """Modify the local recording identification from the edf header.
        
        Parameters
        ----------- i
        val_to_mod : str or int or float or array
            The new field value.
       
        Returns
        -----------
        True if the field can be modified False otherwise 
        
    """
    message_win.append("You want to modify rec_id field to :'{}'\n".format(val_to_mod))
    # Print the specification info from 
    #   https://www.edfplus.info/specs/edfplus.html#additionalspecs
    message_win.append("-------------------------------------------------------------------\n"\
          " Information from edf specification\n"
          "-------------------------------------------------------------------\n"\
          "The 'local recording identification' field must start with the subfields\n"\
          "(subfields do not contain, but are separated by, spaces):\n"\
          "- The text 'Startdate'.\n"\
          "- The startdate itself in dd-MMM-yyyy format using the English "\
              "3-character abbreviations of the month in capitals.\n"\
          "- The hospital administration code of the investigation, "\
              "i.e. EEG number or PSG number.\n"\
          "- A code specifying the responsible investigator or technician.\n"\
          "- A code specifying the used equipment.\n"
          " notes : \n -Any space inside any of these codes "\
              "must be replaced by a different character, for instance an _."\
          " ex: Startdate 02-MAR-2002 PSG-1234/2002 NN Telemetry03\n"\
          " -Subfields whose contents are unknown, not applicable "\
              "or must be made anonymous are replaced by a single character 'X'."\
               " So, if everything is unknown then the 'local patient "\
                   "identification' field would start with: 'Startdate X X X X'.\n\n"\
          " MAKE SURE YOU RESPECT THE EDF SPECT TO USE EDFbrowser\n"\
          "-------------------------------------------------------------------\n")  
    field_mod = False
    # Look for the right separator and the right number of fields
    if val_to_mod.count(' ')>=4:
        rec_id_val = val_to_mod.split(' ')
        # make sure the first field is the Startdate label
        if rec_id_val[0] == 'Startdate':
            # make sure the second field is the startdate itself with some verif
            startdate_val = rec_id_val[1].split('-')
            # make sure it is 3 fields
            if len(startdate_val)==3: 
                # make sure the day is numbers
                if all(startdate_val[0])>0 and all(startdate_val[0])<9:
                    # make sure the format is dd MMM YYYY
                    if len(startdate_val[0])==2 and len(startdate_val[1])==3 \
                        and len(startdate_val[2])==4:
                        # make sure the MMM is capital
                        if startdate_val[1].isupper():
                            # Make sure YYYY is numbers
                            if all(startdate_val[2])>0 and all(startdate_val[2])<9:
                                field_mod = True     
            elif len(startdate_val)==1: 
                if startdate_val[0]=='X':
                    field_mod = True             
                    
    return field_mod


def _modify_startdate(val_to_mod, message_win):
    """Modify the startdate or the starttime from the edf header.
        
        Parameters
        -----------
        val_to_mod : str or int 
            The new field value.
       
        Returns
        -----------
        True if the field can be modified False otherwise 
        
    """
    message_win.append("You want to modify startdate or starttime field to :'{}'\n".format(val_to_mod))
    # Print the specification info from 
    #   https://www.edfplus.info/specs/edfplus.html#additionalspecs
    message_win.append("-------------------------------------------------------------------\n"\
          " Information from edf specification\n"
          "-------------------------------------------------------------------\n"\
          "The 'startdate' and 'starttime' fields in the header should "\
              "contain only characters 0-9, and the period (.) as a separator,"\
              "for example '02.08.51'. In the 'startdate', use 1985 "\
              "as a clipping date in order to avoid the Y2K problem. "\
              "So, the years 1985-1999 must be represented by yy=85-99 and "\
              "the years 2000-2084 by yy=00-84. After 2084, yy must be 'yy' "\
              "and only item 4 of this paragraph defines the date.\n\n"\
          " MAKE SURE YOU RESPECT THE EDF SPECT TO USE EDFbrowser\n"\
          "-------------------------------------------------------------------\n")  
    field_mod = False
    # Look for the right separator
    if val_to_mod.count('.')==2:
        date_time_val = val_to_mod.split('.')
        # make sure there are only numbers
        if all(date_time_val)>0 and all(date_time_val)<9:
            field_mod = True            
                    
    return field_mod


def _modify_text(val_to_mod, field_to_mod, nchan, ch_labels, message_win):
    """Modify the text label for each channel from the edf header.
        
        Parameters i
        -----------
        val_to_mod : list of string
            Values to update, the number of items in the list is the number of channels
        field_to_mod : string
            The field label to modify.
        nchan : int
            Number of channels.
        ch_labels : list of strings
            The label of each channels
       
        Returns
        -----------
        True if the field can be modified False otherwise 
        
    """
    LABELS_ASCII = 16
    TRANSDUCER_ASCII = 80
    PHYDIM_ASCII = 8
    PREFILTER_ASCII = 80
    
    field_mod = False
    if field_to_mod == "ch_labels":
        max_ascii_char = LABELS_ASCII
    elif field_to_mod == "transducer":
        max_ascii_char = TRANSDUCER_ASCII
    elif field_to_mod == "units":
        max_ascii_char = PHYDIM_ASCII
    elif field_to_mod == "prefiltering":
        max_ascii_char = PREFILTER_ASCII
    else:
        message_win.append("ERROR : {} is an unexpected field".format(field_to_mod))
    
    message_win.append("You want to modify the {} to:".format(field_to_mod))
    for i, itext in enumerate(val_to_mod):
        message_win.append("{} ({})\t{}".format(i, ch_labels[i], val_to_mod[i]))
        
    # Extract the Annotations channel if any
    if ch_labels.count('EDF Annotations'.ljust(LABELS_ASCII))>0:
        annot_ch_i = ch_labels.index('EDF Annotations'.ljust(LABELS_ASCII))
    else:
        annot_ch_i = -1; 
        
    # verify the nchan
    if len(val_to_mod) == nchan:
        # Print the specification info from 
        if field_to_mod == "ch_labels":
            #   https://www.edfplus.info/specs/edfplus.html#additionalspecs
            message_win.append("-------------------------------------------------------------------\n"\
                  " Information from edf specification\n"\
                  "-------------------------------------------------------------------\n"\
                  "The {} field offers {} ASCII characters. The standard structure "\
                      "consists of three components, from left to right:\n"\
                      "(Optional)\n"\
                      "-Type of signal (for example EEG).\n"\
                      "-A space.\n"\
                      "-Specification of the sensor (for example Fpz-Cz).\n"\
                      "Ex: EEG Fpz-Cz\n"\
                  "*Even if no annotations are to be kept, an EDF+ file must "\
                  "contain at least one 'EDF Annotations' signal in order to "\
                  "specify the starttime of each datarecord\n"\
                  " MAKE SURE YOU RESPECT THE MAX OF {} ASCII CHAR\n"\
                  " see : https://www.edfplus.info/specs/edftexts.html#signals\n"\
                  "-------------------------------------------------------------------\n"\
                      .format(field_to_mod, max_ascii_char, max_ascii_char))
        elif field_to_mod == "transducer":
            message_win.append("-------------------------------------------------------------------\n"\
                  " Information from edf specification\n"\
                  "-------------------------------------------------------------------\n"\
                  "The {} field offers {} ASCII characters.  It should "\
                  "specify the applied sensor, such as 'AgAgCl electrode' or 'thermistor'.\n\n"\
                  "*{} of the 'EDF Annotations' channel must be filled with spaces\n"\
                  " MAKE SURE YOU RESPECT THE MAX OF {} ASCII CHAR\n"\
                  "-------------------------------------------------------------------\n"\
                      .format(field_to_mod, max_ascii_char, field_to_mod, max_ascii_char))       
        elif field_to_mod == "units":
            message_win.append("-------------------------------------------------------------------\n"\
                  " Information from edf specification\n"\
                  "-------------------------------------------------------------------\n"\
                  "The {} field offers {} ASCII characters. ex: uV for an EEG channel.\n"\
                  "see https://www.edfplus.info/specs/edftexts.html#label_physidim"\
                  "*{} of the 'EDF Annotations' channel must be filled with spaces\n"\
                  " MAKE SURE YOU RESPECT THE MAX OF {} ASCII CHAR\n"\
                  "-------------------------------------------------------------------\n"\
                      .format(field_to_mod, max_ascii_char, field_to_mod, max_ascii_char))               
        elif field_to_mod == "prefiltering":
            message_win.append("-------------------------------------------------------------------\n"\
                  " Information from edf specification\n"\
                  "-------------------------------------------------------------------\n"\
                  "The {} field offers {} ASCII characters. Specify filter as follow:\n"\
                  "-High pass : HP:xHz\n-Low pass : LP:XHz\n-Notch : NXHz\n"\
                  " Ex: HP:0.1Hz LP:75Hz N:60Hz\n"\
                  "see https://www.edfplus.info/specs/edfplus.html#additionalspecs\n"\
                  "*{} of the 'EDF Annotations' channel must be filled with spaces\n"\
                  " MAKE SURE YOU RESPECT THE MAX OF {} ASCII CHAR\n"\
                  "-------------------------------------------------------------------\n"\
                      .format(field_to_mod, max_ascii_char, field_to_mod, max_ascii_char))           
        
        field_mod_ch = []
        for itext in val_to_mod:
            # look if the text respects the max ascii char
            if len(itext) <= max_ascii_char:
                field_mod_ch.append(True)
            else:
                field_mod_ch.append(False)
                err_message = "ERROR : the {} value={} is {} long and the max is {} ASCII"\
                      .format(field_to_mod, itext, len(itext), max_ascii_char)
                message_win.append(err_message)
        # Special case for the EDF Annotations channel
        # Make sure that the EDF Annotations channel is filled with spaces
        if field_to_mod != 'ch_labels' and annot_ch_i>-1:
            if len(val_to_mod[annot_ch_i])>0:
                if val_to_mod[annot_ch_i].isspace()==False:
                    field_mod_ch[annot_ch_i] = False
                    err_message = 'ERROR : {} is not filled with spaces'\
                        ' for the "EDF Annotations" channel, then not '\
                            'EDF+ compatible'.format(field_to_mod)
                    message_win.append(err_message)                
                else:
                    field_mod_ch[annot_ch_i] = True
            else:
                field_mod_ch[annot_ch_i] = False
                err_message = 'ERROR : {} is not filled with spaces'\
                    ' for the "EDF Annotations" channel, then not '\
                        'EDF+ compatible'.format(field_to_mod)
                message_win.append(err_message)                            
      
        if all(field_mod_ch)==True:
            field_mod=True
    else:
        err_message = 'ERROR : {} {} provided and the edf file has {} channels'\
            .format(len(val_to_mod), field_to_mod, nchan)
        message_win.append(err_message)
        err_message = '{} is not modified'.format(field_to_mod)
        message_win.append(err_message)
    return field_mod


def _modify_physical_val(val_to_mod, field_to_mod, nchan, ch_labels, message_win):
    """Modify the physical min and max values for each channel from the edf header.
        
        Parameters i
        -----------
        val_to_mod : list of float
            Values to update, the number of items in the list is the number of channels
        field_to_mod : string
            The field label to modify.
        nchan : int
            Number of channels.
        ch_labels : list of strings
            The label of each channels
       
        Returns
        -----------
        True if the field can be modified False otherwise 
        
    """
    PHYVAL_ASCII = 8
    
    message_win.append("You want to modify the {} to:".format(field_to_mod))
    for i, itext in enumerate(val_to_mod):
        message_win.append("{} ({})\t{}".format(i, ch_labels[i], val_to_mod[i]))
        
    # verify the nchan
    if len(val_to_mod) == nchan:
        # Print the specification info from 
        if field_to_mod == "physical_min" or field_to_mod == "physical_max":
            #   https://www.edfplus.info/specs/edfplus.html#additionalspecs
            message_win.append("-------------------------------------------------------------------\n"\
                  " Information from edf specification\n"\
                  "-------------------------------------------------------------------\n"\
                  "The {} field offers {} ASCII characters. Ex: -1000\n"\
                  "physical minimum and physical maximum must be different\n"\
                  " MAKE SURE YOU RESPECT THE MAX OF {} ASCII CHAR\n"\
                  " see : https://www.edfplus.info/specs/edf.html\n"\
                  "-------------------------------------------------------------------\n"\
                      .format(field_to_mod, PHYVAL_ASCII, PHYVAL_ASCII))           
        
        field_mod_ch = []
        for itext in val_to_mod:
            # look if the text respects the max ascii char
            if len(str(itext)) <= PHYVAL_ASCII:
                field_mod_ch.append(True)
            else:
                field_mod_ch.append(False)
                err_message = "ERROR : the {} value={} is {} long and the max is {} ASCII"\
                      .format(field_to_mod, itext, len(itext), PHYVAL_ASCII)
                message_win.append(err_message)                         
              
        if all(field_mod_ch)==True:
            field_mod=True
    else:
        err_message = 'ERROR : {} {} provided and the edf file has {} channels'\
            .format(len(val_to_mod), field_to_mod, nchan)
        message_win.append(err_message)
        err_message = '{} is not modified'.format(field_to_mod)
        message_win.append(err_message)
    return field_mod

def _modify_digital_val(val_to_mod, field_to_mod, nchan, ch_labels, message_win):
    """Modify the digital min and max values for each channel from the edf header.
        
        Parameters i
        -----------
        val_to_mod : list of integer
            Values to update, the number of items in the list is the number of channels
        field_to_mod : string
            The field label to modify.
        nchan : int
            Number of channels.
        ch_labels : list of strings
            The label of each channels
       
        Returns
        -----------
        True if the field can be modified False otherwise 
        
    """
    DIGVAL_ASCII = 8
    
    field_mod = False
    
    message_win.append("You want to modify the {} to:".format(field_to_mod))
    for i, itext in enumerate(val_to_mod):
        message_win.append("{} ({})\t{}".format(i, ch_labels[i], val_to_mod[i]))
        
    # verify the nchan
    if len(val_to_mod) == nchan:
        # Print the specification info from 
        if field_to_mod == "digital_min" or field_to_mod == "digital_max":
            #   https://www.edfplus.info/specs/edfplus.html#additionalspecs
            message_win.append("-------------------------------------------------------------------\n"\
                  " Information from edf specification\n"\
                  "-------------------------------------------------------------------\n"\
                  "The {} field offers {} ASCII characters. Ex: -2048\n"\
                  "digital minimum and physical maximum must be different\n"\
                  "digital min and max must be integer\n"\
                  " MAKE SURE YOU RESPECT THE MAX OF {} ASCII CHAR\n"\
                  " see : https://www.edfplus.info/specs/edf.html\n"\
                  "-------------------------------------------------------------------\n"\
                      .format(field_to_mod, DIGVAL_ASCII, DIGVAL_ASCII))           
                
        field_mod_ch = []
        for ichan, idigval in enumerate(val_to_mod):
            # if digital value is a float -> convert it to int
            if isinstance(idigval,float):     
                if idigval != int(idigval):
                    err_message = "ERROR : ({}) the {} value={} will be converted to {}"\
                          .format(ch_labels[ichan], field_to_mod, idigval, int(idigval))
                    message_win.append(err_message)
                idigval = int(idigval)
            
            # if digital value is an integer
            if isinstance(idigval,int):
                # look if the text respects the max ascii char
                if len(str(idigval)) <= DIGVAL_ASCII:
                    field_mod_ch.append(True)
                else:
                    field_mod_ch.append(False)
                    err_message = "ERROR : ({}) the {} value={} is {} long and the max is {} ASCII"\
                          .format(ch_labels[ichan], field_to_mod, idigval, len(itext), DIGVAL_ASCII)
                    message_win.append(err_message)
            else:
                field_mod_ch.append(False)
                err_message = "ERROR : ({}) the {} value={} is not an integer or a float"\
                      .format(ch_labels[ichan], field_to_mod, idigval)
                message_win.append(err_message)                                   
              
        if all(field_mod_ch)==True:
            field_mod=True
    else:
        err_message = 'ERROR : {} {} provided and the edf file has {} channels'\
            .format(len(val_to_mod), field_to_mod, nchan)
        message_win.append(err_message)
        err_message = '{} is not modified'.format(field_to_mod)
        message_win.append(err_message)
    return field_mod


def modify_edf_header(edf_info, field_to_mod, val_to_mod, message_win):
    """Modify the edf header of an EDF+
    
    Parameters
    -----------
    edf_info : dict
        edf info dictionary
    field_to_mod : string
        field name to modify in the edf header
    val_to_mod : int, string or float 
        new value of the modified field
        
    Returns
    -----------
    modify_hdr : Bool, True is the header is modified False otherwise
        
    Usage : modify_hdr = modify_edf_header('your_file.edf', 'rec_id', \
                                'CEAMS: Startdate 01-Jan-2000 x x x x ')    
    
    """    
    field_mod = False
    
    #-------------------------------------------------------------------------
    # EDF header 
    #-------------------------------------------------------------------------
    # Modify the field patient_id
    if field_to_mod == "patient_id" :
        # Special case to update to a vlaid EDF+ value
        if val_to_mod == "-1":
            edf_info[field_to_mod] = "X X X X"
            message = '{} is modified to {}'.format(field_to_mod, \
                                                    edf_info.get(field_to_mod)) 
            message_win.append(message)
            field_mod = True
        # Real modification
        elif _modify_patient_id(val_to_mod, message_win):
            edf_info[field_to_mod] = val_to_mod
            field_mod = True
        # No modification
        else:
            err_message = 'ERROR : {} does not respect EDF+ spect\n'\
                'ex: MCH-0234567 F 02-MAY-1951 Haagse_Harry\n'\
                'ex: X X X X\n'.format(val_to_mod)
            message_win.append(err_message)  
            err_message = 'Modify {} to -1 to update to a valid EDF+ value'\
                .format(field_to_mod)
            message_win.append(err_message) 
            
    # Modify the rec_id field
    elif field_to_mod == "rec_id":
        # Special case to update to a vlaid EDF+ value
        if val_to_mod == "-1":
            edf_info[field_to_mod] = "Startdate X X X X"
            message = '{} is modified to {}'.format(field_to_mod, \
                                                    edf_info.get(field_to_mod)) 
            message_win.append(message)
            field_mod = True       
        # Real modification
        elif _modify_rec_id(val_to_mod, message_win):
            edf_info[field_to_mod] = val_to_mod
            field_mod = True
        # No modification
        else:
            err_message = 'ERROR : {} does not respect EDF+ spect\n'\
                'ex: Startdate 02-MAR-2002 PSG-1234/2002 NN Telemetry03\n'\
                'ex: Startdate X X X X\n'.format(val_to_mod)
            message_win.append(err_message)                   
        
    # Modify the field startdate or starttime
    elif field_to_mod == "starttime" or field_to_mod == "startdate":
        # Special case to update to a vlaid EDF+ value
        if val_to_mod == "-1":
            if field_to_mod == "startdate":
                edf_info[field_to_mod] = "01.01.00"
                message = '{} is modified to {}'.format(field_to_mod, \
                                                    edf_info.get(field_to_mod)) 
                message_win.append(message)
                field_mod = True
            elif field_to_mod == "starttime":
                edf_info[field_to_mod] = "00.00.00"
                message = '{} is modified to {}'.format(field_to_mod, \
                                                    edf_info.get(field_to_mod)) 
                message_win.append(message)
                message = 'WARNING : {} should not be modified to a default value'\
                    .format(field_to_mod)
                message_win.append(message)                
                field_mod = True
        # Real modification
        elif _modify_startdate(val_to_mod, message_win):
            edf_info[field_to_mod] = val_to_mod
            field_mod = True
        # No modification
        else:
            if field_to_mod == "startdate":
                err_message = 'ERROR : {} does not respect EDF+ spect (dd.mm.yy)'\
                    .format(val_to_mod)
                message_win.append(err_message)                   
            if field_to_mod == "starttime":
                err_message = 'ERROR : {} does not respect EDF+ spect (hh.mm.ss)'\
                    .format(val_to_mod)
                message_win.append(err_message)  
    
    # Modify the number of bytes in header
    elif field_to_mod == "hdr_nbytes":
        message_win.append("You want to modify {} to {} and the real number of bytes "\
              "in the header is {}".format(field_to_mod, val_to_mod, \
                                           edf_info.get("hdr_nbytes_real")))
        message_win.append("{} will be modified to {}".format(field_to_mod, \
                                           edf_info.get("hdr_nbytes_real")))
        edf_info[field_to_mod] = edf_info.get("hdr_nbytes_real")
        field_mod = True

    # Modify the 44 ascii reserved
    elif field_to_mod == "comment_44rsv":
        CMT_NCHARS = 44
        if val_to_mod.find("EDF")==-1:
            err_message = 'ERROR : "{}" does not respect EDF+ spect, has to \
                start with EDF+C (for continuous) or EDF+D (for discontinuous)\
                    ex: EDF+C\nex: EDF+D'.format(val_to_mod)
            message_win.append(err_message)
        if len(val_to_mod) <= CMT_NCHARS:
            # Any modification to comment_44rsv is acceptable
            edf_info[field_to_mod] = val_to_mod
            field_mod = True
        else:
            edf_info[field_to_mod] = val_to_mod[0:CMT_NCHARS]
            err_message = 'ERROR : "{}" is troncated to {} char'.\
                format(val_to_mod,CMT_NCHARS)
            message_win.append(err_message)
            field_mod = True
            
    # Modify the number of data records
    elif field_to_mod == "n_records":
        message_win.append("WARNING : You want to modify {} to {} and the real number of data records "\
              "is {}".format(field_to_mod, val_to_mod, edf_info.get("n_records_real")))
        message_win.append("WARNING : {} will be modified to {}".format(field_to_mod, \
                                           edf_info.get("n_records_real")))
        edf_info[field_to_mod] = edf_info.get("n_records_real")  
        field_mod = True
        
    # Modify the duration of a data record, in seconds
    elif field_to_mod == "record_length_sec":
        err_message = "ERROR : You can not change for now the {}, use the pyedflib to modify the edf data"\
              .format(field_to_mod)
        message_win.append(err_message)
    
    # Modify the number of signals (ns) in data record
    elif field_to_mod == "nchan":
        err_message = "ERROR : You can not change for now the {}, use the pyedflib to modify the edf data"\
              .format(field_to_mod)
        message_win.append(err_message)
    
    #-------------------------------------------------------------------------
    # channel information 
    #-------------------------------------------------------------------------    
    # Modify the channel label, transducer, physical dim or prefiltering
    elif field_to_mod == "ch_labels" or field_to_mod == "transducer" or\
        field_to_mod == "units" or field_to_mod == "prefiltering":
        # Verify the occurrence of the EDF Annotations channel
        if edf_info.get('ch_labels').count('EDF Annotations'.ljust(16))==0:
            warn_message = "WARNING : no 'EDF Annotations' channel, then no EDF+ compatible"
            message_win.append(warn_message)
            
        # Update the default (empty) value
        if (field_to_mod == "transducer" or field_to_mod == "units" or \
            field_to_mod == "prefiltering") and val_to_mod == "-1":
            field_val = []
            for ichan in range(edf_info.get('nchan')):
                field_val.append('')
            edf_info[field_to_mod] = field_val
            field_mod = True    
            
        # modify the field
        elif _modify_text(val_to_mod, field_to_mod, edf_info.get('nchan'), \
                          edf_info.get('ch_labels'), message_win):
            edf_info[field_to_mod] = val_to_mod
            field_mod = True
    
    # Modify the physical_min or physical_max
    elif field_to_mod == "physical_min" or field_to_mod == "physical_max" :
        
        # Make sure it is the right type
        if isinstance(val_to_mod,np.ndarray):
            # Make sure physical min and max are different
            if field_to_mod == "physical_min" :
                if any(np.equal(np.array(val_to_mod), np.array(edf_info.get('physical_max')))):
                    same_i = (np.array(val_to_mod) == np.array(edf_info.get('physical_max')))
                    ichan_same = [i for i, x in enumerate(same_i) if x]
                    for i in ichan_same:
                        err_message = 'ERROR : ({}) the physical min and max are the same ({})'\
                            .format(edf_info.get('ch_labels')[i], val_to_mod[i])
                        message_win.append(err_message)
                        field_mod = False
            
                elif _modify_physical_val(val_to_mod, field_to_mod, edf_info.get('nchan'),\
                                    edf_info.get('ch_labels'), message_win):
                    edf_info[field_to_mod] = val_to_mod
                    field_mod = True
            if field_to_mod == "physical_max" :
                if any(np.array(val_to_mod) == np.array(edf_info.get('physical_min'))):
                    # True or False array
                    same_i = (np.array(val_to_mod) == np.array(edf_info.get('physical_min')))
                    # Index of Trues (same min and max value)
                    ichan_same = [i for i, x in enumerate(same_i) if x]
                    for i in ichan_same:
                        err_message = 'ERROR : ({}) the physical min and max are the same ({})'\
                            .format(edf_info.get('ch_labels')[i], val_to_mod[i])
                        message_win.append(err_message)
                        field_mod = False
            
                elif _modify_physical_val(val_to_mod, field_to_mod, edf_info.get('nchan'),\
                                    edf_info.get('ch_labels'), message_win):
                    edf_info[field_to_mod] = val_to_mod
                    field_mod = True
        else:
            err_message = 'ERROR : Type of {} is {} and an np.ndarray is needed'\
                .format(type(val_to_mod), field_to_mod)
            message_win.append(err_message)
            field_mod = False            

    # Modify the digital min or max
    elif field_to_mod == "digital_min" or field_to_mod == "digital_max" :
        
        # Make sure physical min and max are different
        if field_to_mod == "digital_min" :
            if any(np.array(val_to_mod) == np.array(edf_info.get('digital_max'))):
                same_i = (np.array(val_to_mod) == np.array(edf_info.get('digital_max')))
                ichan_same = [i for i, x in enumerate(same_i) if x]
                for i in ichan_same:
                    err_message = 'ERROR : ({}) the digital min and max are the same ({})'\
                        .format(edf_info.get('ch_labels')[i], val_to_mod[i])
                    message_win.append(err_message)
                    field_mod = False
        
            elif _modify_digital_val(val_to_mod, field_to_mod, edf_info.get('nchan'),\
                                edf_info.get('ch_labels'), message_win):
                edf_info[field_to_mod] = val_to_mod
                field_mod = True
        elif field_to_mod == "digital_max" :
            if any(np.array(val_to_mod) == np.array(edf_info.get('digital_min'))):
                # True or False array
                same_i = (np.array(val_to_mod) == np.array(edf_info.get('digital_min')))
                # Index of Trues (same min and max value)
                ichan_same = [i for i, x in enumerate(same_i) if x]
                for i in ichan_same:
                    err_message = 'ERROR : ({}) the digital min and max are the same ({})'\
                        .format(edf_info.get('ch_labels')[i], val_to_mod[i])
                    message_win.append(err_message)
                    field_mod = False
        
            elif _modify_digital_val(val_to_mod, field_to_mod, edf_info.get('nchan'),\
                                edf_info.get('ch_labels'), message_win):
                edf_info[field_to_mod] = val_to_mod
                field_mod = True
                
    # You cannot modify the number of samples in each data record for each channel
    elif field_to_mod == "n_samps_record":
        err_message = "ERROR : You can not change for now the {}, "\
            "use the pyedflib to modify the edf data".format(field_to_mod)
        message_win.append(err_message)
            
    # Return the modified edf_info otherwise False
    return field_mod
    
    
def extract_edf_data(fname, edf_info, message_win):    
    """Read the data from EDF+ and convert it to a list of signals (one per channel)
    in digital value (int).  The file must have been already read for the info header.
    
    Parameters
    -----------
    fname : str
        Path to the EDF or EDF+ file.
    edf_info : dict
        edf info dictionary of the filename 'fname'
   
    Returns
    -----------
    edf_data : bytes
        the whole chunk of data in binary format
        
    Usage : edf_data = extract_edf_data(your_file.edf, edf_info, message_win)    
    
    """    
    # https://numpy.org/doc/stable/reference/generated/numpy.fromfile.html
    # type should be based on the digital max- digital min
    data_chunk_int = np.fromfile(fname, dtype='int16', offset=edf_info.get('hdr_nbytes'))
    # Total number of samples in a data record
    tot_smp_record = np.sum(edf_info.get('n_samps_record'))
    # Total number of data records
    records_count = edf_info.get('n_records')
    # To compute the offset of each channel in the datarecord
    cum_samps_rec_count = np.cumsum(edf_info.get('n_samps_record'))
    cum_samps_rec_count = np.concatenate((np.zeros(1),cum_samps_rec_count), axis=0)
    cum_samps_rec_count = cum_samps_rec_count.astype(int)
    if tot_smp_record*records_count == len(data_chunk_int):
        data_per_record = data_chunk_int.reshape((records_count,tot_smp_record))
        chan_data_lst = []
        for chan_index in range(edf_info.get('nchan')):
            cur_samps_rec_count = edf_info.get('n_samps_record')[chan_index]
            # Preallocation
            cur_chan_data = np.zeros(records_count*cur_samps_rec_count)
            # Extract the data record for the current channel
            cur_chan_data = data_per_record[0:,cum_samps_rec_count[chan_index]:\
                        cum_samps_rec_count[chan_index] + cur_samps_rec_count]
            # Flat to have all the data record concatenated
            cur_chan_data = cur_chan_data.flatten()
            chan_data_lst.append(cur_chan_data)
    else:
        message_win.append('ERROR : file dimension does not respect the edf header')
    

def main():

    """ modify the header :
        Here the general usage of modify_edf_header function:  
            edf_info_mod = modify_edf_header(edf_info, field_name, field_val) 
        Here some examples of field_name with field_val.
            Some raise an error to validate the function.
            If available, -1 value updates the field to a default EDF+ compatible value.
        
        ## patient_id (all valid call, -1 update the field to "X X X X")
        field_name = 'patient_id'
        field_val = 'CEAMS X X X Startdate 01-Jan-2000'
        field_val = 'X X X X'  
        field_val = -1
        
        ## rec_id
        field_name = 'rec_id'
        # Valid call (-1 update the field to 'Startdate X X X X')
            field_val = 'Startdate 02-MAR-2002 PSG-1234/2002 NN Telemetry03'
            field_val = 'Startdate X X CEAMS_edfLib X'
            field_val = 'Startdate X X X X'
            field_val = -1
        # False call
            field_val = '02-MAR-2002 PSG-1234/2002 NN Telemetry03'   
        
        ## startdate
        field_name = 'startdate'
        # valid call (-1 updates to '01.01.00')
        field_val = '01.01.00'
        field_val = -1
        # False call, the separator has to be '.'
        field_val = '01:01:00'

        ## starttime (all valid call, -1 update the field to "00.00.00")
        # watch out the starttime can be useful, default value must be used carefully
        field_name = 'starttime'
        field_val = '01.01.00'
        field_val = '-1
        
        ## hdr_nbytes: should not be modified, but can be fixed if corrupted
        # -1 updates the field to the real number of bytes in the header
        field_name = 'hdr_nbytes'
        field_val = '-1        
        
        ## n_records: should not be modified, but can be fixed if corrupted
        # -1 updates the field to the real number of data records in the file
        field_name = 'n_records'
        field_val = '-1       
        
        ## unmodifiable fields: all false calls
        field_name = 'record_length_sec'
        field_name = 'nchan'
        
        ## labels for 27 signal channels and 1 annotation channel
        
        field_name = 'ch_labels'
        # valid call
        field_val = ['EEG Fp1-CLE', 'EEG Fp2-CLE', 'EEG F3-CLE', 'EEG F4-CLE',\
                        'EEG F7-CLE', 'EEG F8-CLE', 'EEG C3-CLE', 'EEG C4-CLE',\
                        'EEG P3-CLE', 'EEG P4-CLE', 'EEG O1-CLE', 'EEG O2-CLE',\
                        'EEG T3-CLE', 'EEG T4-CLE', 'EEG T5-CLE', 'EEG T6-CLE',\
                        'EEG Fpz-CLE', 'EEG Cz-CLE', 'EEG Pz-CLE', 'EOG Upper Vertic',\
                        'EOG Lower Vertic', 'EOG Left Horiz', 'EOG Right Horiz',\
                        'EMG Chin', 'ECG ECGI', 'Resp Nasal', 'EEG A2-CLE',\
                        'EDF Annotations ']
        # false call, a channel is missing
        field_val = ['EEG Fp2-CLE', 'EEG F3-CLE', 'EEG F4-CLE',\
                          'EEG F7-CLE', 'EEG F8-CLE', 'EEG C3-CLE', 'EEG C4-CLE',\
                          'EEG P3-CLE', 'EEG P4-CLE', 'EEG O1-CLE', 'EEG O2-CLE',\
                          'EEG T3-CLE', 'EEG T4-CLE', 'EEG T5-CLE', 'EEG T6-CLE',\
                          'EEG Fpz-CLE', 'EEG Cz-CLE', 'EEG Pz-CLE', 'EOG Upper Vertic',\
                          'EOG Lower Vertic', 'EOG Left Horiz', 'EOG Right Horiz',\
                          'EMG Chin', 'ECG ECGI', 'Resp Nasal', 'EEG A2-CLE',\
                          'EDF Annotations ']
        # false call, a channel label is too long (16 ASCII max)
        field_val = ['Fp1-CLE', 'Fp2-CLE', 'F3-CLE', 'F4-CLE',\
                          'EEG F7-CLExxxxxxx', 'EEG F8-CLE', 'EEG C3-CLE', 'EEG C4-CLE',\
                          'EEG P3-CLE', 'EEG P4-CLE', 'EEG O1-CLE', 'EEG O2-CLE',\
                          'EEG T3-CLE', 'EEG T4-CLE', 'EEG T5-CLE', 'EEG T6-CLE',\
                          'EEG Fpz-CLE', 'EEG Cz-CLE', 'EEG Pz-CLE', 'EOG Upper Vertic',\
                          'EOG Lower Vertic', 'EOG Left Horiz', 'EOG Right Horiz',\
                          'EMG Chin', 'ECG ECGI', 'Resp Nasal', 'EEG A2-CLE',\
                          'EDF Annotations ']
        
        ## transducer type (-1 fills the field with spaces and it is EDF+ compatible)
        # EDF Annotations chan must be filled with spaces
        field_name = 'transducer'
        field_val = -1
        field_val = ['EEG' 'EEG', ..., '']
        
        ## physical dimension (-1 empties the field with spaces and it is EDF+ compatible)
        # EDF Annotations chan must be filled with spaces
        field_name = 'units'
        field_val = -1
        field_val = ['uV', 'uV', ...]     
        
        ## physical minimum
        # physical min and max must be different
        field_name = 'physical_min'
        field_val = [-1000, -1000, ...]

        ## physical maximummodify_edf_header
        # physical min and max must be different
        field_name = 'physical_max'
        field_val = [1000, 1000, ...]
        
        ## digital minimum
        # digital min and max must be different
        # digital min and max must be integer
        field_name = 'digital_min'
        field_val = [-2048, -2048, ...]        

        ## digital maximum
        # digital min and max must be different
        # digital min and max must be integer        
        field_name = 'digital_max'
        field_val = [2047, 2047, ...]       
        
        ## prefiltering (-1 filled the field with spaces and it is EDF+ compatible)
        # EDF Annotations chan must be filled with spaces
        field_name = 'prefiltering'
        field_val = -1
        field_val = ['HP:0.3Hz LP:30Hz', 'HP:0.3Hz LP:30Hz', ...]
        
        ## unmodifiable fields: all false calls
        ## number of samples in each data record
        field_name = 'n_samps_record'
        
        ## 
        
    """
    message_win = []

    # EDF file to read
    fname = "/media/DATADRIVE/data/MASS_V2_recent/SS2_EDF/01-02-0001 PSG.edf"
    output_path = "/media/DATADRIVE/data/data_out/"
    # EDF file to write
    head, tail = os.path.split(fname)
    file_name, file_ext = os.path.splitext(tail)
    fname_to_write = "{}{}_mod{}".format(output_path, file_name, file_ext)

    # Read the edf header
    edf_info = read_edf_header(fname, message_win)    
    
    # # Manage channels dim
    # field_val = []
    # for ichan in range(edf_info.get('nchan')):
    #     field_val.append('')

    # field_name = 'digital_min'
    # field_val = []
    # for ichan in range(edf_info.get('nchan')):
    #     field_val.append(-32768)
    # #field_val[-1]=-1   
    # edf_info_mod = modify_edf_header(edf_info, field_name, field_val)
    # if edf_info_mod:
    #     edf_info = edf_info_mod
    
    # test to load data in order to modify it
    
    # Attemp to modify the field
    field_name = 'n_samps_record'
    field_val = -1
    
    edf_info_mod = edf_info.copy()
    hdr_mod = modify_edf_header(edf_info_mod, field_name, field_val, message_win)
    
    # If the field was modified sucessfully
    if hdr_mod:
        # Read edf data
        edf_data = read_edf_data(fname, edf_info_mod.get('hdr_nbytes'), message_win)
        # Write the edf file
        print("\nAttempt to write {} into {}_mod{}...".format(field_name, \
                                                            file_name, file_ext))
        write_edf_file(fname_to_write, edf_info_mod, edf_data, message_win)
        print("{}_mod{} is written with the field {}".format(file_name, \
                                                              file_ext, field_name))        
    else:
        print("\nERROR : No writing")

    # print in new line all message append
    print(*message_win, sep = "\n")

if __name__ == "__main__":
    main()




