"""topics command: Discover latent topics in the supplied documents via BERTopic."""

from typing import List
from pydantic import BaseModel, Field

from taggly.loaders import load_embedder
from taggly.models.base import AbstractBaseCommand


class TopicsConfig(BaseModel):
    model: str = Field("all-minilm", description="Embedding model: 'all-minilm', 'bge-base', or 'bge-large'")


class TopicsParams(BaseModel):
    top_n: int = Field(3, description="Maximum number of topic keywords to return")


class TopicsInput(BaseModel):
    documents: List[str] = Field(..., description="Two or more document strings to extract topics from.")


class TopicsOutput(BaseModel):
    topics: List[str] = Field(..., description="Common topics shared between the supplied documents.")


class TopicsCommand(AbstractBaseCommand):
    name = "topics"
    Config = TopicsConfig
    Params = TopicsParams
    Input = TopicsInput
    Output = TopicsOutput

    def __init__(self, config: TopicsConfig=None, **kwargs):
        super().__init__(**kwargs)
        self._config = config if config is not None else TopicsConfig()

    def warmup(self) -> None:
        """Pre-load the configured embedding model."""
        load_embedder(self._config.model)

    def operation(self, data: TopicsInput, params: TopicsParams=None) -> TopicsOutput:
        """Discover topic keywords across the supplied documents."""
        p = params or TopicsParams()
        return TopicsOutput(topics=self._topics(data.documents, p))

    def _topics(self, documents: List[str], params: TopicsParams) -> List[str]:
        """Fit BERTopic and return de-duplicated keywords across discovered topics."""
        from bertopic import BERTopic
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import FunctionTransformer
        if len(documents) < 2:
            return []
        n_clusters = max(2, min(len(documents), params.top_n))
        # FunctionTransformer bypasses UMAP, which needs n_neighbors+1 samples (default 16+)
        model = BERTopic(
            embedding_model=load_embedder(self._config.model),
            umap_model=FunctionTransformer(),
            hdbscan_model=KMeans(n_clusters=n_clusters),
        )
        model.fit_transform(documents)
        words = [word for topic in model.get_topics().values() for word, _ in topic]
        return [w for w in dict.fromkeys(words) if w][:params.top_n]
