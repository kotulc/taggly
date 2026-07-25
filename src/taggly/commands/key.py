"""key command: Extract keywords from the supplied text."""

import re
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from taggly.loaders import load_embedder
from taggly.models.base import AbstractBaseCommand

# Drop terms with no letters (pure digits / punctuation) or a single character.
_HAS_LETTER = re.compile(r"[A-Za-z]")
_EDGE_NOISE = re.compile(r"^[\W_]+|[\W_]+$")


class KeyConfig(BaseModel):
    model: str = Field("keybert", description="Extraction model: 'yake' or 'keybert'")
    language: str = Field("en", description="Language code for YAKE stop-word filtering")
    dedup_lim: float = Field(0.9, description="YAKE deduplication similarity threshold (0–1)")
    dedup_func: str = Field("seqm", description="YAKE deduplication function: 'seqm', 'jaro', or 'levs'")
    stop_words: str = Field("english", description="Stop-word list for KeyBERT ('english' or 'None')")
    use_mmr: bool = Field(False, description="Use Maximal Marginal Relevance for KeyBERT diversity")


class KeyParams(BaseModel):
    top_n: int = Field(10, description="Maximum number of keywords to return")
    ngram_max: int = Field(1, description="Maximum n-gram size for keyword phrases")
    normalize: bool = Field(False, description="Normalize candidates to lowercase")


class KeyInput(BaseModel):
    content: str = Field(..., description="A text string to extract keywords from.")


class KeyOutput(BaseModel):
    keywords: List[str] = Field(..., description="The list of extracted keywords.")


class KeyCommand(AbstractBaseCommand):
    name = "key"
    Config = KeyConfig
    Params = KeyParams
    Input = KeyInput
    Output = KeyOutput

    def __init__(self, config: KeyConfig=None, **kwargs):
        super().__init__(**kwargs)
        self._config = config if config is not None else KeyConfig()
        self._kb = None  # cached KeyBERT model — only loaded on first local use
        self._nlp = None  # cached spaCy model for lemmatized dedup

    def warmup(self) -> None:
        """Pre-load the configured extraction and lemmatization models."""
        if self._config.model.lower() == "keybert" and self._kb is None:
            import keybert
            self._kb = keybert.KeyBERT(load_embedder("all-minilm"))
        self._ensure_nlp()

    def operation(self, data: KeyInput, params: KeyParams=None) -> KeyOutput:
        """Extract keywords from the supplied text."""
        p = params or KeyParams()
        # Over-fetch so noise filtering / stem-dedup can still fill top_n.
        raw = self._extract(data.content, p, top_n=max(p.top_n * 3, p.top_n + 10))
        return KeyOutput(keywords=self._postprocess(raw, p)[: p.top_n])

    def _extract(self, content: str, params: KeyParams, top_n: Optional[int] = None) -> list:
        """Run extraction using system config for model settings, params for output controls."""
        n = params.top_n if top_n is None else top_n
        if self._config.model.lower() == "keybert":
            if self._kb is None:
                import keybert
                self._kb = keybert.KeyBERT(load_embedder("all-minilm"))
            return self._kb.extract_keywords(
                content,
                keyphrase_ngram_range=(1, params.ngram_max),
                stop_words=self._config.stop_words or None,
                top_n=n,
                use_mmr=self._config.use_mmr,
            )
        else:
            import yake
            extractor = yake.KeywordExtractor(
                lan=self._config.language,
                n=params.ngram_max,
                dedupLim=self._config.dedup_lim,
                dedupFunc=self._config.dedup_func,
                top=n,
            )
            return extractor.extract_keywords(content)

    def _postprocess(self, pairs: List[Tuple[str, float]], params: KeyParams) -> List[str]:
        """Drop noisy terms and collapse morphological duplicates, preserving extractor order."""
        seen = set()
        out: List[str] = []
        for kw, _ in pairs:
            cleaned = self._clean_term(kw)
            if cleaned is None:
                continue
            surface = cleaned.lower() if params.normalize else cleaned
            key = self._stem_key(cleaned)
            if key in seen:
                continue
            seen.add(key)
            out.append(surface)
        return out

    @staticmethod
    def _clean_term(term: str) -> Optional[str]:
        """Strip edge punctuation/noise; drop empty, non-alpha, and single-character terms."""
        term = _EDGE_NOISE.sub("", " ".join(term.split()))
        if len(term) < 2 or not _HAS_LETTER.search(term):
            return None
        return term

    def _stem_key(self, term: str) -> str:
        """Lemmatize tokens so 'models' / 'modeling' / 'model' collapse to one key."""
        self._ensure_nlp()
        return " ".join(t.lemma_.lower() for t in self._nlp(term) if not t.is_space)

    def _ensure_nlp(self) -> None:
        """Lazy-load the spaCy model used for lemmatized keyword dedup."""
        if self._nlp is not None:
            return
        import spacy
        model = "en_core_web_sm"
        try:
            self._nlp = spacy.load(model)
        except OSError:
            spacy.cli.download(model)
            self._nlp = spacy.load(model)
