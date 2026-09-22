from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class SettingsDocument(BaseModel):
    event_date: date = Field(alias="eventDate")

    model_config = ConfigDict(populate_by_name=True)
