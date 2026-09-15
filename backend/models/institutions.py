from pydantic import BaseModel, ConfigDict, Field


class Institution(BaseModel):
    """Representação pública de uma instituição de ensino."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=200)
    state: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")
