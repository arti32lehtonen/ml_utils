import codecs
import re
import os
import sys

from collections import Counter
from contextlib import ExitStack



def get_list_of_modalities(text):
    """
    Get list of all modalities (namespaces in vowpal wabbit notation).
    
    Warning! This script works bad with nameless modalities.
    
    Args:
    
    text — string, one line in vowpal wabbit format
    """
    modalities_list = []
    index_start = 0
    while len(text[index_start:]) > 0:
        additional_to_index = text[index_start:].find('|')
        if additional_to_index != -1:
            index_start += additional_to_index + 1
            modalities_list.append(text[index_start:][:text[index_start:].find(' ')].strip())
        else:
            index_start = len(text)
        
    return modalities_list

def get_text_id(text):
    """
    Get id of text (tag in vowpal wabbit notation)
    
    Warning! This script works bad with nameless texts.
    
    Args:
    
    text — string, one line in vowpal wabbit format
    """
    text_id = text[:text.find('|')]
    return text_id.strip()

def get_content_of_modality(text, modality):
    """
    Get modality (namespace) raw content of one document.
    
    Args:
    
    text — string, one line in vowpal wabbit format
    
    modality — name of vowpal wabbit namespace 
    """
    index_start = text.find('|' + modality) + len(modality) + 1
    index_finish = text[index_start:].find('|')
    if index_finish == -1:
        index_finish = len(text)
    else:
        index_finish += index_start
    return text[index_start:index_finish].strip()

def preprocess_delimetrs(text):
    """
    Replace \t, \n delimiters with a ' ' delimiter
    
    Args:
    
    text — string
    """
    return ' '.join([x for x in re.split('[\t \n]', text) if len(x) > 0]) + '\n'

def get_valid_filenames(list_of_filenames):
    """
    Filter files, whish are not satisfy to pattern {collection}.{modality}.txt
    """
    return list(filter(lambda name: re.match('[A-Za-z0-9_]+\.[A-Za-z0-9_]+\.txt', name), list_of_filenames))

class File_id_simulator:
    """
    Class which imitate real id file
    """
    def __init__(self, first_index=0):
        self.current_index = first_index - 1
    
    def __iter__(self):
        return self
    
    def __next__(self):
        return self.readline()
    
    def readline(self):
        self.current_index += 1
        return str(self.current_index) 
    
    def close(self):
        del current_index
        
def parse_vowpal_wabbit(input_file_name, folder_with_collection=None, collection_name=None):
    """
    Args:
    
    input_file_name — name of vowpal wabbit file with the input collection
    
    folder_with_collection — raw files with the content of each modality will be saved in this folder
    
    collection_name — start name of each raw file
    """
    # Set name of the folder with the collection
    if not folder_with_collection:
        folder_with_collection = 'folder_with_' + input_file_name
    
    # Check path
    if folder_with_collection in os.listdir():
        if len(os.listdir(folder_with_collection)):
            raise FileExistsError('Directory is not empty')
        
        if not os.path.isdir(folder_with_collection):
            raise NotADirectoryError('Directory is expected, but {} is a file'.format(folder_with_collection))
    else:
        os.mkdir(folder_with_collection)
    
    
    # Process vowpal wabbit file
    with ExitStack() as stack:
        input_file = stack.enter_context(codecs.open(input_file_name, 'r', encoding='utf-8'))
        
        for i, one_document in enumerate(input_file):
            text_id = get_text_id(one_document)
            
            # Get list of modalities. Check that there is no new modalities for new documents
            # Initialize new files
            if i == 0:
                modalities = get_list_of_modalities(one_document)
                current_modalities = list(modalities)
                
                
                output_files = {modality:stack.enter_context(codecs.open('{}/{}.{}.txt'.format(
                                                                         folder_with_collection,
                                                                         collection_name,
                                                                         modality), 'w', encoding='utf-8'))
                                for modality in modalities}
                    
            else:
                current_modalities = get_list_of_modalities(one_document)
                assert set(current_modalities).difference(modalities) != {}

                
            for modality in current_modalities:
                output_files[modality].write(preprocess_delimetrs(get_content_of_modality(one_document,
                                                                                          modality)))
                                                                                          
def parse_raw_collection_to_vw(folder_with_collection, output_vw_name=None, id_modality=None):
    """
    Parse raw files with modalities to a vowpal wabbit file.
    """
    if id_modality is None:
        id_modality = '|id'
    else:
        id_modality = '|' + id_modality
    
    if not output_vw_name:
        output_vw_name = 'collection.' + folder_with_collection + '.vw'
        
    
    if not len(os.listdir(folder_with_collection)):
        raise FileNotFoundError('Directory is empty')
    
    input_file_names = get_valid_filenames(os.listdir(folder_with_collection))
    input_file_names = [folder_with_collection + '/' + file_name for file_name in input_file_names]
    modalities = ['|' + re.findall('[^.][A-Za-z0-9_]+\.txt', file_name)[0][:-4]
                      for file_name in input_file_names]
                
    with ExitStack() as stack:
        output_file = stack.enter_context(codecs.open(output_vw_name, 'w', encoding='utf-8'))
        
        input_files = []
        
        if id_modality in modalities:
            index_id = modalities.index(id_modality)
            modalities.pop(index_id) 
            modalities = [''] + modalities
            id_file = input_file_names.pop(index_id)
            input_file_names = [id_file] + input_file_names
            input_files = [stack.enter_context(codecs.open(file_name, 'r', encoding='utf-8'))
                              for file_name in input_file_names]
        else:
            modalities = [''] + modalities
            input_files = [File_id_simulator(first_index=1)]
            input_files += [stack.enter_context(codecs.open(file_name, 'r', encoding='utf-8'))
                              for file_name in input_file_names]
        
        for i, document_contents in enumerate(zip(*input_files)):
            document_contents = [Counter(modality_content.split()) for modality_content in document_contents]
            document_contents = [[x[0] + ':' + str(x[1])if x[1] != 1 else x[0]
                                    for x in modality_content.items()]
                                        for modality_content in document_contents]
            document_contents = [" ".join(modality_content) for modality_content in document_contents]
            one_document = (list(zip(modalities, document_contents)))
            one_document = [x[0] + ' ' + x[1].strip() for x in one_document]
            # [1:] because we need nonspace first character
            output_file.write(" ".join(one_document)[1:] + '\n')
                                                                                         