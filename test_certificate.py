
from certificate import generate_certificate

file_path = generate_certificate(
    certificate_id="test001",
    recipient_name="Ravela Buela",
    event_name="Python Workshop",
    issue_date="2026-10-09"
)

print("Certificate created:", file_path)