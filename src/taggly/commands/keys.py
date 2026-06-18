"""keys command: Extract keywords from the supplied text."""

from typing import List
from pydantic import BaseModel, Field

from taggly.models.base import AbstractBaseCommand


class KeysConfig(BaseModel):
    model: str = Field("keybert", description="Extraction model: 'yake' or 'keybert'")
    language: str = Field("en", description="Language code for YAKE stop-word filtering")
    dedup_lim: float = Field(0.9, description="YAKE deduplication similarity threshold (0–1)")
    dedup_func: str = Field("seqm", description="YAKE deduplication function: 'seqm', 'jaro', or 'levs'")
    stop_words: str = Field("english", description="Stop-word list for KeyBERT ('english' or 'None')")
    use_mmr: bool = Field(False, description="Use Maximal Marginal Relevance for KeyBERT diversity")


class KeysParams(BaseModel):
    top_n: int = Field(10, description="Maximum number of keywords to return")
    ngram_max: int = Field(1, description="Maximum n-gram size for keyword phrases")


class KeysInput(BaseModel):
    content: str = Field(..., description="A text string to extract keywords from.")


class KeysOutput(BaseModel):
    keywords: List[str] = Field(..., description="The list of extracted keywords.")


class KeysCommand(AbstractBaseCommand):
    name = "keys"
    Config = KeysConfig
    Params = KeysParams
    Input = KeysInput
    Output = KeysOutput

    def __init__(self, config: KeysConfig=None, **kwargs):
        super().__init__(**kwargs)
        self._config = config if config is not None else KeysConfig()
        self._kb = None  # cached KeyBERT model — only loaded on first local use

    def warmup(self) -> None:
        """Pre-load the configured extraction model."""
        if self._config.model.lower() == "keybert" and self._kb is None:
            import keybert
            self._kb = keybert.KeyBERT("all-MiniLM-L6-v2")

    def operation(self, data: KeysInput, params: KeysParams=None) -> KeysOutput:
        """Extract keywords from the supplied text."""
        p = params or KeysParams()
        return KeysOutput(keywords=[kw for kw, _ in self._extract(data.content, p)])

    def _extract(self, content: str, params: KeysParams) -> list:
        """Run extraction using system config for model settings, params for output controls."""
        if self._config.model.lower() == "keybert":
            if self._kb is None:
                import keybert
                self._kb = keybert.KeyBERT("all-MiniLM-L6-v2")
            return self._kb.extract_keywords(
                content,
                keyphrase_ngram_range=(1, params.ngram_max),
                stop_words=self._config.stop_words or None,
                top_n=params.top_n,
                use_mmr=self._config.use_mmr,
            )
        import yake
        extractor = yake.KeywordExtractor(
            lan=self._config.language,
            n=params.ngram_max,
            dedupLim=self._config.dedup_lim,
            dedupFunc=self._config.dedup_func,
            top=params.top_n,
        )
        return extractor.extract_keywords(content)
