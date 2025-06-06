#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A Model-View
The model stores the data.
The view requests data from the model and displays what is returned on the widget.

To subclass the QAbstractTable, you must reimplement its virtual methods :
    rowCount(), columnCount(), and data().
    
To subclass the QAbstractListModel, you must reimplement its virtual methods :
    rowCount() and data().
    
To make QListView editable, you must reimplement flags() and setData().

Created on Mon Nov 23 12:43:34 2020
file was originally taken from 
https://www.learnpyqt.com/tutorials/qtableview-modelviews-numpy-pandas/

@author: Karine Lacourse karine.lacourse.cnmtl@ssss.gouv.qc.ca
"""
import CEAMS_edfLib
import numpy as np
from PyQt5.QtCore import Qt, QAbstractTableModel, QAbstractListModel, QCoreApplication


class FieldTableModel(QAbstractTableModel):
    '''
    Class to store data in order to show and navigate through the edf fields 
    with their values (the linked view is not appropriate to see the field value).
    '''
    def __init__( self, message_win):
        super(FieldTableModel, self).__init__()
        
        # Data of the model shown on the table view
        # what needs to be updated
        self.edf_info = []
        
        # Set the labels
        self.retranslateUi()

        # Reference to the message window to print messages
        self.message_win = message_win


    def data(self, index, role):
        # The length of the outer list.
        # The nb of edf fields
        if role == Qt.DisplayRole:
            return self.edf_info[index.row()][index.column()]
        
        
    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        # the number of edf field value
        #   all channel label must be packed in one string for now
        if self.rowCount(index):
            return len(self.edf_info[0])
        else:
            return 0
        

    def rowCount(self, index):
        return len(self.edf_info)
    
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.hor_header_labels[section]
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return self.ver_header_labels[section]        
        return QAbstractTableModel.headerData(self, section, orientation, role)
    
    
    # To make the code easier to read : its the translate fonction
    def tr(self, text_to_translate):
        "Text translation to support different languages in the application."
        return QCoreApplication.translate('FieldTableModel', text_to_translate)
    
    
    # Called by the constructor and by the changeEvent when LanguageChange
    def retranslateUi(self):
        # Headers labels
        self.ver_header_labels = [self.tr('patient identification'), self.tr('recording identification'),\
                                    self.tr('start date'), self.tr('start time'), self.tr('number of bytes in header'),\
                                    self.tr('comment 44 char reserved'), self.tr('number of data records'),\
                                    self.tr('record length (sec)'), self.tr('number of channels'),\
                                    self.tr('channel labels'), self.tr('transducer'), self.tr('physical dimension'),\
                                    self.tr('physical min'), self.tr('physical max'), self.tr('digital min'),\
                                    self.tr('digital max'), self.tr('prefiltering'), self.tr('number of samples in a record'),\
                                    self.tr('comment 32 char rsv'), self.tr('*real nb of bytes in header'),\
                                    self.tr('*real nb of records')]
        self.hor_header_labels = [self.tr('value')]        
        
        
class FileListModel(QAbstractListModel):
    '''
    Class to store data in order to show and navigate through the edf files.
    It contains a list of edf_hdr, an edf_edf for each edf file loaded.
    '''
    def __init__( self):
        '''
        Initializes the two members the class holds:
        the file name and its contents.
        '''
        super(FileListModel, self).__init__()
        # Data useful to manage the model
        self.edf_complete_path = [] # path of each edf loaded
        self.edf_hdr_list = [] # list of edf_hdr_dict for each edf loaded
        # Data of the model, data actually shown on the list
        self.edf_file_names = []

    # the two methods rowcount() and data() are standard Model methods 
    # we must implement for a list model.
    def data(self, index, role):
        if role == Qt.DisplayRole:
            text = self.edf_file_names[index.row()]
            return text
        
    # the two methods rowcount() and data() are standard Model methods 
    # we must implement for a list model.
    def rowCount(self, index):
        return len(self.edf_file_names)
    

class ValueTableModel(QAbstractTableModel):
    '''
    Class to store data in order to show and navigate through the selected 
    edf field from the selected edf file.  The linked view allows to see the 
    edf field values.  This model is editable through the function setData.
    '''    
    def __init__( self, message_win):
        super(ValueTableModel, self).__init__()
        
        # Specific to our data
        self.ch_labels = []
        # To store a copy of what is shown on table field
        self.edf_info = []
        # To store a copy of what is read in the edf
        self.edf_dict = []
        
        # Data of the model shown on the table view
        # what needs to be updated
        self.field_value = []
        
        # Set the labels
        self.ver_header_labels = ['value'] # value or all the channel labels
        self.hor_header_labels = ['patient_id']        

        # Reference to the message window to print messages
        self.message_win = message_win


    # To make the code easier to read : its the translate fonction
    def tr(self, text_to_translate):
        "Text translation to support different languages in the application."
        return QCoreApplication.translate('ValueTableModel', text_to_translate)
        
        
    def tool_tip_string(self, hor_header_labels):
        if hor_header_labels=='patient_id':
            tool_tip_mess_patient = self.tr("*** To be edf+ compatible ***\n"\
                + "The 'local patient identification' must start with the subfields\n"\
                + "   (subfields do not contain, but are separated by, spaces):\n"\
                + "\t- the code by which the patient is known in the hospital "\
                + "administration. ex. MCH-0234567\n"\
                + "\t- sex (English, so F or M).\n"\
                + "\t- birthdate in dd-MMM-yyyy format using the English 3-character\n"\
                + "\t   abbreviations of the month in capitals. 02-AUG-1951 is OK,\n"\
                + "\t   while 2-AUG-1951 is not.\n"\
                + "\t- the patients name.\n\n"\
                + " notes : \n"\
                + "\t-Any space inside the hospital code or patient name\n"\
                + "\t   must be replaced by a different character, for instance an _.\n"\
                + "\t-Subfields whose contents are unknown, not applicable\n"\
                + "\t   or must be made anonymous are replaced by a single character 'X'.\n"\
                + "\t   So, if everything is unknown then the 'local patient\n"\
                + "\t   identification' field would start with: 'X X X X'.\n\n"\
                + "Examples to be EDF+ compatible: \n"\
                + "\t MCH-0234567 F 02-MAY-1951 Haagse_Harry\n"\
                + "\t X F 02-MAY-1951 Haagse_Harry\n"\
                + "\t X X X X\n\n")#\
                #+ "*** Any edits will be accepted. ***")
            return tool_tip_mess_patient
        elif hor_header_labels=='rec_id':
            tool_tip_mess_rec = self.tr("*** To be edf+ compatible ***\n"\
                + "The 'local recording identification' must start with the subfields\n"\
                + "   (subfields do not contain, but are separated by, spaces):\n"\
                + "\t- The text 'Startdate'.\n"\
                + "\t- The startdate itself in dd-MMM-yyyy format using the English\n"\
                + "\t   3-character abbreviations of the month in capitals.\n"\
                + "\t- The hospital administration code of the investigation, "\
                + "i.e. EEG number or PSG number.\n"\
                + "\t- A code specifying the responsible investigator or technician.\n"\
                + "\t- A code specifying the used equipment.\n\n"\
                + " notes : \n"\
                + "\t-Any space inside the hospital code or name\n"\
                + "\t   must be replaced by a different character, for instance an _.\n"\
                + "\t-Subfields whose contents are unknown, not applicable\n"\
                + "\t   or must be made anonymous are replaced by a single character 'X'.\n"\
                + "\t   So, if everything is unknown then the 'local recording\n"\
                + "\t   identification' field would start with: 'Startdate X X X X'.\n\n"\
                + "Examples to be EDF+ compatible: \n"\
                + "\t Startdate 02-MAR-2002 PSG-1234/2002 NN Telemetry03\n"\
                + "\t Startdate X X X X\n\n")#\
                #+ "*** Any edits will be accepted. ***")
            return tool_tip_mess_rec    
        else:
            tool_tip_mess_err = self.tr("ToolTip message not coded yet, \n"\
                          + "see https://www.edfplus.info/specs/edf.html")
            return tool_tip_mess_err               


    # called when data is displayed or edited
    def data(self, index, role):
        
        # The length of the outer list.
        # The nb of edf fields
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self.field_value[index.row()][index.column()]
        if role == Qt.ToolTipRole:
            return self.tool_tip_string(self.hor_header_labels[0])
        
        
    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        # the number of edf field valuemodel_table_value
        #   all channel label must be packed in one string for now
        if self.rowCount(index):
            return len(self.field_value[0])
        else:
            return 0
        

    def rowCount(self, index):
        return len(self.field_value)

    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.hor_header_labels[section]
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return self.ver_header_labels[section]        
        return QAbstractTableModel.headerData(self, section, orientation, role)
    
    
    # Needed to edit the field in the table view
    # otherwise user can only select the field without modifying it.
    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsEditable
        
    
    # called when data is edited
    def setData(self, index, value, role):
        if role == Qt.EditRole:
            
            # To know which field is edited
            edited_field = self.hor_header_labels
            self.message_win.append("User edits '{}' row {} value is {}'".format(edited_field[0],\
                                                index.row(), value))
             
            # Update the current model 
            # To see the edited data on the table view
            self.field_value[index.row()][index.column()] = value
            self.layoutChanged.emit() 
            
            # Flat the list (the selected field creates a list of list)
            flat_list = [item for sublist in self.field_value for item in sublist]
            
            # Evaluate the instance of edited field
            if isinstance(self.edf_dict.get(edited_field[0]), np.ndarray):
                edited_array = np.zeros(len(flat_list))
                for index, item in enumerate(flat_list):
                    edited_array[index] = item
                self.message_win.append("value to provide to modify_edf_header is {}'".format(edited_array))
                hdr_mod = CEAMS_edfLib.modify_edf_header(self.edf_dict, \
                        edited_field[0], edited_array, self.message_win)
            elif isinstance(self.edf_dict.get(edited_field[0]), list):
                self.message_win.append("value to provide to modify_edf_header is {}'".format(flat_list))
                hdr_mod = CEAMS_edfLib.modify_edf_header(self.edf_dict, \
                        edited_field[0], flat_list, self.message_win)
            elif isinstance(self.edf_dict.get(edited_field[0]), str):
                self.message_win.append("value to provide to modify_edf_header is '{}'".format(str(flat_list[0])))
                hdr_mod = CEAMS_edfLib.modify_edf_header(self.edf_dict, \
                        edited_field[0], str(flat_list[0]), self.message_win)
            elif isinstance(self.edf_dict.get(edited_field[0]), int) or \
                isinstance(self.edf_dict.get(edited_field[0]), float):
                self.message_win.append("value to provide to modify_edf_header is '{}'".format(flat_list[0]))
                hdr_mod = CEAMS_edfLib.modify_edf_header(self.edf_dict, \
                        edited_field[0], flat_list[0], self.message_win)                
            else:
                self.message_win.append("The edited field has an unexpecetd type = {}".\
                      format(type(self.edf_dict.get(edited_field[0]))))
                hdr_mod = False
            
            
            # If the field was modified sucessfully
            if hdr_mod:
                # Update the current model
                # Store the modified data into edf_info
                self.edf_info = []
                for label_dict, value_dict in self.edf_dict.items():
                    self.edf_info.append([label_dict, value_dict])
                self.message_win.append("{} was modified to '{}'".format(edited_field[0],value))
                
                # set the channel labels into the model
                if edited_field[0]=="ch_labels":
                    self.ch_labels = []
                    self.ver_header_labels = []
                    for chan in self.edf_dict.get('ch_labels'):
                        self.ch_labels.append(chan)
                        self.ver_header_labels.append(chan)
                        self.layoutChanged.emit()
                        
                self.layoutChanged.emit()
            else:
                self.message_win.append("{} was not modified!".format(edited_field[0]))
            return True
    
    
    