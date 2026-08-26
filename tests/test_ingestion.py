import pytest
from app.ingestion.stripe_webhook import StripeWebhookParser
from app.ingestion.razorpay_webhook import RazorpayWebhookParser
from app.ingestion.chargebee_webhook import ChargebeeWebhookParser
from app.ingestion.erp_invoice_feed import ERPInvoiceFeedParser


def test_stripe_webhook_parsing():
    payload = {
        "type": "payment_intent.payment_failed",
        "data": {
            "object": {
                "id": "pi_12345",
                "customer": "cus_9999",
                "amount": 25000,
                "currency": "usd",
                "receipt_email": "jane@acme.com",
                "billing_details": {"name": "Jane Doe"},
                "last_payment_error": {
                    "code": "insufficient_funds",
                    "message": "Your card has insufficient funds."
                }
            }
        }
    }
    event = StripeWebhookParser.parse_event(payload)
    assert event is not None
    assert event.source == "stripe"
    assert event.customer_id == "cus_9999"
    assert event.amount == 250.00
    assert event.currency == "USD"
    assert event.decline_code == "insufficient_funds"


def test_razorpay_webhook_parsing():
    payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_9876",
                    "amount": 499900,
                    "currency": "INR",
                    "email": "amit@startup.in",
                    "contact": "+919876543210",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_reason": "payment_failed"
                }
            }
        }
    }
    event = RazorpayWebhookParser.parse_event(payload)
    assert event is not None
    assert event.source == "razorpay"
    assert event.amount == 4999.00
    assert event.currency == "INR"


def test_chargebee_webhook_parsing():
    payload = {
        "event_type": "payment_failed",
        "content": {
            "invoice": {
                "id": "inv_cb_55",
                "amount_due": 15000,
                "currency_code": "USD",
                "customer_id": "cust_cb_10"
            },
            "customer": {
                "id": "cust_cb_10",
                "email": "user@chargebee.test",
                "first_name": "Alan",
                "last_name": "Turing"
            },
            "transaction": {
                "error_code": "card_declined"
            }
        }
    }
    event = ChargebeeWebhookParser.parse_event(payload)
    assert event is not None
    assert event.source == "chargebee"
    assert event.amount == 150.00
    assert event.customer_name == "Alan Turing"


def test_erp_invoice_feed_parsing():
    batch = [
        {
            "invoice_id": "INV-2024-001",
            "customer_id": "CUST-NETSUITE-42",
            "customer_name": "Global Logistics Corp",
            "billing_email": "ap@globallogistics.com",
            "amount_due": 7500.00,
            "currency": "USD",
            "days_overdue": 65,
            "due_date": "2024-06-15"
        }
    ]
    events = ERPInvoiceFeedParser.parse_batch_feed(batch, erp_source="netsuite")
    assert len(events) == 1
    assert events[0].source == "netsuite"
    assert events[0].event_type == "invoice.aged_60"
    assert events[0].amount == 7500.00
    assert events[0].days_overdue == 65
