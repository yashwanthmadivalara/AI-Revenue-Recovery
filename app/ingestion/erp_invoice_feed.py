import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from app.schemas.events import IngestionEvent

logger = logging.getLogger(__name__)


class ERPInvoiceFeedParser:
    """Parses ERP (NetSuite, QuickBooks, SAP) overdue AR reports into standardized IngestionEvents."""

    @staticmethod
    def parse_invoice_record(record: Dict[str, Any], erp_source: str = "netsuite") -> Optional[IngestionEvent]:
        try:
            invoice_id = record.get("invoice_id") or record.get("id") or "INV-UNKNOWN"
            customer_id = record.get("customer_id") or record.get("entity_id") or "ERP-CUST"
            customer_name = record.get("customer_name") or record.get("company_name") or "Corporate Account"
            customer_email = record.get("billing_email") or record.get("email") or "ap@corporate.com"
            customer_phone = record.get("phone") or record.get("billing_phone")

            amount = float(record.get("balance_due", 0.0) or record.get("amount_due", 0.0) or record.get("amount", 0.0))
            currency = (record.get("currency") or "USD").upper()
            days_overdue = int(record.get("days_overdue", 0))

            # Determine event_type
            if days_overdue >= 90:
                event_type = "invoice.aged_90_plus"
            elif days_overdue >= 60:
                event_type = "invoice.aged_60"
            elif days_overdue >= 30:
                event_type = "invoice.aged_30"
            else:
                event_type = "invoice.overdue"

            return IngestionEvent(
                source=erp_source,
                event_type=event_type,
                customer_id=customer_id,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                amount=amount,
                currency=currency,
                days_overdue=days_overdue,
                metadata={
                    "invoice_id": invoice_id,
                    "due_date": record.get("due_date"),
                    "terms": record.get("terms", "Net 30"),
                    "po_number": record.get("po_number"),
                    "sales_rep": record.get("sales_rep")
                }
            )
        except Exception as ex:
            logger.error(f"Error parsing ERP invoice record: {ex}")
            return None

    @classmethod
    def parse_batch_feed(cls, records: List[Dict[str, Any]], erp_source: str = "netsuite") -> List[IngestionEvent]:
        events = []
        for r in records:
            event = cls.parse_invoice_record(r, erp_source=erp_source)
            if event:
                events.append(event)
        return events
