from dataclasses import dataclass


@dataclass
class ModVersion:
    name: str
    zip_name: str
    download_url: str


def make_mod() -> ModVersion:
    """在这个文件里定义并实例化 ModVersion。"""
    return ModVersion(
        name="跳蚤市场快速出售 v1.2.0",
        zip_name="FastSell-1.2.0.zip",
        download_url="https://example.com/FastSell-1.2.0.zip",
    )
