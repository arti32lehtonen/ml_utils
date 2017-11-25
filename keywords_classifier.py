import numpy as np
from sklearn.base import BaseEstimator

from collections import Counter

from nltk.corpus import stopwords
from string import ascii_letters


class KeywordsClassifier(BaseEstimator):
    def __init__(self, n_tf=10, n_df=10, stop_words=None):
        """
        Initializaton of the class.
        
        Parameters:
        -----------
        n_tf - number of top words (by total frequency)
        
        n_df - number of top words (by document frequency)
        
        stop_words - set of stop words (will be ignored by
            classifier in future)
        
        Note:
        -----
        n_tf or n_df must be set!
        """
        BaseEstimator.__init__(self)
        if n_tf is None and n_df is None:
            raise TypeError('Either n_tf or n_df must be not None')
        self.n_tf = n_tf
        self.n_df = n_df
        self.stop_words = set(stop_words)
        
    def fit(self, X, y):
        """
        Find the most common words for each class.
        
        Para
        ----------
        X - list of str
        
        y - list of int or numpy array of int
        """
        self._class_top_words_tf = dict()
        self._class_top_words_df = dict()

        
        if isinstance(X, list) and isinstance(X[0], str):
            set_of_classes = sorted(list(set(y)))
            for one_class in set_of_classes:
                class_object_indices = np.where(y == one_class)[0]
                
                word_counter_tf = Counter()
                word_counter_df = Counter()
                
                for i in class_object_indices:
                    document_without_stop_words = [x for x in X[i].split()
                                                   if not x in self.stop_words]
                    word_counter_tf += Counter(document_without_stop_words)
                    word_counter_df += Counter(set(document_without_stop_words))
                
                    self._class_top_words_tf[one_class] = word_counter_tf.most_common()[:self.n_df]
                    self._class_top_words_df[one_class] = word_counter_df.most_common()[:self.n_tf]
    
    def _count_keywords_in_one_doc(self, one_doc, use_df=True, consider_repeated=True):
        """
        one_doc - string
        
        use_df - bool
        
        consider_repeated - bool
        """
        if use_df:
            class_top_words = {one_class:[x[0] for x in list_of_wordcounts]
                                   for (one_class, list_of_wordcounts)
                                       in self._class_top_words_df.items()}
            
        else:
            class_top_words = {one_class:[x[0] for x in list_of_wordcounts]
                                   for (one_class, list_of_wordcounts)
                                       in self._class_top_words_tf.items()}
        
        if consider_repeated:
            one_doc_split = one_doc.split()
        else:
            one_doc_split = set(one_doc.split())
        
        one_doc_keywords_count = dict()
        
        for one_class in class_top_words.keys():
            one_doc_keywords_count[one_class] = \
                sum([1 if word in class_top_words[one_class] else 0
                     for word in one_doc_split])
        return one_doc_keywords_count
    
    def predict(self, X, use_df=True, consider_repeated=True):
        """
        For each object in test set count the number of keywords 
        """
        predictions = []
        
        for i, one_doc in enumerate(X):
            words_count = self._count_keywords_in_one_doc(one_doc, use_df, consider_repeated)
            predictions.append(sorted(words_count.items(), key=lambda x:x[1])[-1][0])
        
        return predictions
    
    def get_keywords(self, use_df=True):
        if use_df:
            return self._class_top_words_df
        else:
            return self._class_top_words_tf