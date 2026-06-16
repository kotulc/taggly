"""keys command: Extract keywords from the supplied text."""

from typing import List
from pydantic import BaseModel, Field

from taggly.models.base import AbstractBaseCommand


class KeysConfig(BaseModel):
    model: str = Field("keybert", description="Extraction model to use: 'yake' or 'keybert'")
    top_n: int = Field(10, description="Number of keywords to extract")
    ngram_max: int = Field(1, description="Maximum n-gram size for keyword phrases")
    language: str = Field("en", description="Language code for YAKE stop-word filtering")
    dedup_lim: float = Field(0.9, description="YAKE deduplication similarity threshold (0–1)")
    dedup_func: str = Field("seqm", description="YAKE deduplication function (seqm, jaro, or levs)")
    stop_words: str = Field("english", description="Stop-word list for KeyBERT ('english' or None)")
    use_mmr: bool = Field(False, description="Use Maximal Marginal Relevance for KeyBERT diversity")


class KeysInput(BaseModel):
    content: str = Field(..., description="A text string to extract keywords from.")


class KeysOutput(BaseModel):
    keywords: List[str] = Field(..., description="The list of extracted keywords.")


class KeysCommand(AbstractBaseCommand):
    name = "keys"
    Input = KeysInput
    Output = KeysOutput
    Config = KeysConfig

    def __init__(self, api_url: str=None, config: BaseModel=None, **kwargs):
        super().__init__(api_url, config, **kwargs)
        self._kb = None  # cached KeyBERT model — only loaded on first local use

    def warmup(self) -> None:
        """Pre-load the configured extraction model."""
        cfg = self.config or KeysConfig()
        if cfg.model.lower() == "keybert" and self._kb is None:
            import keybert
            self._kb = keybert.KeyBERT("all-MiniLM-L6-v2")

    def operation(self, data: KeysInput, config: KeysConfig=None) -> KeysOutput:
        """Extract keywords from the supplied text."""
        cfg = config or self.config or KeysConfig()
        return KeysOutput(keywords=[kw for kw, _ in self._extract(data.content, cfg)])

    def _extract(self, content: str, cfg: KeysConfig) -> list:
        """Run extraction with the current config, caching only the KeyBERT model."""
        if cfg.model.lower() == "keybert":
            # Cache the KeyBERT model on first use since loading is slow
            if self._kb is None:
                import keybert
                self._kb = keybert.KeyBERT("all-MiniLM-L6-v2")
            return self._kb.extract_keywords(
                content,
                keyphrase_ngram_range=(1, cfg.ngram_max),
                stop_words=cfg.stop_words or None,
                top_n=cfg.top_n,
                use_mmr=cfg.use_mmr,
            )
        # Default to the lightweight YAKE if the model name is unrecognized
        import yake
        extractor = yake.KeywordExtractor(
            lan=cfg.language,
            n=cfg.ngram_max,
            dedupLim=cfg.dedup_lim,
            dedupFunc=cfg.dedup_func,
            top=cfg.top_n,
        )
        return extractor.extract_keywords(content)
