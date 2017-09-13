import codecs
import re
import os

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


                output_files = {modality: stack.enter_context(codecs.open('{}/{}.{}.txt'.format(
                    folder_with_collection,
                    collection_name,
                    modality), 'w', encoding='utf-8'))
                    for modality in modalities}
                output_file_id = codecs.open('{}/{}.{}.txt'.format(folder_with_collection, collection_name, 'id'),
                                             'w', encoding='utf-8')

            else:
                current_modalities = get_list_of_modalities(one_document)
                assert set(current_modalities).difference(modalities) != {}

            for modality in current_modalities:
                output_files[modality].write(preprocess_delimetrs(get_content_of_modality(one_document,
                                                                                          modality)))
            output_file_id.write(text_id + '\n')
