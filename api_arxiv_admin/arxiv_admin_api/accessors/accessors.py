"""File accessor classes that abstracts the storage and path for each file type."""
# The number of classes here are a bit too many. Having a class for each file type is not a good
# design. There is a room for redesign.

import os.path
import shutil
import typing
import urllib.parse
from abc import abstractmethod
from pathlib import Path
from typing import Any, BinaryIO, TextIO
from logging import getLogger

# from typing_extensions import TypedDict
from arxiv.identifier import Identifier as arXivID
from google.cloud import storage as cloud_storage
from google.cloud.storage.fileio import BlobReader, BlobWriter

from .path_mapper import (
    arxiv_id_to_local_orig,
    arxiv_id_to_local_paper,
    arxiv_id_to_local_pdf_path,
    local_path_to_blob_key,
)

logger = getLogger(__name__)


def make_subpath(path_str: str) -> str:
    """Make a subpath from a path string. If the path string starts with /, remove it."""
    return path_str[1:] if path_str.startswith("/") else path_str


# noinspection Pylint
class ArxivIdentified:
    """Thing identified by arXiv ID."""

    identifier: arXivID

    def __init__(self, identifier: arXivID, **_kwargs: typing.Any):
        self.identifier = identifier
        pass


class AccessorFlavor(ArxivIdentified):
    """Accessor flavor is a mix-in for access."""

    root_dir: str | None

    def __init__(self, identifier: arXivID, **kwargs: typing.Any):
        self.root_dir = kwargs.pop("root_dir", None)
        super().__init__(identifier, **kwargs)
        pass

    @property
    def local_path(self) -> str:
        """Tarball filename from arXiv ID."""
        return ""

    @property
    def blob_name(self) -> str | None:
        """Turn webnode path to GCP blob name."""
        return local_path_to_blob_key(self.local_path)

    @property
    def flavor(self) -> str:
        return ""

    pass


class BaseAccessor(AccessorFlavor):
    """Abstract class for accessing files from GCP and local file system."""

    @abstractmethod
    async def exists(self) -> bool:
        """Return True if the file exists in the storage."""
        raise NotImplementedError("Not implemented")

    @abstractmethod
    async def download_to_filename(self, filename: str = "unnamed.bin") -> None:
        """Download the file to the local file system."""
        raise NotImplementedError("Not implemented")

    @abstractmethod
    async def upload_from_filename(self, filename: str = "unnamed.bin") -> None:
        """Upload the file to the storage."""
        raise NotImplementedError("Not implemented")

    @abstractmethod
    async def download_as_bytes(self, **kwargs: typing.Any) -> bytes:
        """Download the file as bytes."""
        raise NotImplementedError("Not implemented")

    @abstractmethod
    async def upload_from_stream(self, fd: Any) -> None:
        """Upload the file to the storage."""
        raise NotImplementedError("Not implemented")

    @property
    @abstractmethod
    def canonical_name(self) -> str:
        """Canonical name - URI."""
        raise NotImplementedError("Not implemented")

    @property
    def content_type(self) -> str | None:
        """MIME type of the file, mostly for uploading to GCP."""
        return None

    @abstractmethod
    def open(self, **kwargs: typing.Any) -> BlobReader | BinaryIO | TextIO | BlobWriter:
        """Open the srorage (file or GCP blob) and return the file-ish object."""
        raise NotImplementedError("Not implemented")

    @property
    async def bytesize(self) -> int | None:
        """Object byte size, if applicable."""
        return None

    @property
    @abstractmethod
    def basename(self) -> str:
        """Base name of the file."""
        raise NotImplementedError("Not implemented")

    pass


# noinspection Pylint
class GCPStorage:
    """GCP storage client and bucket."""

    client: cloud_storage.Client
    bucket_name: str
    bucket: cloud_storage.Bucket

    def __init__(self, client: cloud_storage.Client, bucket_name: str):
        self.client = client
        self.bucket_name = bucket_name
        self.bucket = self.client.bucket(self.bucket_name)


class GCPBlobAccessor(BaseAccessor):
    """GCP Blob accessor for a given arXiv ID. This is an abstract class.

    You need to implement to_blob_name property in the subclass.
    """

    gcp_storage: GCPStorage
    blob: cloud_storage.Blob
    timeout: int

    def __init__(self, identifier: arXivID, **kwargs: typing.Any):
        self.gcp_storage = kwargs.pop("storage")
        self.timeout = kwargs.pop("timeout", 300)
        super().__init__(identifier, **kwargs)
        if self.blob_name is None:
            raise ValueError("blob_name is None")
        self.blob = self.bucket.blob(self.blob_name)

    async def download_to_filename(self, filename: str = "unnamed.bin") -> None:
        self.blob.download_to_filename(filename)

    async def upload_from_filename(self, filename: str = "unnamed.bin") -> None:
        logger.debug(f"upload_from_filename: {filename} to {self.blob_name} with timeout {self.timeout}")
        self.blob.upload_from_filename(filename, content_type=self.content_type, timeout=self.timeout)

    async def download_as_bytes(self, **kwargs: typing.Any) -> bytes:
        return self.blob.download_as_bytes(**kwargs)  # type: ignore

    async def upload_from_stream(self, fd: Any) -> None:
        """Upload the file to the storage."""
        return self.blob.upload_from_file(fd)


    @property
    def bucket(self) -> cloud_storage.Bucket:
        """GCP bucket."""
        return self.gcp_storage.bucket

    async def exists(self) -> bool:
        return self.blob.exists(client=self.gcp_storage.client)  # type: ignore

    @property
    def basename(self) -> str:
        if self.blob_name is None:
            raise ValueError("blob_name is None")
        return os.path.basename(urllib.parse.urlparse(self.blob_name).path)

    @property
    def canonical_name(self) -> str:
        return f"gs://{self.gcp_storage.bucket_name}/{self.blob_name}"

    def open(self, **kwargs: Any) -> BlobReader | BinaryIO | TextIO | BlobWriter:
        mode = kwargs.pop("mode", "rb")  # the default mode is read binary
        return self.blob.open(mode=mode)

    @property
    async def bytesize(self) -> int | None:
        if self.blob.exists(client=self.gcp_storage.client):
            self.blob.reload()
            return self.blob.size  # type: ignore
        return None


class LocalFileAccessor(BaseAccessor):
    """Local file accessor for a given arXiv ID. This is an abstract class."""

    def __init__(self, identifier: arXivID, **kwargs: Any):
        super().__init__(identifier, **kwargs)
        pass

    async def download_to_filename(self, filename: str = "unnamed.bin") -> None:
        local_path = self.local_path
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        shutil.copyfile(self.local_path, filename)

    async def upload_from_filename(self, filename: str = "unnamed.bin") -> None:
        local_path = self.local_path
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        shutil.copyfile(filename, local_path)

    async def download_as_bytes(self, **kwargs: Any) -> bytes:
        with open(self.local_path, "rb") as fd:
            return bytes(fd.read())

    async def upload_from_stream(self, fd_from: Any, chunk_size: int = 65536) -> None:
        """Upload the file to the storage with chunked streaming."""
        with open(self.local_path, "wb") as fd_to:
            while chunk := fd_from.read(chunk_size):
                fd_to.write(chunk)

    async def exists(self) -> bool:
        return Path(self.local_path).exists()

    @property
    def basename(self) -> str:
        return os.path.basename(self.local_path)

    @property
    def canonical_name(self) -> str:
        return f"file://{self.local_path}"

    def open(self, **kwargs: typing.Any) -> BlobReader | BinaryIO | TextIO | BlobWriter:
        mode: str = kwargs.pop("mode", "rb")
        return open(self.local_path, mode=mode)

    @property
    async def bytesize(self) -> int | None:
        po = Path(self.local_path)
        if po.exists():
            return po.stat().st_size
        return None

    @property
    def blob_name(self) -> str | None:
        return None

    pass


def merge_path(root_dir: str | None, local_path: str) -> str:
    """Merge root_dir and local_path."""
    if root_dir:
        return os.path.join(root_dir, make_subpath(local_path))
    return local_path


class VersionedFlavor(AccessorFlavor):
    """Versioned flavor needs to look at two places to decide the path.

    If it is latest, it is in arxiv_id_to_local_paper() (aka under /ftp), and else  arxiv_id_to_local_orig()
    (aka under /data/orig).
    """

    def __init__(self, arxiv_id: arXivID, **kwargs: typing.Any):
        latest = kwargs.pop("latest", None)
        if latest is None:
            raise ValueError("latest is not set. It must be True or False.")
        self.path_mapper = arxiv_id_to_local_paper if latest else arxiv_id_to_local_orig
        super().__init__(arxiv_id, **kwargs)
        pass

    @property
    def flavor(self) -> str:
        return ""


class TarballFlavor(VersionedFlavor):
    """Tarball flavor."""

    @property
    def local_path(self) -> str:
        """Tarball filename from arXiv ID."""
        return merge_path(self.root_dir, self.path_mapper(self.identifier, extent=".tar.gz"))

    @property
    def flavor(self) -> str:
        return "tarball"

    pass


class AbsFlavor(VersionedFlavor):
    """GCP abstract text blob accessor for a given arXiv ID."""

    @property
    def local_path(self) -> str:
        return merge_path(self.root_dir, self.path_mapper(self.identifier, extent=".abs"))

    @property
    def flavor(self) -> str:
        return "abs"

    pass


class PDFFlavor(AccessorFlavor):
    """GCP PDF blob accessor for a given arXiv ID."""

    @property
    def local_path(self) -> str:
        return merge_path(self.root_dir, arxiv_id_to_local_pdf_path(self.identifier))

    @property
    def flavor(self) -> str:
        return "pdf"

    pass


class OutcomeFlavor(AccessorFlavor):
    """GCP pdfgen outcome blob accessor for a given arXiv ID.

    Outcome blob is a tarball containing the output files from running pdflatex except actual PDF.
    """

    @property
    def local_path(self) -> str:
        # If outcome is at webnode, this is where it would be - next to the PDF.
        return merge_path(self.root_dir, arxiv_id_to_local_pdf_path(self.identifier, extent=".outcome.tar.gz"))

    @property
    def flavor(self) -> str:
        return "outcome"

    pass


class LocalTarballAccessor(LocalFileAccessor, TarballFlavor):
    """Local tarball accessor for a given arXiv ID."""


class LocalPDFAccessor(LocalFileAccessor, PDFFlavor):
    """Local PDF accessor for a given arXiv ID."""


class LocalAbsAccessor(LocalFileAccessor, AbsFlavor):
    """Local abstract text accessor for a given arXiv ID."""


class LocalOutcomeAccessor(LocalFileAccessor, OutcomeFlavor):
    """Local outcome accessor for a given arXiv ID."""


class GCPTarballAccessor(GCPBlobAccessor, TarballFlavor):
    """GCP tarball accessor for a given arXiv ID."""


class GCPPDFAccessor(GCPBlobAccessor, PDFFlavor):
    """GCP PDF accessor for a given arXiv ID."""


class GCPAbsAccessor(GCPBlobAccessor, AbsFlavor):
    """GCP abstract text accessor for a given arXiv ID."""
    pass


class GCPOutcomeAccessor(GCPBlobAccessor, OutcomeFlavor):
    """GCP outcome accessor for a given arXiv ID."""
    pass


class LocalPathAccessor(BaseAccessor):
    path: Path

    def __init__(self, identifier: arXivID, **kwargs: typing.Any):
        self.path = kwargs.pop("path")
        if not isinstance(self.path, Path):
            raise ValueError(f"path must be a Path object, not {type(self.path)}")
        super().__init__(identifier, **kwargs)

    async def exists(self) -> bool:
        """Return True if the file exists in the storage."""
        return self.path.exists()

    async def download_to_filename(self, filename: str = "unnamed.bin") -> None:
        """Download the file to the local file system."""
        with self.path.open("rb") as fd_from:
            with open(filename, "wb") as fd_to:
                shutil.copyfileobj(fd_from, fd_to)

    async def upload_from_filename(self, filename: str = "unnamed.bin") -> None:
        """Upload the file to the storage."""
        with open(filename, "rb") as fd_from:
            with self.path.open("wb") as fd_to:
                shutil.copyfileobj(fd_from, fd_to)

    async def download_as_bytes(self, **kwargs: typing.Any) -> bytes:
        """Download the file as bytes."""
        with open(self.path, "rb") as fd_from:
            return bytes(fd_from.read())

    async def upload_from_stream(self, fd_from: Any) -> None:
        """Upload the file to the storage."""
        with open(self.path, "wb") as fd_to:
            shutil.copyfileobj(fd_from, fd_to)

    @property
    def canonical_name(self) -> str:
        """Canonical name - URI."""
        return f"file://{self.path}"

    @property
    def content_type(self) -> str | None:
        """MIME type of the file, mostly for uploading to GCP."""
        return None

    def open(self, **kwargs: typing.Any) -> BlobReader | BinaryIO | TextIO | BlobWriter:
        """Open the srorage (file or GCP blob) and return the file-ish object."""
        return self.path.open(**kwargs)

    @property
    async def bytesize(self) -> int | None:
        """Object byte size, if applicable."""
        return self.path.stat().st_size

    @property
    def basename(self) -> str:
        """Base name of the file."""
        return os.path.basename(self.path.name)

    @property
    def local_path(self) -> str:
        """Tarball filename from arXiv ID."""
        return self.path.as_posix()

    @property
    def flavor(self) -> str:
        return "binary"


class GCPPathAccessor(GCPBlobAccessor):
    path: Path

    def __init__(self, identifier: arXivID, **kwargs: typing.Any):
        self.identifier = identifier
        self.root_dir = kwargs.pop("root_dir", None)
        self.gcp_storage = kwargs.pop("storage")
        self.timeout = kwargs.pop("timeout", 300)
        self.path = kwargs.pop("path")
        if not isinstance(self.path, Path):
            raise ValueError(f"path must be a Path object, not {type(self.path)}")

        if self.blob_name is None:
            raise ValueError("blob_name is None")
        self.blob = self.bucket.blob(self.blob_name)


    @property
    def blob_name(self) -> str | None:
        """Turn webnode path to GCP blob name."""
        return local_path_to_blob_key(self.local_path)

    @property
    def local_path(self) -> str:
        """Tarball filename from arXiv ID."""
        return self.path.as_posix()

    @property
    def flavor(self) -> str:
        return "binary"

    pass

