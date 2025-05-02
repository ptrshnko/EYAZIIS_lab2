import os
import json
import logging
from collections import Counter
from natasha import (
    Segmenter,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    Doc
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKENS_DIR = os.path.join(BASE_DIR, 'data', 'tokens')
METADATA_PATH = os.path.join(BASE_DIR, 'data', 'metadata', 'metadata.json')

class CorpusManager:
    def __init__(self):
        self.metadata = {}
        try:
            with open(METADATA_PATH, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            if not self.metadata:
                logger.error("Metadata is empty. No documents available.")
                raise ValueError("Metadata is empty")
            logger.info(f"Corpus manager initialized with {len(self.metadata)} documents")
        except Exception as e:
            logger.error(f"Error initializing corpus manager: {e}")
            raise

        self.segmenter = Segmenter()
        self.morph_vocab = MorphVocab()
        self.emb = NewsEmbedding()
        self.morph_tagger = NewsMorphTagger(self.emb)

    def load_tokens(self, doc_ids=None):
        tokens = []
        if doc_ids is None:
            doc_ids = self.metadata.keys()
        for doc_id in doc_ids:
            token_path = os.path.join(TOKENS_DIR, f'doc_{doc_id}.json')
            if os.path.exists(token_path):
                try:
                    with open(token_path, 'r', encoding='utf-8') as f:
                        doc_tokens = json.load(f)
                        tokens.extend(doc_tokens)
                    logger.debug(f"Loaded tokens for doc {doc_id}: {len(doc_tokens)} tokens")
                except Exception as e:
                    logger.error(f"Error loading tokens for doc {doc_id}: {e}")
        return tokens

    def get_filtered_doc_ids(self, filters):
        if not filters:
            return list(self.metadata.keys())
        filtered_ids = []
        for doc_id, meta in self.metadata.items():
            match = True
            for key, value in filters.items():
                if meta.get(key) != value:
                    match = False
                    break
            if match:
                filtered_ids.append(doc_id)
        return filtered_ids

    def get_wordform_frequency(self, query, filters=None):
        doc_ids = self.get_filtered_doc_ids(filters)
        tokens = self.load_tokens(doc_ids=doc_ids)
        words = query.split()
        results = {}
        for word in words:
            count = sum(1 for t in tokens if t['token'].lower() == word.lower())
            results[word] = count
        return results

    def get_pos_analysis(self, query):
        doc = Doc(query)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)
        results = []
        for token in doc.tokens:
            results.append((token.text, token.pos or 'Неизвестно'))
        return results

    def get_morphological_analysis(self, query):
        doc = Doc(query)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)
        results = []
        for token in doc.tokens:
            token.lemmatize(self.morph_vocab)
            morph = {
                'token': token.text,
                'lemma': token.lemma or 'Неизвестно',
                'pos': token.pos or 'Неизвестно'
            }
            results.append(morph)
        return results

    def get_concordance(self, query, window=5, filters=None):
        doc_ids = self.get_filtered_doc_ids(filters)
        tokens = self.load_tokens(doc_ids=doc_ids)
        concordances = []
        for token in tokens:
            if token['token'].lower() == query.lower():
                sent_tokens = [t for t in tokens if t['doc_id'] == token['doc_id'] and t['sent_id'] == token['sent_id']]
                sent_tokens.sort(key=lambda x: x['token_id'])
                idx = next(i for i, t in enumerate(sent_tokens) if t['token_id'] == token['token_id'])
                left = [t['token'] for t in sent_tokens[max(0, idx-window):idx]]
                right = [t['token'] for t in sent_tokens[idx+1:idx+1+window]]
                concordances.append((left, token['token'], right, token['doc_id'], token['sent_id']))
        return concordances

    def remove_document(self, filename):
        for doc_id, meta in list(self.metadata.items()):
            if meta['filename'] == filename:
                del self.metadata[doc_id]
                with open(METADATA_PATH, 'w', encoding='utf-8') as f:
                    json.dump(self.metadata, f, ensure_ascii=False, indent=2)
                path_txt = meta['path_txt']
                if os.path.exists(path_txt):
                    os.remove(path_txt)
                token_path = os.path.join(TOKENS_DIR, f'doc_{doc_id}.json')
                if os.path.exists(token_path):
                    os.remove(token_path)
                path_raw = meta['path_raw']
                if os.path.exists(path_raw):
                    os.remove(path_raw)
                logger.info(f"Document {filename} removed")
                break