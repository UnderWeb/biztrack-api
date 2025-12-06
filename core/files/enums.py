from enum import Enum


class S3ACL(str, Enum):
    PRIVATE = "private"
    PUBLIC_READ = "public-read"
    SYSTEM = "private"


class FileTypeValidation(Enum):
    IMAGE = "image"
    DOCUMENT = "document"
    ANY = "any"
