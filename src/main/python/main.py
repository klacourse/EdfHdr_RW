#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EDF Header Info application read/modify/write edf header.

The User Interface is created through Qt Designer, MainWindow.py is generated 
from mainwindow.ui and the class Ui_MainWindow is imported in the current main.

The source code is saved in the fbs structure in order to create multiplatform 
installers.

fbs structure : 
    Main : src/main/python/main.py
    Resources : src/main/resources/base or in a specific platform folder

Created on Fri Nov 20 09:37:12 2020

@author: Karine Lacourse karine.lacourse.cnmtl@ssss.gouv.qc.ca
"""

import CEAMS_edfLib
from customTableModel import FieldTableModel, FileListModel, ValueTableModel
# import datetime
from fbs_runtime.application_context.PyQt5 import ApplicationContext
import locale # to read the local system language
from MainWindow import Ui_MainWindow
import numpy as np
import os
import pandas as pd
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtCore import pyqtSlot, QEvent, Qt, QTranslator, QCoreApplication
import qdarkstyle
import sys


class MainWindow(QMainWindow, Ui_MainWindow):    


    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        
        # reduce the lower part of the splitter to hide the 
        # debug window under normal operations
        self.splitter.setSizes([650, 150])
        self.splitter_2.setSizes([600, 400])
        self.splitter_3.setSizes([200, 1000])
        
        # Create the data model for the edf files list
        # The field list and field content model are created only 
        # when a edf file is loaded
        self.model_file_list = FileListModel()
        self.listView.setModel(self.model_file_list)

        # To detect the enter pressed on the edf field content view
        self.tableView_2.installEventFilter(self)
        
        # To load the translation file and install the translator
        self.trans = QTranslator(self)
        
        # Store a reference to the context for resources
        self.ctx = appctxt 


    @pyqtSlot( )
    def browseSlot( self ):
        ''' Called when the user presses the Browse button
        '''
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileNames, _ = QFileDialog.getOpenFileNames(
                        None,
                        "getOpenFileNames()",
                        "",
                        "EDF files (*.edf);;REC files (*.rec)",
                        options=options)        
        if fileNames:
            # Keep the selected field if any
            my_qmodelindex = self.tableView.currentIndex()
            selected_field = my_qmodelindex.row()
            for fileName in fileNames:
                # Load the edf file 
                edf_hdr_dict = CEAMS_edfLib.read_edf_header(fileName, self.message_win)            
                # Fill the edf list model
                self.fill_list_model(fileName, edf_hdr_dict)
                # Fill the edf field table and the edf value table
                self.fill_table_model(fileName, edf_hdr_dict, selected_field)
                # Plot debug message
                self.debugPrint( "setting file name: " + fileName )
    
    
    @pyqtSlot( )
    def changeLangFrSlot( self ):
        ''' Called when the user select français from the submenu
        '''      
        # Load the binary translation file qm for the MainWindow
        #   (the extension has been removed from the file)
        QCoreApplication.instance().removeTranslator(self.trans)
        self.trans.load(self.ctx.get_resource('EdfHdr_RW.' + 'fr'))       
        QCoreApplication.instance().installTranslator(self.trans)   
        

    @pyqtSlot( )
    def changeLangEnSlot( self ):
        ''' Called when the user select français from the submenu
        '''
        # Load the binary translation file qm for the MainWindow
        #   (the extension has been removed from the file)        
        QCoreApplication.instance().removeTranslator(self.trans)
        self.trans.load(self.ctx.get_resource('EdfHdr_RW.' + 'en'))
        QCoreApplication.instance().installTranslator(self.trans)
        
        
    # Called by installTranslator (I guessed)
    # Needed to see the effect of the translation file on the GUI.
    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            
            # This function was created by uic from the Designer form.
            # It translates all user visible texts in the form
            self.retranslateUi(self) # calls tr()
            
            # This function has been added manually to translate user visible
            # texts that are not in the form. ex) the models
            if hasattr(self, 'model_table_field'):
                self.retranslateAll()
        super(MainWindow, self).changeEvent(event)


    @pyqtSlot( )
    def clrEdfListSlot( self ):
        ''' Called when the user click on the "clear" push buttom in the listView.
            The EDF list will be cleared.
        '''
        # Re-create the data model for the edf files list, field list and value
        self.model_file_list = FileListModel()
        self.listView.setModel(self.model_file_list)
        self.model_table_field = FieldTableModel(self.message_win)
        self.model_table_value = ValueTableModel(self.message_win)
        self.tableView.setModel(self.model_table_field)
        self.tableView_2.setModel(self.model_table_value)        
        # Turn off the clear and the remove button
        self.pushButton_clr.setEnabled(False)        
        self.pushButton_rm.setEnabled(False) 
        

    @pyqtSlot( )
    # To complete this feature :
    # -We need to modify the channel EDF Annotations properly.
    # -We need to add verification to merge more than 2 files :
    #   should work with more than one files if all the dates are different
    #   or all the same date with different starttime.
    def concat2FilesSlot( self ):
        ''' Called when the user select concatenate 2 files from submenu.
            The user will be asked to load 2 files and they will be concatenate 
            if possible.
        '''           
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileNames, _ = QFileDialog.getOpenFileNames(
                        None,
                        "getOpenFileNames()",
                        "",
                        "EDF files (*.edf);;REC files (*.rec)",
                        options=options)
        
        if fileNames:
            edf_hdr_lst = []
            for fileName in fileNames:
                # Add the edf header file into the list      
                edf_hdr_lst.append(CEAMS_edfLib.read_edf_header(fileName, self.message_win))
                
            # Verification if the concatenation is possible
            # Some fields need to be the same through the files :
            string_2_cmp = ['patient_id', 'hdr_nbytes', 'record_length_sec',\
                'nchan', 'ch_labels', 'physical_min', 'physical_max', \
                'digital_min', 'digital_max', 'prefiltering', 'n_samps_record']
            concat_true = True
            
            # Compare each field of the loaded files
            for field in string_2_cmp:               
                # Loop through the files
                tmp_lst = []
                for edf_hdr in edf_hdr_lst:
                    tmp_lst.append(edf_hdr.get(field))
                
                # Compare each edf field for all the files
                # for arrays
                if isinstance(tmp_lst[0], np.ndarray):
                    for i in range(len(tmp_lst)-1):
                        if any(tmp_lst[0]!=tmp_lst[i+1]):
                            self.debugPrint(field + " is not the same through"\
                                            + " the files to concatenate")                            
                            concat_true = False
                # for single value as string, float, int
                else:
                    if tmp_lst.count(tmp_lst[0]) != len(tmp_lst):
                        self.debugPrint(field + " is not the same through "\
                                        + "the files to concatenate")
                        concat_true = False
            
            # Verification of the starttime and the duration
            # should work with more than one files if all the date are different
            # or all the same date with different starttime.
            #   ERROR : could have problem if the first 2 files have 
            #   the same date but not the third one.
            if concat_true:
                field = 'startdate'
                # ex) dd.mm.yy
                # Loop through the files
                date_lst = []
                for edf_hdr in edf_hdr_lst:
                    date_lst.append(edf_hdr.get(field))
                field = 'starttime'
                # ex) hh.mm.ss
                # Loop through the files
                time_lst = []
                for edf_hdr in edf_hdr_lst:
                    time_lst.append(edf_hdr.get(field))                
                
                # if the startdate recording are not the same
                if date_lst.count(date_lst[0]) != len(date_lst):
                    # find the order of the recordings
                    year_lst = []
                    month_lst = []
                    day_lst = []
                    for lst in date_lst:
                        year_lst.append(int(lst[6:8]))
                        month_lst.append(int(lst[3:5]))   
                        day_lst.append(int(lst[0:2]))
                    if year_lst.count(year_lst[0]) != len(year_lst):
                        file_order = np.argsort(year_lst)
                    elif month_lst.count(month_lst[0]) != len(month_lst):
                        file_order = np.argsort(month_lst)
                    elif day_lst.count(day_lst[0]) != len(day_lst):
                        file_order = np.argsort(day_lst)
                    else:
                        file_order = []
                # if the starttime recording are not the same
                elif time_lst.count(time_lst[0]) != len(time_lst):
                    # find the order of the recordings
                    hour_lst = []
                    min_lst = []
                    sec_lst = []
                    for lst in time_lst:
                        hour_lst.append(int(lst[0:2]))
                        min_lst.append(int(lst[3:5]))   
                        sec_lst.append(int(lst[6:8]))
                    if hour_lst.count(hour_lst[0]) != len(hour_lst):
                        file_order = np.argsort(hour_lst)
                    elif min_lst.count(min_lst[0]) != len(min_lst):
                        file_order = np.argsort(min_lst)
                    elif sec_lst.count(sec_lst[0]) != len(sec_lst):
                        file_order = np.argsort(sec_lst)
                    else:
                        file_order = []                                 
                else:
                    concat_true = False
                    self.debugPrint("Startdate and starttime are the same")
                
                if len(file_order)==len(edf_hdr_lst):
                    self.debugPrint("Files could be concatenated")
                    
                    # Ask to the user to select or write the filename to save the edf
                    sl_file_name = QFileDialog.getSaveFileName(self, self.tr(\
                            'Write the file name to save the edf'))
                    edffilename_2write = sl_file_name[0]                    
                    
                    # Extract the first edf hdr
                    edf_hdr = edf_hdr_lst[file_order[0]]
                    # Sum the n_records
                    field = 'n_records'
                    n_records = 0
                    for edf_hdr_tmp in edf_hdr_lst:
                        n_records = n_records + edf_hdr_tmp.get(field)              
                    edf_hdr['n_records'] = n_records
                    
                    # Write the header
                    CEAMS_edfLib.write_edf_hdr(edffilename_2write, edf_hdr, self.message_win)
                    # Extract data in the right order
                    for ifile in range(len(fileNames)):
                        edf_data = CEAMS_edfLib.read_edf_data(\
                            fileNames[file_order[ifile]], edf_hdr.get('hdr_nbytes'))
                        # Write the data
                        CEAMS_edfLib.write_edf_data(edffilename_2write,\
                                edf_hdr, edf_data, self.message_win)
                else:
                    self.debugPrint("Files could not be concatenated")
            else:
                self.debugPrint("Files could not be concatenated")

            
    @pyqtSlot( )
    def darkModeSlot( self ):
        ''' Called when the user select dark mode from the submenu
        '''        
        # Remove the setStyleSheet
        self.ctx.app.setStyleSheet("")      
        self.ctx.app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5()) 
        

    def debugPrint( self, msg ):
        '''Print the message in the text edit at the bottom of the
        horizontal splitter.
        '''
        self.message_win.append( msg )


    @pyqtSlot( )
    def fileSelSlot( self ):
        '''
        When the user select a edf file in the loaded list.
        It loads the selected file into the model "model_table_field".
        '''
        # Keep the selected field if any
        my_qmodelindex = self.tableView.currentIndex()
        selected_field = my_qmodelindex.row()
        
        # listView is a QListView Class and it Inherits QAbstractItemView
        # QAbstractItemView has a public function currentIndex()
        # the function currentIndex returns a QModelIndex Class
        # QModelIndex has a function row() and it returns a int
        # Extract the selected row index
        my_qmodelindex = self.listView.currentIndex()
        file_sel_row = my_qmodelindex.row() 
        selected_file = self.model_file_list.edf_complete_path[file_sel_row]
        
        # Extract the edf content models to avoid loading the file again
        edf_hdr_dict = self.model_file_list.edf_hdr_list[file_sel_row]             
        # fill the table view from the edf_dict saved 
        self.fill_table_model(selected_file, edf_hdr_dict, selected_field)
        
        # Turn on the remove button if a file is selected
        self.pushButton_rm.setEnabled(True)      


    def fill_list_model(self, fileName, edf_hdr_dict):
        '''
        When the user asked for a new edf file to be loaded.
        The edf file list is updated with the new edf file, just loaded.
        Parameters
        ----------
        fileName : string
            Filename including the path of the edf file to show.
        edf_hdr_dict : dict
            Dictionnary of the edf header.

        Returns
        -------
        None

        '''
        # Clear selection of the edf list when a new edf is loaded
        # self.listView.clearSelection()
        # Show the new edf file loaded           
        head, tail = os.path.split(fileName)
        # If it is the first edf file to be loaded
        if not self.model_file_list.edf_file_names:
            self.model_file_list.edf_complete_path.append(fileName)
            self.model_file_list.edf_file_names.append(tail)
            self.model_file_list.edf_hdr_list.append(edf_hdr_dict)
        else:
            # Extract the selected row index
            my_qmodelindex = self.listView.currentIndex()                
            file_sel_row = my_qmodelindex.row()
            # Insert the new edf file where the cursor is on the list view
            if file_sel_row > -1:
                self.model_file_list.edf_complete_path.insert(file_sel_row,fileName)
                self.model_file_list.edf_file_names.insert(file_sel_row,tail)
                self.model_file_list.edf_hdr_list.insert(file_sel_row, edf_hdr_dict)
                # Turn on the remove button if a file is selected
                self.pushButton_rm.setEnabled(True)                
            # If there is no file selected
            else: 
                self.model_file_list.edf_complete_path.append(fileName)
                self.model_file_list.edf_file_names.append(tail)    
                self.model_file_list.edf_hdr_list.append(edf_hdr_dict)
        # Update the changes on the list view
        self.model_file_list.layoutChanged.emit()
        
        # Turn on the write button
        self.pushButton_clr.setEnabled(True)
    

    def fill_table_model(self, fileName, edf_hdr_dict, selected_field):
        '''
        When an edf header is shown. The 2 lists (edf field and field content)
        are filled.
                -model_table_field : edf hdr fields of the selected file
                -model_table_value : hdr field value of the selected field
            Only the patient id is shown (by default) for the model_table_value.
        Parameters
        ----------
        fileName : string
            Filename including the path of the edf file to show.
        edf_hdr_dict : dict
            Dictionnary of the edf header.

        Returns
        -------
        None        
        '''
        
        # Contruct the model based on the edf file to show
        self.model_table_field = FieldTableModel(self.message_win)
        self.model_table_value = ValueTableModel(self.message_win)
        self.tableView.setModel(self.model_table_field)
        self.tableView_2.setModel(self.model_table_value)

        # Dict of all the edf field
        # Where the current data is stored
        # Where the data to write in a new edf is taken
        # Edited field will be saved there and propagated to 
        # model_table_field.edf_info after the "enter" pressed
        self.model_table_value.edf_dict = edf_hdr_dict
        
        # Convert the dict into a list (field label : field value)
        # because the view needs a list
        for label_dict, value_dict in edf_hdr_dict.items():
            # Access the edf field list via the model model_table_field.
            # Plot the field label selected as horizontal header (first field per default) 
            self.model_table_field.edf_info.append([str(value_dict)])
            self.model_table_value.edf_info.append([label_dict, value_dict])
            self.model_table_field.layoutChanged.emit()
        
        self.model_table_field.layoutChanged.emit()
        self.model_table_value.layoutChanged.emit()
        
        # the table value is init to the first field by default to show something
        self.model_table_value.field_value.append([str(self.model_table_value.\
                            edf_info[0][1])])
        
        # set the channel labels into the model in order to show them when the
        # field selected is specific to each channel (such as "digital min")
        self.model_table_value.ch_labels = []
        for chan in edf_hdr_dict.get('ch_labels'):
            self.model_table_value.ch_labels.append(chan)
        
        # Set the current selection to be the same as it was before edf file changed
        if selected_field>-1:
            self.tableView.selectRow(selected_field)
            self.rowClickedSlot()
        else:
            # Plot the field label selected as horizontal header (first field per default)
            self.model_table_value.hor_header_labels = ["patient_id"]
            self.model_table_value.ver_header_labels = ["value"]
            self.model_table_value.layoutChanged.emit()                       
        
        # Empty the input
        self.lineEdit.setText("")
        
        # Turn on the write button
        self.pushButton_Write.setEnabled(True)
        
        
    def eventFilter(self, obj, event):
        '''
        When the user press ENTER or RETURN in the tableView_2 (edf field content).
        It means a field has probably been edited in model_table_value 
        and the modification needs to be propagated through model_table_field.
        '''
        if obj is self.tableView_2 and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                # Update the model : model_table_field
                # Convert the dict into a list for the model_table_field
                self.model_table_field.edf_info = []
                for label_dict, value_dict in self.model_table_value.edf_dict.items():
                    # Access the edf field list via the model model_table_field.
                    # Plot the field label selected as horizontal header (first field per default) 
                    self.model_table_field.edf_info.append([str(value_dict)])
                    self.model_table_field.layoutChanged.emit() 
        return super(MainWindow, self).eventFilter(obj, event)        


    @pyqtSlot( )
    def genAllReportsSlot(self):
        '''
        When the user click "Generate -> All reports" from the menu.
        These reports will be generated for all the loaded files:
            -EDF header Report
            -Channel Count Report
            -Complete Channels reports
        '''
        # Ask to the user to select the directory to save the report
        directory_name = QFileDialog.getExistingDirectory(self, \
                                self.tr("Select a directory to save reports"))  
        self._write_chan_count(directory_name)
        self._write_hdr_rep(directory_name)
        self._write_chan_reports(directory_name)
            
            
    @pyqtSlot( )
    def genChanCntslot(self):
        '''
        When the user click "Generate -> Channel Count Report" from the menu.
        A report of the channel occurence through the EDF files loaded will
        be generated.
        '''
        # Ask to the user to select the directory to save the report
        directory_name = QFileDialog.getExistingDirectory(self, \
                                self.tr("Select a directory to save report"))          
        self._write_chan_count(directory_name)
     
        
    @pyqtSlot( )
    def genChanRptsSlot(self):
        '''
        When the user click "Generate -> Complete Channels reports" from the menu.
        A report of the channel header fields of each loaded file will be 
        generated.  One report per channel, including all the loaded files.
        '''
        # Ask to the user to select the directory to save the report
        directory_name = QFileDialog.getExistingDirectory(self, \
                                self.tr("Select a directory to save reports"))
        self._write_chan_reports(directory_name)
        
        
    @pyqtSlot( )
    def genHdrRepSlot(self):
        '''
        When the user click "Generate -> EDF header Report" from the menu.
        A report of all the EDF fields (channel fields excluded) 
        through the EDF files loaded will be generated.
        '''
        # Ask to the user to select the directory to save the report
        directory_name = QFileDialog.getExistingDirectory(self, \
                                self.tr("Select a directory to save report"))  
        self._write_hdr_rep(directory_name)
       
        
    def isFileValid( self, fileName ):
        '''
        returns True if the file exists and can be
        opened.  Returns False otherwise.
        '''
        try: 
            file = open( fileName, 'r' )
            file.close()
            return True
        except:
            return False        

 
    @pyqtSlot( )
    def lightModeSlot( self ):
        ''' Called when the user select light mode from the submenu
        '''         
        # ['Breeze', 'Oxygen', 'QtCurve', 'Windows', 'Fusion']
        self.ctx.app.setStyle('Fusion') 
        # Remove the setStyleSheet
        self.ctx.app.setStyleSheet("")
        # Change the background color.
        # self.setStyleSheet("""QToolTip { 
        #                             background-color: white; 
        #                             color: black; 
        #                             border: black solid 1px;
        #                             opacity: 255
        #                             }""")
        self.setStyleSheet("""QToolTip { 
                            color: black; 
                            border: black solid 1px;
                            opacity: 255
                            }""")

            
    # To translate user visible texts that are not in the form. ex) the models
    def retranslateAll( self ):
        # Retranslate the QtableView of fields
        self.model_table_field.retranslateUi()
        
        
    @pyqtSlot( )
    def returnPressedSlot( self ):
        ''' Called when the user enters a string in the line edit and
        presses the ENTER key.
        '''
        # Read the filename written by the user after the return pressed
        fileName =  self.lineEdit.text()
        if self.isFileValid( fileName ):
            # Keep the selected field if any
            my_qmodelindex = self.tableView.currentIndex()
            selected_field = my_qmodelindex.row()                 
            # Load the edf file 
            edf_hdr_dict = CEAMS_edfLib.read_edf_header(fileName, self.message_win)            
            # Fill the edf list model
            self.fill_list_model(fileName, edf_hdr_dict)
            # Fill the edf field table and the edf value table
            self.fill_table_model(fileName, edf_hdr_dict, selected_field)            
            # Plot debug message
            self.debugPrint( "setting file name: " + fileName )
        else:
            # Plot debug message
            self.debugPrint( "Invalid file specified: " + fileName  )
            

    @pyqtSlot( )
    def rmSlEdfFileSlot( self ):
        ''' Called when the user click on the "remove" push buttom in the listView.
            The selected edf file will be removed from the EDF list.
        '''
        # Extract the selected row index
        my_qmodelindex = self.listView.currentIndex()                
        file_sel_row = my_qmodelindex.row()
        # pop the selected edf file
        self.model_file_list.edf_complete_path.pop(file_sel_row)
        self.model_file_list.edf_file_names.pop(file_sel_row)
        self.model_file_list.edf_hdr_list.pop(file_sel_row)
        # Update the changes on the list view
        self.model_file_list.layoutChanged.emit()
        # Cleat the QTableView of the edf fields
        self.model_table_value = ValueTableModel(self.message_win)
        self.tableView.setModel(self.model_table_field)
        self.tableView_2.setModel(self.model_table_value)          
        

    @pyqtSlot( )
    def rowClickedSlot( self ):
        ''' Called when the user click on a row in the tableView (fields list).
            The tableView (field content) is updated with the content of the
            selected field.  Note : channel labels are also printed when 
            the field content is an array.
        '''
        # tableView is a QTableView Class and it Inherits QAbstractItemView
        # QAbstractItemView has a public function currentIndex()
        # the function currentIndex returns a QModelIndex Class
        # QModelIndex has a function row() and it returns a int
        # Extract the selected row index        
        my_qmodelindex = self.tableView.currentIndex()
        selected_row = my_qmodelindex.row()        
        selected_field = self.model_table_value.edf_info[selected_row][0]
        selected_content = self.model_table_value.edf_info[selected_row][1]
        
        # Plot the field label selected as horizontal header
        self.model_table_value.hor_header_labels = [str(selected_field)] 
        
        # Fill model_table_value
        self.model_table_value.field_value = []
        self.model_table_value.ver_header_labels = []
        
        if isinstance(selected_content, list) or \
            isinstance(selected_content, np.ndarray):

            # Print channel labels and content
            for ichan, value_list in enumerate(selected_content):
                self.model_table_value.field_value.append([str(value_list)])
                self.model_table_value.ver_header_labels.append(\
                                self.model_table_value.ch_labels[ichan])               
                self.model_table_value.layoutChanged.emit()
        else:
            self.model_table_value.field_value.append([str(selected_content)]) 
            self.model_table_value.ver_header_labels = ["value"]         
            self.model_table_value.layoutChanged.emit()        


    # To make the code easier to read : its the translate fonction
    def tr(self, text_to_translate):
        "Text translation to support different languages in the application."
        return QCoreApplication.translate('MainWindow', text_to_translate)
            
        
    @pyqtSlot( )
    def writeSlot( self ):
        ''' Called when the user presses the write button.
        '''
        # Ask to the user to select or write the filename to save the edf
        sl_file_name = QFileDialog.getSaveFileName(self, self.tr(\
                'Write the file name to save the edf'))
        # Look for the right loaded file to write
        my_qmodelindex = self.listView.currentIndex()
        file_sel = my_qmodelindex.row()
        # If no selection, the last one is taken
        edf_complete_path = self.model_file_list.edf_complete_path[file_sel]
        edffilename_2write = sl_file_name[0]
        # Load the edf data to write a complete edf file
        edf_data = CEAMS_edfLib.read_edf_data(edf_complete_path, \
                            self.model_table_value.edf_dict.get('hdr_nbytes'),\
                                self.message_win)
        # Write the edf file with the modified header
        CEAMS_edfLib.write_edf_file(edffilename_2write, \
                        self.model_table_value.edf_dict, edf_data, self.message_win)
        self.debugPrint( "{} is written".format(edffilename_2write))


    # function to write the channel count report.
    def _write_chan_count(self, directory_name):
        # List of edf header
        edf_hdr_list = self.model_file_list.edf_hdr_list
        # Create a master flat list of all the channels through the loaded files
        master_chan_lst = []
        for edf_hdr_dict in edf_hdr_list:
            cur_labels = edf_hdr_dict.get('ch_labels')
            # Strip spaces
            labels_stp = []
            for labels in cur_labels: 
                labels_stp.append(labels.strip())
            master_chan_lst.extend(labels_stp)        
        # Extract unique channel list 
        chan_np_unique = np.unique(master_chan_lst)
        chan_lst_unique = chan_np_unique.tolist()
        # Count the occurrence of each channel labels
        occur_count = {}
        for i_chan in range(len(chan_lst_unique)):
             occurrence = master_chan_lst.count(chan_lst_unique[i_chan])
             occur_count[chan_lst_unique[i_chan]] = occurrence
        # Create a dataframe from the count
        df = pd.DataFrame.from_dict(occur_count, orient='index')
        # Write the DataFrame into a cvs file
        chanCount_rep_fname = directory_name + "/chanCountRep.csv"  
        # Write the DataFrame into a cvs file
        df.to_csv(chanCount_rep_fname, index_label='channel', header=['count'])        
        # Plot debug message
        self.debugPrint( "Channel Count Report is written to {}".\
                        format(chanCount_rep_fname))
            
            
    # function to write the channels reports.
    def _write_chan_reports(self, directory_name):
        
        # Create a subfolder to save all the reports if it does not exist
        if not os.path.exists(directory_name + "/EdfHdr_RW_chans_rep"):
            os.mkdir(directory_name + "/EdfHdr_RW_chans_rep")
            
        # List of edf header
        edf_hdr_list = self.model_file_list.edf_hdr_list
        
        # Create a master flat list of all the channels through the loaded files
        master_chan_lst = []
        for edf_hdr_dict in edf_hdr_list:
            cur_labels = edf_hdr_dict.get('ch_labels')
            # Strip spaces
            labels_stp = []
            for labels in cur_labels: 
                labels_stp.append(labels.strip())
            master_chan_lst.extend(labels_stp)        
        # Extract unique channel list 
        chan_np_unique = np.unique(master_chan_lst)
        chan_lst_unique = chan_np_unique.tolist()
        
        # For each channel from the unique master list
        for i_chan in range(len(chan_lst_unique)):
            # List to group all fields for the same channel (through the loaded files) 
            all_edf_chan = [] 
            # For each edf file loaded
            file_i = 0
            for edf_hdr_dict in edf_hdr_list:
                # Look for the current channel
                cur_labels = edf_hdr_dict.get('ch_labels')
                # Strip spaces
                labels_stp = []
                for labels in cur_labels: 
                    labels_stp.append(labels.strip())
                cur_labels = labels_stp
                # If the current channel is in the current edf
                if cur_labels.count(chan_lst_unique[i_chan]):
                    # Dict to store fields for the current channel and file
                    cur_edf_chan = {'filename': self.model_file_list.edf_file_names[file_i]}                    
                    cur_index = cur_labels.index(chan_lst_unique[i_chan])
                    # For each channel field
                    for field_key, field_val in edf_hdr_dict.items():
                        if isinstance(field_val, list) or \
                            isinstance(field_val, np.ndarray):
                            # Extract the value for the current channel
                            cur_field = field_val[cur_index]
                            cur_edf_chan.update({field_key: cur_field})
                            #print({field_key: cur_field})
                    # Add the channel dict into a list
                    all_edf_chan.append(cur_edf_chan)
                file_i +=1
            # Write the current channel report
            # Create a dataframe from the list of dicts
            dp = pd.DataFrame(all_edf_chan)
            # Write the DataFrame into a cvs file
            chan_reps_filen = directory_name + "/EdfHdr_RW_chans_rep/" + \
                chan_lst_unique[i_chan] + "_rep.csv"
            dp.to_csv(chan_reps_filen)
            
            
        # Plot debug message
        self.debugPrint( "Channels header reports are written to {}".\
                        format(directory_name + "/EdfHdr_RW_chans_rep/")) 
        
            
    # function to write the edf header report.
    def _write_hdr_rep(self, directory_name):
        # List of edf header from the files loaded
        edf_hdr_list = self.model_file_list.edf_hdr_list
        # Create an empty list of dicts (to extract only single field)
        # A single field does not include fields specific to channels (no array)
        edf_hdr_s_all = []
        # Loop through the dicts of loaded files
        file_i = 0
        for edf_hdr_dict in edf_hdr_list:
            # Dict of single field
            # Add the filename into the dict
            edf_hdr_single = {'filename': self.model_file_list.edf_file_names[file_i]}
            for field_key, field_val in edf_hdr_dict.items():
                if isinstance(field_val, str) or isinstance(field_val, int) or \
                    isinstance(field_val, float):
                        # Construct a dict with only single values
                        # one edf_hdr_single dist per edf file
                        edf_hdr_single.update({field_key: field_val})
            # Add the single dict into a list
            edf_hdr_s_all.append(edf_hdr_single)
            file_i +=1
        # Create a dataframe from the list of dicts
        dp = pd.DataFrame(edf_hdr_s_all)
        # Write the DataFrame into a cvs file
        hdr_rep_fname = directory_name + "/edfHdrRep.csv"
        dp.to_csv(hdr_rep_fname)
        # Plot debug message
        self.debugPrint( "EDF header Report is written to {}".format(hdr_rep_fname)) 
        
        
# To retrieve the computer system’s local language and load the right 
# language file at the application startup automatically.
class translator(QTranslator):
    " Translator class definition"
    
    def __init__(self):
        " Translator class contructor "
        QTranslator.__init__(self)
        
        try:
            if len(sys.argv) == 1:
                lang = locale.getdefaultlocale()[0].split('_')[0]
                self.load(self.ctx.get_resource('EdfHdr_RW.' + lang))
                self.debugPrint('"EdfHdr_RW. + lang" wich is EdfHdr_RW.{}'.format(lang))
            else:
                self.load(self.ctx.get_resource('EdfHdr_RW.' + sys.argv[1]))
                self.debugPrint('"EdfHdr_RW. + sys.argv[1]" which is EdfHdr_RW.{}'.format(sys.argv[1]))
                
        except Exception as ex:
            print('Execution error')
            print('Function : Translator()')
            print(str(ex))
        
    
class AppContext(ApplicationContext):           # 1. Subclass ApplicationContext
    def run(self):                              # 2. Implement run()
        window = MainWindow()
        version = self.build_settings['version']
        window.setWindowTitle("EdfHdr_RW v" + version)
        window.resize(1200, 800)
        window.show()
        return self.app.exec_()                 # 3. End run() with this line
    

if __name__ == '__main__':
    appctxt = AppContext()                      # 4. Instantiate the subclass
    appctxt.app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    exit_code = appctxt.run()                   # 5. Invoke run()
    sys.exit(exit_code)
    
