from pathlib import Path
from urllib.parse import quote
import re
import xml.etree.ElementTree as ET
import zipfile

import httpx


BUCKET_URL = "https://s3.amazonaws.com/tripdata"

S3_NAMESPACE = {
    "s3": "http://s3.amazonaws.com/doc/2006-03-01/"
}

ARCHIVE_PATTERN = re.compile(
    r"^(?P<period>\d{6}).*citibike-tripdata.*\.zip$",
    re.IGNORECASE,
)


def _list_objects(prefix: str = "") -> list[str]:
    """
    List object keys from the public Citi Bike S3 bucket.
    Handles S3 pagination automatically.
    """

    keys: list[str] = []
    continuation_token: str | None = None

    with httpx.Client(
        follow_redirects=True,
        timeout=60.0,
    ) as client:
        while True:
            params = {
                "list-type": "2",
                "prefix": prefix,
            }

            if continuation_token:
                params["continuation-token"] = continuation_token

            response = client.get(
                BUCKET_URL,
                params=params,
            )

            response.raise_for_status()

            root = ET.fromstring(response.content)

            for key_element in root.findall(
                "s3:Contents/s3:Key",
                S3_NAMESPACE,
            ):
                if key_element.text:
                    keys.append(key_element.text)

            is_truncated = (
                root.findtext(
                    "s3:IsTruncated",
                    default="false",
                    namespaces=S3_NAMESPACE,
                )
                .lower()
                == "true"
            )

            if not is_truncated:
                break

            continuation_token = root.findtext(
                "s3:NextContinuationToken",
                namespaces=S3_NAMESPACE,
            )

            if not continuation_token:
                raise RuntimeError(
                    "S3 response says more data exists "
                    "but no continuation token was returned."
                )

    return keys


def _extract_period(key: str) -> str | None:
    """
    Extract YYYYMM from a Citi Bike archive key.
    """

    filename = key.rsplit("/", 1)[-1]

    match = ARCHIVE_PATTERN.match(filename)

    if not match:
        return None

    return match.group("period")


def discover_archive(
    year: int,
    month: int,
) -> tuple[str, str]:
    """
    Find the requested Citi Bike monthly archive.

    If the requested month is not available yet,
    automatically fall back to the latest available
    month before it.

    Returns:
        (s3_key, actual_period)
    """

    requested_period = f"{year}{month:02d}"

    print(
        f"Looking for Citi Bike data: "
        f"{requested_period}"
    )

    # First try the exact month.
    exact_keys = _list_objects(
        prefix=requested_period
    )

    exact_candidates: list[str] = []

    for key in exact_keys:
        period = _extract_period(key)

        if period == requested_period:
            exact_candidates.append(key)

    if exact_candidates:
        selected_key = sorted(exact_candidates)[0]

        print(
            f"Found exact archive: {selected_key}"
        )

        return selected_key, requested_period

    print(
        f"No archive found for {requested_period}."
    )
    print(
        "Searching for latest available month..."
    )

    # Search current year first.
    candidate_keys = _list_objects(
        prefix=str(year)
    )

    candidates: list[tuple[str, str]] = []

    for key in candidate_keys:
        period = _extract_period(key)

        if (
            period is not None
            and period <= requested_period
        ):
            candidates.append(
                (period, key)
            )

    # Extremely defensive fallback:
    # search the whole bucket if current year
    # contains nothing usable.
    if not candidates:
        print(
            "No usable archive found in requested year."
        )
        print(
            "Searching full Citi Bike archive..."
        )

        all_keys = _list_objects()

        for key in all_keys:
            period = _extract_period(key)

            if (
                period is not None
                and period <= requested_period
            ):
                candidates.append(
                    (period, key)
                )

    if not candidates:
        raise FileNotFoundError(
            "Could not find any Citi Bike trip "
            f"archive up to {requested_period}."
        )

    actual_period, selected_key = max(
        candidates,
        key=lambda item: item[0],
    )

    print(
        f"Using latest available archive: "
        f"{selected_key}"
    )

    return selected_key, actual_period


def download_month(
    year: int,
    month: int,
    output_dir: Path,
) -> tuple[Path, str]:
    """
    Discover and download Citi Bike monthly data.
    """

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    key, actual_period = discover_archive(
        year=year,
        month=month,
    )

    filename = key.rsplit("/", 1)[-1]

    output_path = output_dir / filename

    if output_path.exists():
        print(
            f"Archive already exists: {output_path}"
        )

        return output_path, actual_period

    encoded_key = quote(
        key,
        safe="/",
    )

    download_url = (
        f"{BUCKET_URL}/{encoded_key}"
    )

    print(
        f"Downloading: {download_url}"
    )

    with httpx.stream(
        "GET",
        download_url,
        follow_redirects=True,
        timeout=180.0,
    ) as response:
        response.raise_for_status()

        total_bytes = 0

        with output_path.open("wb") as file:
            for chunk in response.iter_bytes():
                file.write(chunk)
                total_bytes += len(chunk)

    size_mb = total_bytes / (1024 * 1024)

    print(
        f"Saved: {output_path}"
    )
    print(
        f"Archive size: {size_mb:.2f} MB"
    )

    return output_path, actual_period


def extract_zip(
    zip_path: Path,
    output_dir: Path,
) -> list[Path]:
    """
    Extract all CSV files from a Citi Bike archive.
    """

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        f"Extracting: {zip_path.name}"
    )

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:
        archive.extractall(output_dir)

    csv_files = sorted(
        output_dir.rglob("*.csv")
    )

    if not csv_files:
        raise RuntimeError(
            f"No CSV files found inside {zip_path}"
        )

    print(
        f"Extracted {len(csv_files)} CSV file(s)"
    )

    for csv_file in csv_files:
        size_mb = (
            csv_file.stat().st_size
            / (1024 * 1024)
        )

        print(
            f"  - {csv_file.name} "
            f"({size_mb:.2f} MB)"
        )

    return csv_files