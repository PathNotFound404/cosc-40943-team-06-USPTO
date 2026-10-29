"""Failures that refuse a whole file. A single bad record is a rejected record, not one of these."""

from patent_intelligence.errors import AppError


class UnsupportedFileError(AppError):
    """The file is not in a layout the application reads (UC-FEAT-decompile-files 3a)."""

    def __init__(self, file_name: str, detail: str) -> None:
        super().__init__(
            f"{file_name} is not a supported weekly file: {detail}. The application reads "
            "USPTO office action files with one JSON record per line. Nothing was imported."
        )
        self.file_name = file_name


class LayoutMismatchError(AppError):
    """The file's field names differ from the expected layout (3a, QS-changed-layout-refused)."""

    def __init__(self, file_name: str, missing: list[str], unexpected: list[str]) -> None:
        parts = []
        if missing:
            parts.append("missing " + ", ".join(missing))
        if unexpected:
            parts.append("unexpected " + ", ".join(unexpected))
        super().__init__(
            f"{file_name} does not have the expected fields ({'; '.join(parts)}). "
            "The USPTO may have changed the file layout. Nothing was imported."
        )
        self.file_name = file_name
        self.missing = missing
        self.unexpected = unexpected


class UnreadableFileError(AppError):
    """The file is damaged or incomplete (4a, QS-corrupt-file-reported)."""

    def __init__(self, file_name: str, line_number: int | None) -> None:
        where = f"line {line_number} is not a complete record" if line_number else "it is damaged"
        super().__init__(
            f"{file_name} could not be read: {where}. The file may be damaged or only partly "
            "downloaded. Nothing was imported."
        )
        self.file_name = file_name
        self.line_number = line_number
