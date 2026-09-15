from pydantic import BaseModel, ConfigDict, Field


class Participant(BaseModel):
    """Representação pública de um participante."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=200)
    cpf: str = Field(pattern=r"^\d{11}$")
    email: str = Field(min_length=1, max_length=254)
    institutionId: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")
