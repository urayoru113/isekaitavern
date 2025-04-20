import dataclasses
import typing

import dacite


@dataclasses.dataclass
class MusicInfo:
    title: str
    stream_url: str
    url: str
    description: str

    to_dict = dataclasses.asdict

    @classmethod
    def from_dict(cls, data: dict[str, typing.Any]) -> typing.Self:
        return dacite.from_dict(data_class=cls, data=data)
