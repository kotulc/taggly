"""keys command: Extract keywords from the supplied text."""

import sys
from typing import List

from pydantic import BaseModel, Field

from taggly.base import AbstractBaseCommand


class KeysConfig(BaseModel):
    model: str = Field("yake", description="Extraction model to use: 'yake' or 'keybert'")
    top_n: int = Field(3, description="Number of keywords to extract")
    ngram_max: int = Field(1, description="Maximum n-gram size for keyword phrases")
    language: str = Field("en", description="Language code for YAKE stop-word filtering")
    dedup_lim: float = Field(0.9, description="YAKE deduplication similarity threshold (0–1)")
    dedup_func: str = Field("seqm", description="YAKE deduplication function (seqm, jaro, or levs)")
    stop_words: str = Field("english", description="Stop-word list for KeyBERT ('english' or None)")
    use_mmr: bool = Field(False, description="Use Maximal Marginal Relevance for KeyBERT diversity")


class KeysInput(BaseModel):
    content: str


class KeysOutput(BaseModel):
    keywords: List[str]


class KeysCommand(AbstractBaseCommand):
    name = "keys"
    Input = KeysInput
    Output = KeysOutput
    Config = KeysConfig

    def __init__(self, api_url: str=None, config: BaseModel=None):
        cfg = config if config is not None else KeysConfig()
        super().__init__(api_url, cfg)
        self._extractor = None  # lazy — only built if API is unavailable

    def operation(self, data: KeysInput, config: KeysConfig=None) -> KeysOutput:
        """Extract keywords from the supplied text."""
        cfg = config or self.config or KeysConfig()
        return KeysOutput(keywords=[kw for kw, _ in self._get_extractor(cfg)(data.content)])

    def _get_extractor(self, cfg: KeysConfig):
        """Return the cached local extractor, building it on first use."""
        if self._extractor is None:
            print("[keys] loading local model...", file=sys.stderr)
            self._extractor = self._build_extractor(cfg)
        return self._extractor

    def _build_extractor(self, config: KeysConfig):
        """Return a callable that produces (keyword, score) pairs for the given config."""
        if config.model.lower() == "keybert":
            import keybert
            kb = keybert.KeyBERT("all-MiniLM-L6-v2")
            def extract(content: str) -> list:
                return kb.extract_keywords(
                    content,
                    keyphrase_ngram_range=(1, config.ngram_max),
                    stop_words=config.stop_words or None,
                    top_n=config.top_n,
                    use_mmr=config.use_mmr,
                )
            return extract
        else:
            import yake
            extractor = yake.KeywordExtractor(
                lan=config.language,
                n=config.ngram_max,
                dedupLim=config.dedup_lim,
                dedupFunc=config.dedup_func,
                top=config.top_n,
            )
            return extractor.extract_keywords
