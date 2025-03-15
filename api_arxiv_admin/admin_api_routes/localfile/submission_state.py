import os
import re

FTP_DIR = "/ftp"


def arxiv_is_pending(paper_id: str) -> bool:
    """Check if the paper is in a pending state based on file existence and permissions."""

    match = re.match(r"(\d{4})\.\d{4,5}", paper_id)
    if match:
        yrmo = match.group(1)
        absfile = os.path.join(FTP_DIR, "arxiv", "papers", yrmo, f"{paper_id}.abs")
    else:
        try:
            archive, papernum = paper_id.split("/")
            yrmo = papernum[:4]
            absfile = os.path.join(FTP_DIR, archive, "papers", yrmo, f"{papernum}.abs")
        except ValueError:
            return False  # Invalid paper ID format

    # If file doesn't exist, return False
    if not os.path.exists(absfile):
        return False

    # Check file permissions
    file_stats = os.stat(absfile)
    public_read = bool(file_stats.st_mode & 0o004)  # Checking if "others" have read permission

    return not public_read
