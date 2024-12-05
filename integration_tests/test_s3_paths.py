from pathvein.lib import (
    ScanResult,
    ShuffleResult,
    scan,
    shuffle_to,
)
from pathvein.pattern import FileStructurePattern
from tests import ephemeral_s3_bucket

S3_CONFIG = {
    "key": "minioadmin",
    "secret": "minioadmin",
    "endpoint_url": "http://localhost:9000",
}


def test_scan_s3():
    with ephemeral_s3_bucket(**S3_CONFIG) as bucket:
        assert bucket.exists()
        dirname = "dir"
        filename = "file.txt"
        pattern = FileStructurePattern(dirname, files=[filename])
        file = bucket / dirname / filename
        match = file.parent
        file.write_text("Hello World!")
        assert file.exists()
        result = scan(bucket, [pattern])
        assert isinstance(result, set)
        assert all(isinstance(r, ScanResult) for r in result)
        assert len(result) == 1
        assert result == {ScanResult(match, pattern)}


def test_shuffle_s3():
    with ephemeral_s3_bucket(**S3_CONFIG) as bucket:
        assert bucket.exists()
        dirname = "dir"
        filename = "file.txt"
        pattern = FileStructurePattern(dirname, files=[filename])
        file = bucket / dirname / filename
        match = file.parent
        destination = bucket / "destination"
        assert not destination.exists()
        file.write_text("Hello World!")
        assert file.exists()
        scan_result = scan(bucket, [pattern])
        result = shuffle_to(scan_result, destination)
        assert isinstance(result, list)
        assert all(isinstance(r, ShuffleResult) for r in result)
        assert len(result) == 1
        assert result == [ShuffleResult(match, destination / dirname, pattern)]
