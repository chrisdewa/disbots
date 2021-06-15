from datetime import datetime
from typing import Optional, List

from odmantic import AIOEngine, Model, Field, EmbeddedModel
from odmantic.query import QueryExpression

from configuration import DEFAULT_PREFIX

engine = AIOEngine(database='mongo_giveaway_bot')


class Giveaway(EmbeddedModel):
    prize: str                                 # what the giveaway is
    creator_id: int                            # the id of the person who made the giveaway
    channel_id: int                            # the channel where the giveaway message is sent to
    message_id: int                            # the message ID of the giveaway
    created_at: datetime                       # when it was created
    finishes_at: datetime                      # this on will be set by the user on creation
    finished_on: Optional[datetime] = None     # this will be set upon actually ending
    cancelled: int = 0                         # 0=not cancelled, 1=unreachable, 2=No participants, 3=admin cancelled
    winners: List[int] = []                    # non-existent until the giveaway ends
    participants: List[int] = []               # the list of participants in the giveaway
    max_winners: int = Field(default=1, ge=1)  # defaults to 1, maximum 10 minimum 1

    class Config:
        collection = 'giveaways'

    @classmethod
    def query(cls, message_id) -> QueryExpression:
        return cls.message_id == message_id


class GuildConfig(Model):
    guild_id: int                      # important for us to relocate our data
    prefix: str = DEFAULT_PREFIX       # the prefix for the server
    giveaways: List[Giveaway] = []     # this will hold all of our giveaways
    giveaway_count: int = 0            # a count of how many giveaways have been created in the server

    class Config:
        collection = 'guild_configs'

    @classmethod
    def query(cls, guild_id) -> QueryExpression:
        return cls.guild_id == guild_id






