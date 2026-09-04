from datetime import date

from src.edtech_listing import CourseListing, ListingReport, publish_listing


class FakeClient:
    def upload(self, image: bytes, filename: str) -> str:
        assert image and filename.endswith(".jpg")
        return "uploaded-1"

    def background_remove(self, image_id: str) -> dict[str, str]:
        assert image_id == "uploaded-1"
        return {"id": "cutout-1"}


def test_expired_deadline_is_reported_closed():
    listing = CourseListing("Algebra", "Dr. Lee", date(2026, 9, 1), b"pixels")
    report = publish_listing(listing, FakeClient(), today=date(2026, 9, 2))
    assert report == ListingReport("Algebra", "Dr. Lee", "closed", "cutout-1", "2026-09-01")
